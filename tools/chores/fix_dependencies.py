# Copyright 2026 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Audit (and optionally fix) the root ament_package() of every vendored package.

For every vendored package (workspace/vendor/<pkg>+/), this checks that the
root BUILD.bazel declares exactly one

    ament_package(
        name = "ament_package",
        package_xml = "package.xml",
        deps = [
            "@<dep>//:ament_package",   # one per RCR dependency
            ...
        ],
    )

whose `@<dep>//:ament_package` deps are exactly the bazel_deps listed in the
"# RCR Dependencies" block of the package's MODULE.bazel: missing ones are
added, ones for modules the package doesn't depend on (which fail with "No
repository visible as '@<dep>'") are removed, and any other deps (headers,
local targets, ...) are left alone. A missing ament_package() is created.
Packages with no root BUILD.bazel at all (not yet packaged for Bazel) are only
reported, unless --create-missing-root is given.

Bazel forbids cycles between targets even though cycles between modules are
fine, so before sweeping, the wanted edges of *every* vendored package are
planned globally: edges are accepted in order of how "real" they are (declared
as a build/exec dependency in package.xml first, then test/doc-only, then not
in package.xml at all), and an edge that would close a cycle is dropped and
reported as a warning. Edges to vendored packages that have no root
BUILD.bazel (so no ament_package target) are dropped too.

Packages are walked breadth-first over their package.xml dependency graph on a
thread pool, exactly like fix_interfaces.

Scope: this only ever reads and writes the vendored sources under
workspace/vendor/<pkg>+/. It never touches modules/; roll fixes up with
create_patch.

Usage (from the repo root):

    bazel run //tools/chores:fix_dependencies                 # report only
    bazel run //tools/chores:fix_dependencies -- --fix        # rewrite BUILDs
    bazel run //tools/chores:fix_dependencies -- --fix tf2_ros rclcpp
"""

import ast
import collections
import dataclasses
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import AbstractSet, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from tools.chores.vendor_lib import (
    AMENT_DEFS,
    AMENT_LOAD,
    COPYRIGHT_HEADER,
    SEVERITY_MANUAL,
    SEVERITY_WARNING,
    FileCheck,
    Issue,
    PackageAuditor,
    PackageResult,
    Reporter,
    ament_package_labels,
    call_name,
    find_buildifier,
    format_list,
    load_packages,
    make_parser,
    parse_rcr_deps,
    render_ament_package,
    replace_node_span,
    run_sweep,
    sort_labels,
    str_list,
)

# Per-package change categories: RCR ament_package deps added / removed.
STAT_ADDED = "added"
STAT_REMOVED = "removed"
STAT_KEYS = (STAT_ADDED, STAT_REMOVED)

AMENT_PACKAGE = "ament_package"
_AMENT_LABEL_RE = re.compile(r"^@([A-Za-z0-9_.\-]+)//:ament_package$")
_REPO_SHORTHAND_RE = re.compile(r"^@([A-Za-z0-9_.\-]+)$")


def canonical_label(label: str) -> str:
    """Expand buildifier's `@repo` shorthand to `@repo//:repo`."""
    m = _REPO_SHORTHAND_RE.match(label)
    return f"@{m.group(1)}//:{m.group(1)}" if m else label


@dataclasses.dataclass
class DependencyResult(PackageResult):
    rcr_count: int = 0

    def details(self) -> List[str]:
        return [f"{self.rcr_count} RCR deps"]


### PURE HELPERS: EDGE PLANNING

# Edge priorities: lower is kept in preference when edges form a cycle.
PRIORITY_RUNTIME = 0  # build/exec/run/buildtool/export dependency in package.xml
PRIORITY_TEST = 1  # only a test_depend/doc_depend in package.xml
PRIORITY_EXTRA = 2  # not in package.xml at all (e.g. a synthetic tooling dep)
_TEST_TAGS = ("test_depend", "doc_depend")
_RUNTIME_TAGS = ("build_depend", "build_export_depend", "buildtool_depend", "buildtool_export_depend",
                 "depend", "exec_depend", "run_depend")


def dep_priorities(package_xml_text: str) -> Dict[str, int]:
    """Map each package.xml dependency to its PRIORITY_* (the best tag it appears under)."""
    root = ET.fromstring(package_xml_text)
    out: Dict[str, int] = {}
    for tags, prio in ((_TEST_TAGS, PRIORITY_TEST), (_RUNTIME_TAGS, PRIORITY_RUNTIME)):
        for tag in tags:
            for el in root.findall(tag):
                name = (el.text or "").strip()
                if name:
                    out[name] = prio
    return out


def _reaches(graph: Mapping[str, Iterable[str]], src: str, dst: str) -> bool:
    """Whether `dst` is reachable from `src` in `graph` (iterative DFS)."""
    if src == dst:
        return True
    seen, stack = {src}, [src]
    while stack:
        for nxt in graph.get(stack.pop(), ()):
            if nxt == dst:
                return True
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return False


def plan_edges(wanted: Mapping[str, Iterable[str]],
               priority: Callable[[str, str], int]) -> Dict[str, Set[str]]:
    """
    Choose an acyclic subset of the `wanted` package -> dep edges. Edges are
    accepted greedily in (priority(pkg, dep), pkg, dep) order and an edge is
    rejected if `dep` can already reach `pkg`. Returns the rejected edges as
    {pkg: {dep, ...}}; only deps that are themselves keys of `wanted` can ever
    be part of a cycle, so edges to anything else are always accepted.
    """
    edges = sorted((priority(pkg, dep), pkg, dep)
                   for pkg, deps in wanted.items() for dep in set(deps) if dep in wanted)
    accepted: Dict[str, Set[str]] = collections.defaultdict(set)
    blocked: Dict[str, Set[str]] = collections.defaultdict(set)
    for _, pkg, dep in edges:
        if _reaches(accepted, dep, pkg):
            blocked[pkg].add(dep)
        else:
            accepted[pkg].add(dep)
    return dict(blocked)


### PURE HELPERS: BUILD FILES


def render_root_build(want: Sequence[str]) -> str:
    """A brand-new root BUILD.bazel holding just the ament_package()."""
    return "\n\n".join([
        COPYRIGHT_HEADER.rstrip("\n"),
        AMENT_LOAD,
        'package(default_visibility = ["//visibility:public"])',
        "### PACKAGING",
        render_ament_package(want),
    ]) + "\n"


def ensure_ament_load(text: str, tree: ast.Module) -> Optional[str]:
    """`text` with ament_package loaded from @rosdistro//ament:defs.bzl, or None if that can't be done safely."""
    loads = [s for s in tree.body if call_name(s) == "load"]
    for stmt in loads:
        call = stmt.value
        if not (call.args and isinstance(call.args[0], ast.Constant) and call.args[0].value == AMENT_DEFS):
            continue
        symbols = call.args[1:]
        if not all(isinstance(a, ast.Constant) and isinstance(a.value, str) for a in symbols):
            return None
        names = [a.value for a in symbols]
        if AMENT_PACKAGE in names or any(kw.value.value == AMENT_PACKAGE for kw in call.keywords
                                         if isinstance(kw.value, ast.Constant)):
            return text
        parts = [f'"{AMENT_DEFS}"'] + [f'"{n}"' for n in sorted(names + [AMENT_PACKAGE])]
        parts += [ast.get_source_segment(text, kw) for kw in call.keywords]
        return replace_node_span(text, stmt, f"load({', '.join(parts)})")
    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    if loads:
        pos, insert = loads[-1].end_lineno, AMENT_LOAD + "\n"
    elif tree.body:
        pos, insert = tree.body[0].lineno - 1, AMENT_LOAD + "\n\n"
    else:
        pos, insert = len(lines), ("\n" if lines else "") + AMENT_LOAD + "\n"
    lines[pos:pos] = [insert]
    return "".join(lines)


def _render_call(text: str, call: ast.Call, deps: Sequence[str]) -> str:
    """ament_package(...) with name/package_xml/deps canonicalised and every other attribute kept verbatim."""
    out = ["ament_package("]
    seen = set()
    for kw in call.keywords:
        seen.add(kw.arg)
        if kw.arg == "name":
            out.append(f'    name = "{AMENT_PACKAGE}",')
        elif kw.arg == "deps":
            out.append(f"    deps = {format_list(sort_labels(deps), '    ')},")
        else:
            out.append(f"    {kw.arg} = {ast.get_source_segment(text, kw.value)},")
    if "name" not in seen:
        out.insert(1, f'    name = "{AMENT_PACKAGE}",')
    if "package_xml" not in seen:
        out.insert(2, '    package_xml = "package.xml",')
    if "deps" not in seen:
        out.append(f"    deps = {format_list(sort_labels(deps), '    ')},")
    return "\n".join(out + [")"])


def check_ament_package(text: Optional[str], want: Sequence[str]) -> FileCheck:
    """
    Check the root BUILD.bazel's ament_package() lists exactly `want` as its
    `@<dep>//:ament_package` deps (other deps are left alone). `text` is
    None if the file doesn't exist.
    """
    want = sorted(set(want))
    stats: collections.Counter = collections.Counter()
    if text is None:
        stats[STAT_ADDED] = len(want)
        return FileCheck([("missing-root-build", "BUILD.bazel does not exist")], render_root_build(want), stats=stats)
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        return FileCheck([("unparseable", f"BUILD.bazel: {e}")], None, "unparseable BUILD file")

    calls = [s for s in tree.body if call_name(s) == AMENT_PACKAGE]
    if len(calls) > 1:
        return FileCheck([("multiple-ament-package", f"BUILD.bazel declares {len(calls)} ament_package() targets")],
                         None, "merge the ament_package() targets by hand")
    if not calls:
        stats[STAT_ADDED] = len(want)
        problems = [("no-ament-package", "BUILD.bazel has no ament_package(...) target")]
        new_text = ensure_ament_load(text, tree)
        if new_text is None:
            return FileCheck(problems, None, f"add ament_package to the {AMENT_DEFS} load by hand", stats=stats)
        new_text = new_text.rstrip("\n") + "\n\n### PACKAGING\n\n" + render_ament_package(want) + "\n"
        return FileCheck(problems, new_text, stats=stats)

    stmt = calls[0]
    call = stmt.value
    if call.args or any(kw.arg is None for kw in call.keywords):
        return FileCheck([("unexpected-args", "BUILD.bazel ament_package() has positional or **kwargs arguments")],
                         None, "ament_package() has positional or **kwargs arguments")
    kwargs = {kw.arg: kw.value for kw in call.keywords}
    problems: List[Tuple[str, str]] = []
    name = kwargs.get("name")
    if not (isinstance(name, ast.Constant) and name.value == AMENT_PACKAGE):
        shown = ast.get_source_segment(text, name) if name is not None else "<none>"
        problems.append(("wrong-name", f'BUILD.bazel ament_package() has name = {shown}, expected "{AMENT_PACKAGE}"'))
    if "package_xml" not in kwargs:
        problems.append(("no-package-xml", "BUILD.bazel ament_package() has no package_xml"))

    have = str_list(kwargs["deps"]) if "deps" in kwargs else []
    if have is None:
        return FileCheck(problems + [("deps-not-literal", "BUILD.bazel ament_package(deps=...) is not a literal list")],
                         None, "ament_package() deps is not a literal list")
    canonical = {d: canonical_label(d) for d in have}
    ament_have = {canonical[d] for d in have if _AMENT_LABEL_RE.match(canonical[d])}
    missing = sorted(set(want) - ament_have)
    stale = sorted(ament_have - set(want))
    if missing:
        problems.append(("missing-deps", f"BUILD.bazel ament_package() is missing {missing}"))
        stats[STAT_ADDED] = len(missing)
    if stale:
        problems.append(("stale-deps", f"BUILD.bazel ament_package() depends on modules not in MODULE.bazel: {stale}"))
        stats[STAT_REMOVED] = len(stale)
    if not problems:
        return FileCheck([], None)
    deps = [d for d in have if canonical[d] not in ament_have] + want
    if "deps" in kwargs and all(code in ("missing-deps", "stale-deps") for code, _ in problems):
        # Only the list changes: swap it in place, keeping comments elsewhere in the call.
        line = text.splitlines()[kwargs["deps"].lineno - 1]
        indent = line[: len(line) - len(line.lstrip())]
        return FileCheck(problems, replace_node_span(text, kwargs["deps"], format_list(sort_labels(deps), indent)),
                         stats=stats)
    return FileCheck(problems, replace_node_span(text, stmt, _render_call(text, call, deps)), stats=stats)


### WORKSPACE LAYER


class DependencyAuditor(PackageAuditor):
    """Audits (and optionally fixes) one package's root ament_package() at a time; thread-safe."""

    result_type = DependencyResult

    def __init__(self, packages: Mapping[str, Path], fix: bool, buildifier: Optional[str],
                 create_missing_root: bool = False,
                 cyclic: Optional[Mapping[str, AbstractSet[str]]] = None,
                 unpackaged: AbstractSet[str] = frozenset()):
        super().__init__(packages, fix, buildifier)
        self.create_missing_root = create_missing_root
        self.cyclic = cyclic or {}  # pkg -> deps dropped to keep the target graph acyclic
        self.unpackaged = unpackaged  # vendored packages with no @pkg//:ament_package target

    def _audit(self, package: str, result: DependencyResult) -> None:
        pkg_dir = self.packages[package]
        module_path = pkg_dir / "MODULE.bazel"
        if not module_path.is_file():
            result.issues.append(Issue(SEVERITY_MANUAL, "no-module", "MODULE.bazel", "does not exist"))
            return
        rcr = parse_rcr_deps(module_path.read_text())
        if rcr is None:
            result.issues.append(Issue(SEVERITY_MANUAL, "no-rcr-block", "MODULE.bazel",
                                       'has no "# RCR Dependencies" block to mirror'))
            return
        root_path = pkg_dir / "BUILD.bazel"
        if not root_path.is_file() and not self.create_missing_root:
            # Not yet packaged for Bazel at all (e.g. freshly bootstrapped):
            # an ament_package()-only BUILD would export nothing, so don't
            # pretend. Use --create-missing-root to generate one anyway.
            result.rcr_count = len(ament_package_labels(rcr, package))
            result.issues.append(Issue(SEVERITY_WARNING, "unpackaged", "BUILD.bazel",
                                       "does not exist (package has no Bazel build yet)"))
            return
        cyclic = sorted(set(rcr) & set(self.cyclic.get(package, ())))
        unpackaged = sorted(d for d in set(rcr) - set(cyclic) if d in self.unpackaged and d != package)
        if cyclic:
            result.issues.append(Issue(SEVERITY_WARNING, "cycle", "BUILD.bazel",
                                       f"not depending on {cyclic}: they (transitively) depend back on {package}"))
        if unpackaged:
            result.issues.append(Issue(SEVERITY_WARNING, "unpackaged-dep", "BUILD.bazel",
                                       f"not depending on {unpackaged}: they have no root BUILD.bazel yet"))
        want = ament_package_labels(set(rcr) - set(cyclic) - set(unpackaged), package)
        result.rcr_count = len(want)
        text = root_path.read_text() if root_path.is_file() else None
        self._apply(result, root_path, "BUILD.bazel", check_ament_package(text, want))


def plan_package_edges(packages: Mapping[str, Path], unpackaged: AbstractSet[str]) -> Dict[str, Set[str]]:
    """plan_edges() over every vendored package's MODULE.bazel RCR deps (see the module docstring)."""
    wanted: Dict[str, Set[str]] = {}
    priorities: Dict[str, Dict[str, int]] = {}
    for pkg, pkg_dir in packages.items():
        if pkg in unpackaged:
            continue  # never gets an ament_package target, so can't be on a cycle
        module_path, xml_path = pkg_dir / "MODULE.bazel", pkg_dir / "package.xml"
        rcr = parse_rcr_deps(module_path.read_text()) if module_path.is_file() else None
        wanted[pkg] = {d for d in rcr or () if d != pkg and d not in unpackaged}
        try:
            priorities[pkg] = dep_priorities(xml_path.read_text()) if xml_path.is_file() else {}
        except ET.ParseError:
            priorities[pkg] = {}
    return plan_edges(wanted, lambda pkg, dep: priorities[pkg].get(dep, PRIORITY_EXTRA))


### MAIN


def main() -> None:
    parser = make_parser(__doc__)
    parser.add_argument("--create-missing-root", action="store_true",
                        help="Generate an ament_package()-only root BUILD.bazel for packages that have none")
    args = parser.parse_args()
    vendor_dir, packages = load_packages(parser, args)
    selected = args.packages or sorted(packages)
    buildifier = find_buildifier(args)
    unpackaged = set() if args.create_missing_root else {
        p for p, d in packages.items() if not (d / "BUILD.bazel").is_file()}
    cyclic = plan_package_edges(packages, unpackaged)
    print(f"Auditing ament_package() deps of {len(selected)} package(s) under {vendor_dir} "
          f"with {args.jobs} thread(s){' (fixing)' if args.fix else ''}...", file=sys.stderr)
    auditor = DependencyAuditor(packages, fix=args.fix, buildifier=buildifier,
                                create_missing_root=args.create_missing_root,
                                cyclic=cyclic, unpackaged=unpackaged)
    reporter = Reporter(len(selected), progress=not args.no_progress, verbose=args.verbose, fix=args.fix,
                        title="Dependency audit", stat_keys=STAT_KEYS, stat_noun="ament_package deps")
    sys.exit(run_sweep(packages, selected, auditor, reporter, args.jobs))


if __name__ == "__main__":
    main()

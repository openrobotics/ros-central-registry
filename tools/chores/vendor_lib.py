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
Shared plumbing for the tools/chores sweeps over a vendored workspace
(workspace/vendor/<pkg>+/): result types, package.xml / MODULE.bazel helpers,
a threaded BFS scheduler over the package dependency graph, status reporting
(tqdm), guarded in-place writes and the common command line.

Every sweep only ever reads and writes the vendored sources under
workspace/vendor/<pkg>+/; it never touches modules/ (roll fixes up with
create_patch).
"""

import argparse
import ast
import collections
import concurrent.futures
import dataclasses
import os
import re
import shutil
import subprocess
import sys
import threading
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover - tqdm is a declared dep; degrade gracefully.
    tqdm = None


### CONSTANTS

PACKAGE_XML_DEPEND_TAGS = (
    "build_depend", "build_export_depend", "buildtool_depend",
    "buildtool_export_depend", "depend", "doc_depend", "exec_depend",
    "run_depend", "test_depend",
)

SEVERITY_FIXABLE = "fixable"
SEVERITY_MANUAL = "manual"
SEVERITY_WARNING = "warning"

COPYRIGHT_HEADER = """\
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

RCR_DEPS_HEADER = "# RCR Dependencies"
AMENT_DEFS = "@rosdistro//ament:defs.bzl"
AMENT_LOAD = f'load("{AMENT_DEFS}", "ament_package")'


### RESULT TYPES


@dataclasses.dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    where: str
    message: str


@dataclasses.dataclass
class FileCheck:
    problems: List[Tuple[str, str]]  # (code, message)
    fixed_text: Optional[str]  # None => can't (or needn't) fix automatically
    manual_reason: Optional[str] = None
    stats: collections.Counter = dataclasses.field(default_factory=collections.Counter)


@dataclasses.dataclass
class PackageResult:
    package: str
    issues: List[Issue] = dataclasses.field(default_factory=list)
    fixed_files: List[str] = dataclasses.field(default_factory=list)
    stats: collections.Counter = dataclasses.field(default_factory=collections.Counter)
    # Fixes queued by PackageAuditor._apply() until the package is committed:
    # (path, where, fixed text, check).
    pending: List[Tuple[Path, str, str, "FileCheck"]] = dataclasses.field(
        default_factory=list, repr=False, compare=False)

    @property
    def status(self) -> str:
        severities = {i.severity for i in self.issues}
        if SEVERITY_MANUAL in severities:
            return "manual"
        if SEVERITY_FIXABLE in severities:
            return "needs-fix"
        if self.fixed_files:
            return "fixed"
        return "clean"

    def details(self) -> List[str]:
        """Tool-specific leading details for the per-package status line."""
        return []


### PURE HELPERS: PACKAGE.XML


def parse_package_xml(text: str) -> Tuple[str, Set[str], Optional[str]]:
    """(name, declared dependency names, first license string)."""
    root = ET.fromstring(text)
    name = (root.findtext("name") or "").strip()
    deps = {
        (el.text or "").strip()
        for tag in PACKAGE_XML_DEPEND_TAGS
        for el in root.findall(tag)
        if (el.text or "").strip()
    }
    license_text = root.findtext("license")
    return name, deps, license_text.strip() if license_text else None


_XML_DEPEND_LINE_RE = re.compile(r"^(\s*)<(%s)(\s[^>]*)?>" % "|".join(PACKAGE_XML_DEPEND_TAGS))


def add_package_xml_depends(text: str, deps: Iterable[str]) -> str:
    """
    Add `<depend>dep</depend>` lines to a package.xml with a minimal textual
    edit (so the resulting upstream patch is tiny): right after the last
    existing <depend> line, else after the last *_depend line, else before
    <export>/</package>. Raises ValueError if the result isn't valid XML.
    """
    _, declared, _ = parse_package_xml(text)
    new = sorted(set(deps) - declared)
    if not new:
        return text
    lines = text.splitlines(keepends=True)
    newline = "\r\n" if lines and lines[0].endswith("\r\n") else "\n"
    matches = [(i, m) for i, line in enumerate(lines) if (m := _XML_DEPEND_LINE_RE.match(line))]
    plain = [(i, m) for i, m in matches if m.group(2) == "depend"]
    export = next((i for i, line in enumerate(lines) if re.match(r"\s*(<export\b|</package>)", line)), None)
    if plain or matches:
        i, m = (plain or matches)[-1]
        pos, indent = i + 1, m.group(1)
    elif export is not None:
        pos, indent = export, "  "
    else:  # No line-anchored tags to hang off (e.g. a one-line package.xml).
        end = text.rfind("</package>")
        if end < 0:
            raise ValueError("package.xml has no </package>")
        out = text[:end] + "".join(f"<depend>{d}</depend>" for d in new) + text[end:]
        ET.fromstring(out)
        return out
    if pos > 0 and not lines[pos - 1].endswith("\n"):
        lines[pos - 1] += newline
    lines[pos:pos] = [f"{indent}<depend>{d}</depend>{newline}" for d in new]
    out = "".join(lines)
    try:
        ET.fromstring(out)
    except ET.ParseError as e:
        raise ValueError(f"adding <depend>s produced invalid package.xml: {e}") from e
    return out


### PURE HELPERS: MODULE.BAZEL


_MODULE_VERSION_RE = re.compile(r'\bmodule\((?:[^()]|\([^()]*\))*?\bversion\s*=\s*"([^"]+)"', re.DOTALL)
_BAZEL_DEP_LINE_RE = re.compile(r'^bazel_dep\(\s*name\s*=\s*"([^"]+)"')


def parse_module_bazel_deps(text: str) -> Set[str]:
    return set(re.findall(r'bazel_dep\(\s*name\s*=\s*"([^"]+)"', text))


def parse_module_version(text: str) -> Optional[str]:
    """The version declared by a MODULE.bazel's module() call."""
    m = _MODULE_VERSION_RE.search(text)
    return m.group(1) if m else None


def _rcr_block(lines: Sequence[str]) -> Optional[Tuple[int, int]]:
    """[start, end) line span of the bazel_deps under "# RCR Dependencies", or None."""
    header = next((i for i, line in enumerate(lines) if line.strip() == RCR_DEPS_HEADER), None)
    if header is None:
        return None
    end = header + 1
    while end < len(lines) and _BAZEL_DEP_LINE_RE.match(lines[end]):
        end += 1
    return header + 1, end


def parse_rcr_deps(text: str) -> Optional[List[str]]:
    """Sorted names of the bazel_deps in the "# RCR Dependencies" block, or None if there's no block."""
    lines = text.splitlines()
    span = _rcr_block(lines)
    if span is None:
        return None
    return sorted({_BAZEL_DEP_LINE_RE.match(line).group(1) for line in lines[span[0]:span[1]]})


def add_bazel_deps(text: str, deps: Mapping[str, str]) -> str:
    """
    Add `bazel_dep(name = <name>, version = <version>)` lines for `deps` to a
    package MODULE.bazel, merged (sorted by name) into its "# RCR Dependencies"
    block. If there's no such block, one is started after the last bazel_dep
    (or at the end of the file). Deps that are already declared are skipped.
    """
    existing = parse_module_bazel_deps(text)
    new_lines = {n: f'bazel_dep(name = "{n}", version = "{v}")' for n, v in deps.items() if n not in existing}
    if not new_lines:
        return text
    lines = text.splitlines()
    span = _rcr_block(lines)
    if span is not None:
        start, end = span
        block = {_BAZEL_DEP_LINE_RE.match(line).group(1): line for line in lines[start:end]}
        block.update(new_lines)
        lines[start:end] = [block[n] for n in sorted(block)]
    else:
        last = max((i for i, line in enumerate(lines) if _BAZEL_DEP_LINE_RE.match(line)), default=len(lines) - 1)
        lines[last + 1:last + 1] = ["", RCR_DEPS_HEADER] + [new_lines[n] for n in sorted(new_lines)]
    return "\n".join(lines) + "\n"


def ament_package_labels(rcr_deps: Iterable[str], package: str) -> List[str]:
    """`@<dep>//:ament_package` for every RCR dependency (except the package itself)."""
    return sorted({f"@{d}//:ament_package" for d in rcr_deps if d != package})


### PURE HELPERS: STARLARK


def _label_sort_key(label: str) -> Tuple[int, str]:
    if label.startswith(":"):
        return (0, label)
    if label.startswith("//"):
        return (1, label)
    return (2, label)


def sort_labels(labels: Iterable[str]) -> List[str]:
    """Deduplicated labels: local (:x), then //pkg, then @repo, each sorted."""
    return sorted(set(labels), key=_label_sort_key)


def str_list(node: ast.AST) -> Optional[List[str]]:
    """The value of a literal list of strings, else None."""
    if isinstance(node, ast.List) and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in node.elts):
        return [e.value for e in node.elts]
    return None


def call_name(stmt: ast.stmt) -> Optional[str]:
    """`foo` for a top-level `foo(...)` statement, else None."""
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name):
        return stmt.value.func.id
    return None


def replace_node_span(text: str, node: ast.AST, replacement: str) -> str:
    data = text.encode("utf-8")
    line_starts = [0]
    for line in data.splitlines(keepends=True):
        line_starts.append(line_starts[-1] + len(line))
    start = line_starts[node.lineno - 1] + node.col_offset
    end = line_starts[node.end_lineno - 1] + node.end_col_offset
    return (data[:start] + replacement.encode("utf-8") + data[end:]).decode("utf-8")


def format_list(labels: Sequence[str], indent: str) -> str:
    if not labels:
        return "[]"
    return "[\n" + "".join(f'{indent}    "{label}",\n' for label in labels) + f"{indent}]"


def render_ament_package(deps: Sequence[str]) -> str:
    """The canonical root `ament_package(...)` call."""
    return "\n".join([
        "ament_package(",
        '    name = "ament_package",',
        '    package_xml = "package.xml",',
        f"    deps = {format_list(sort_labels(deps), '    ')},",
        ")",
    ])


### PURE HELPERS: BFS SCHEDULING


def _graph_maps(graph: Mapping[str, Iterable[str]]):
    nodes = set(graph)
    deps = {n: (set(graph[n]) & nodes) - {n} for n in nodes}
    rdeps: Dict[str, Set[str]] = collections.defaultdict(set)
    for n, ds in deps.items():
        for d in ds:
            rdeps[d].add(n)
    indeg = {n: len(ds) for n, ds in deps.items()}
    return nodes, rdeps, indeg


def _release_cycle(nodes: Set[str], done: Set[str], busy: Set[str], indeg: Dict[str, int]) -> List[str]:
    """
    Break a dependency cycle by releasing the single least-blocked remaining
    node (ties broken by name). Releasing just one keeps nodes that merely
    depend on the cycle waiting until the cycle itself is done.
    """
    remaining = nodes - done - busy
    return [min(remaining, key=lambda n: (indeg[n], n))]


def dependency_levels(graph: Mapping[str, Iterable[str]]) -> List[List[str]]:
    """
    BFS (Kahn) levels over `graph` (node -> its dependencies): every node
    appears after all of its dependencies. Cycles are broken by releasing the
    least-blocked remaining node.
    """
    nodes, rdeps, indeg = _graph_maps(graph)
    done: Set[str] = set()
    levels: List[List[str]] = []
    level = sorted(n for n in nodes if indeg[n] == 0)
    while len(done) < len(nodes):
        if not level:
            level = _release_cycle(nodes, done, set(), indeg)
        levels.append(level)
        done.update(level)
        nxt: Set[str] = set()
        for n in level:
            for r in rdeps[n]:
                if r in done:
                    continue
                indeg[r] -= 1
                if indeg[r] == 0:
                    nxt.add(r)
        level = sorted(nxt)
    return levels


def run_bfs(
    graph: Mapping[str, Iterable[str]],
    work: Callable[[str], object],
    jobs: int,
    on_done: Callable[[str, object], None],
    on_progress: Optional[Callable[[int, int, int], None]] = None,
) -> Dict[str, object]:
    """
    Non-blocking BFS over `graph` on a thread pool: each node is submitted as
    soon as all of its dependencies have completed. `on_done` runs on the
    calling thread as each node completes; `on_progress(running, done,
    remaining)` runs on the calling thread whenever those counts change
    (`remaining` excludes nodes currently running). `work` must not raise.
    """
    nodes, rdeps, indeg = _graph_maps(graph)
    done: Set[str] = set()
    results: Dict[str, object] = {}
    ready = collections.deque(sorted(n for n in nodes if indeg[n] == 0))

    def progress(pending: Mapping[concurrent.futures.Future, str]) -> None:
        if on_progress is not None:
            on_progress(len(pending), len(done), len(nodes) - len(done) - len(pending))

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        pending: Dict[concurrent.futures.Future, str] = {}
        while len(done) < len(nodes):
            busy = set(pending.values())
            while ready:
                n = ready.popleft()
                if n in done or n in busy:
                    continue
                pending[pool.submit(work, n)] = n
                busy.add(n)
            if not pending:
                ready.extend(_release_cycle(nodes, done, busy, indeg))
                continue
            progress(pending)
            finished, _ = concurrent.futures.wait(pending, return_when=concurrent.futures.FIRST_COMPLETED)
            for fut in finished:
                n = pending.pop(fut)
                done.add(n)
                results[n] = fut.result()
                progress(pending)
                on_done(n, results[n])
                for r in rdeps[n]:
                    if r in done:
                        continue
                    indeg[r] -= 1
                    if indeg[r] == 0:
                        ready.append(r)
    return results


### WORKSPACE LAYER


def discover_packages(vendor_dir: Path) -> Dict[str, Path]:
    """Vendored ROS packages: <vendor>/<name>+/ directories with a package.xml."""
    packages = {}
    for entry in sorted(vendor_dir.iterdir()):
        if entry.is_symlink() or not entry.is_dir() or not entry.name.endswith("+"):
            continue
        if (entry / "package.xml").is_file():
            packages[entry.name[:-1]] = entry
    return packages


def build_graph(packages: Mapping[str, Path], selected: Iterable[str]) -> Dict[str, Set[str]]:
    """package -> its package.xml deps, restricted to the selected packages."""
    selected = set(selected)
    graph: Dict[str, Set[str]] = {}
    for name in selected:
        try:
            _, deps, _ = parse_package_xml((packages[name] / "package.xml").read_text())
        except (ET.ParseError, OSError):
            deps = set()
        graph[name] = deps & selected
    return graph


class PackageAuditor:
    """
    Base class for a per-package audit/fix pass; thread-safe. Subclasses
    implement `_audit(package, result)` and record problems through
    `_apply()`, which writes fixes (with --fix) or turns them into issues.
    """

    result_type = PackageResult

    def __init__(self, packages: Mapping[str, Path], fix: bool, buildifier: Optional[str]):
        self.packages = packages
        self.fix = fix
        self.buildifier = buildifier
        self._versions: Dict[str, Optional[str]] = {}
        self._lock = threading.Lock()

    def module_version(self, package: str) -> Optional[str]:
        """The version of `package` vendored into this workspace, or None."""
        if package not in self.packages:
            return None
        with self._lock:
            if package in self._versions:
                return self._versions[package]
        path = self.packages[package] / "MODULE.bazel"
        version = parse_module_version(path.read_text()) if path.is_file() else None
        with self._lock:
            self._versions[package] = version
        return version

    def audit(self, package: str) -> PackageResult:
        result = self.result_type(package)
        try:
            self._audit(package, result)
            self._commit(result)
            self._format(package, result)
        except Exception as e:  # Keep the pool alive; surface as a manual issue.
            result.issues.append(Issue(SEVERITY_MANUAL, "error", package, f"{type(e).__name__}: {e}"))
        return result

    def _audit(self, package: str, result: PackageResult) -> None:
        raise NotImplementedError

    def _format(self, package: str, result: PackageResult) -> None:
        """Run buildifier over any Starlark files this pass rewrote."""
        starlark = [str(self.packages[package] / p) for p in result.fixed_files if p.endswith((".bazel", ".bzl"))]
        if starlark and self.buildifier:
            subprocess.run([self.buildifier, "-mode", "fix", *starlark], check=False, capture_output=True)

    def _apply(self, result: PackageResult, path: Path, where: str, check: FileCheck) -> None:
        """
        Record `check` for `path`. Fixable problems are queued and written by
        `_commit()` once the whole package has been audited; anything else
        becomes an issue straight away.
        """
        if not check.problems:
            return
        result.stats.update(check.stats)
        if self.fix and check.fixed_text is not None:
            result.pending.append((path, where, check.fixed_text, check))
            return
        severity = SEVERITY_FIXABLE if check.fixed_text is not None else SEVERITY_MANUAL
        for code, message in check.problems:
            result.issues.append(Issue(severity, code, where, message))
        if check.manual_reason:
            result.issues.append(Issue(SEVERITY_MANUAL, "manual", where, check.manual_reason))

    def _commit(self, result: PackageResult) -> None:
        """
        Write every queued fix, all or nothing: if the package has any manual
        issue we don't fully understand it, so leave every file untouched and
        report the would-be fixes instead.
        """
        pending, result.pending = result.pending, []
        if any(i.severity == SEVERITY_MANUAL for i in result.issues):
            for _, where, _, check in pending:
                for code, message in check.problems:
                    result.issues.append(Issue(SEVERITY_FIXABLE, code, where,
                                               f"{message} (not written: package needs manual fixes first)"))
            return
        pkg_root = self.packages[result.package].resolve()
        for path, where, text, _ in pending:
            target = path.resolve()
            if not target.is_relative_to(pkg_root):
                raise ValueError(f"refusing to write {target}: outside vendored package {pkg_root}")
        for path, where, text, _ in pending:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(f".{path.name}.chores.tmp")
            tmp.write_text(text)
            os.replace(tmp, path)
            result.fixed_files.append(where)


### STATUS REPORTING


STATUS_ICONS = {"clean": "✔", "fixed": "✎", "needs-fix": "✘", "manual": "✘"}
STATUS_VERBS = {"clean": "clean", "fixed": "fixed", "needs-fix": "needs fix", "manual": "manual fix needed"}


def format_stats(stats: Mapping[str, int], keys: Sequence[str]) -> str:
    """e.g. '1 old, 3 new, 2 buggy'."""
    return ", ".join(f"{stats.get(k, 0)} {k}" for k in keys)


def format_package_line(package: str, result: PackageResult, stat_keys: Sequence[str]) -> str:
    """e.g. '✎ fixed sensor_msgs (1 old, 3 new, 2 buggy) [40 default interfaces; rewrote msg/BUILD.bazel]'."""
    status = result.status
    line = f"{STATUS_ICONS[status]} {STATUS_VERBS[status]} {package} ({format_stats(result.stats, stat_keys)})"
    details = list(result.details())
    if result.fixed_files:
        details.append("rewrote " + ", ".join(result.fixed_files))
    issues = [i for i in result.issues if i.severity != SEVERITY_WARNING]
    if issues:
        details.append(f"{len(issues)} open issue(s)")
    warnings = len(result.issues) - len(issues)
    if warnings:
        details.append(f"{warnings} warning(s)")
    return f"{line} [{'; '.join(details)}]" if details else line


def format_progress(running: int, done: int, remaining: int) -> str:
    """'Currently processing 32 packages (67 done, 128 remain)'."""
    noun = "package" if running == 1 else "packages"
    return f"Currently processing {running} {noun} ({done} done, {remaining} remain)"


class Reporter:
    """Live per-package status lines plus a global progress bar and summary."""

    def __init__(self, total: int, progress: bool, verbose: bool, fix: bool,
                 title: str, stat_keys: Sequence[str], stat_noun: str):
        self.total = total
        self.verbose = verbose
        self.fix = fix
        self.title = title
        self.stat_keys = tuple(stat_keys)
        self.stat_noun = stat_noun
        self.counts: collections.Counter = collections.Counter()
        self.codes: collections.Counter = collections.Counter()
        self.stats: collections.Counter = collections.Counter()
        self.status = format_progress(0, 0, total)
        self.bar = None
        if progress and tqdm is not None:
            self.bar = tqdm(total=total, unit="pkg", desc=self.status, dynamic_ncols=True, file=sys.stderr,
                            bar_format="{desc} |{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]{postfix}")

    def write(self, line: str) -> None:
        if self.bar is not None:
            self.bar.write(line)
        else:
            print(line, flush=True)

    def progress(self, running: int, done: int, remaining: int) -> None:
        self.status = format_progress(running, done, remaining)
        if self.bar is not None:
            self.bar.set_description_str(self.status, refresh=True)

    def done(self, package: str, result: PackageResult) -> None:
        status = result.status
        self.counts[status] += 1
        self.stats.update(result.stats)
        for issue in result.issues:
            self.codes[(issue.severity, issue.code)] += 1
        warnings = [i for i in result.issues if i.severity == SEVERITY_WARNING]
        problems = [i for i in result.issues if i.severity != SEVERITY_WARNING]

        if status != "clean" or self.verbose:
            line = format_package_line(package, result, self.stat_keys)
            if self.bar is None:
                # No live status bar: prefix the global status instead.
                line = f"[{self.status}] {line}"
            self.write(line)
            for issue in problems + (warnings if self.verbose or status != "clean" else []):
                self.write(f"    [{issue.severity}:{issue.code}] {issue.where}: {issue.message}")

        if self.bar is not None:
            self.bar.update(1)
            self.bar.set_postfix(clean=self.counts["clean"], fixed=self.counts["fixed"],
                                 todo=self.counts["needs-fix"] + self.counts["manual"])

    def headline(self) -> str:
        return f"{self.title}: {sum(self.counts.values())} packages"

    def summary(self) -> str:
        if self.bar is not None:
            self.bar.close()
        verb = "changed" if self.fix else "to change"
        lines = [
            "",
            self.headline(),
            f"  {self.stat_noun} {verb}: {format_stats(self.stats, self.stat_keys)}",
            f"  clean:      {self.counts['clean']}",
            f"  fixed:      {self.counts['fixed']}",
            f"  needs fix:  {self.counts['needs-fix']}" + ("" if self.fix else "  (re-run with --fix)"),
            f"  manual:     {self.counts['manual']}",
        ]
        if self.codes:
            lines.append("  issues by category:")
            for (severity, code), n in sorted(self.codes.items(), key=lambda kv: (-kv[1], kv[0])):
                lines.append(f"    {n:5d}  {severity}:{code}")
        return "\n".join(lines)


### COMMAND LINE


def make_parser(description: str) -> argparse.ArgumentParser:
    """The command line shared by every sweep."""
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("packages", nargs="*", help="Only audit these packages (default: all vendored packages)")
    parser.add_argument("--vendor-dir", type=Path, default=None,
                        help="Vendor directory (default: <repo>/workspace/vendor)")
    parser.add_argument("--fix", action="store_true", help="Rewrite files in place where possible")
    parser.add_argument("--jobs", "-j", type=int, default=min(32, (os.cpu_count() or 4) * 2),
                        help="Worker threads")
    parser.add_argument("--no-buildifier", action="store_true", help="Don't run buildifier on rewritten files")
    parser.add_argument("--no-progress", action="store_true", help="Disable the progress bar")
    parser.add_argument("--verbose", "-v", action="store_true", help="Also list clean packages and warnings")
    return parser


def load_packages(parser: argparse.ArgumentParser, args: argparse.Namespace) -> Tuple[Path, Dict[str, Path]]:
    """(vendor dir, all vendored packages); exits via parser.error on bad input."""
    repo_root = Path(os.environ.get("BUILD_WORKSPACE_DIRECTORY", ".")).resolve()
    vendor_dir = (args.vendor_dir or repo_root / "workspace" / "vendor").resolve()
    if not vendor_dir.is_dir():
        parser.error(f"{vendor_dir} does not exist; run //tools/ci:setup_workspace and //tools/ci:vendor_modules first")
    packages = discover_packages(vendor_dir)
    unknown = sorted(set(args.packages) - set(packages))
    if unknown:
        parser.error(f"not vendored: {', '.join(unknown)}")
    return vendor_dir, packages


def find_buildifier(args: argparse.Namespace) -> Optional[str]:
    if args.no_buildifier:
        return None
    buildifier = shutil.which("buildifier")
    if args.fix and buildifier is None:
        print("warning: buildifier not found on PATH; rewritten files won't be formatted", file=sys.stderr)
    return buildifier


def run_sweep(packages: Mapping[str, Path], selected: Sequence[str], auditor: PackageAuditor,
              reporter: Reporter, jobs: int) -> int:
    """BFS over `selected` (package.xml order); prints the summary; returns an exit code."""
    run_bfs(build_graph(packages, selected), auditor.audit, jobs, reporter.done, on_progress=reporter.progress)
    print(reporter.summary())
    return 1 if reporter.counts["needs-fix"] or reporter.counts["manual"] else 0

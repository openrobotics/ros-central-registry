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
Audit (and optionally fix) ROS interface declarations in a vendored workspace.

For every vendored package (workspace/vendor/<pkg>+/) that ships interface
files, this:

  1. finds every .msg / .srv / .action / .idl file the package builds (the
     rosidl_generate_interfaces() list in CMakeLists.txt, falling back to a
     recursive scan of msg/, srv/ and action/);
  2. decides whether the package uses rosidl_core_generators or
     rosidl_default_generators (from its package.xml);
  3. scans every interface file for non-builtin field types (and #includes,
     for .idl files) to work out which other interfaces it depends on;
  4. checks that one BUILD.bazel per interface directory declares every
     interface with the right macro, src and deps, and that the root
     BUILD.bazel's core_generators()/default_generators() lists every one;
  5. adds dependencies missing from the package's MODULE.bazel (at the
     version vendored in this workspace) and package.xml, and reports types
     that don't resolve.

Packages are walked breadth-first over their package.xml dependency graph and
processed on a thread pool: a package is scheduled as soon as all of its
dependencies have finished, so dependencies are always audited (and fixed)
before the packages that depend on them.

Scope: this only ever reads and writes the vendored sources under
workspace/vendor/<pkg>+/ (whatever version setup_workspace/vendor_modules
resolved). It never touches modules/; roll fixes up with create_patch.

Usage (from the repo root):

    bazel run //tools/chores:fix_interfaces                 # report only
    bazel run //tools/chores:fix_interfaces -- --fix        # rewrite BUILDs
    bazel run //tools/chores:fix_interfaces -- --fix sensor_msgs nav_msgs
"""

import ast
import collections
import dataclasses
import posixpath
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from tools.chores.vendor_lib import (
    AMENT_LOAD,
    COPYRIGHT_HEADER,
    SEVERITY_MANUAL,
    SEVERITY_WARNING,
    FileCheck,
    Issue,
    PackageAuditor,
    PackageResult,
    Reporter,
    add_bazel_deps,
    add_package_xml_depends,
    ament_package_labels,
    call_name,
    find_buildifier,
    format_list,
    load_packages,
    make_parser,
    parse_module_bazel_deps,
    parse_package_xml,
    parse_rcr_deps,
    render_ament_package,
    replace_node_span,
    run_sweep,
    sort_labels,
    str_list,
)


### CONSTANTS

INTERFACE_KINDS = ("msg", "srv", "action")

KIND_EXTENSIONS = {
    "msg": (".msg", ".idl"),
    "srv": (".srv", ".idl"),
    "action": (".action", ".idl"),
}

# Mirrors rosidl_adapter.parser.PRIMITIVE_TYPES (minus time/duration, which
# rosidl_adapter maps onto builtin_interfaces messages).
PRIMITIVE_TYPES = frozenset([
    "bool", "byte", "char", "float32", "float64", "int8", "uint8", "int16",
    "uint16", "int32", "uint32", "int64", "uint64", "string", "wstring",
])
BUILTIN_TIME_TYPES = {"time": "Time", "duration": "Duration"}

CORE = "core"
DEFAULT = "default"
GENERATOR_PACKAGES = {CORE: "rosidl_core_generators", DEFAULT: "rosidl_default_generators"}
GENERATOR_FUNCTIONS = {CORE: "core_generators", DEFAULT: "default_generators"}
INTERFACE_MACROS = frozenset(["ros_interface", "ros_message", "ros_service", "ros_action", "ros_idl"])

# package.xml <license> strings are free-form. license_kind() normalises them
# (lowercase, drop "license"/"licence"/"version", punctuation -> nothing) and
# looks the result up here. Covers every spelling seen in lyrical.
LICENSE_KINDS = {
    "apache": "Apache-2.0",
    "apache2": "Apache-2.0",
    "apache20": "Apache-2.0",
    "alv2": "Apache-2.0",
    "bsd": "BSD-3-Clause",
    "bsd20": "BSD-3-Clause",  # ROS' historical "BSD License 2.0" is 3-clause.
    "bsd3": "BSD-3-Clause",
    "bsd3clause": "BSD-3-Clause",
    "bsdclause3": "BSD-3-Clause",
    "3clausebsd": "BSD-3-Clause",
    "bsd2": "BSD-2-Clause",
    "bsd2clause": "BSD-2-Clause",
    "mit": "MIT",
    "mit0": "MIT-0",
    "bsl10": "BSL-1.0",
    "mpl20": "MPL-2.0",
    "mpl11": "MPL-1.1",
    "epl20": "EPL-2.0",
    "gpl2": "GPL-2.0-only",
    "gplv2": "GPL-2.0-only",
    "gpl20": "GPL-2.0-only",
    "gpl20only": "GPL-2.0-only",
    "gplv2+": "GPL-2.0-or-later",
    "gpl20orlater": "GPL-2.0-or-later",
    "gplv3": "GPL-3.0-only",
    "gpl30": "GPL-3.0-only",
    "gpl30only": "GPL-3.0-only",
    "gpl30orlater": "GPL-3.0-or-later",
    "lgplv21": "LGPL-2.1-only",
    "lgpl21": "LGPL-2.1-only",
    "gnulesserpublic21": "LGPL-2.1-only",
    "lgpl21orlater": "LGPL-2.1-or-later",
    "lgplv3": "LGPL-3.0-only",
    "lgpl30only": "LGPL-3.0-only",
    "lgpl30orlater": "LGPL-3.0-or-later",
    "agplv3": "AGPL-3.0-only",
    "agpl30only": "AGPL-3.0-only",
}


@dataclasses.dataclass(frozen=True, order=True)
class InterfaceRef:
    """A reference to an interface: <package>/<kind>/<name>."""
    package: str
    kind: str
    name: str


# Interfaces that rosidl_default_generators' ros_service()/ros_action() macros
# add implicitly. Packages built with rosidl_core_generators (plain
# ros_interface()) have to list them explicitly.
SUPPORT_REFS = {
    "msg": (),
    "srv": (InterfaceRef("service_msgs", "msg", "ServiceEventInfo"),),
    "action": (
        InterfaceRef("action_msgs", "msg", "GoalInfo"),
        InterfaceRef("action_msgs", "msg", "GoalStatus"),
        InterfaceRef("action_msgs", "msg", "GoalStatusArray"),
        InterfaceRef("action_msgs", "srv", "CancelGoal"),
    ),
}

# Deps that are redundant-but-harmless under rosidl_default_generators (the
# macro already adds them, or the generated action types use them anyway).
REDUNDANT_OK_REFS = {
    "msg": (),
    "srv": SUPPORT_REFS["srv"],
    "action": SUPPORT_REFS["action"] + (
        InterfaceRef("service_msgs", "msg", "ServiceEventInfo"),
        InterfaceRef("builtin_interfaces", "msg", "Time"),
        InterfaceRef("unique_identifier_msgs", "msg", "UUID"),
    ),
}


@dataclasses.dataclass(frozen=True)
class InterfaceFile:
    kind: str
    name: str
    path: Path
    # Directory (relative to the package root) whose BUILD.bazel declares
    # this interface. rosidl_adapter requires src to sit directly in the
    # declaring Bazel package, so this is always the file's own parent dir,
    # e.g. "msg", "msg/fields", "msg-ros2", "msg_ros2/msg". "" => kind.
    dir: str = ""

    @property
    def bazel_dir(self) -> str:
        return self.dir or self.kind

    @property
    def src(self) -> str:
        return self.path.name

    @property
    def ext(self) -> str:
        return self.path.suffix


@dataclasses.dataclass
class DeclaredRule:
    macro: str
    name: str
    src: Optional[str]
    deps: Optional[List[str]]  # None => not a literal list of strings.
    extra_kwargs: Tuple[str, ...] = ()


@dataclasses.dataclass
class ParsedBuild:
    header: str
    loads: List[Tuple[str, str]]  # (module label, verbatim source)
    rules: Dict[str, DeclaredRule]
    preserved: List[str]  # verbatim package()/license() statements
    unknown: List[str]  # descriptions of statements we don't understand


# Per-interface change categories reported for each package:
#   old   - a declared rule with no matching interface file (stale, removed);
#   new   - an interface file with no declared rule (added);
#   buggy - a declared rule whose macro/src/deps are wrong (rewritten).
STAT_OLD = "old"
STAT_NEW = "new"
STAT_BUGGY = "buggy"
STAT_KEYS = (STAT_OLD, STAT_NEW, STAT_BUGGY)


@dataclasses.dataclass
class InterfaceResult(PackageResult):
    generator: Optional[str] = None
    interface_count: int = 0

    def details(self) -> List[str]:
        return [f"{self.interface_count} {self.generator or '?'} interfaces"]


### PURE HELPERS: PARSING INTERFACES


def parse_type_token(token: str, context_package: str) -> Optional[InterfaceRef]:
    """
    Resolve one field type token from a .msg/.srv/.action file into the
    interface it refers to, or None for builtin types. Raises ValueError for
    malformed type names.
    """
    base = token.split("[", 1)[0]
    if base in PRIMITIVE_TYPES:
        return None
    if base in BUILTIN_TIME_TYPES:
        return InterfaceRef("builtin_interfaces", "msg", BUILTIN_TIME_TYPES[base])
    if re.match(r"^w?string<=\d+$", base):
        return None
    parts = base.split("/")
    if parts == ["Header"]:
        # rosidl_adapter special-cases a bare "Header" as std_msgs/Header.
        return InterfaceRef("std_msgs", "msg", "Header")
    if len(parts) == 1:
        package, name = context_package, parts[0]
    elif len(parts) == 2:
        package, name = parts
    elif len(parts) == 3 and parts[1] in INTERFACE_KINDS:
        package, name = parts[0], parts[2]
    else:
        raise ValueError(f"invalid type name {token!r}")
    if not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", package or "") or not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", name):
        raise ValueError(f"invalid type name {token!r}")
    return InterfaceRef(package, "msg", name)


def scan_rosidl_text(text: str, context_package: str) -> List[InterfaceRef]:
    """All non-builtin types referenced by a .msg/.srv/.action file, in order."""
    refs: List[InterfaceRef] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line == "---":
            continue
        ref = parse_type_token(line.split()[0], context_package)
        if ref is not None and ref not in refs:
            refs.append(ref)
    return refs


_IDL_INCLUDE_RE = re.compile(
    r'^\s*#\s*include\s+[<"]([A-Za-z0-9_]+)/(msg|srv|action)/([A-Za-z0-9_]+)\.idl[>"]',
    re.MULTILINE,
)
_IDL_ANY_INCLUDE_RE = re.compile(r'^\s*#\s*include\s+[<"]([^<>"]+\.idl)[>"]', re.MULTILINE)


def scan_idl_text(text: str, context_package: Optional[str] = None,
                  context_dir: Optional[str] = None) -> List[InterfaceRef]:
    """
    All interfaces #included by a .idl file, in order. Includes that aren't
    of the `<pkg>/<kind>/<Name>.idl` form are resolved relative to the
    including file's directory `context_dir` (relative to the root of package
    `context_package`), e.g. `#include "Basic.idl"` next to it.
    """
    refs: List[InterfaceRef] = []
    for m in _IDL_ANY_INCLUDE_RE.finditer(text):
        full = _IDL_INCLUDE_RE.match(m.group(0))
        if full:
            ref = InterfaceRef(*full.groups())
        elif context_package is not None and context_dir is not None:
            path = PurePosixPath(posixpath.normpath(posixpath.join(context_dir, m.group(1))))
            if path.parts[:1] == ("..",):
                continue
            ref = InterfaceRef(context_package, kind_for_path(path), path.stem)
        else:
            continue
        if ref not in refs:
            refs.append(ref)
    return refs


_EXT_KINDS = {".msg": "msg", ".srv": "srv", ".action": "action"}
_CMAKE_ROOT_VARS = ("${CMAKE_CURRENT_SOURCE_DIR}", "${PROJECT_SOURCE_DIR}", "${CMAKE_SOURCE_DIR}")
_ROSIDL_KEYWORDS = frozenset([
    "DEPENDENCIES", "LIBRARY_NAME", "ADD_LINTER_TESTS", "SKIP_INSTALL", "SKIP_GROUP_MEMBERSHIP_CHECK",
])


def kind_for_path(path: PurePosixPath) -> Optional[str]:
    """msg/srv/action for an interface file path (.idl: from its directory), else None."""
    if path.suffix in _EXT_KINDS:
        return _EXT_KINDS[path.suffix]
    if path.suffix == ".idl":
        return next((part for part in reversed(path.parts[:-1]) if part in INTERFACE_KINDS), "msg")
    return None


def _strip_cmake_comments(text: str) -> str:
    text = re.sub(r"#\[(=*)\[.*?\]\1\]", "", text, flags=re.DOTALL)  # bracket comments
    out = []
    for line in text.splitlines():
        in_str = False
        for i, ch in enumerate(line):
            if ch == '"' and (i == 0 or line[i - 1] != "\\"):
                in_str = not in_str
            elif ch == "#" and not in_str:
                line = line[:i]
                break
        out.append(line)
    return "\n".join(out)


def _cmake_calls(text: str, command: str) -> List[List[str]]:
    """Argument token lists of every `command(...)` call (case-insensitive)."""
    calls = []
    for m in re.finditer(r"\b%s\s*\(" % re.escape(command), text, re.IGNORECASE):
        depth, i = 1, m.end()
        while i < len(text) and depth:
            depth += {"(": 1, ")": -1}.get(text[i], 0)
            i += 1
        body = text[m.end():i - 1]
        calls.append([t[1:-1] if t.startswith('"') else t for t in re.findall(r'"(?:[^"\\]|\\.)*"|[^\s"]+', body)])
    return calls


def parse_cmake_interfaces(text: str, pkg_dir: Optional[Path] = None) -> Tuple[Optional[List[str]], bool]:
    """
    (interface file paths relative to the package root, whether some entries
    couldn't be resolved) from every rosidl_generate_interfaces() call, or
    (None, False) if there is none. Expands variables from set(),
    list(APPEND) and (given pkg_dir) file(GLOB[_RECURSE]); handles the
    "<base dir>:<relative path>" form.
    """
    text = _strip_cmake_comments(text)
    calls = _cmake_calls(text, "rosidl_generate_interfaces")
    if not calls:
        return None, False

    variables: Dict[str, List[str]] = collections.defaultdict(list)
    for args in _cmake_calls(text, "set"):
        if args:
            variables[args[0]] += [a for a in args[1:] if a not in ("PARENT_SCOPE", "CACHE")]
    for args in _cmake_calls(text, "list"):
        if len(args) >= 2 and args[0].upper() == "APPEND":
            variables[args[1]] += args[2:]
    for args in _cmake_calls(text, "file"):
        if len(args) >= 3 and args[0].upper() in ("GLOB", "GLOB_RECURSE") and pkg_dir is not None:
            recurse = args[0].upper() == "GLOB_RECURSE"
            patterns = [a for a in args[2:] if a not in ("RELATIVE", "CONFIGURE_DEPENDS", "LIST_DIRECTORIES")
                        and not any(a.startswith(v) and a == v for v in _CMAKE_ROOT_VARS)]
            for pattern in patterns:
                for root in _CMAKE_ROOT_VARS:
                    pattern = pattern.replace(root + "/", "")
                if "${" in pattern:
                    continue
                if recurse and "/" in pattern:
                    head, tail = pattern.rsplit("/", 1)
                    pattern = f"{head}/**/{tail}"
                variables[args[1]] += sorted(p.relative_to(pkg_dir).as_posix()
                                             for p in pkg_dir.glob(pattern) if p.is_file())

    unresolved = False

    def expand(token: str, depth: int = 0) -> List[str]:
        nonlocal unresolved
        for root in _CMAKE_ROOT_VARS:
            token = token.replace(root, "")
        token = token.replace("${PROJECT_NAME}", "")
        m = re.fullmatch(r"\$\{([A-Za-z0-9_]+)\}", token)
        if m:
            if m.group(1) in variables and depth < 10:
                return [x for v in variables[m.group(1)] for x in expand(v, depth + 1)]
            unresolved = True
            return []
        if "${" in token:
            unresolved = True
            return []
        return [token]

    paths: List[str] = []
    for args in calls:
        for token in args[1:]:
            if token in _ROSIDL_KEYWORDS:
                break
            for value in expand(token):
                value = value.lstrip("/")
                if ":" in value:
                    base, rel = value.split(":", 1)
                    value = f"{base.strip('/')}/{rel}" if base.strip("/") else rel
                if value.startswith("./"):
                    value = value[2:]
                if kind_for_path(PurePosixPath(value)) and value not in paths:
                    paths.append(value)
    return paths, unresolved


def select_generator(declared_deps: Set[str]) -> Tuple[str, bool]:
    """(generator, whether package.xml actually declared one)."""
    if GENERATOR_PACKAGES[CORE] in declared_deps:
        return CORE, True
    if GENERATOR_PACKAGES[DEFAULT] in declared_deps:
        return DEFAULT, True
    return DEFAULT, False


def _normalise_license(text: str) -> str:
    text = re.sub(r"\b(the|licen[cs]e|version)\b", "", text.lower())
    return re.sub(r"[^a-z0-9+]", "", text)


def license_kind(license_text: Optional[str]) -> Optional[str]:
    """SPDX id for a package.xml <license> string, or None if unrecognised."""
    if not license_text:
        return None
    for candidate in (license_text, license_text.split(",")[0]):
        spdx = LICENSE_KINDS.get(_normalise_license(candidate))
        if spdx:
            return spdx
    return None


def macro_for(generator: str, kind: str, ext: str) -> str:
    if generator == CORE:
        return "ros_interface"
    if ext == ".idl":
        return "ros_idl"
    return {"msg": "ros_message", "srv": "ros_service", "action": "ros_action"}[kind]


### PURE HELPERS: LABELS


# Maps a referenced interface to the Bazel package dir that declares it
# (None => the conventional <kind>/ dir).
Locator = Callable[[InterfaceRef], Optional[str]]


def _no_locator(ref: InterfaceRef) -> Optional[str]:
    return None


def label_for(ref: InterfaceRef, package: str, from_dir: str, ref_dir: Optional[str] = None) -> str:
    """Label for `ref` as seen from <package>/<from_dir>/BUILD.bazel."""
    d = ref_dir or ref.kind
    if ref.package == package:
        return f":{ref.name}" if d == from_dir else f"//{d}:{ref.name}"
    return f"@{ref.package}//{d}:{ref.name}"


def required_refs(iface: InterfaceFile, refs: Sequence[InterfaceRef], generator: str, package: str) -> List[InterfaceRef]:
    """Every interface `iface` must declare as a dep (excluding itself)."""
    own = InterfaceRef(package, iface.kind, iface.name)
    out = [r for r in refs if r != own]
    if generator == CORE:
        out += [r for r in SUPPORT_REFS[iface.kind] if r != own]
    return sorted(set(out))


def required_labels(iface: InterfaceFile, refs: Sequence[InterfaceRef], generator: str, package: str,
                    locate: Locator = _no_locator) -> List[str]:
    return sort_labels(label_for(r, package, iface.bazel_dir, locate(r))
                       for r in required_refs(iface, refs, generator, package))


def allowed_extra_labels(kind: str, generator: str, package: str, from_dir: Optional[str] = None) -> Set[str]:
    if generator == CORE:
        return set()
    return {label_for(r, package, from_dir or kind) for r in REDUNDANT_OK_REFS[kind]}


### PURE HELPERS: BUILD FILES


def _leading_comment_block(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            lines.append(line)
        else:
            break
    return "\n".join(lines).strip("\n")


def parse_build_file(text: str) -> ParsedBuild:
    """Parse an interface-directory BUILD.bazel. Raises SyntaxError."""
    tree = ast.parse(text)
    parsed = ParsedBuild(header=_leading_comment_block(text), loads=[], rules={}, preserved=[], unknown=[])
    for stmt in tree.body:
        segment = ast.get_source_segment(text, stmt) or ""
        if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name)):
            parsed.unknown.append(f"line {stmt.lineno}: {segment.splitlines()[0] if segment else type(stmt).__name__}")
            continue
        call = stmt.value
        fn = call.func.id
        if fn == "load":
            module = call.args[0].value if call.args and isinstance(call.args[0], ast.Constant) else ""
            parsed.loads.append((module, segment))
        elif fn in INTERFACE_MACROS:
            kwargs = {kw.arg: kw.value for kw in call.keywords}
            name_node = kwargs.get("name")
            src_node = kwargs.get("src")
            name = name_node.value if isinstance(name_node, ast.Constant) else None
            if name is None:
                parsed.unknown.append(f"line {stmt.lineno}: {fn}() without a literal name")
                continue
            parsed.rules[name] = DeclaredRule(
                macro=fn,
                name=name,
                src=src_node.value if isinstance(src_node, ast.Constant) else None,
                deps=str_list(kwargs["deps"]) if "deps" in kwargs else [],
                extra_kwargs=tuple(sorted(k for k in kwargs if k not in ("name", "src", "deps"))),
            )
        elif fn in ("package", "license"):
            parsed.preserved.append(segment)
        elif fn == "exports_files":
            pass  # Regenerated canonically.
        else:
            parsed.unknown.append(f"line {stmt.lineno}: {fn}(...)")
    return parsed


def check_interface_build(
    package: str,
    bazel_dir: str,
    files: Sequence[InterfaceFile],
    required: Mapping[str, List[str]],
    generator: str,
    text: Optional[str],
    license_text: Optional[str] = None,
    templates: Sequence[str] = (),
) -> FileCheck:
    """
    Compare <pkg>/<bazel_dir>/BUILD.bazel against what the interface files on
    disk require. `required` maps interface name -> required dep labels.
    `templates` names interfaces generated from CMake .in templates: their
    hand-written rules are never flagged stale, and a file declaring them is
    never rewritten (the canonical rendering would drop them).
    """
    where_build = f"{bazel_dir}/BUILD.bazel"
    problems: List[Tuple[str, str]] = []
    stats: collections.Counter = collections.Counter()
    if text is None:
        problems.append(("missing-build", f"{where_build} does not exist"))
        stats[STAT_NEW] = len(files)
        return FileCheck(problems, render_interface_build(package, bazel_dir, files, required, generator, None,
                                                          license_text), stats=stats)
    try:
        parsed = parse_build_file(text)
    except SyntaxError as e:
        return FileCheck([("unparseable", f"{where_build}: {e}")], None, "unparseable BUILD file")

    other_gen = GENERATOR_PACKAGES[CORE if generator == DEFAULT else DEFAULT]
    if any(module.startswith(f"@{other_gen}//") for module, _ in parsed.loads):
        problems.append(("wrong-generator", f"{where_build} loads from @{other_gen}, expected @{GENERATOR_PACKAGES[generator]}"))

    by_name = {f.name: f for f in files}
    manual_reason = None
    for f in files:
        rule = parsed.rules.get(f.name)
        where = f"{where_build}:{f.name}"
        if rule is None:
            problems.append(("missing-rule", f"{where} is not declared"))
            stats[STAT_NEW] += 1
            continue
        before = len(problems)
        want_macro = macro_for(generator, f.kind, f.ext)
        if rule.macro != want_macro:
            problems.append(("wrong-macro", f"{where} uses {rule.macro}(), expected {want_macro}()"))
        if rule.src != f.src:
            problems.append(("wrong-src", f"{where} has src={rule.src!r}, expected {f.src!r}"))
        if rule.extra_kwargs:
            manual_reason = f"{where} has unexpected attributes {list(rule.extra_kwargs)}"
        if rule.deps is None:
            problems.append(("deps-not-literal", f"{where} deps is not a literal list"))
            manual_reason = manual_reason or f"{where} deps is not a literal list"
        else:
            have = set(rule.deps)
            want = set(required.get(f.name, []))
            missing = sort_labels(want - have)
            extra = sort_labels(have - want - allowed_extra_labels(f.kind, generator, package, bazel_dir))
            if missing:
                problems.append(("missing-deps", f"{where} is missing deps {missing}"))
            if extra:
                problems.append(("extra-deps", f"{where} has unneeded deps {extra}"))
        if len(problems) > before:
            stats[STAT_BUGGY] += 1
    for name in sorted(set(parsed.rules) - set(by_name) - set(templates)):
        problems.append(("stale-rule", f"{where_build}:{name} has no matching interface file"))
        stats[STAT_OLD] += 1

    if parsed.unknown:
        manual_reason = manual_reason or f"{where_build} has unrecognised statements: {parsed.unknown}"
    kept = sorted(set(parsed.rules) & set(templates))
    if kept:
        manual_reason = manual_reason or f"{where_build} hand-declares templated interfaces {kept}"
    if not problems:
        return FileCheck([], None)
    if manual_reason:
        return FileCheck(problems, None, manual_reason, stats=stats)
    return FileCheck(problems, render_interface_build(package, bazel_dir, files, required, generator, parsed,
                                                      license_text), stats=stats)


def _render_rule(macro: str, name: str, src: str, deps: Sequence[str]) -> str:
    lines = [f"{macro}(", f'    name = "{name}",', f'    src = "{src}",']
    if deps:
        lines.append("    deps = [")
        lines += [f'        "{d}",' for d in deps]
        lines.append("    ],")
    lines.append(")")
    return "\n".join(lines)


def render_interface_build(
    package: str,
    bazel_dir: str,
    files: Sequence[InterfaceFile],
    required: Mapping[str, List[str]],
    generator: str,
    parsed: Optional[ParsedBuild],
    license_text: Optional[str] = None,
) -> str:
    """Canonical <pkg>/<bazel_dir>/BUILD.bazel, preserving header/package/license."""
    macros = sorted({macro_for(generator, f.kind, f.ext) for f in files})
    gen_load = "load(\"@{}//:defs.bzl\", {})".format(
        GENERATOR_PACKAGES[generator], ", ".join(f'"{m}"' for m in macros))

    loads: List[Tuple[str, str]] = []
    preserved: List[str] = []
    header = COPYRIGHT_HEADER.rstrip("\n")
    if parsed is not None:
        header = parsed.header or header
        loads = [(m, s) for m, s in parsed.loads if not re.match(r"^@rosidl_(core|default)_generators//", m)]
        preserved = list(parsed.preserved)
    else:
        spdx = license_kind(license_text)
        if spdx:
            loads.append(("@rules_license//rules:license.bzl", LICENSE_LOAD))
            preserved = render_license_blocks(spdx).split("\n\n")
    if macros:
        loads.append((f"@{GENERATOR_PACKAGES[generator]}//:defs.bzl", gen_load))
    if not any(p.lstrip().startswith("package(") for p in preserved):
        preserved.insert(0, 'package(default_visibility = ["//visibility:public"])')

    blocks = [header, "\n".join(s for _, s in sorted(loads))]
    blocks += preserved
    exts = sorted({f"*{f.ext}" for f in files})
    if exts:
        blocks.append("exports_files(glob([{}]))".format(", ".join(f'"{e}"' for e in exts)))
    for f in files:
        blocks.append(_render_rule(macro_for(generator, f.kind, f.ext), f.name, f.src, required.get(f.name, [])))
    return "\n\n".join(b for b in blocks if b) + "\n"


_ANY_LOCAL_LABEL_RE = re.compile(r"^//[A-Za-z0-9_\-./]+:[A-Za-z0-9_]+$")

# Targets core_generators()/default_generators() create in the root package.
GENERATED_TARGET_NAMES = frozenset(["ament_index", "c", "c_internal", "cc", "cc_internal", "idl", "proto", "py", "rs"])
LICENSE_LOAD = 'load("@rules_license//rules:license.bzl", "license")'


def _generators_load(generator: str) -> str:
    return f'load("@{GENERATOR_PACKAGES[generator]}//:defs.bzl", "{GENERATOR_FUNCTIONS[generator]}")'


def render_generators_call(generator: str, required: Sequence[str]) -> str:
    return "\n".join([
        f"{GENERATOR_FUNCTIONS[generator]}(",
        '    package_xml = "package.xml",',
        f"    deps = {format_list(sort_labels(required), '    ')},",
        ")",
    ])


def render_license_blocks(spdx: str) -> str:
    """package() + license() declaring the package's SPDX license."""
    return (
        "package(\n"
        '    default_applicable_licenses = [":license"],\n'
        '    default_visibility = ["//visibility:public"],\n'
        ")\n\n"
        "license(\n"
        '    name = "license",\n'
        "    license_kinds = [\n"
        f'        "@rules_license//licenses/spdx:{spdx}",\n'
        "    ],\n"
        ")"
    )


def render_root_build(generator: str, required: Sequence[str], license_text: Optional[str],
                      ament_deps: Sequence[str]) -> str:
    """A brand-new root BUILD.bazel, modelled on action_msgs' overlay."""
    spdx = license_kind(license_text)
    loads = [AMENT_LOAD, _generators_load(generator)] + ([LICENSE_LOAD] if spdx else [])
    blocks = [
        COPYRIGHT_HEADER.rstrip("\n"),
        "\n".join(sorted(loads)),
        render_license_blocks(spdx) if spdx else 'package(default_visibility = ["//visibility:public"])',
        render_generators_call(generator, required),
        "### PACKAGING",
        render_ament_package(ament_deps),
    ]
    return "\n\n".join(blocks) + "\n"


def _kwarg_names(stmt: ast.stmt) -> List[str]:
    return [kw.arg for kw in stmt.value.keywords]


def insert_generators(text: str, tree: ast.Module, generator: str, required: Sequence[str],
                      license_text: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Add a generators call (and its load, plus a license() if the file has
    none) to an existing root BUILD.bazel. Returns (new_text, manual_reason).
    """
    target_names = set()
    for stmt in tree.body:
        if call_name(stmt):
            for kw in stmt.value.keywords:
                if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                    target_names.add(kw.value.value)
    clashes = sorted(target_names & GENERATED_TARGET_NAMES)
    if clashes:
        return None, f"existing targets {clashes} clash with {GENERATOR_FUNCTIONS[generator]}() outputs"

    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    loads = [s for s in tree.body if call_name(s) == "load"]
    first_stmt = tree.body[0].lineno - 1 if tree.body else len(lines)
    load_pos = loads[-1].end_lineno if loads else first_stmt
    edits: List[Tuple[int, int, int, str]] = []  # (start, end, order, replacement)

    new_loads = [_generators_load(generator)]
    spdx = license_kind(license_text)
    has_license = any(call_name(s) == "license" for s in tree.body)
    if spdx and not has_license:
        packages = [s for s in tree.body if call_name(s) == "package"]
        if not packages:
            edits.append((load_pos, load_pos, 1, "\n" + render_license_blocks(spdx) + "\n"))
            new_loads.append(LICENSE_LOAD)
        elif _kwarg_names(packages[0]) == ["default_visibility"]:
            pkg = packages[0]
            edits.append((pkg.lineno - 1, pkg.end_lineno, 1, render_license_blocks(spdx) + "\n"))
            new_loads.append(LICENSE_LOAD)
    if LICENSE_LOAD in new_loads and LICENSE_LOAD in text:
        new_loads.remove(LICENSE_LOAD)
    edits.append((load_pos, load_pos, 0, "".join(f"{line}\n" for line in new_loads)))

    anchor = next((s for s in tree.body if call_name(s) == "ament_package"), None)
    block = render_generators_call(generator, required) + "\n\n"
    if anchor is not None:
        edits.append((anchor.lineno - 1, anchor.lineno - 1, 2, block))
    else:
        edits.append((len(lines), len(lines), 2, "\n" + block))

    # Apply bottom-up so earlier line numbers stay valid; at equal positions
    # apply higher `order` first so lower orders end up earlier in the text.
    for start, end, _, replacement in sorted(edits, key=lambda e: (e[0], e[2]), reverse=True):
        lines[start:end] = [replacement]
    return "".join(lines), None


def check_root_build(text: str, generator: str, required: Sequence[str],
                     license_text: Optional[str] = None) -> FileCheck:
    """
    Check the root BUILD.bazel's core_generators()/default_generators() call
    lists exactly the interfaces on disk (other non-interface deps are left
    alone), and uses the right generator. Adds the call if it's missing.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        return FileCheck([("unparseable", f"BUILD.bazel: {e}")], None, "unparseable BUILD file")
    want_fn = GENERATOR_FUNCTIONS[generator]
    other = CORE if generator == DEFAULT else DEFAULT
    other_fn = GENERATOR_FUNCTIONS[other]
    calls = [
        s.value for s in tree.body
        if isinstance(s, ast.Expr) and isinstance(s.value, ast.Call)
        and isinstance(s.value.func, ast.Name) and s.value.func.id in (want_fn, other_fn)
    ]
    if not calls:
        problems = [("no-generators", f"BUILD.bazel has no {want_fn}(...) call")]
        new_text, manual_reason = insert_generators(text, tree, generator, required, license_text)
        return FileCheck(problems, new_text, manual_reason)
    call = calls[0]
    problems: List[Tuple[str, str]] = []
    manual_reason = None
    new_text = text

    deps_kw = next((kw for kw in call.keywords if kw.arg == "deps"), None)
    have = str_list(deps_kw.value) if deps_kw is not None else []
    if have is None:
        problems.append(("deps-not-literal", f"BUILD.bazel {call.func.id}(deps=...) is not a literal list"))
        manual_reason = "root generators deps is not a literal list"
    else:
        iface_dirs = set(INTERFACE_KINDS) | {lbl[2:].split(":", 1)[0] for lbl in required}

        def is_iface(label: str) -> bool:
            return bool(_ANY_LOCAL_LABEL_RE.match(label)) and label[2:].split(":", 1)[0] in iface_dirs

        have_ifaces = {d for d in have if is_iface(d)}
        missing = sort_labels(set(required) - have_ifaces)
        stale = sort_labels(have_ifaces - set(required))
        if missing:
            problems.append(("root-missing", f"BUILD.bazel {call.func.id}() is missing {missing}"))
        if stale:
            problems.append(("root-stale", f"BUILD.bazel {call.func.id}() lists nonexistent {stale}"))
        if missing or stale:
            if deps_kw is None:
                manual_reason = "root generators call has no deps attribute"
            else:
                others = [d for d in have if not is_iface(d)]
                line = text.splitlines()[deps_kw.value.lineno - 1]
                indent = line[: len(line) - len(line.lstrip())]
                new_text = replace_node_span(new_text, deps_kw.value, format_list(sort_labels(others + list(required)), indent))

    if call.func.id == other_fn:
        problems.append(("wrong-generator", f"BUILD.bazel uses {other_fn}(), expected {want_fn}()"))
        load_re = re.compile(r'load\("@{}//:defs\.bzl",\s*"{}"\)'.format(GENERATOR_PACKAGES[other], other_fn))
        if load_re.search(new_text) and new_text.count(f"{other_fn}(") == 1:
            new_text = load_re.sub(f'load("@{GENERATOR_PACKAGES[generator]}//:defs.bzl", "{want_fn}")', new_text)
            new_text = new_text.replace(f"{other_fn}(", f"{want_fn}(")
        else:
            manual_reason = manual_reason or f"switch BUILD.bazel from {other_fn} to {want_fn} by hand"

    if not problems:
        return FileCheck([], None)
    if manual_reason:
        return FileCheck(problems, None, manual_reason)
    return FileCheck(problems, new_text)


### WORKSPACE LAYER


@dataclasses.dataclass
class Discovery:
    files: List[InterfaceFile]
    warnings: List[str]
    # Interfaces generated by CMake configure_file() from <name>.<ext>.in;
    # `path` points at the .in template.
    templates: List[InterfaceFile]

    def catalogue(self) -> Dict[Tuple[str, str], str]:
        """{(kind, name): bazel_dir} for everything this package defines."""
        return {(f.kind, f.name): f.bazel_dir for f in self.files + self.templates}


def discover_interfaces(pkg_dir: Path) -> Discovery:
    """
    Find the interfaces a package actually builds. The file list passed to
    rosidl_generate_interfaces() in CMakeLists.txt is authoritative (it's what
    upstream builds, including subfolders and ROS 2-only dirs); if it can't be
    fully resolved, msg/, srv/ and action/ are scanned recursively instead.
    """
    warnings: List[str] = []
    templates: List[InterfaceFile] = []
    chosen: Dict[Tuple[str, str], InterfaceFile] = {}
    # Explicit entries that didn't resolve to a file: (kind, name) -> warning.
    # Often a CMake foreach() prefixes bare names; only warn if the fallback
    # scan doesn't find them either.
    misses: Dict[Tuple[str, str], str] = {}

    def make(rel: str) -> Optional[InterfaceFile]:
        p = PurePosixPath(rel)
        kind = kind_for_path(p)
        if kind is None:
            return None
        parent = str(p.parent)
        if parent == ".":
            if (pkg_dir / rel).is_file():
                warnings.append(f"{rel} sits at the package root; interfaces must live in a subdirectory")
            else:
                misses[(kind, p.stem)] = f"CMakeLists.txt lists {rel}, which does not exist"
            return None
        return InterfaceFile(kind, p.stem, pkg_dir / rel, dir=parent)

    def add(f: InterfaceFile) -> None:
        key = (f.kind, f.name)
        prev = chosen.get(key)
        if prev is None:
            chosen[key] = f
        elif prev.path != f.path:
            keep = prev if prev.ext != ".idl" else f
            warnings.append(f"{prev.bazel_dir}/{prev.src} and {f.bazel_dir}/{f.src} define the same interface; "
                            f"using {keep.bazel_dir}/{keep.src}")
            chosen[key] = keep

    cmake = pkg_dir / "CMakeLists.txt"
    explicit, unresolved = (parse_cmake_interfaces(cmake.read_text(errors="replace"), pkg_dir)
                            if cmake.is_file() else (None, False))
    for rel in explicit or []:
        f = make(rel)
        if f is None:
            continue
        if f.path.is_file():
            add(f)
        elif Path(f"{f.path}.in").is_file():
            templates.append(dataclasses.replace(f, path=Path(f"{f.path}.in")))
        else:
            misses[(f.kind, f.name)] = f"CMakeLists.txt lists {rel}, which does not exist"

    if not explicit or unresolved or misses:
        explicit_keys = set(chosen)
        for kind in INTERFACE_KINDS:
            kind_dir = pkg_dir / kind
            if not kind_dir.is_dir():
                continue
            for path in sorted(kind_dir.rglob("*")):
                if not path.is_file() or any(part.startswith(".") for part in path.relative_to(pkg_dir).parts):
                    continue
                rel = path.relative_to(pkg_dir).as_posix()
                if path.suffix == ".in":
                    f = make(rel[:-3])
                    if f is not None and (f.kind, f.name) not in chosen:
                        templates.append(dataclasses.replace(f, path=path))
                    continue
                f = make(rel)
                if f is not None and (f.kind, f.name) not in explicit_keys:
                    add(f)

    template_keys = {(t.kind, t.name) for t in templates}
    warnings += [w for k, w in misses.items() if k not in chosen and k not in template_keys]
    files = sorted((f for k, f in chosen.items() if k not in template_keys), key=lambda f: (f.bazel_dir, f.name))
    return Discovery(files, warnings, sorted(templates, key=lambda f: (f.bazel_dir, f.name)))


class InterfaceAuditor(PackageAuditor):
    """Audits (and optionally fixes) one package's interfaces at a time; thread-safe."""

    result_type = InterfaceResult

    def __init__(self, packages: Mapping[str, Path], fix: bool, buildifier: Optional[str]):
        super().__init__(packages, fix, buildifier)
        self._catalogue: Dict[str, Dict[Tuple[str, str], str]] = {}

    def catalogue(self, package: str) -> Optional[Dict[Tuple[str, str], str]]:
        """{(kind, name): bazel_dir} of interfaces a vendored package ships, or None."""
        if package not in self.packages:
            return None
        with self._lock:
            cached = self._catalogue.get(package)
        if cached is None:
            cached = discover_interfaces(self.packages[package]).catalogue()
            with self._lock:
                self._catalogue[package] = cached
        return cached

    def _audit(self, package: str, result: InterfaceResult) -> None:
        pkg_dir = self.packages[package]
        _, declared, license_text = parse_package_xml((pkg_dir / "package.xml").read_text())
        generator, generator_declared = select_generator(declared)
        result.generator = generator
        discovery = discover_interfaces(pkg_dir)
        files = discovery.files
        result.interface_count = len(files) + len(discovery.templates)
        for w in discovery.warnings:
            result.issues.append(Issue(SEVERITY_WARNING, "discovery", package, w))
        for t in discovery.templates:
            result.issues.append(Issue(SEVERITY_MANUAL, "template", f"{t.bazel_dir}/{t.path.name}",
                                       f"{t.kind}/{t.name} is generated by CMake configure_file(); declare it by hand "
                                       f"(expand_template/genrule feeding {macro_for(generator, t.kind, '.' + t.kind)}())"))
        if not files:
            return
        if not generator_declared:
            # Interface files in a package that doesn't depend on a generator
            # are data (rosidl test fixtures such as test_interface_files) or
            # belong to a generator itself (rosidl_generator_py); wiring
            # default_generators() into those creates dependency cycles.
            result.issues.append(Issue(SEVERITY_WARNING, "no-generator", "package.xml",
                                       "declares neither rosidl_core_generators nor rosidl_default_generators; "
                                       "treating its interface files as data and leaving it alone"))
            return
        local = discovery.catalogue()

        def locate(ref: InterfaceRef) -> Optional[str]:
            cat = local if ref.package == package else self.catalogue(ref.package)
            return cat.get((ref.kind, ref.name)) if cat else None

        # Scan every interface file for the interfaces it references.
        refs_by_file: Dict[InterfaceFile, List[InterfaceRef]] = {}
        for f in files:
            text = f.path.read_text(errors="replace")
            try:
                refs_by_file[f] = (scan_idl_text(text, package, f.bazel_dir) if f.ext == ".idl"
                                   else scan_rosidl_text(text, package))
            except ValueError as e:
                result.issues.append(Issue(SEVERITY_MANUAL, "parse", f"{f.bazel_dir}/{f.src}", str(e)))
                refs_by_file[f] = []

        # Resolve references and collect external packages.
        external: Set[str] = set()
        for f, refs in refs_by_file.items():
            for ref in required_refs(f, refs, generator, package):
                if ref.package != package:
                    external.add(ref.package)
                cat = local if ref.package == package else self.catalogue(ref.package)
                if cat is None:
                    result.issues.append(Issue(SEVERITY_WARNING, "unresolved", f"{f.bazel_dir}/{f.src}",
                                               f"references {ref.package}/{ref.kind}/{ref.name}, but {ref.package} is not vendored"))
                elif (ref.kind, ref.name) not in cat:
                    result.issues.append(Issue(SEVERITY_MANUAL, "unresolved", f"{f.bazel_dir}/{f.src}",
                                               f"references {ref.package}/{ref.kind}/{ref.name}, which does not exist"))

        # Module graph: add missing bazel_deps at the version vendored in this
        # workspace. (Bazel only sees this after create_patch + setup_workspace.)
        module_path = pkg_dir / "MODULE.bazel"
        module_text = module_path.read_text() if module_path.is_file() else None
        module_deps = parse_module_bazel_deps(module_text) if module_text is not None else set()
        added_deps: Set[str] = set()
        if module_text is None:
            result.issues.append(Issue(SEVERITY_MANUAL, "no-module", "MODULE.bazel", "does not exist"))
        else:
            missing_deps = sorted((external | {GENERATOR_PACKAGES[generator]}) - module_deps - {package})
            to_add: Dict[str, str] = {}
            for dep in missing_deps:
                version = self.module_version(dep)
                if version is None:
                    result.issues.append(Issue(SEVERITY_MANUAL, "module-dep", "MODULE.bazel",
                                               f'missing bazel_dep(name = "{dep}", ...), and {dep} is not vendored '
                                               "so its version is unknown"))
                else:
                    to_add[dep] = version
            if to_add:
                self._apply(result, module_path, "MODULE.bazel", FileCheck(
                    [("module-dep", f'missing bazel_dep(name = "{d}", version = "{v}")') for d, v in to_add.items()],
                    add_bazel_deps(module_text, to_add)))
                module_deps |= set(to_add)
                added_deps = set(to_add)
        # package.xml: declare the same deps, so create_patch records a
        # patches/*.patch against upstream that reminds us to upstream it.
        missing_xml = sorted(external - declared - {package})
        if missing_xml:
            xml_path = pkg_dir / "package.xml"
            self._apply(result, xml_path, "package.xml", FileCheck(
                [("package-xml", f"does not declare <depend>{d}</depend>") for d in missing_xml],
                add_package_xml_depends(xml_path.read_text(), missing_xml)))

        # One BUILD file per directory holding interface files: rosidl_adapter
        # requires each src to sit directly in its declaring Bazel package.
        template_dirs: Dict[str, List[str]] = collections.defaultdict(list)
        for t in discovery.templates:
            template_dirs[t.bazel_dir].append(t.name)
        dirs = sorted({f.bazel_dir for f in files}
                      | {k for k in INTERFACE_KINDS if (pkg_dir / k / "BUILD.bazel").is_file()})
        for d in dirs:
            dir_files = [f for f in files if f.bazel_dir == d]
            build_path = pkg_dir / d / "BUILD.bazel"
            if not dir_files:
                if d not in template_dirs:
                    on_disk = sorted(p.name for p in (pkg_dir / d).iterdir() if kind_for_path(PurePosixPath(p.name)))
                    why = (f"{on_disk} are not listed in CMakeLists.txt's rosidl_generate_interfaces()"
                           if on_disk else f"{d}/ has no interface files")
                    result.issues.append(Issue(SEVERITY_MANUAL, "stale-build", f"{d}/BUILD.bazel",
                                               f"exists but {why}"))
                continue
            required = {f.name: required_labels(f, refs_by_file[f], generator, package, locate) for f in dir_files}
            text = build_path.read_text() if build_path.is_file() else None
            self._apply(result, build_path, f"{d}/BUILD.bazel",
                        check_interface_build(package, d, dir_files, required, generator, text, license_text,
                                              template_dirs.get(d, ())))

        root_path = pkg_dir / "BUILD.bazel"
        root_required = sort_labels(f"//{f.bazel_dir}:{f.name}" for f in files)
        if license_kind(license_text) is None:
            result.issues.append(Issue(SEVERITY_WARNING, "license", "package.xml",
                                       f"unrecognised <license> {license_text!r}; no license() declared"))
        if not root_path.is_file():
            rcr = parse_rcr_deps(module_text) if module_text is not None else None
            if rcr is None:
                rcr = [d for d in module_deps if d in self.packages or d == "rosdistro"]
            ament_deps = ament_package_labels(set(rcr) | added_deps, package)
            extras = sorted(p.name for p in pkg_dir.iterdir()
                            if p.is_dir() and p.name in ("include", "src", package, "launch", "config"))
            if extras:
                result.issues.append(Issue(SEVERITY_WARNING, "uncovered", "BUILD.bazel",
                                           f"generated root BUILD.bazel only covers interfaces; also ships {extras}"))
            self._apply(result, root_path, "BUILD.bazel", FileCheck(
                [("missing-root-build", "BUILD.bazel does not exist")],
                render_root_build(generator, root_required, license_text, ament_deps)))
        else:
            self._apply(result, root_path, "BUILD.bazel",
                        check_root_build(root_path.read_text(), generator, root_required, license_text))


class InterfaceReporter(Reporter):
    def __init__(self, total: int, progress: bool, verbose: bool, fix: bool):
        super().__init__(total, progress, verbose, fix, title="Interface audit", stat_keys=STAT_KEYS,
                         stat_noun="interfaces")
        self.interfaces = 0
        self.generators: collections.Counter = collections.Counter()

    def done(self, package: str, result: InterfaceResult) -> None:
        self.interfaces += result.interface_count
        if result.generator and result.interface_count:
            self.generators[result.generator] += 1
        super().done(package, result)

    def headline(self) -> str:
        return (f"{super().headline()}, {self.interfaces} interfaces "
                f"(core: {self.generators[CORE]}, default: {self.generators[DEFAULT]})")


### MAIN


def main() -> None:
    parser = make_parser(__doc__)
    args = parser.parse_args()
    vendor_dir, packages = load_packages(parser, args)
    candidates = args.packages or sorted(packages)

    def has_interfaces(p: str) -> bool:
        d = discover_interfaces(packages[p])
        return bool(d.files or d.templates)

    selected = [p for p in candidates if args.packages or has_interfaces(p)]
    buildifier = find_buildifier(args)
    print(f"Auditing {len(selected)} interface package(s) under {vendor_dir} "
          f"with {args.jobs} thread(s){' (fixing)' if args.fix else ''}...", file=sys.stderr)
    auditor = InterfaceAuditor(packages, fix=args.fix, buildifier=buildifier)
    reporter = InterfaceReporter(len(selected), progress=not args.no_progress, verbose=args.verbose, fix=args.fix)
    sys.exit(run_sweep(packages, selected, auditor, reporter, args.jobs))


if __name__ == "__main__":
    main()

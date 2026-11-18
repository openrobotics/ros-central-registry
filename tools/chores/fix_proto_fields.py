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
Add or update trailing protobuf field-number mapping comment blocks in
.msg, .srv, .action, and .idl interface files across vendored packages.

For every vendored package (workspace/vendor/<pkg>+/) that ships interface
files (.msg, .srv, .action, .idl), this script parses each interface's
fields (ignoring constants and comments) and ensures a trailing comment
block at the bottom of the file records a deterministic 1-based protobuf
field number for each field:

    # ================================================================================
    # Protobuf Field Numbers — do not change assigned numbers; append new fields only.
    # ================================================================================
    # [proto]
    #   header = 1
    #   format = 2
    #   data = 3
    # ================================================================================

For services (.srv and 2-struct service .idl files), the lookup table is
partitioned into `[proto:Request]` and `[proto:Response]`, each starting
from 1. For actions (.action and 3-struct action .idl files), it is
partitioned into `[proto:Goal]`, `[proto:Result]`, and `[proto:Feedback]`,
each starting from 1. For .idl files, `//` line comments are used instead
of `#`.

If a file already carries a `[proto...]` block, existing field numbers are
preserved and any newly added fields are appended with the next available
field numbers (`max(existing) + 1`, ...).

Scope: this only ever reads and writes the vendored sources under
workspace/vendor/<pkg>+/. It never touches modules/.

Usage (from the repo root):

    bazel run //tools/chores:fix_proto_fields
    bazel run //tools/chores:fix_proto_fields -- sensor_msgs tf2_msgs
    bazel run //tools/chores:fix_proto_fields -- --dry-run sensor_msgs tf2_msgs
"""

import collections
import dataclasses
import re
import sys
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from tools.chores.fix_interfaces import discover_interfaces
from tools.chores.vendor_lib import (
    SEVERITY_WARNING,
    FileCheck,
    Issue,
    PackageAuditor,
    PackageResult,
    Reporter,
    load_packages,
    make_parser,
    run_sweep,
)


### CONSTANTS

PROTO_BANNER_TEXT = "Protobuf Field Numbers — do not change assigned numbers; append new fields only."
PROTO_BORDER = "=" * len(PROTO_BANNER_TEXT)

EMPTY_STRUCT_MEMBER = "structure_needs_at_least_one_member"

STAT_ADDED = "added"
STAT_UPDATED = "updated"
STAT_KEYS = (STAT_ADDED, STAT_UPDATED)

_CONSTANT_RHS_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\s*=")
_SECTION_HEADER_RE = re.compile(r"^\[proto(?::([A-Za-z0-9_]+))?\]$")
_ENTRY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(\d+)$")


@dataclasses.dataclass
class ProtoFieldResult(PackageResult):
    interface_count: int = 0

    def details(self) -> List[str]:
        return [f"{self.interface_count} interface(s)"]


### PURE HELPERS: PARSING EXISTING PROTO COMMENT BLOCKS


def _comment_prefix(ext: str) -> str:
    return "//" if ext == ".idl" else "#"


def _strip_comment_prefix(line: str, prefix: str) -> Optional[str]:
    stripped = line.strip()
    if not stripped.startswith(prefix):
        return None
    return stripped[len(prefix):].strip()


def split_existing_proto_block(
    text: str, ext: str
) -> Tuple[str, Optional[Dict[str, List[Tuple[str, int]]]]]:
    """
    Split `text` into `(body_without_proto_block, existing_sections)`.

    If no trailing proto comment block is present, returns `(text, None)`.
    `existing_sections` maps section name (`""` for `[proto]`, `"Request"`
    for `[proto:Request]`, etc.) to an ordered list of `(field_name, number)`
    pairs.
    """
    prefix = _comment_prefix(ext)
    lines = text.splitlines()

    # Locate the first `[proto...]` header within a trailing comment block.
    proto_header_idx: Optional[int] = None
    for i, line in enumerate(lines):
        inner = _strip_comment_prefix(line, prefix)
        if inner is not None and _SECTION_HEADER_RE.match(inner):
            proto_header_idx = i
            break

    if proto_header_idx is None:
        return text, None

    # Walk upwards from proto_header_idx over any banner/border comment lines
    # that belong to the proto metadata block.
    start_idx = proto_header_idx
    while start_idx > 0:
        prev_inner = _strip_comment_prefix(lines[start_idx - 1], prefix)
        if prev_inner is None:
            break
        if (
            prev_inner == PROTO_BANNER_TEXT
            or (set(prev_inner) == {"="} and len(prev_inner) >= 10)
            or prev_inner == ""
        ):
            start_idx -= 1
        else:
            break

    # Verify that every non-empty line from proto_header_idx to the end of the
    # file is a comment line belonging to this block.
    sections: Dict[str, List[Tuple[str, int]]] = collections.OrderedDict()
    current_section: Optional[str] = None
    for i in range(proto_header_idx, len(lines)):
        raw = lines[i].strip()
        if not raw:
            continue
        inner = _strip_comment_prefix(raw, prefix)
        if inner is None:
            raise ValueError(f"non-comment line after [proto] block at line {i + 1}: {lines[i]!r}")
        if not inner or (set(inner) == {"="} and len(inner) >= 10):
            continue
        m_sec = _SECTION_HEADER_RE.match(inner)
        if m_sec:
            current_section = m_sec.group(1) or ""
            sections.setdefault(current_section, [])
            continue
        m_entry = _ENTRY_RE.match(inner)
        if m_entry and current_section is not None:
            sections[current_section].append((m_entry.group(1), int(m_entry.group(2))))
            continue
        raise ValueError(f"unrecognised line in [proto] block at line {i + 1}: {lines[i]!r}")

    body_lines = lines[:start_idx]
    while body_lines and not body_lines[-1].strip():
        body_lines.pop()
    body = "\n".join(body_lines) + ("\n" if body_lines else "")
    return body, sections


### PURE HELPERS: PARSING FIELDS FROM .msg / .srv / .action / .idl


def parse_msg_section_fields(section_text: str) -> List[str]:
    """
    Extract field names in declaration order from a single .msg body (or one
    section of a .srv / .action file), ignoring comments, constants, and
    `@optional` annotations.
    """
    fields: List[str] = []
    for raw in section_text.splitlines():
        line = raw.replace("\t", " ")
        comment_idx = line.find("#")
        if comment_idx >= 0:
            line = line[:comment_idx]
        line = line.strip()
        if not line:
            continue
        if line.startswith("@optional"):
            line = line[len("@optional"):].lstrip()
            if not line:
                continue
        _type_str, _, rest = line.partition(" ")
        rest = rest.lstrip()
        if not rest:
            raise ValueError(f"invalid field definition: {raw!r}")
        if _CONSTANT_RHS_RE.match(rest):
            continue
        field_name = rest.split()[0]
        fields.append(field_name)
    return fields


def parse_rosidl_sections(text: str, ext: str) -> List[Tuple[str, List[str]]]:
    """
    Return `[(section_name, [field_name, ...]), ...]` for a `.msg`, `.srv`,
    or `.action` body (with any trailing proto block already stripped).
    """
    lines = text.splitlines()
    sep_indices = [i for i, line in enumerate(lines) if line.strip() == "---"]
    if ext == ".msg":
        if sep_indices:
            raise ValueError("unexpected '---' separator in .msg file")
        return [("", parse_msg_section_fields(text))]
    if ext == ".srv":
        if len(sep_indices) != 1:
            raise ValueError(f"expected 1 '---' separator in .srv file, found {len(sep_indices)}")
        req = "\n".join(lines[:sep_indices[0]])
        resp = "\n".join(lines[sep_indices[0] + 1:])
        return [
            ("Request", parse_msg_section_fields(req)),
            ("Response", parse_msg_section_fields(resp)),
        ]
    if ext == ".action":
        if len(sep_indices) != 2:
            raise ValueError(f"expected 2 '---' separators in .action file, found {len(sep_indices)}")
        goal = "\n".join(lines[:sep_indices[0]])
        result = "\n".join(lines[sep_indices[0] + 1:sep_indices[1]])
        feedback = "\n".join(lines[sep_indices[1] + 1:])
        return [
            ("Goal", parse_msg_section_fields(goal)),
            ("Result", parse_msg_section_fields(result)),
            ("Feedback", parse_msg_section_fields(feedback)),
        ]
    raise ValueError(f"unsupported extension {ext!r}")


def _strip_idl_comments_and_strings(text: str) -> str:
    """
    Replace string literals, character literals, `//` line comments, and
    `/* ... */` block comments with spaces so brace/struct scanning sees only
    IDL tokens.
    """
    pattern = re.compile(
        r'L?"(?:[^"\\]|\\.)*"'
        r"|L?'(?:[^'\\]|\\.)*'"
        r"|//[^\n]*"
        r"|/\*.*?\*/",
        re.DOTALL,
    )
    return pattern.sub(lambda m: "\n" * m.group(0).count("\n") + " ", text)


def _strip_idl_annotations(text: str) -> str:
    """Remove `@name` and `@name(...)` annotations from cleaned IDL text."""
    out: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == "@":
            i += 1
            while i < n and (text[i].isalnum() or text[i] in "_:"):
                i += 1
            while i < n and text[i].isspace():
                i += 1
            if i < n and text[i] == "(":
                depth = 1
                i += 1
                while i < n and depth > 0:
                    if text[i] == "(":
                        depth += 1
                    elif text[i] == ")":
                        depth -= 1
                    i += 1
            out.append(" ")
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def _parse_idl_struct_members(body: str) -> List[str]:
    """Extract member names from the body of an IDL `struct { ... }`."""
    cleaned = _strip_idl_annotations(body)
    members: List[str] = []
    for stmt in cleaned.split(";"):
        stmt = stmt.strip()
        if not stmt:
            continue
        # Remove template arguments `<...>` (e.g. `sequence<double, 3>`) so
        # commas inside template parameters are not mistaken for declarator
        # separators.
        prev = None
        while prev != stmt:
            prev = stmt
            stmt = re.sub(r"<[^<>]*>", "", stmt)
        # Remove array bounds `[...]` on declarators.
        stmt = re.sub(r"\[[^\]]*\]", "", stmt)
        parts = [p.strip() for p in stmt.split(",") if p.strip()]
        if not parts:
            continue
        # First part has `<type_spec> <first_declarator>`.
        first_tokens = parts[0].split()
        if len(first_tokens) < 2:
            raise ValueError(f"cannot parse IDL struct member {stmt!r}")
        members.append(first_tokens[-1])
        for extra in parts[1:]:
            tokens = extra.split()
            if not tokens:
                raise ValueError(f"cannot parse IDL struct declarator in {stmt!r}")
            members.append(tokens[-1])
    if members == [EMPTY_STRUCT_MEMBER]:
        return []
    return members


def parse_idl_sections(text: str) -> List[Tuple[str, List[str]]]:
    """
    Return `[(section_name, [field_name, ...]), ...]` for an `.idl` file
    (with any trailing proto block already stripped).
    """
    cleaned = _strip_idl_comments_and_strings(text)
    structs: List[Tuple[str, List[str]]] = []
    for m in re.finditer(r"\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{", cleaned):
        name = m.group(1)
        depth = 1
        i = m.end()
        while i < len(cleaned) and depth > 0:
            if cleaned[i] == "{":
                depth += 1
            elif cleaned[i] == "}":
                depth -= 1
            i += 1
        if depth != 0:
            raise ValueError(f"unclosed struct {name!r} in .idl file")
        body = cleaned[m.end():i - 1]
        structs.append((name, _parse_idl_struct_members(body)))

    if not structs:
        raise ValueError("no struct definition found in .idl file")
    if len(structs) == 1:
        return [("", structs[0][1])]
    if (
        len(structs) == 2
        and structs[0][0].endswith("_Request")
        and structs[1][0].endswith("_Response")
    ):
        return [("Request", structs[0][1]), ("Response", structs[1][1])]
    if (
        len(structs) == 3
        and structs[0][0].endswith("_Goal")
        and structs[1][0].endswith("_Result")
        and structs[2][0].endswith("_Feedback")
    ):
        return [
            ("Goal", structs[0][1]),
            ("Result", structs[1][1]),
            ("Feedback", structs[2][1]),
        ]
    return structs


### PURE HELPERS: ASSIGNING & RENDERING PROTO FIELD NUMBERS


def assign_section_numbers(
    sections: Sequence[Tuple[str, Sequence[str]]],
    existing: Optional[Mapping[str, Sequence[Tuple[str, int]]]] = None,
) -> List[Tuple[str, List[Tuple[str, int]]]]:
    """
    Compute `(section_name, [(field_name, field_number), ...])` for each
    section. Existing assignments in `existing` are preserved; any new
    fields in `sections` receive sequential numbers starting after the
    highest assigned number in that section (or from 1 when none exist).
    """
    assigned: List[Tuple[str, List[Tuple[str, int]]]] = []
    for sec_name, fields in sections:
        prev_entries = list(existing.get(sec_name, ())) if existing else []
        prev_map = dict(prev_entries)
        next_num = max(prev_map.values(), default=0) + 1
        active_set = set(fields)
        # Keep existing entries for fields that still exist, in their existing
        # order, then append any newly added fields.
        entries: List[Tuple[str, int]] = [
            (name, num) for name, num in prev_entries if name in active_set
        ]
        seen = {name for name, _ in entries}
        for field in fields:
            if field not in seen:
                entries.append((field, next_num))
                seen.add(field)
                next_num += 1
        assigned.append((sec_name, entries))
    return assigned


def render_proto_block(
    sections: Sequence[Tuple[str, Sequence[Tuple[str, int]]]],
    ext: str,
) -> str:
    """Render the trailing comment block for `.msg`/`.srv`/`.action`/`.idl`."""
    prefix = _comment_prefix(ext)
    lines = [
        f"{prefix} {PROTO_BORDER}",
        f"{prefix} {PROTO_BANNER_TEXT}",
        f"{prefix} {PROTO_BORDER}",
    ]
    for i, (sec_name, entries) in enumerate(sections):
        if i > 0:
            lines.append(prefix)
        header = f"[proto:{sec_name}]" if sec_name else "[proto]"
        lines.append(f"{prefix} {header}")
        for field_name, num in entries:
            lines.append(f"{prefix}   {field_name} = {num}")
    lines.append(f"{prefix} {PROTO_BORDER}")
    return "\n".join(lines) + "\n"


def update_interface_text(text: str, ext: str) -> Tuple[str, Optional[str]]:
    """
    Return `(updated_text, change_kind)` where `change_kind` is:
      - `None` if `text` already has an up-to-date proto block,
      - `"added"` if `text` had no proto block,
      - `"updated"` if `text` had a proto block that needed updating.
    """
    body, existing = split_existing_proto_block(text, ext)
    sections = parse_idl_sections(body) if ext == ".idl" else parse_rosidl_sections(body, ext)
    assigned = assign_section_numbers(sections, existing)
    block = render_proto_block(assigned, ext)
    new_text = (body.rstrip("\n") + "\n\n" + block) if body.strip() else block
    if new_text == text:
        return text, None
    return new_text, (STAT_ADDED if existing is None else STAT_UPDATED)


def check_interface_file(text: str, ext: str, where: str) -> FileCheck:
    """Check one `.msg`/`.srv`/`.action`/`.idl` file and return a `FileCheck`."""
    try:
        new_text, kind = update_interface_text(text, ext)
    except ValueError as e:
        return FileCheck([("parse", f"{where}: {e}")], None, str(e))
    if kind is None:
        return FileCheck([], None)
    msg = "missing [proto] field number block" if kind == STAT_ADDED else "outdated [proto] field number block"
    return FileCheck([(kind, msg)], new_text, stats=collections.Counter({kind: 1}))


### WORKSPACE LAYER


class ProtoFieldAuditor(PackageAuditor):
    """Scans and updates interface files in each vendored package; thread-safe."""

    result_type = ProtoFieldResult

    def _audit(self, package: str, result: ProtoFieldResult) -> None:
        pkg_dir = self.packages[package]
        discovery = discover_interfaces(pkg_dir)
        files = discovery.files
        templates = discovery.templates
        result.interface_count = len(files) + len(templates)
        for w in discovery.warnings:
            result.issues.append(Issue(SEVERITY_WARNING, "discovery", package, w))
        for f in files:
            where = f"{f.bazel_dir}/{f.src}"
            text = f.path.read_text(encoding="utf-8", errors="replace")
            self._apply(result, f.path, where, check_interface_file(text, f.ext, where))
        for t in templates:
            where = f"{t.bazel_dir}/{t.path.name}"
            inner_ext = t.path.with_suffix("").suffix
            text = t.path.read_text(encoding="utf-8", errors="replace")
            self._apply(result, t.path, where, check_interface_file(text, inner_ext, where))


class ProtoFieldReporter(Reporter):
    def __init__(self, total: int, progress: bool, verbose: bool, fix: bool):
        super().__init__(
            total,
            progress,
            verbose,
            fix,
            title="Protobuf field mapping",
            stat_keys=STAT_KEYS,
            stat_noun="interface files",
        )
        self.interfaces = 0

    def done(self, package: str, result: ProtoFieldResult) -> None:
        self.interfaces += result.interface_count
        super().done(package, result)

    def headline(self) -> str:
        return f"{super().headline()}, {self.interfaces} interfaces"


### MAIN


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = make_parser(__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without modifying files in place",
    )
    args = parser.parse_args(argv)
    fix = not args.dry_run
    vendor_dir, packages = load_packages(parser, args)
    candidates = args.packages or sorted(packages)

    def has_interfaces(p: str) -> bool:
        d = discover_interfaces(packages[p])
        return bool(d.files or d.templates)

    selected = [p for p in candidates if args.packages or has_interfaces(p)]
    mode = "dry-run" if args.dry_run else "updating in place"
    print(
        f"Scanning {len(selected)} interface package(s) under {vendor_dir} "
        f"with {args.jobs} thread(s) ({mode})...",
        file=sys.stderr,
    )
    auditor = ProtoFieldAuditor(packages, fix=fix, buildifier=None)
    reporter = ProtoFieldReporter(
        len(selected),
        progress=not args.no_progress,
        verbose=args.verbose,
        fix=fix,
    )
    return run_sweep(packages, selected, auditor, reporter, args.jobs)


if __name__ == "__main__":
    sys.exit(main())

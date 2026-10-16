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
Bring carry-forward module versions in line with a fresh bootstrap.

Module versions that were carried forward (or patched) from an older
bootstrap still carry that bootstrap's boilerplate: a stale "# BCR
dependencies" block (old pins, plus deps a fresh bootstrap no longer
declares, e.g. aspect_rules_py / rules_rust) and, in their overlays,
load() statements for @aspect_rules_py that have since been replaced by
@rules_python.  A freshly bootstrapped version (see
//tools/ci:bootstrap_release) gets exactly BCR_DEPS + BOOTSTRAP_TRAILER;
this chore rewrites every not-yet-published version directory so that it
matches, keeping only what is genuinely per-package (the module() block
and the RCR bazel_dep pins).

For each modules/<package>/<version>/:

  1. MODULE.bazel is re-rendered through bootstrap_release.render_module_dot_bazel()
     with the canned BCR_DEPS block and BOOTSTRAP_TRAILER (module extensions,
     toolchain registration) and the module's own RCR bazel_dep pins --
     including any that were appended *after* the trailer by earlier
     tooling.  A MODULE.bazel with content this script does not recognise
     (hand-written extension stanzas etc.) is left untouched and reported.
  2. Every overlay BUILD/.bzl file loading from @aspect_rules_py//py:defs.bzl
     is rewritten to load the same symbols from @rules_python//python:defs.bzl
     (merging with an existing @rules_python load if there is one).  Symbols
     that have no @rules_python equivalent (e.g. py_image_layer) are left
     alone and reported.
  3. source.json's overlay/patches integrity hashes are regenerated when
     an overlay file changed.

Versions that already exist at --base-ref (default origin/main) are
immutable (see AGENTS.md) and are always skipped; "0.0.0" stubs and
rosdistro (which has a custom MODULE.bazel body) are skipped too.

Usage (from the repo root):

    bazel run //tools/chores:sync_module_boilerplate -- --dry-run
    bazel run //tools/chores:sync_module_boilerplate -- rclcpp rclpy
    bazel run //tools/chores:sync_module_boilerplate
"""

import argparse
import dataclasses
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from tools.ci import bootstrap_release
from tools.ci import bzlmod_lib

# load() labels to migrate, with the symbols the replacement actually
# provides.  Anything else loaded from the old label can't be migrated
# mechanically and is reported instead.
LOAD_MIGRATIONS: Dict[str, Tuple[str, frozenset]] = {
    "@aspect_rules_py//py:defs.bzl": (
        "@rules_python//python:defs.bzl",
        frozenset({"py_binary", "py_library", "py_test"}),
    ),
}

OVERLAY_FILE_GLOBS = ("*.bazel", "*.bzl", "BUILD")

_LOAD_RE = re.compile(r'^load\(\s*"([^"]+)"\s*,\s*(.*?)\)[ \t]*$', re.M | re.S)


### MODULE.bazel

# The parse/re-render core lives next to the template it targets, in
# bootstrap_release (which also uses it to refresh carried-forward versions
# during a bootstrap); re-exported here for the tests and for readers.
ParsedModule = bootstrap_release.ParsedModule
parse_module_dot_bazel = bootstrap_release.parse_module_dot_bazel


def sync_module_dot_bazel_text(text: str) -> Tuple[str, ParsedModule]:
    """
    Returns (new_text, parsed).  new_text == text when nothing needs to
    change.  Raises ValueError when the file can't be safely rewritten.
    """
    return bootstrap_release.refresh_module_dot_bazel(text)


### load() migration


def _split_load_symbols(args_text: str) -> List[str]:
    """'"a", b = "c"' -> ['"a"', 'b = "c"'] (whitespace/trailing-comma tolerant)."""
    parts = [p.strip() for p in args_text.replace("\n", " ").split(",")]
    return [p for p in parts if p]


def _symbol_target(entry: str) -> str:
    """The exported name a load() entry refers to: '"py_test"' or '_t = "py_test"' -> py_test."""
    return entry.split("=")[-1].strip().strip('"')


def _symbol_sort_key(entry: str) -> str:
    # buildifier sorts load() entries by the local (possibly aliased) name.
    local = entry.split("=")[0].strip().strip('"')
    return local


def _render_load(label: str, entries: Iterable[str]) -> str:
    uniq = sorted(dict.fromkeys(entries), key=_symbol_sort_key)
    return f'load("{label}", {", ".join(uniq)})'


def migrate_loads(text: str) -> Tuple[str, List[str]]:
    """
    Rewrite load()s per LOAD_MIGRATIONS, in place (nothing between load
    statements -- license headers, comments -- is disturbed).  If the file
    already loads from the replacement label, the migrated symbols are
    merged into that statement.  Returns (new_text, unsupported) where
    `unsupported` lists symbols left on the old label because the new one
    doesn't provide them.  Statement ordering is left to buildifier.
    """
    unsupported: List[str] = []
    loads = list(_LOAD_RE.finditer(text))
    old = [m for m in loads if m.group(1) in LOAD_MIGRATIONS]
    if not old:
        return text, unsupported
    existing = {m.group(1): m for m in loads if m.group(1) not in LOAD_MIGRATIONS}

    # start offset -> (end offset, {label: entries}); each affected statement
    # is replaced by the load()s in its dict (possibly none).
    stmts: Dict[int, Tuple[int, Dict[str, List[str]]]] = {}
    created: Dict[str, List[str]] = {}

    def slot(m: "re.Match") -> Dict[str, List[str]]:
        return stmts.setdefault(m.start(), (m.end(), {}))[1]

    for m in old:
        old_label = m.group(1)
        new_label, provided = LOAD_MIGRATIONS[old_label]
        entries = _split_load_symbols(m.group(2))
        keep = [e for e in entries if _symbol_target(e) in provided]
        leftover = [e for e in entries if _symbol_target(e) not in provided]
        unsupported.extend(_symbol_target(e) for e in leftover)
        labels = slot(m)
        if keep and new_label in existing:
            dest = existing[new_label]
            slot(dest).setdefault(new_label, _split_load_symbols(dest.group(2))).extend(keep)
        elif keep and new_label in created:
            created[new_label].extend(keep)
        elif keep:
            labels[new_label] = created[new_label] = list(keep)
        if leftover:
            labels[old_label] = leftover

    out = text
    for start in sorted(stmts, reverse=True):
        end, labels = stmts[start]
        replacement = "\n".join(_render_load(label, entries) for label, entries in labels.items())
        if not replacement and text[end:end + 1] == "\n":
            end += 1  # drop the now-empty line too
        out = out[:start] + replacement + out[end:]
    return out, unsupported


def _call_bodies(text: str, names: Tuple[str, ...]) -> List[str]:
    """Bodies (text between the parens) of top-level-ish calls to any of `names`."""
    bodies = []
    for m in re.finditer(r"\b(" + "|".join(names) + r")\(", text):
        depth, i = 1, m.end()
        while i < len(text) and depth:
            depth += {"(": 1, ")": -1}.get(text[i], 0)
            i += 1
        bodies.append(text[m.end():i - 1])
    return bodies


def find_main_less_executables(text: str) -> List[str]:
    """
    Names of py_binary/py_test targets that rely on aspect_rules_py's
    "single src is the main" inference, which rules_python doesn't do
    (it only infers main from <name>.py).  Reported for manual review.
    """
    flagged = []
    for body in _call_bodies(text, ("py_binary", "py_test")):
        if re.search(r"^\s*main\s*=", body, re.M):
            continue
        name = re.search(r'^\s*name\s*=\s*"([^"]+)"', body, re.M)
        srcs = re.search(r'^\s*srcs\s*=\s*\[\s*"([^"]+)",?\s*\]', body, re.M)
        if not name or not srcs:
            continue
        if Path(srcs.group(1)).name != name.group(1) + ".py":
            flagged.append(name.group(1))
    return flagged


def overlay_files(overlay_dir: Path) -> List[Path]:
    files: List[Path] = []
    for pattern in OVERLAY_FILE_GLOBS:
        files.extend(p for p in overlay_dir.rglob(pattern) if p.is_file())
    return sorted(set(files))


### Per-version driver


@dataclasses.dataclass
class VersionReport:
    module_dir: Path
    module_changed: bool = False
    dropped_bcr: Dict[str, str] = dataclasses.field(default_factory=dict)
    stale_bcr: Dict[str, str] = dataclasses.field(default_factory=dict)
    missing_bcr: List[str] = dataclasses.field(default_factory=list)
    overlay_changed: List[Path] = dataclasses.field(default_factory=list)
    unsupported_symbols: Dict[Path, List[str]] = dataclasses.field(default_factory=dict)
    review_targets: Dict[Path, List[str]] = dataclasses.field(default_factory=dict)
    skipped: Optional[str] = None

    @property
    def changed(self) -> bool:
        return self.module_changed or bool(self.overlay_changed)


def sync_version_dir(module_dir: Path, dry_run: bool, buildifier: Optional[str]) -> VersionReport:
    report = VersionReport(module_dir)
    module_dot_bazel = module_dir / "MODULE.bazel"
    text = module_dot_bazel.read_text()
    try:
        new_text, parsed = sync_module_dot_bazel_text(text)
    except ValueError as exc:
        report.skipped = f"MODULE.bazel: {exc}"
        return report
    report.dropped_bcr = parsed.dropped_bcr_deps
    report.stale_bcr = parsed.stale_bcr_deps
    report.missing_bcr = parsed.missing_bcr_deps
    if new_text != text:
        report.module_changed = True
        if not dry_run:
            module_dot_bazel.write_text(new_text)

    overlay_dir = module_dir / "overlay"
    if overlay_dir.is_dir():
        for path in overlay_files(overlay_dir):
            original = path.read_text()
            migrated, unsupported = migrate_loads(original)
            if unsupported:
                report.unsupported_symbols[path] = unsupported
            if migrated == original:
                continue
            report.overlay_changed.append(path)
            flagged = find_main_less_executables(migrated)
            if flagged:
                report.review_targets[path] = flagged
            if not dry_run:
                path.write_text(migrated)
                if buildifier:
                    subprocess.run([buildifier, "-mode", "fix", str(path)], check=False)
        if report.overlay_changed and not dry_run:
            bzlmod_lib.regenerate_integrity_hashes(module_dir)
    return report


def discover_version_dirs(modules_dir: Path, only: Sequence[str]) -> List[Path]:
    dirs = []
    for pkg_dir in sorted(modules_dir.iterdir()):
        if not pkg_dir.is_dir() or pkg_dir.name == "rosdistro":
            continue
        if only and pkg_dir.name not in only:
            continue
        for version_dir in sorted(pkg_dir.iterdir()):
            if version_dir.is_dir() and version_dir.name != "0.0.0" and (version_dir / "MODULE.bazel").is_file():
                dirs.append(version_dir)
    return dirs


def resolve_base_ref(repo_root: Path, base_ref: str) -> str:
    # Same fallback create_patch uses: a fresh clone may only have "main".
    if base_ref == "origin/main" and not bzlmod_lib.git_ref_exists(repo_root, base_ref) \
            and bzlmod_lib.git_ref_exists(repo_root, "main"):
        return "main"
    return base_ref


def published_version_dirs(repo_root: Path, base_ref: str, modules_dir: Path) -> set:
    """
    Every modules/<package>/<version>/ directory (as a path relative to
    repo_root) that already exists at base_ref -- the bulk equivalent of
    bzlmod_lib.is_version_published, since checking ~5k versions one
    `git cat-file` at a time is slow.  Fails closed if base_ref doesn't
    resolve, for the same reason path_exists_at_git_ref does.
    """
    if not bzlmod_lib.git_ref_exists(repo_root, base_ref):
        raise RuntimeError(
            f"git ref {base_ref!r} does not resolve in {repo_root}; fetch it or pass --base-ref"
        )
    rel_modules = modules_dir.relative_to(repo_root).as_posix()
    out = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", base_ref, "--", rel_modules],
        cwd=repo_root, capture_output=True, text=True, check=True,
    ).stdout
    return {
        Path(line).parent for line in out.splitlines()
        if line.endswith("/MODULE.bazel") and line.count("/") == rel_modules.count("/") + 3
    }


def format_summary(reports: Iterable[VersionReport], published: int, repo_root: Path, verbose: bool) -> str:
    reports = list(reports)
    changed = [r for r in reports if r.changed]
    skipped = [r for r in reports if r.skipped]
    lines = [
        f"versions examined: {len(reports)}  (+{published} already published at base ref, left alone)",
        f"MODULE.bazel rewritten: {sum(r.module_changed for r in reports)}",
        f"overlay files with migrated load()s: {sum(len(r.overlay_changed) for r in reports)}",
        f"skipped (unrecognized MODULE.bazel): {len(skipped)}",
    ]
    dropped: Dict[str, int] = {}
    for r in reports:
        for dep in r.dropped_bcr:
            dropped[dep] = dropped.get(dep, 0) + 1
    if dropped:
        lines.append("BCR deps dropped: " + ", ".join(f"{k} x{v}" for k, v in sorted(dropped.items())))
    for r in skipped:
        lines.append(f"  skip {r.module_dir.relative_to(repo_root)}: {r.skipped}")
    for r in reports:
        for path, syms in r.unsupported_symbols.items():
            lines.append(f"  MANUAL {path.relative_to(repo_root)}: no @rules_python equivalent for {', '.join(syms)}")
        for path, names in r.review_targets.items():
            lines.append(f"  REVIEW {path.relative_to(repo_root)}: py_binary/py_test without main= "
                         f"(rules_python won't infer it): {', '.join(names)}")
    if verbose:
        for r in changed:
            bits = []
            if r.module_changed:
                bits.append("MODULE.bazel")
            bits.extend(p.name for p in r.overlay_changed)
            lines.append(f"  {r.module_dir.relative_to(repo_root)}: {', '.join(bits)}")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("packages", nargs="*", help="Only sync these packages (default: every package under modules/)")
    parser.add_argument("--modules-dir", type=Path, default=None, help="Registry directory (default: <repo>/modules)")
    parser.add_argument("--base-ref", default="origin/main",
                        help="Git ref at which a version counts as published/immutable (default: origin/main, "
                             "falling back to main)")
    parser.add_argument("--dry-run", action="store_true", help="Report what would change without writing")
    parser.add_argument("--no-buildifier", action="store_true", help="Don't run buildifier on rewritten overlay files")
    parser.add_argument("--verbose", "-v", action="store_true", help="List every rewritten version directory")
    args = parser.parse_args(argv)

    repo_root = Path(os.environ.get("BUILD_WORKSPACE_DIRECTORY", ".")).resolve()
    modules_dir = (args.modules_dir or repo_root / "modules").resolve()
    if not modules_dir.is_dir():
        parser.error(f"{modules_dir} does not exist")
    unknown = sorted(set(args.packages) - {p.name for p in modules_dir.iterdir()})
    if unknown:
        parser.error(f"not in {modules_dir}: {', '.join(unknown)}")

    buildifier = None if args.no_buildifier else shutil.which("buildifier")
    if not args.no_buildifier and not args.dry_run and buildifier is None:
        print("warning: buildifier not found on PATH; rewritten overlay files won't be re-formatted "
              "(CI's buildifier check may fail on load() ordering)", file=sys.stderr)

    base_ref = resolve_base_ref(repo_root, args.base_ref)
    try:
        published_dirs = published_version_dirs(repo_root, base_ref, modules_dir)
    except RuntimeError as exc:
        parser.error(str(exc))
    reports: List[VersionReport] = []
    published = 0
    for version_dir in discover_version_dirs(modules_dir, args.packages):
        if version_dir.relative_to(repo_root) in published_dirs:
            published += 1
            continue
        reports.append(sync_version_dir(version_dir, args.dry_run, buildifier))

    print(("[dry-run] " if args.dry_run else "") + format_summary(reports, published, repo_root, args.verbose))
    return 0


if __name__ == "__main__":
    sys.exit(main())

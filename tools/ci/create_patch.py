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
Roll a developer's in-place edits to one or more vendored modules (see
//tools/ci:vendor_modules) up into brand-new module versions, e.g.
rclcpp@32.0.0-1.rcr.1 -> rclcpp@32.0.0-1.rcr.2.

Pass an explicit module name to roll up just that module. Omit it to
auto-detect every vendored module with local edits and roll all of them
up at once, after a single confirmation.
"""

import argparse
import base64
import dataclasses
import difflib
import filecmp
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple

from tools.ci import bzlmod_lib
from tools.ci import vendor_modules
from tools.ci.bzlmod_lib import read_module_version


def load_existing_patches_and_overlays(module_dir: Path) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Load the currently-published patches/overlay content for a module
    version, keyed the same way diff_module_source() keys its output, so
    the two can be compared for the no-op case.
    """
    with open(module_dir / "source.json", "r") as f:
        source = json.load(f)
    result = {"patches": {}, "overlay": {}}
    for key in ("patches", "overlay"):
        for rel_path in source.get(key, {}).keys():
            with open(module_dir / key / rel_path, "r") as f:
                result[key][rel_path] = f.read()
    return result["patches"], result["overlay"]


def fetch_raw_upstream(source_json_path: Path, dest_dir: Path) -> None:
    """
    Fetch and extract a module's raw upstream archive (no patches/overlay
    applied) into dest_dir, verifying integrity against source.json.

    This matters because a module version's patches/overlay always
    describe a transformation relative to RAW upstream, not relative to a
    previously-patched version -- every .rcr.N of a package shares the
    same url/integrity/strip_prefix (carried forward by this script's own
    copytree step), so diffing a developer's edits against an
    already-patched reference would silently compute patches that don't
    apply cleanly against upstream once published.
    """
    with open(source_json_path, "r") as f:
        source = json.load(f)
    url = source["url"]
    strip_prefix = source.get("strip_prefix", "")
    expected_integrity = source["integrity"]

    algorithm, expected_digest = expected_integrity.split("-", 1)
    if algorithm != "sha256":
        raise RuntimeError(f"Unsupported integrity algorithm in {source_json_path}: {algorithm}")

    hex_digest = base64.b64decode(expected_digest).hex()
    data = None
    cache_base = Path.home() / ".cache" / "bazel"
    if cache_base.exists():
        for candidate in cache_base.glob(f"*/cache/repos/v1/content_addressable/sha256/{hex_digest}/file"):
            if candidate.is_file():
                candidate_data = candidate.read_bytes()
                if hashlib.sha256(candidate_data).hexdigest() == hex_digest:
                    data = candidate_data
                    break

    if data is None:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as response:
                data = response.read()
        except Exception:
            res = subprocess.run(["curl", "-sL", "-f", "-A", "Mozilla/5.0", url], capture_output=True, check=True)
            data = res.stdout

        actual_digest = base64.b64encode(hashlib.sha256(data).digest()).decode()
        if actual_digest != expected_digest:
            raise RuntimeError(
                f"Integrity check failed fetching {url}: expected {expected_integrity}, "
                f"got sha256-{actual_digest}"
            )

    dest_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as raw_extract_dir_str:
        raw_extract_dir = Path(raw_extract_dir_str)
        archive_path = raw_extract_dir / "archive"
        archive_path.write_bytes(data)
        if url.endswith(".zip"):
            with zipfile.ZipFile(archive_path) as zf:
                zf.extractall(raw_extract_dir)
        else:
            with tarfile.open(archive_path, mode="r:*") as tf:
                tf.extractall(raw_extract_dir, filter="fully_trusted")
        archive_path.unlink()
        extracted_root = raw_extract_dir / strip_prefix if strip_prefix else raw_extract_dir
        for item in extracted_root.iterdir():
            shutil.move(str(item), str(dest_dir / item.name))


def diff_module_source(pristine_dir: Path, edited_dir: Path) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Diff a pristine (unedited) vendored module tree against a developer's
    edited copy. Changed files become unified-diff patches; brand-new
    files become overlays; files deleted by the developer become deletion
    patches. MODULE.bazel is never diffed -- it's authored separately.
    MODULE.bazel.lock is never diffed or added as an overlay -- lockfiles
    belong to the consumer workspace, not individual module packages.
    """
    patches: Dict[str, str] = {}
    overlays: Dict[str, str] = {}
    ignored_names = {"MODULE.bazel", "MODULE.bazel.lock"}

    for edited_file in sorted(edited_dir.rglob("*")):
        if not edited_file.is_file() or edited_file.name in ignored_names:
            continue
        rel_path = edited_file.relative_to(edited_dir)
        pristine_file = pristine_dir / rel_path
        if pristine_file.exists():
            if filecmp.cmp(pristine_file, edited_file, shallow=False):
                continue
            with open(pristine_file, "r") as f_ref, open(edited_file, "r") as f_new:
                ref_lines = [line if line.endswith("\n") else line + "\n" for line in f_ref.readlines()]
                new_lines = [line if line.endswith("\n") else line + "\n" for line in f_new.readlines()]
                diff_lines = list(difflib.unified_diff(
                    ref_lines, new_lines,
                    fromfile=f"a/{rel_path}", tofile=f"b/{rel_path}",
                ))
                if diff_lines:
                    patches[bzlmod_lib.patch_file_name_from_rel_path(rel_path)] = "".join(diff_lines)
        else:
            with open(edited_file, "r") as f:
                overlays[str(rel_path)] = f.read()

    for pristine_file in sorted(pristine_dir.rglob("*")):
        if not pristine_file.is_file() or pristine_file.name in ignored_names:
            continue
        rel_path = pristine_file.relative_to(pristine_dir)
        if not (edited_dir / rel_path).exists():
            with open(pristine_file, "r") as f_ref:
                ref_lines = [line if line.endswith("\n") else line + "\n" for line in f_ref.readlines()]
                diff_lines = list(difflib.unified_diff(
                    ref_lines, [],
                    fromfile=f"a/{rel_path}", tofile="/dev/null",
                ))
                if diff_lines:
                    patches[bzlmod_lib.patch_file_name_from_rel_path(rel_path)] = "".join(diff_lines)

    return patches, overlays


@dataclasses.dataclass
class ModuleRollup:
    """
    Everything needed to print a summary of, and (optionally) write, a new
    patch version for a single vendored module.
    """
    module: str
    current_version: str
    new_version: str
    current_module_dir: Path
    new_module_dir: Path
    vendor_module_dir: Path
    new_patches: Dict[str, str]
    new_overlays: Dict[str, str]
    old_patches: Dict[str, str]
    old_overlays: Dict[str, str]
    overwrite_in_place: bool

    @property
    def changed(self) -> bool:
        if self.module == "rosdistro":
            old_module_dot_bazel = (self.current_module_dir / "MODULE.bazel").read_text()
            new_module_dot_bazel = (self.vendor_module_dir / "MODULE.bazel").read_text()
            if old_module_dot_bazel != new_module_dot_bazel:
                return True
        return self.new_patches != self.old_patches or self.new_overlays != self.old_overlays


def _check_package_dir_not_stale(
    target_workspace: Path, modules_dir: Path, module: str, version: str
) -> None:
    """
    Guards the overwrite-in-place path: raises RuntimeError if
    modules/<module>/<version>/ has changed on disk since this workspace
    vendored it (e.g. a concurrent git pull/checkout/rebase brought in
    someone else's edit to this not-yet-published version) -- blindly
    overwriting in that case would silently discard their change. A
    missing or version-mismatched manifest is treated the same way (can't
    verify), not conservatively skipped, since the failure mode of
    proceeding wrongly here is destructive rather than merely redundant.
    """
    manifest_path = target_workspace / vendor_modules.PACKAGE_MANIFEST_DIR_NAME / f"{module}.json"
    if not manifest_path.exists():
        raise RuntimeError(
            f"No package-directory snapshot found for {module} in this "
            f"workspace ({manifest_path} is missing) -- can't verify "
            f"modules/{module}/{version}/ hasn't changed since vendoring. "
            f"Re-run 'bazel run //tools/ci:vendor_modules -- {module}' "
            "before creating a patch."
        )
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    if manifest.get("version") != version:
        raise RuntimeError(
            f"This workspace vendored {module} at version "
            f"{manifest.get('version')!r}, but is now trying to amend "
            f"{version!r} -- re-run 'bazel run //tools/ci:vendor_modules -- "
            f"{module}' before creating a patch."
        )
    current_hashes = bzlmod_lib.hash_directory_tree(
        modules_dir / module / version, exclude_names=()
    )
    if current_hashes != manifest.get("hashes"):
        raise RuntimeError(
            f"modules/{module}/{version}/ has changed on disk since this "
            "workspace vendored it (likely a concurrent git pull/checkout/"
            "rebase) -- refusing to overwrite it blind. Re-run 'bazel run "
            f"//tools/ci:vendor_modules -- {module}' (if you have no local "
            "edits worth keeping), or 'bazel run //tools/ci:rebase_module "
            f"-- {module}' (to preserve your edits) before creating a "
            "patch."
        )


def compute_rollup(
    module: str, modules_dir: Path, target_workspace: Path,
    repo_root: Path, base_ref: str = "origin/main",
) -> ModuleRollup:
    """
    Fetches raw upstream and diffs it against a vendored module's tree,
    returning everything needed to print a summary and (optionally) write
    a new patch version. Raises RuntimeError for user-facing error
    conditions (missing vendor dir, stale workspace).

    If the module's current_version doesn't yet exist at git ref
    base_ref (i.e. it only exists on the current branch, never merged),
    the rollup overwrites that version in place instead of incrementing
    to a new one -- see bzlmod_lib.is_version_published.
    """
    vendor_module_dir = target_workspace / "vendor" / f"{module}+"
    if not vendor_module_dir.exists():
        raise RuntimeError(
            f"{vendor_module_dir} does not exist. Run "
            f"'bazel run //tools/ci:vendor_modules -- {module}' first."
        )

    # Determine the version Bazel actually resolved for this module (which
    # reflects any single_version_override from setup_workspace), not the
    # textual bazel_dep pin in the root workspace's MODULE.bazel.
    current_version = read_module_version(vendor_module_dir / "MODULE.bazel", module)

    metadata_path = modules_dir / module / "metadata.json"
    metadata = bzlmod_lib.read_metadata_json(metadata_path)
    latest_published = bzlmod_lib.get_latest_non_yanked_version(metadata)
    if bzlmod_lib.version_sort_key(current_version) != bzlmod_lib.version_sort_key(latest_published):
        raise RuntimeError(
            f"this workspace resolved {module} to {current_version}, but the "
            f"latest published version is {latest_published}. This "
            "workspace is stale (likely set up before a concurrent patch "
            "landed). Re-run //tools/ci:setup_workspace, then "
            "//tools/ci:vendor_modules, before creating a patch."
        )

    current_module_dir = modules_dir / module / current_version

    resolved_base_ref = base_ref
    if base_ref == "origin/main" and not bzlmod_lib.git_ref_exists(repo_root, "origin/main") and bzlmod_lib.git_ref_exists(repo_root, "main"):
        resolved_base_ref = "main"

    # A version that only exists on the current branch (never reached
    # base_ref) can be safely amended in place instead of incremented --
    # see is_version_published's docstring for the exact invariant.
    overwrite_in_place = not bzlmod_lib.is_version_published(
        repo_root, resolved_base_ref, current_module_dir
    )
    if overwrite_in_place:
        _check_package_dir_not_stale(target_workspace, modules_dir, module, current_version)

    # Obtain the raw (unpatched) upstream source for diffing -- NOT the
    # currently-published version's vendored tree, since that already has
    # existing patches/overlay applied (see fetch_raw_upstream's docstring
    # for why that distinction matters). Namespaced by module so that
    # auto-detect mode (which calls this in a loop) can't have one
    # module's fetch collide with another's leftovers.
    pristine_root = target_workspace / ".pristine_upstream" / module
    shutil.rmtree(pristine_root, ignore_errors=True)
    try:
        print(f"Fetching raw upstream source for {module} (no patches applied)...")
        fetch_raw_upstream(current_module_dir / "source.json", pristine_root)
        new_patches, new_overlays = diff_module_source(pristine_root, vendor_module_dir)
    except Exception:
        print(
            f"Error occurred while computing the diff for {module}; leaving "
            f"raw upstream reference at {pristine_root} for inspection.",
            file=sys.stderr,
        )
        raise
    else:
        shutil.rmtree(pristine_root, ignore_errors=True)

    old_patches, old_overlays = load_existing_patches_and_overlays(current_module_dir)
    if overwrite_in_place:
        new_version = current_version
        new_module_dir = current_module_dir
    else:
        new_version = bzlmod_lib.increment_version(current_version)
        new_module_dir = modules_dir / module / new_version

    return ModuleRollup(
        module=module,
        current_version=current_version,
        new_version=new_version,
        current_module_dir=current_module_dir,
        new_module_dir=new_module_dir,
        vendor_module_dir=vendor_module_dir,
        new_patches=new_patches,
        new_overlays=new_overlays,
        old_patches=old_patches,
        old_overlays=old_overlays,
        overwrite_in_place=overwrite_in_place,
    )


def print_rollup_summary(rollup: ModuleRollup) -> None:
    if rollup.overwrite_in_place:
        print(
            f"Amending {rollup.module}@{rollup.new_version} in place "
            "(branch-only, not yet published):"
        )
    else:
        print(f"Creating {rollup.module}@{rollup.new_version} (from {rollup.current_version}):")
    print(f"  patches: {len(rollup.new_patches)} (was {len(rollup.old_patches)})")
    print(f"  overlay: {len(rollup.new_overlays)} (was {len(rollup.old_overlays)})")


def apply_rollup(
    rollup: ModuleRollup,
    metadata_path: Path,
    updated_versions: Dict[str, str] = None,
    modules_dir: Path = None,
) -> None:
    if rollup.new_module_dir != rollup.current_module_dir:
        shutil.copytree(rollup.current_module_dir, rollup.new_module_dir, dirs_exist_ok=True)
    shutil.rmtree(rollup.new_module_dir / "patches", ignore_errors=True)
    shutil.rmtree(rollup.new_module_dir / "overlay", ignore_errors=True)
    for patch_name, content in rollup.new_patches.items():
        patch_path = rollup.new_module_dir / "patches" / patch_name
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        patch_path.write_text(content)
    for overlay_name, content in rollup.new_overlays.items():
        overlay_path = rollup.new_module_dir / "overlay" / overlay_name
        overlay_path.parent.mkdir(parents=True, exist_ok=True)
        overlay_path.write_text(content)

    module_file = rollup.new_module_dir / "MODULE.bazel"
    if rollup.module == "rosdistro":
        shutil.copy2(rollup.vendor_module_dir / "MODULE.bazel", module_file)

    content = module_file.read_text()
    content = bzlmod_lib.rewrite_module_version(content, rollup.module, rollup.new_version)

    modules_path = modules_dir or rollup.new_module_dir.parent.parent
    if module_file.exists():
        deps = bzlmod_lib.scan_module_for_dependencies(module_file, modules_path)
        for dep_name, pinned_ver in deps.items():
            target_ver = None
            if updated_versions and dep_name in updated_versions:
                target_ver = updated_versions[dep_name]
            elif (modules_path / dep_name / "metadata.json").exists():
                try:
                    meta = bzlmod_lib.read_metadata_json(modules_path / dep_name / "metadata.json")
                    target_ver = bzlmod_lib.get_latest_matching_patch_version(pinned_ver, meta)
                except Exception:
                    target_ver = None

            if target_ver and target_ver != pinned_ver:
                if bzlmod_lib.version_sort_key(target_ver) > bzlmod_lib.version_sort_key(pinned_ver):
                    content = bzlmod_lib.rewrite_bazel_dep_version(content, dep_name, target_ver)

    module_file.write_text(content)
    bzlmod_lib.regenerate_integrity_hashes(rollup.new_module_dir)
    bzlmod_lib.add_version_to_metadata_json(metadata_path, rollup.new_version)


def discover_vendored_modules(target_workspace: Path, modules_dir: Path) -> List[str]:
    """
    Lists every module currently vendored into this workspace: every
    "<name>+" directory under vendor/ (Bazel's canonical-repo-name suffix
    for a bazel_dep) that corresponds to a declared RCR module.
    """
    vendor_dir = target_workspace / "vendor"
    if not vendor_dir.exists():
        return []
    modules = []
    for entry in sorted(vendor_dir.iterdir()):
        if entry.is_dir() and entry.name.endswith("+") and (modules_dir / entry.name[:-1]).exists():
            modules.append(entry.name[:-1])
    return modules


def module_has_local_edits(target_workspace: Path, module: str) -> bool:
    """
    Cheap, network-free check for whether a vendored module's files differ
    from the manifest snapshot //tools/ci:vendor_modules records right
    after vendoring. Conservatively returns True if no manifest exists
    (e.g. it was vendored before this workspace had one), so the module
    still gets checked by the full upstream diff rather than silently
    skipped.
    """
    manifest_path = target_workspace / vendor_modules.VENDOR_MANIFEST_DIR_NAME / f"{module}.json"
    if not manifest_path.exists():
        return True
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    vendor_module_dir = target_workspace / "vendor" / f"{module}+"
    return bzlmod_lib.hash_directory_tree(vendor_module_dir) != manifest


def confirm(prompt: str) -> bool:
    return input(prompt).strip().lower() in ("y", "yes")


def main():
    parser = argparse.ArgumentParser(
        description="Roll a developer's in-place edits to one or more "
        "vendored modules up into new module version(s), from edits made "
        "via //tools/ci:vendor_modules."
    )
    parser.add_argument(
        "module",
        nargs="?",
        help="Name of the module to create a patch for, e.g. rclcpp. If "
        "omitted, auto-detects every vendored module with local edits and "
        "rolls all of them up after a single confirmation.",
    )
    parser.add_argument(
        "--workspace-dir",
        type=Path,
        default=Path("workspace"),
        help="Workspace directory created by //tools/ci:setup_workspace",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute and print what would happen, but don't write anything",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="In auto-detect mode, skip the confirmation prompt.",
    )
    parser.add_argument(
        "--base-ref",
        default="origin/main",
        help="Git ref a version must already exist at to be treated "
        "as published/immutable; versions that only exist on the current "
        "branch relative to this ref are amended in place instead of "
        "incremented. Defaults to 'origin/main'.",
    )
    args = parser.parse_args()

    workspace_root = Path(os.environ.get("BUILD_WORKSPACE_DIRECTORY", ".")).resolve()
    modules_dir = workspace_root / "modules"
    target_workspace = (workspace_root / args.workspace_dir).resolve()

    module_dot_bazel = target_workspace / "MODULE.bazel"
    if not module_dot_bazel.exists():
        print(
            f"Error: {module_dot_bazel} does not exist. Run "
            "//tools/ci:setup_workspace first.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.module:
        try:
            rollup = compute_rollup(
                args.module, modules_dir, target_workspace, workspace_root, args.base_ref
            )
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        if not rollup.changed:
            print(f"No changes detected for {args.module}; nothing to do.")
            return

        print_rollup_summary(rollup)
        if args.dry_run:
            print("Dry run: no files written.")
            return

        apply_rollup(
            rollup,
            modules_dir / args.module / "metadata.json",
            updated_versions={rollup.module: rollup.new_version},
            modules_dir=modules_dir,
        )
        print(f"Done. modules/{args.module}/{rollup.new_version}/ is ready to commit as a PR.")
        return

    # Auto-detect mode: find vendored modules, cheaply filter to those with
    # local edits, then confirm the real (upstream-diffed) changes before
    # rolling anything up.
    candidates = [
        m for m in discover_vendored_modules(target_workspace, modules_dir)
        if module_has_local_edits(target_workspace, m)
    ]
    if not candidates:
        print("No vendored modules have local edits; nothing to do.")
        return

    rollups = []
    for module in candidates:
        try:
            rollup = compute_rollup(
                module, modules_dir, target_workspace, workspace_root, args.base_ref
            )
        except RuntimeError as e:
            print(f"Warning: skipping {module}: {e}", file=sys.stderr)
            continue
        if rollup.changed:
            rollups.append(rollup)

    if not rollups:
        print("No changes detected in any vendored module; nothing to do.")
        return

    print(f"Detected changes in {len(rollups)} vendored module(s):")
    for rollup in rollups:
        print_rollup_summary(rollup)

    if args.dry_run:
        print("Dry run: no files written.")
        return

    if not args.yes and not confirm(
        f"Roll up {len(rollups)} module(s) into new patch versions? [y/N]: "
    ):
        print("Aborted; no files written.")
        return

    updated_versions = {r.module: r.new_version for r in rollups}
    for rollup in rollups:
        apply_rollup(
            rollup,
            modules_dir / rollup.module / "metadata.json",
            updated_versions=updated_versions,
            modules_dir=modules_dir,
        )
        print(f"Done. modules/{rollup.module}/{rollup.new_version}/ is ready to commit as a PR.")


if __name__ == "__main__":
    main()

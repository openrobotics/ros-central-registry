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
Vendor a set of modules into a Bazel workspace created by
//tools/ci:setup_workspace, so their sources can be edited in place.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Set

from tools.ci.bzlmod_lib import hash_directory_tree, read_module_version, scan_module_for_dependencies
from tools.ci.setup_workspace import VARIANTS

VENDOR_DIR_RC_LINE = "common --vendor_dir=vendor"

# Where per-module file-hash snapshots are recorded right after vendoring,
# so //tools/ci:create_patch can later detect local edits without a
# network fetch (see create_patch.module_has_local_edits).
VENDOR_MANIFEST_DIR_NAME = ".vendor_manifest"

# Where per-module file-hash snapshots of the PACKAGED modules/<module>/
# <version>/ directory (not the exploded vendor tree) are recorded right
# after vendoring, so //tools/ci:create_patch's overwrite-in-place mode can
# detect on-disk drift since vendoring before blindly overwriting it (see
# create_patch._check_package_dir_not_stale).
PACKAGE_MANIFEST_DIR_NAME = ".package_manifest"

# Where a full-content copy of the freshly-vendored tree is kept per
# module, so //tools/ci:rebase_module can later diff a developer's edits
# against it (hashes alone can't reconstruct lost content once the
# packaged module dir is the thing that drifted).
VENDOR_SNAPSHOT_DIR_NAME = ".vendor_snapshot"

# setup_workspace.VARIANTS maps a short workspace-file key (e.g. "core") to
# the ROS variant package name it corresponds to (e.g. "ros_core"), and
# writes the packages that belong to it into a "ros-<key>.txt" target
# pattern file. We expose the variant package names as the --variant
# choices here, and use the inverse mapping to find the right file.
VARIANT_KEY_BY_NAME = {package: key for key, package in VARIANTS.items()}
VARIANT_CHOICES = sorted(VARIANT_KEY_BY_NAME)


def declared_module_names(module_dot_bazel: Path, modules_dir: Path) -> set:
    """Every bazel_dep in the workspace, RCR packages and BCR modules alike."""
    return set(
        scan_module_for_dependencies(
            module_dot_bazel, modules_dir, include_bcr=True, include_rcr=True
        ).keys()
    )


def declared_rcr_module_names(module_dot_bazel: Path, modules_dir: Path) -> set:
    """
    Only the bazel_deps that are RCR packages (i.e. have a modules/<name>/
    directory in this registry). This is what --all expands to: BCR modules
    such as `platforms` or `rules_cc` are not something you'd vendor to edit
    in place, and Bazel doesn't even materialize some of them (e.g.
    `platforms`) under --vendor_dir.
    """
    return set(
        scan_module_for_dependencies(
            module_dot_bazel, modules_dir, include_bcr=False, include_rcr=True
        ).keys()
    )


def parse_module_tokens(tokens: Iterable[str]) -> List[str]:
    """
    Splits each token on whitespace/commas, so a single quoted argument
    like "rclcpp rclcpp_action rclcpp_lifecycle" (or comma-separated)
    behaves the same as passing each module as its own argument.
    """
    modules = []
    for token in tokens:
        for part in re.split(r"[\s,]+", token.strip()):
            if part:
                modules.append(part)
    return modules


def modules_for_variant(target_workspace: Path, variant: str) -> List[str]:
    """
    Reads the ros-<variant>.txt target-pattern file written by
    //tools/ci:setup_workspace (lines look like "@rclcpp//...") and
    returns the bare module names it lists. Raises FileNotFoundError if
    that variant wasn't generated for this workspace.
    """
    key = VARIANT_KEY_BY_NAME[variant]
    variant_file = target_workspace / f"ros-{key}.txt"
    modules = []
    for line in variant_file.read_text().splitlines():
        line = line.strip()
        if line:
            modules.append(line.lstrip("@").split("//", 1)[0])
    return modules


def resolve_modules(
    module_args: List[str],
    variants: List[str],
    vendor_all: bool,
    target_workspace: Path,
    declared: Set[str],
) -> List[str]:
    """
    Combines explicit module names, --variant selections, and/or --all
    into a single deduplicated, order-preserving list of module names to
    vendor. For --all, `declared` should be the RCR-only set (see
    declared_rcr_module_names).
    """
    if vendor_all:
        return sorted(declared)
    modules = parse_module_tokens(module_args)
    for variant in variants:
        modules += modules_for_variant(target_workspace, variant)
    return list(dict.fromkeys(modules))


def vendored_module_dir(target_workspace: Path, module: str) -> Path:
    return target_workspace / "vendor" / f"{module}+"


def was_vendored(target_workspace: Path, module: str) -> bool:
    """
    Whether `bazel vendor` actually materialized this module. Bazel quietly
    skips some repos it won't vendor (built-in modules like `platforms`),
    and still reports success for the overall command.
    """
    return (vendored_module_dir(target_workspace, module) / "MODULE.bazel").is_file()


def write_vendor_manifest(target_workspace: Path, module: str) -> None:
    """
    Snapshots the file hashes of a freshly-vendored module tree, so a
    later //tools/ci:create_patch run can cheaply tell whether it's been
    edited since, without re-fetching upstream just to check.
    """
    vendor_module_dir = target_workspace / "vendor" / f"{module}+"
    manifest_path = target_workspace / VENDOR_MANIFEST_DIR_NAME / f"{module}.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    hashes = hash_directory_tree(vendor_module_dir)
    with open(manifest_path, "w") as f:
        json.dump(hashes, f, indent=4, sort_keys=True)
        f.write("\n")


def write_package_manifest(target_workspace: Path, modules_dir: Path, module: str, version: str) -> None:
    """
    Snapshots file hashes of modules/<module>/<version>/ itself (the
    PACKAGED directory //tools/ci:create_patch's overwrite-in-place mode
    later reads/overwrites -- not workspace/vendor/<module>+/), keyed by
    the version it was taken at. Lets create_patch detect on-disk drift
    (e.g. a concurrent git pull/checkout/rebase brought in someone else's
    edit to this not-yet-published version) before blindly overwriting.
    Unlike write_vendor_manifest, this does NOT exclude MODULE.bazel --
    drift there is exactly what this guard exists to catch.
    """
    module_dir = modules_dir / module / version
    manifest_path = target_workspace / PACKAGE_MANIFEST_DIR_NAME / f"{module}.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    hashes = hash_directory_tree(module_dir, exclude_names=())
    with open(manifest_path, "w") as f:
        json.dump({"version": version, "hashes": hashes}, f, indent=4, sort_keys=True)
        f.write("\n")


def write_vendor_snapshot(target_workspace: Path, module: str) -> None:
    """
    Full-content copy of the freshly-vendored tree into
    workspace/.vendor_snapshot/<module>+/, replacing any prior snapshot.
    File-hash manifests are enough to detect that a developer edited
    something, but not to reconstruct what it looked like beforehand --
    this snapshot is the baseline //tools/ci:rebase_module diffs a
    developer's later edits against when recovering from a stale
    workspace.
    """
    vendor_module_dir = target_workspace / "vendor" / f"{module}+"
    snapshot_dir = target_workspace / VENDOR_SNAPSHOT_DIR_NAME / f"{module}+"
    shutil.rmtree(snapshot_dir, ignore_errors=True)
    shutil.copytree(vendor_module_dir, snapshot_dir, symlinks=True)


def ensure_vendor_dir_flag(bazelrc: Path) -> None:
    """
    Older workspaces may have been created before setup_workspace started
    writing --vendor_dir into the .bazelrc. Patch it in so builds/tests in
    this workspace actually read from the vendored sources.
    """
    content = bazelrc.read_text()
    if VENDOR_DIR_RC_LINE in content:
        return
    with open(bazelrc, "a") as f:
        f.write(f"\n{VENDOR_DIR_RC_LINE}\n")


def clear_vendored_module(target_workspace: Path, module: str) -> bool:
    """
    Removes a previously vendored copy of `module` (its vendor/<module>+/
    tree and vendor/@<module>+.marker) so the following `bazel vendor`
    re-extracts it from the registry's *current* content.

    `bazel vendor` keys its "already vendored, nothing to do" check on the
    marker file, which can stay stale after modules/<module>/<version>/
    changed on disk (e.g. create_patch amended a branch-only version in
    place). Bazel then silently ignores the vendored tree and builds from
    the registry copy instead, so in-place edits appear to have no effect.
    Re-vendoring is documented as resetting the module anyway, so always
    start from a clean slate. Returns True if anything was removed.
    """
    vendor_dir = target_workspace / "vendor"
    removed = False
    module_dir = vendor_dir / f"{module}+"
    marker = vendor_dir / f"@{module}+.marker"
    if module_dir.exists():
        shutil.rmtree(module_dir)
        removed = True
    if marker.exists():
        marker.unlink()
        removed = True
    return removed


def main():
    parser = argparse.ArgumentParser(
        description="Vendor a set of modules into a Bazel workspace for "
        "in-place editing, e.g. to test local patches."
    )
    parser.add_argument(
        "modules",
        nargs="*",
        default=[],
        help="Names of modules to vendor, e.g. rclcpp rmw_fastrtps_cpp. "
        "A single space- or comma-separated string is also accepted, "
        'e.g. "rclcpp rclcpp_action rclcpp_lifecycle".',
    )
    parser.add_argument(
        "--variant",
        nargs="+",
        choices=VARIANT_CHOICES,
        default=[],
        help="Vendor every module belonging to one or more canned ROS "
        "variants (as generated by //tools/ci:setup_workspace).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Vendor every module declared as a bazel_dep in the workspace.",
    )
    parser.add_argument(
        "--workspace-dir",
        type=Path,
        default=Path("workspace"),
        help="Workspace directory created by //tools/ci:setup_workspace",
    )
    args = parser.parse_args()

    if args.all and (args.modules or args.variant):
        parser.error("--all cannot be combined with explicit modules or --variant.")
    if not args.modules and not args.variant and not args.all:
        parser.error("Specify at least one module, --variant <name>, or --all.")

    workspace_root = Path(
        os.environ.get("BUILD_WORKSPACE_DIRECTORY", ".")
    ).resolve()
    target_workspace = (workspace_root / args.workspace_dir).resolve()
    module_dot_bazel = target_workspace / "MODULE.bazel"
    bazelrc = target_workspace / ".bazelrc"

    if not module_dot_bazel.exists():
        print(
            f"Error: {module_dot_bazel} does not exist. Run "
            "//tools/ci:setup_workspace first.",
            file=sys.stderr,
        )
        sys.exit(1)

    declared = declared_module_names(module_dot_bazel, workspace_root / "modules")
    declared_rcr = declared_rcr_module_names(module_dot_bazel, workspace_root / "modules")

    try:
        modules = resolve_modules(
            args.modules, args.variant, args.all, target_workspace,
            declared_rcr if args.all else declared,
        )
    except FileNotFoundError as e:
        print(
            f"Error: {e}. Run //tools/ci:setup_workspace first to generate "
            "the ros-<variant>.txt target-pattern files.",
            file=sys.stderr,
        )
        sys.exit(1)

    unknown = [m for m in modules if m not in declared]
    if unknown:
        print(
            f"Error: {', '.join(unknown)} not declared as bazel_dep in "
            f"{module_dot_bazel}.",
            file=sys.stderr,
        )
        sys.exit(1)

    ensure_vendor_dir_flag(bazelrc)

    for module in modules:
        if clear_vendored_module(target_workspace, module):
            print(f"Discarding previously vendored {module} (re-vendoring from current modules/).")

    cmd = ["bazel", "vendor", "--vendor_dir=vendor"]
    cmd += [f"--repo=@{m}" for m in modules]
    print(f"Vendoring {', '.join(modules)} into "
          f"{target_workspace / 'vendor'}...")
    subprocess.run(cmd, cwd=target_workspace, check=True)

    skipped = []
    for module in modules:
        if not was_vendored(target_workspace, module):
            # `bazel vendor` reports success even for repos it declines to
            # materialize (e.g. the built-in `platforms` module); don't let
            # one of those abort the bookkeeping for everything after it.
            skipped.append(module)
            continue
        write_vendor_manifest(target_workspace, module)
        version = read_module_version(
            vendored_module_dir(target_workspace, module) / "MODULE.bazel", module
        )
        write_package_manifest(target_workspace, workspace_root / "modules", module, version)
        write_vendor_snapshot(target_workspace, module)

    if skipped:
        print(
            f"Warning: bazel vendor did not materialize {', '.join(skipped)} "
            f"under {target_workspace / 'vendor'}; skipped.",
            file=sys.stderr,
        )

    print(
        "Done. Edit sources under "
        f"{target_workspace / 'vendor'} to test local patches; "
        "builds/tests in this workspace will pick them up automatically."
    )


if __name__ == "__main__":
    main()

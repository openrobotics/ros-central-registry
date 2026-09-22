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
Weekly patch rollup: update the distribution's top-level variant modules
(ros, ros_core, ros_base, perception, simulation, desktop, desktop_full)
to point to the latest matching patch versions of their member packages,
and increment each variant module to the next .rcr.N release.

Relies on Bazel's Minimal Version Selection (MVS) to resolve transitive
dependencies to their latest patch versions at build time without
churning/copying non-variant packages.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, Tuple

from tools.ci import bzlmod_lib

VARIANT_MODULES = [
    "ros",
    "ros_core",
    "ros_base",
    "perception",
    "simulation",
    "desktop",
    "desktop_full",
]


def find_current_ros_version(modules_dir: Path, distro: str, date: str) -> str:
    """
    Find the highest-numbered .rcr.N release for the given <distro>.<date>
    row under modules/ros/.
    """
    candidates = []
    ros_dir = modules_dir / "ros"
    if not ros_dir.exists():
        raise RuntimeError(f"No ros directory found at {ros_dir}")
    for entry in ros_dir.iterdir():
        if not entry.is_dir():
            continue
        parts = entry.name.split(".")
        if len(parts) != 4 or parts[0] != distro or parts[1] != date or parts[2] != "rcr":
            continue
        if not parts[3].isdigit():
            continue
        candidates.append((int(parts[3]), entry.name))
    if not candidates:
        raise RuntimeError(
            f"No .rcr.N release found for {distro}.{date} under {ros_dir}; "
            "a rollup requires at least one existing patch release to build on."
        )
    return max(candidates)[1]


def get_base_version(version: str) -> str:
    """
    Strips the trailing .rcr.N patch suffix from an RCR version string.
    e.g. '32.0.0-1.rcr.1' -> '32.0.0-1'
         'lyrical.2026-06-08.rcr.1' -> 'lyrical.2026-06-08'
         '1.0.0' -> '1.0.0'
    """
    parts = version.split(".")
    if len(parts) >= 2 and parts[-2] == "rcr" and parts[-1].isdigit():
        return ".".join(parts[:-2])
    return version


def get_latest_matching_patch_version(pinned_version: str, metadata: Dict) -> str:
    """
    Finds the highest non-yanked version in metadata sharing the exact same
    base upstream version as pinned_version. Never crosses to a different
    upstream release (e.g. 1.0.0.rcr.1 -> 1.0.0.rcr.2, ignoring 2.0.0.rcr.1).
    """
    yanked = metadata.get("yanked_versions", {})
    available = [v for v in metadata.get("versions", []) if v not in yanked]
    base = get_base_version(pinned_version)
    matching = [v for v in available if get_base_version(v) == base]
    if not matching:
        return pinned_version
    return max(matching, key=bzlmod_lib.version_sort_key)


def check_no_yanked_dependencies(packages: Dict[str, str], modules_dir: Path) -> None:
    """
    Refuse to roll up on top of a currently-referenced package version
    that's already yanked -- that's a pre-existing data-integrity problem
    this rollup didn't cause and shouldn't silently build on top of.
    """
    for name, pinned_version in packages.items():
        meta_path = modules_dir / name / "metadata.json"
        if not meta_path.exists():
            continue
        metadata = bzlmod_lib.read_metadata_json(meta_path)
        yanked = metadata.get("yanked_versions", {})
        if pinned_version in yanked:
            raise RuntimeError(
                f"{name}@{pinned_version} is referenced by the current release "
                f"but is yanked ({yanked[pinned_version]}); refusing to roll up on "
                "top of a yanked dependency."
            )


def rollup_variants(modules_dir: Path, distro: str, date: str, dry_run: bool = False) -> str:
    current_ros_version = find_current_ros_version(modules_dir, distro, date)
    new_ros_version = bzlmod_lib.increment_version(current_ros_version)
    print(f"Current ros release: {current_ros_version}")

    # Determine which variant modules exist for this release
    active_variants = [
        v for v in VARIANT_MODULES
        if (modules_dir / v / current_ros_version / "MODULE.bazel").exists()
    ]
    if not active_variants:
        raise RuntimeError(f"No variant modules found for {current_ros_version} under {modules_dir}")

    # Collect all current dependencies across all active variants
    variant_deps: Dict[str, Dict[str, str]] = {}
    all_packages: Dict[str, str] = {}
    for variant in active_variants:
        module_file = modules_dir / variant / current_ros_version / "MODULE.bazel"
        deps = bzlmod_lib.scan_module_for_dependencies(module_file, modules_dir)
        variant_deps[variant] = deps
        all_packages.update(deps)

    check_no_yanked_dependencies(all_packages, modules_dir)

    # Compute the latest matching patch version for every referenced package
    target_package_versions: Dict[str, str] = {}
    changed_packages: Dict[str, Tuple[str, str]] = {}
    for name, pinned_version in all_packages.items():
        if name in VARIANT_MODULES:
            continue
        meta_path = modules_dir / name / "metadata.json"
        if not meta_path.exists():
            target_package_versions[name] = pinned_version
            continue
        metadata = bzlmod_lib.read_metadata_json(meta_path)
        latest_patch = get_latest_matching_patch_version(pinned_version, metadata)
        target_package_versions[name] = latest_patch
        if latest_patch != pinned_version:
            changed_packages[name] = (pinned_version, latest_patch)

    if not changed_packages:
        print(
            f"Nothing to roll up -- every package referenced by {current_ros_version} "
            "is already at its latest matching patch version."
        )
        return current_ros_version

    print(f"Found {len(changed_packages)} package(s) with newer matching patches:")
    for name, (old_v, new_v) in sorted(changed_packages.items()):
        print(f"  {name}: {old_v} -> {new_v}")

    # Materialize each active variant at the new release version
    for variant in active_variants:
        old_dir = modules_dir / variant / current_ros_version
        new_dir = modules_dir / variant / new_ros_version
        print(f"Rolling up variant '{variant}': {current_ros_version} -> {new_ros_version}...")

        content = (old_dir / "MODULE.bazel").read_text()
        content = bzlmod_lib.rewrite_module_version(content, variant, new_ros_version)

        # Rewrite other variant dependencies
        for other_variant in active_variants:
            if other_variant == variant:
                continue
            if f'name = "{other_variant}"' in content:
                content = bzlmod_lib.rewrite_bazel_dep_version(content, other_variant, new_ros_version)

        # Rewrite package dependencies
        for pkg_name, (_old_v, new_v) in changed_packages.items():
            if f'name = "{pkg_name}"' in content:
                content = bzlmod_lib.rewrite_bazel_dep_version(content, pkg_name, new_v)

        if not dry_run:
            shutil.copytree(old_dir, new_dir, dirs_exist_ok=True)
            (new_dir / "MODULE.bazel").write_text(content)
            bzlmod_lib.add_version_to_metadata_json(modules_dir / variant / "metadata.json", new_ros_version)

    if dry_run:
        print("Dry run: no files written.")
    else:
        print(f"Rolled up to ros version {new_ros_version}.")

    return new_ros_version


def main():
    parser = argparse.ArgumentParser(
        description="Roll up variant modules to reference latest package patches."
    )
    parser.add_argument(
        "--release",
        required=True,
        help="<distribution>.<date> row to roll up, e.g. lyrical.2026-06-08",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute and print what would happen, but don't write anything",
    )
    args = parser.parse_args()

    release_parts = args.release.split(".")
    if len(release_parts) != 2:
        print(f"Error: --release must be <distribution>.<date>, got {args.release!r}", file=sys.stderr)
        sys.exit(1)
    distro, date = release_parts

    repo_root = Path(os.environ.get("BUILD_WORKSPACE_DIRECTORY", ".")).resolve()
    modules_dir = repo_root / "modules"

    rollup_variants(modules_dir, distro, date, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

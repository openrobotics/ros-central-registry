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
from collections import deque
from pathlib import Path
from typing import Dict, List, Tuple

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


get_base_version = bzlmod_lib.get_base_version
get_latest_matching_patch_version = bzlmod_lib.get_latest_matching_patch_version


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


def propagate_transitive_patches(
    modules_dir: Path,
    active_variants: List[str],
    current_ros_version: str,
    dry_run: bool = False,
) -> Dict[str, Tuple[str, str]]:
    """
    Propagates patch updates through transitive dependencies in the distribution.

    1. Discovers all packages and their active versions in the distribution release.
    2. Builds the dependency graph of reachable packages.
    3. Finds unpinned packages in the closure of active variants with newer patches.
    4. Finds the tree of module paths connecting those unpinned packages to the
       direct dependencies of active variants.
    5. Resolves the target versions (at most one version bump per module).
    6. Materializes the updated packages with their bazel_dep references updated.

    Returns a dict of package name -> (old_version, new_version) for all packages
    that received dep-only version bumps.
    """
    # 1. Discover all packages and their currently referenced versions by traversing from active variants
    current_graph_versions: Dict[str, str] = {}
    queue: list[str] = []
    for variant in active_variants:
        v_module_file = modules_dir / variant / current_ros_version / "MODULE.bazel"
        if not v_module_file.exists():
            continue
        deps = bzlmod_lib.scan_module_for_dependencies(v_module_file, modules_dir)
        for dep_name, pinned_ver in deps.items():
            if dep_name not in VARIANT_MODULES and dep_name != "rosdistro":
                if dep_name not in current_graph_versions or bzlmod_lib.version_sort_key(pinned_ver) > bzlmod_lib.version_sort_key(current_graph_versions[dep_name]):
                    current_graph_versions[dep_name] = pinned_ver
                    queue.append(dep_name)

    while queue:
        pkg = queue.pop(0)
        ver = current_graph_versions[pkg]
        module_file = modules_dir / pkg / ver / "MODULE.bazel"
        if not module_file.exists():
            continue
        deps = bzlmod_lib.scan_module_for_dependencies(module_file, modules_dir)
        for dep_name, pinned_ver in deps.items():
            if dep_name not in VARIANT_MODULES and dep_name != "rosdistro":
                if dep_name not in current_graph_versions:
                    current_graph_versions[dep_name] = pinned_ver
                    queue.append(dep_name)

    if not current_graph_versions:
        return {}

    # 2. Determine latest matching patch on disk for every reachable package
    latest_on_disk: Dict[str, str] = {}
    for pkg, pinned_ver in current_graph_versions.items():
        meta_path = modules_dir / pkg / "metadata.json"
        if meta_path.exists():
            meta = bzlmod_lib.read_metadata_json(meta_path)
            latest_on_disk[pkg] = bzlmod_lib.get_latest_matching_patch_version(pinned_ver, meta)
        else:
            latest_on_disk[pkg] = pinned_ver

    # 3. Collect packages directly pinned across sub-variants (excluding VARIANT_MODULES and rosdistro)
    union_direct: set[str] = set()
    for variant in active_variants:
        if variant == "ros":
            continue
        v_module_file = modules_dir / variant / current_ros_version / "MODULE.bazel"
        if not v_module_file.exists():
            continue
        deps = bzlmod_lib.scan_module_for_dependencies(v_module_file, modules_dir)
        for dep_name in deps:
            if dep_name not in VARIANT_MODULES and dep_name != "rosdistro":
                union_direct.add(dep_name)

    # If no sub-variants exist (e.g. in test fixtures where only "ros" exists),
    # use the direct dependencies of the "ros" module
    if not union_direct:
        ros_module_file = modules_dir / "ros" / current_ros_version / "MODULE.bazel"
        if ros_module_file.exists():
            deps = bzlmod_lib.scan_module_for_dependencies(ros_module_file, modules_dir)
            union_direct = {d for d in deps if d not in VARIANT_MODULES and d != "rosdistro"}
        else:
            union_direct = set(current_graph_versions.keys())

    # 4. Build dependency graph and reverse dependencies across all reachable packages
    pkg_deps: Dict[str, Dict[str, str]] = {}
    dependents: Dict[str, set[str]] = {}
    for pkg, ver in latest_on_disk.items():
        module_file = modules_dir / pkg / ver / "MODULE.bazel"
        if not module_file.exists():
            continue
        deps = bzlmod_lib.scan_module_for_dependencies(module_file, modules_dir)
        pkg_deps[pkg] = {
            k: v for k, v in deps.items()
            if k not in VARIANT_MODULES and k != "rosdistro"
        }
        for dep_name in pkg_deps[pkg]:
            dependents.setdefault(dep_name, set()).add(pkg)

    # 5. Transitive closure of packages reachable from union_direct
    closure: set[str] = set(union_direct)
    c_queue = list(union_direct)
    while c_queue:
        curr = c_queue.pop(0)
        for dep in pkg_deps.get(curr, {}):
            if dep not in closure:
                closure.add(dep)
                c_queue.append(dep)

    # 6. Unpinned packages in closure that have newer patches on disk
    unpinned_patched: set[str] = {
        pkg for pkg in closure - union_direct
        if bzlmod_lib.version_sort_key(latest_on_disk[pkg]) > bzlmod_lib.version_sort_key(current_graph_versions[pkg])
    }

    if not unpinned_patched:
        return {}

    # 7. Compute minimum distance to union_direct for each unpinned package
    min_dist: Dict[str, int] = {}
    for u in unpinned_patched:
        q_dist = deque([(u, 0)])
        vis_dist = {u}
        while q_dist:
            curr, d = q_dist.popleft()
            if curr in union_direct:
                min_dist[u] = d
                break
            for p in dependents.get(curr, ()):
                if p in closure and p not in vis_dist:
                    vis_dist.add(p)
                    q_dist.append((p, d + 1))

    # Process nodes closest to union_direct first so that multiple unpinned packages share paths
    sorted_unpinned = sorted(unpinned_patched, key=lambda p: (min_dist.get(p, 999), p))

    # 8. Build tree of paths connecting unpinned_patched to union_direct
    tree_edges: set[Tuple[str, str]] = set()  # (child, parent) where parent depends on child
    tree_nodes: set[str] = set()

    for u in sorted_unpinned:
        targets = (union_direct | tree_nodes) - {u}
        q_path = deque([[u]])
        visited = {u}
        found_path = None
        while q_path:
            path = q_path.popleft()
            node = path[-1]
            if node in targets:
                found_path = path
                break
            # Prefer parents already in tree_nodes (sharing paths), then alphabetical
            def sort_key(p: str):
                return (0 if p in tree_nodes else 1, p)
            parents = sorted([p for p in dependents.get(node, ()) if p in closure], key=sort_key)
            for p in parents:
                if p not in visited:
                    visited.add(p)
                    q_path.append(path + [p])
        if found_path:
            tree_nodes.update(found_path)
            for i in range(len(found_path) - 1):
                tree_edges.add((found_path[i], found_path[i + 1]))

    # 9. Topological sort of tree_nodes using tree_edges (dependencies before dependents)
    in_degree = {n: 0 for n in tree_nodes}
    children_map: Dict[str, set[str]] = {n: set() for n in tree_nodes}
    for child, parent in tree_edges:
        in_degree[parent] += 1
        children_map[child].add(parent)

    topo_order: list[str] = []
    zero_in = [n for n, deg in in_degree.items() if deg == 0]
    while zero_in:
        curr = zero_in.pop(0)
        topo_order.append(curr)
        for parent in sorted(children_map[curr]):
            in_degree[parent] -= 1
            if in_degree[parent] == 0:
                zero_in.append(parent)

    # 10. Resolve target versions along tree_nodes (AT MOST ONE bump per module)
    target_versions: Dict[str, str] = dict(latest_on_disk)
    dep_bumps: Dict[str, Tuple[str, str]] = {}
    for p in topo_order:
        has_outdated = False
        for dep_name, pinned_ver in pkg_deps.get(p, {}).items():
            t_v = target_versions.get(dep_name)
            if t_v and bzlmod_lib.get_base_version(t_v) == bzlmod_lib.get_base_version(pinned_ver):
                if bzlmod_lib.version_sort_key(t_v) > bzlmod_lib.version_sort_key(pinned_ver):
                    has_outdated = True
                    break
        if has_outdated:
            old_v = latest_on_disk[p]
            new_v = bzlmod_lib.increment_version(old_v)
            target_versions[p] = new_v
            dep_bumps[p] = (old_v, new_v)

    # 11. Materialize new module versions on disk
    for pkg, (old_v, new_v) in sorted(dep_bumps.items()):
        old_dir = modules_dir / pkg / old_v
        new_dir = modules_dir / pkg / new_v

        content = (old_dir / "MODULE.bazel").read_text()
        content = bzlmod_lib.rewrite_module_version(content, pkg, new_v)
        for dep_name, pinned_dep_ver in pkg_deps.get(pkg, {}).items():
            if dep_name in target_versions:
                target_dep_v = target_versions[dep_name]
                if bzlmod_lib.version_sort_key(target_dep_v) > bzlmod_lib.version_sort_key(pinned_dep_ver):
                    content = bzlmod_lib.rewrite_bazel_dep_version(content, dep_name, target_dep_v)

        if not dry_run:
            shutil.copytree(old_dir, new_dir, dirs_exist_ok=True)
            (new_dir / "MODULE.bazel").write_text(content)
            if (new_dir / "source.json").exists():
                bzlmod_lib.regenerate_integrity_hashes(new_dir)
            bzlmod_lib.add_version_to_metadata_json(modules_dir / pkg / "metadata.json", new_v)

    return dep_bumps


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

    # Propagate any transitive dependency patches up through intermediate packages
    dep_bumps = propagate_transitive_patches(
        modules_dir, active_variants, current_ros_version, dry_run=dry_run
    )
    if dep_bumps:
        print(f"Propagated {len(dep_bumps)} transitive dependency patch(es):")
        for name, (old_v, new_v) in sorted(dep_bumps.items()):
            print(f"  {name}: {old_v} -> {new_v} (dep-only bump)")

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
        if name in dep_bumps:
            latest_patch = dep_bumps[name][1]
        else:
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

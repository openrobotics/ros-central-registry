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
Nightly bootstrap: discover new upstream ros/rosdistro tags (via
tools/ci/rosdistro_lib.py) and stage them into the RCR -- a bare
(unpatched) module version for every package the new tag references, a
0.0.0 placeholder for any package that's never existed in the registry
before, and a new .rcr.0 version per package that carries forward
whatever patch set applied to its previous version.
"""

import argparse
import concurrent.futures
import json
import os
import re
import shutil
import sys
import tarfile
import urllib.parse
from pathlib import Path
from typing import Dict, Optional, Set

import requests

from tools.ci import bzlmod_lib
from tools.ci import rosdistro_lib

# BCR dependencies every module gets, matching the current registry-wide
# convention (see any real modules/<pkg>/<version>/MODULE.bazel).
BCR_DEPS = {
    "aspect_rules_py": "1.11.7",
    "bazel_skylib": "1.9.0",
    "cmake_configure_file": "0.1.7",
    "google_benchmark": "1.9.5",
    "googletest": "1.17.0.bcr.2",
    "llvm": "0.8.11",
    "platforms": "1.1.0",
    "protobuf": "35.1",
    "rules_build_error": "0.11.0",
    "rules_cc": "0.2.22",
    "rules_license": "1.0.0",
    "rules_pkg": "1.2.0",
    "rules_python": "2.2.0",
    "rules_qt": "0.0.6",
    "rules_rs": "0.0.93",
    "rules_rust": "0.71.3",
    "rules_shell": "0.8.0",
}

BOOTSTRAP_TRAILER = """
# Setup Python
python = use_extension("@rules_python//python/extensions:python.bzl", "python")
python.toolchain(
    is_default = True,
    python_version = "3.12",
)

# Setup Pip
pip_ros = use_extension("@rosdistro//python:defs.bzl", "pip_ros")
use_repo(pip_ros, "pip_ros")

# Setup Qt6
qt = use_extension("@rules_qt//extension:qt.bzl", "fetch")
qt.install(
    name = "qt_linux_x86_64",
    build_file = "@rules_qt//extension:qt/6.8.3/linux_x86_64.BUILD",
    os = "linux",
    version = "6.8.3",
)
use_repo(qt, "qt_linux_x86_64")

register_toolchains("@rules_qt//tools:all")
"""

# "rosdistro" pins third-party (non-ROS) native deps and the real pip hub
# every other module's pip_ros proxy forwards to -- it gets a fixed custom
# body instead of the generic RCR-deps-from-package.xml treatment, since it
# has no package.xml of its own.
ROSDISTRO_CUSTOM_BODY = """
# Third party deps
bazel_dep(name = "assimp", version = "6.0.3")
bazel_dep(name = "boost.endian", version = "1.90.0.bcr.1")
bazel_dep(name = "bullet", version = "3.26.0-rc0.bcr.2")
bazel_dep(name = "console_bridge", version = "1.0.1")
bazel_dep(name = "cppcheck", version = "2.20.0")
bazel_dep(name = "cpplint", version = "2.0.2")
bazel_dep(name = "curl", version = "8.12.0")
bazel_dep(name = "cyclonedds", version = "0.10.5")
bazel_dep(name = "eigen", version = "5.0.1.bcr.1")
bazel_dep(name = "fastcdr", version = "2.3.5.bcr.0")
bazel_dep(name = "fastdds", version = "3.4.2.bcr.1")
bazel_dep(name = "gz-common", version = "7.1.1")
bazel_dep(name = "gz-fuel-tools", version = "11.0.0")
bazel_dep(name = "gz-math", version = "9.1.0")
bazel_dep(name = "gz-msgs", version = "12.0.1")
bazel_dep(name = "gz-physics", version = "9.2.0")
bazel_dep(name = "gz-plugin", version = "4.0.0")
bazel_dep(name = "gz-rendering", version = "10.0.1")
bazel_dep(name = "gz-sensors", version = "10.0.1")
bazel_dep(name = "gz-sim", version = "10.2.0")
bazel_dep(name = "gz-transport", version = "15.0.2")
bazel_dep(name = "gz-utils", version = "4.0.0")
bazel_dep(name = "libyaml", version = "0.2.5")
bazel_dep(name = "lz4", version = "1.9.4")
bazel_dep(name = "mcap", version = "1.4.0")
bazel_dep(name = "mimick", version = "0.9.0.bcr.0")
bazel_dep(name = "ogre", version = "1.12.10")
bazel_dep(name = "opencv", version = "4.13.0.bcr.5")
bazel_dep(name = "orocos-kdl", version = "1.5.3")
bazel_dep(name = "pybind11_bazel", version = "3.0.1")
bazel_dep(name = "sdl2", version = "2.32.0.bcr.beta.5")
bazel_dep(name = "spdlog", version = "1.17.0")
bazel_dep(name = "sqlite3", version = "3.51.2.bcr.1")
bazel_dep(name = "tinyxml2", version = "10.0.0")
bazel_dep(name = "uncrustify", version = "0.82.0")
bazel_dep(name = "yaml-cpp", version = "0.9.0")
bazel_dep(name = "zenoh-cpp", version = "1.8.0")
bazel_dep(name = "zlib", version = "1.3.1.bcr.5")
bazel_dep(name = "zstd", version = "1.5.6")

# Setup python
python = use_extension("@rules_python//python/extensions:python.bzl", "python")
python.toolchain(
    is_default = True,
    python_version = "3.12",
)

# Setup pip
pip = use_extension("@rules_python//python/extensions:pip.bzl", "pip")
pip.parse(
    hub_name = "pip_ros",
    python_version = "3.12",
    requirements_lock = "requirements.txt",
)
use_repo(pip, "pip_ros")

# Set up llvm for clang-format and clang-tidy
llvm = use_extension("@llvm//extensions:llvm.bzl", "llvm")
use_repo(llvm, "llvm-project")

# Setup qt
qt = use_extension("@rules_qt//extension:qt.bzl", "fetch")
qt.install(
    name = "qt_linux_x86_64",
    build_file = "@rules_qt//extension:qt/6.8.3/linux_x86_64.BUILD",
    os = "linux",
    version = "6.8.3",
)
use_repo(qt, "qt_linux_x86_64")

register_toolchains("@rules_qt//tools:all")
"""


def render_stub_module_dot_bazel(module_name: str) -> str:
    """
    A "0.0.0" placeholder MODULE.bazel: just the module() block, no
    BCR/RCR deps or bootstrap trailer at all -- matches every existing
    0.0.0 stub in the registry (e.g. modules/rosdistro/0.0.0/MODULE.bazel).
    Its only purpose is to be a resolvable placeholder version (see
    tools/ci/setup_workspace.py's BAZELRC_TEMPLATE comment on
    --check_direct_dependencies=off), so it deliberately carries no
    dependencies of its own.
    """
    return (
        bzlmod_lib.get_copyright_header()
        + "# ROS package information\n"
        + "module(\n"
        + f'    name = "{module_name}",\n'
        + '    version = "0.0.0",\n'
        + '    bazel_compatibility = [">=7.2.1"],\n'
        + ")\n"
    )


def render_module_dot_bazel(
    module_name: str,
    version: str,
    rcr_deps: Dict[str, str],
    distro: str,
    date: str,
    custom_body: Optional[str] = None,
) -> str:
    lines = [bzlmod_lib.get_copyright_header()]
    lines.append("# ROS package information\n")
    lines.append("module(\n")
    lines.append(f'    name = "{module_name}",\n')
    lines.append(f'    version = "{version}",\n')
    lines.append('    bazel_compatibility = [">=7.2.1"],\n')
    lines.append(")\n")
    lines.append("\n# BCR dependencies\n")
    for dep_name in sorted(BCR_DEPS.keys()):
        lines.append(f'bazel_dep(name = "{dep_name}", version = "{BCR_DEPS[dep_name]}")\n')
    if custom_body is not None:
        lines.append(custom_body)
    else:
        lines.append("\n# RCR Dependencies\n")
        all_rcr = dict(rcr_deps)
        all_rcr["rosdistro"] = f"{distro}.{date}"
        for dep_name in sorted(all_rcr.keys()):
            lines.append(f'bazel_dep(name = "{dep_name}", version = "{all_rcr[dep_name]}")\n')
        lines.append(BOOTSTRAP_TRAILER)
    return "".join(lines)


def render_boilerplate_overlay_build_bazel(rcr_deps: Dict[str, str]) -> str:
    """
    A minimal overlay/BUILD.bazel for a package that has never had one --
    see bootstrap_one_tag's migrate step, which normally carries an
    existing overlay forward from the package's own previous patched
    version. A genuinely brand-new package has no such version to carry
    forward from, and without this, its fresh .rcr.0 would have no
    buildable target at all, which fails CI's check that every newly
    bootstrapped package builds. This is not a substitute for a real
    implementation -- a human should still flesh it out via the normal
    vendor-module/edit/create-patch workflow once the package needs more
    than an ament_index entry (headers, libraries, executables, etc.) --
    it only wires up the same RCR deps already declared in the package's
    own MODULE.bazel (see render_module_dot_bazel) as an ament_package,
    matching the shape of every hand-written overlay/BUILD.bazel in this
    registry (e.g. modules/acado_vendor/1.0.0-8.rcr.1/overlay/BUILD.bazel).
    """
    lines = [bzlmod_lib.get_copyright_header()]
    lines.append('load("@rosdistro//ament:defs.bzl", "ament_package")\n')
    lines.append('\npackage(default_visibility = ["//visibility:public"])\n')
    lines.append("\n### PACKAGING\n\n")
    lines.append("ament_package(\n")
    lines.append('    name = "ament_package",\n')
    lines.append('    package_xml = "package.xml",\n')
    lines.append("    deps = [\n")
    for dep_name in sorted(set(rcr_deps) | {"rosdistro"}):
        lines.append(f'        "@{dep_name}//:ament_package",\n')
    lines.append("    ],\n")
    lines.append(")\n")
    return "".join(lines)


def download_archive(url: str, cache_path: Path) -> Path:
    if not cache_path.exists():
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        cache_path.write_bytes(response.content)
    return cache_path


def compute_source_json(pkg_name: str, pkg_source: rosdistro_lib.PackageSource, cache_dir: Path) -> dict:
    """
    Download the archive (cached) and compute its integrity hash plus the
    strip_prefix: default to the deterministic GitHub-archive convention,
    but override it with the containing directory of a package.xml whose
    <name> matches pkg_name, if one is found inside the archive (handles
    multi-package mono-repo tarballs, e.g. the hardcoded rosidl_typesupport_protobuf
    extras, where each package lives in its own subdirectory).
    """
    cache_path = cache_dir / f"{pkg_name}-{pkg_source.version}.tar.gz"
    archive = download_archive(pkg_source.url, cache_path)
    integrity = bzlmod_lib.calculate_integrity_hash_for_file(archive)

    strip_prefix = pkg_source.default_strip_prefix
    try:
        with tarfile.open(archive, "r:*") as tar:
            for member in tar.getmembers():
                if not member.name.endswith("package.xml"):
                    continue
                fileobj = tar.extractfile(member)
                if fileobj is None:
                    continue
                content = fileobj.read().decode("utf-8", errors="ignore")
                if re.search(r"<name>\s*" + re.escape(pkg_name) + r"\s*</name>", content):
                    parent = Path(member.name).parent.as_posix()
                    strip_prefix = "" if parent == "." else parent
                    break
    except tarfile.TarError as exc:
        print(f"Warning: failed to introspect archive for {pkg_name}: {exc}", file=sys.stderr)

    return {"integrity": integrity, "url": pkg_source.url, "strip_prefix": strip_prefix}


def derive_homepage(module_url: str) -> str:
    parsed = urllib.parse.urlparse(module_url)
    if parsed.netloc == "github.com":
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 2:
            return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, "/" + "/".join(parts[:2]), "", "", ""))
    return module_url


def write_metadata_json_if_missing(pkg_dir: Path, module_url: str, version: str) -> None:
    metadata_path = pkg_dir / "metadata.json"
    if metadata_path.exists():
        bzlmod_lib.add_version_to_metadata_json(metadata_path, version)
        return
    metadata = {
        "homepage": derive_homepage(module_url),
        "maintainers": [
            {
                "email": "simmers@google.com",
                "github": "asymingt",
                "github_user_id": 37671,
                "name": "Andrew Symington",
            }
        ],
        "versions": [version],
        "yanked_versions": {},
    }
    pkg_dir.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=4)
        f.write("\n")


def find_existing_release(package_dir: Path, bare_version: str) -> Optional[str]:
    """
    Mirrors legacy release_bootstrap.py's _find_previous_package_release:
    if this exact upstream version has already been bootstrapped (bare or
    patched) in a prior run, reuse its latest existing form instead of
    creating anything new for it in this run.
    """
    if not package_dir.exists():
        return None
    best = None
    best_patch = -2
    for item in package_dir.iterdir():
        if not item.is_dir():
            continue
        name = item.name
        if name == bare_version and best_patch < -1:
            best, best_patch = name, -1
        elif name.startswith(bare_version + ".rcr."):
            patch_num = int(name.split(".")[-1])
            if patch_num > best_patch:
                best, best_patch = name, patch_num
    return best


def find_candidate_patch_version(package_dir: Path) -> Optional[str]:
    """
    Mirrors legacy release_migrate.py's _find_candidate_patch_version:
    across this package's ENTIRE history (any prior upstream version), find
    the most recent existing "<version>.rcr.<N>" to carry patches/overlay
    forward from.
    """
    if not package_dir.exists():
        return None
    candidates = []
    for item in package_dir.iterdir():
        if not item.is_dir() or ".rcr." not in item.name:
            continue
        parts = item.name.split(".")
        patch_str = ".".join(parts[:-2])
        patch_num = int(parts[-1])
        candidates.append((patch_str, patch_num, item.name))
    if not candidates:
        return None
    candidates.sort()
    return candidates[-1][2]


def already_bootstrapped_dates(modules_dir: Path, distro: str) -> Set[str]:
    result = set()
    ros_dir = modules_dir / "ros"
    if not ros_dir.exists():
        return result
    for item in ros_dir.iterdir():
        if not item.is_dir():
            continue
        parts = item.name.split(".")
        if len(parts) == 2 and parts[0] == distro:
            result.add(item.name)
    return result


def bootstrap_one_tag(modules_dir: Path, cache_dir: Path, distro: str, date: str, dry_run: bool) -> None:
    print(f"Bootstrapping {distro}/{date}...")
    distribution = rosdistro_lib.fetch_distribution_yaml(distro, date)
    packages = rosdistro_lib.resolve_packages(distribution, distro, date)

    ros_url = f"https://github.com/ros/rosdistro/archive/refs/tags/{distro}/{date}.tar.gz"
    ros_strip_prefix = rosdistro_lib.compute_default_strip_prefix("rosdistro", f"{distro}/{date}")
    packages["ros"] = rosdistro_lib.PackageSource(
        version=f"{distro}.{date}", url=ros_url, default_strip_prefix=ros_strip_prefix,
        dependencies=set(packages.keys()),
    )
    packages["rosdistro"] = rosdistro_lib.PackageSource(
        version=f"{distro}.{date}", url=ros_url, default_strip_prefix=ros_strip_prefix,
        dependencies=set(),
    )
    print(f"  Resolved {len(packages)} packages.")

    # Phase 1: fetch each package's raw dependency names, filtered to
    # names that are themselves resolved packages here (anything else --
    # an apt/system dependency -- is meaningless to Bazel and dropped).
    # Fetched concurrently: this is ~1500 independent, tiny HTTP GETs
    # (package.xml per package) and sequential fetching is prohibitively
    # slow (10+ minutes) for a distro this size.
    to_fetch = {name: src for name, src in packages.items() if src.dependencies is None}
    fetched_deps: Dict[str, Set[str]] = {}
    print(f"  Fetching package.xml for {len(to_fetch)} packages...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
        future_to_name = {
            executor.submit(rosdistro_lib.fetch_package_xml_dependencies, src): name
            for name, src in to_fetch.items()
        }
        for future in concurrent.futures.as_completed(future_to_name):
            name = future_to_name[future]
            fetched_deps[name] = future.result()

    filtered_deps: Dict[str, Set[str]] = {}
    for pkg_name, pkg_source in packages.items():
        raw_deps = set(pkg_source.dependencies) if pkg_source.dependencies is not None \
            else fetched_deps[pkg_name]
        raw_deps |= rosdistro_lib.EXTRA_PACKAGE_DEPS.get(pkg_name, set())
        filtered_deps[pkg_name] = {
            d for d in raw_deps
            if d in packages and d not in rosdistro_lib.FORBIDDEN_DEPS and d != pkg_name
        }

    # Phase 2: decide, per package, whether this exact upstream version was
    # already bootstrapped in a prior run (reuse it) or is genuinely new
    # (will need a fresh bare version + .rcr.0). Compute final pins for
    # EVERY package up front so bazel_dep entries can be written correctly
    # in one pass, without a second dependency-rewriting pass.
    final_pin: Dict[str, str] = {}
    needs_bootstrap: Dict[str, bool] = {}
    is_brand_new_package: Dict[str, bool] = {}
    for pkg_name, pkg_source in packages.items():
        pkg_dir = modules_dir / pkg_name
        is_brand_new_package[pkg_name] = not pkg_dir.exists()
        existing = find_existing_release(pkg_dir, pkg_source.version)
        if existing is not None:
            final_pin[pkg_name] = existing
            needs_bootstrap[pkg_name] = False
        else:
            final_pin[pkg_name] = f"{pkg_source.version}.rcr.0"
            needs_bootstrap[pkg_name] = True

    fresh = [name for name, needed in needs_bootstrap.items() if needed]
    print(f"  {len(fresh)} package(s) need a fresh bare version + .rcr.0; "
          f"{len(packages) - len(fresh)} unchanged since a prior bootstrap.")

    # Phase 3: create bare versions + 0.0.0 stubs + migrate to .rcr.0, for
    # every package that actually needs it.
    for pkg_name in fresh:
        pkg_source = packages[pkg_name]
        pkg_dir = modules_dir / pkg_name
        bare_version = pkg_source.version
        bare_dir = pkg_dir / bare_version
        rcr_deps = {dep: final_pin[dep] for dep in filtered_deps[pkg_name]}
        custom_body = ROSDISTRO_CUSTOM_BODY if pkg_name == "rosdistro" else None

        print(f"  + {pkg_name}@{bare_version} (bare) -> {final_pin[pkg_name]}")
        if dry_run:
            continue

        source_json = compute_source_json(pkg_name, pkg_source, cache_dir)
        bare_dir.mkdir(parents=True, exist_ok=True)
        (bare_dir / "MODULE.bazel").write_text(
            render_module_dot_bazel(pkg_name, bare_version, rcr_deps, distro, date, custom_body)
        )
        with open(bare_dir / "source.json", "w") as f:
            json.dump(source_json, f, indent=4)
            f.write("\n")

        if is_brand_new_package[pkg_name]:
            stub_dir = pkg_dir / "0.0.0"
            stub_dir.mkdir(parents=True, exist_ok=True)
            (stub_dir / "MODULE.bazel").write_text(render_stub_module_dot_bazel(pkg_name))
            with open(stub_dir / "source.json", "w") as f:
                json.dump(source_json, f, indent=4)
                f.write("\n")
            write_metadata_json_if_missing(pkg_dir, pkg_source.url, "0.0.0")

        write_metadata_json_if_missing(pkg_dir, pkg_source.url, bare_version)

        # Migrate: carry forward this package's own most recent patch set
        # (from any prior upstream version) onto the new bare version.
        old_patched_version = find_candidate_patch_version(pkg_dir)
        new_version = final_pin[pkg_name]
        new_dir = pkg_dir / new_version
        new_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(bare_dir / "MODULE.bazel", new_dir / "MODULE.bazel")
        shutil.copy(bare_dir / "source.json", new_dir / "source.json")
        if old_patched_version is not None:
            for subdir in ("patches", "overlay"):
                src = pkg_dir / old_patched_version / subdir
                if src.exists():
                    shutil.copytree(src, new_dir / subdir)
            bzlmod_lib.regenerate_integrity_hashes(new_dir)
            print(f"    migrated patches/overlay from {pkg_name}@{old_patched_version}")
        elif custom_body is None:
            # No prior patched version exists to carry an overlay forward
            # from -- this package has never had one (rosdistro is exempt:
            # it has no package.xml of its own, so an ament_package target
            # doesn't apply to it). Without at least this, CI's new-package
            # check has nothing to build.
            overlay_dir = new_dir / "overlay"
            overlay_dir.mkdir(exist_ok=True)
            (overlay_dir / "BUILD.bazel").write_text(
                render_boilerplate_overlay_build_bazel(rcr_deps)
            )
            bzlmod_lib.regenerate_integrity_hashes(new_dir)
            print(f"    added boilerplate overlay/BUILD.bazel for {pkg_name}@{new_version}")
        bzlmod_lib.add_version_to_metadata_json(pkg_dir / "metadata.json", new_version)

    print(f"Done with {distro}/{date}.")


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap any new upstream ros/rosdistro tags for a distro."
    )
    parser.add_argument("--distro", required=True, help="ROS distro to scan, e.g. lyrical")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen, write nothing")
    args = parser.parse_args()

    repo_root = Path(os.environ.get("BUILD_WORKSPACE_DIRECTORY", ".")).resolve()
    modules_dir = repo_root / "modules"
    cache_dir = repo_root / ".cache"

    bootstrapped = already_bootstrapped_dates(modules_dir, args.distro)
    new_dates = rosdistro_lib.list_new_tags(args.distro, bootstrapped)
    if not new_dates:
        print(f"Nothing to bootstrap -- {args.distro} has no new tags beyond {sorted(bootstrapped)}.")
        return

    print(f"Found {len(new_dates)} new tag(s) to bootstrap: {new_dates}")
    for date in new_dates:
        bootstrap_one_tag(modules_dir, cache_dir, args.distro, date, args.dry_run)


if __name__ == "__main__":
    main()

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
tools/ci/rosdistro_lib.py) and stage them into the RCR -- a 0.0.0
placeholder for any package that's never existed in the registry before,
and a new .rcr.0 version per package that carries forward whatever patch
set applied to its previous version.

Packages whose upstream version is unchanged since a prior bootstrap are
pinned to their existing .rcr.N -- unless that version's BCR deps /
module-extension boilerplate no longer match BCR_DEPS + BOOTSTRAP_TRAILER,
in which case a .rcr.N+1 copy with a re-rendered MODULE.bazel is minted
instead, so every version a release pins declares the same third-party
deps and extensions as a freshly bootstrapped one.
"""

import argparse
import concurrent.futures
import dataclasses
import json
import os
import re
import shutil
import sys
import tarfile
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import requests

from tools.ci import bzlmod_lib
from tools.ci import rosdistro_lib

# BCR dependencies every module gets, matching the current registry-wide
# convention (see any real modules/<pkg>/<version>/MODULE.bazel).
BCR_DEPS = {
    "bazel_skylib": "1.9.2",
    "cmake_configure_file": "0.2.0",
    "google_benchmark": "1.9.5",
    "googletest": "1.18.0.bcr.1",
    "llvm": "0.8.24",
    "platforms": "1.1.0",
    "protobuf": "36.2",
    "rules_build_error": "0.11.0",
    "rules_cc": "0.2.26",
    "rules_cc_autoconf": "0.24.0",
    "rules_foreign_cc": "0.16.0",
    "rules_img": "0.3.22",
    "rules_license": "1.0.0",
    "rules_pkg": "1.3.0",
    "rules_python": "2.4.1",
    "rules_rs": "0.1.0",
    "rules_shell": "0.8.0",
}

# From-source Qt 6 modules (staged under bcr_staging/modules/ until they land
# in the BCR), replacing the prebuilt rules_qt binaries. Every module gets
# them so any package can depend on @qtbase//:widgets, @qtdeclarative//:quick,
# ... directly. Keep in sync with tools/ci/setup_workspace.py:QT_MODULES.
QT_VERSION = "6.10.2"
QT_MODULES = (
    "qt",
    "qtbase",
    "qtsvg",
    "qtlanguageserver",
    "qtimageformats",
    "qtshadertools",
    "qtdeclarative",
    "qtwebsockets",
    "qtwebchannel",
    "qthttpserver",
    "qtnetworkauth",
    "qtserialport",
    "qtserialbus",
    "qtsensors",
    "qt5compat",
    "qtcharts",
    "qtpositioning",
    "qtlocation",
    "qtconnectivity",
    "qtlottie",
    "qtquicktimeline",
    "qtvirtualkeyboard",
    "qtremoteobjects",
    "qtscxml",
    "qtquick3d",
    "qtquick3dphysics",
    "qtgraphs",
    "qtdatavis3d",
    "qt3d",
    "qtmultimedia",
    "qtspeech",
    "qtwayland",
    "qtwebview",
    "qtgrpc",
    "qttools",
    "qttranslations",
)
BCR_DEPS.update({name: QT_VERSION for name in QT_MODULES})

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
"""

# Previous vintages of BOOTSTRAP_TRAILER.  A MODULE.bazel whose trailer
# matches one of these is a plain carry-forward from an older bootstrap and
# is safe to re-render; anything else is treated as a hand edit and left
# alone (see parse_module_dot_bazel / refresh_module_dot_bazel).
_SINGLE_PLATFORM_QT = """qt = use_extension("@rules_qt//extension:qt.bzl", "fetch")
qt.install(
    name = "qt_linux_x86_64",
    build_file = "@rules_qt//extension:qt/6.8.3/linux_x86_64.BUILD",
    os = "linux",
    version = "6.8.3",
)
use_repo(qt, "qt_linux_x86_64")
"""
_RULES_QT_BOOTSTRAP_TRAILER = """
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
    os = "linux_x86_64",
    version = "6.8.3",
)
qt.install(
    name = "qt_linux_aarch64",
    build_file = "@rules_qt//extension:qt/6.8.3/linux_aarch64.BUILD",
    os = "linux_aarch64",
    version = "6.8.3",
)
qt.install(
    name = "qt_mac_aarch64",
    build_file = "@rules_qt//extension:qt/6.8.3/mac_aarch64.BUILD",
    os = "macos",
    version = "6.8.3",
)
qt.install(
    name = "qt_mac_x86_64",
    build_file = "@rules_qt//extension:qt/6.8.3/mac_aarch64.BUILD",
    os = "macos",
    version = "6.8.3",
)
qt.install(
    name = "qt_windows_x86_64",
    build_file = "@rules_qt//extension:qt/6.8.3/windows_x86_64.BUILD",
    os = "windows",
    version = "6.8.3",
    windows_architecture = "win64_msvc2022",
)
use_repo(qt, "qt_linux_aarch64", "qt_linux_x86_64", "qt_mac_aarch64", "qt_mac_x86_64", "qt_windows_x86_64")

register_toolchains("@rules_qt//tools:all")
"""

LEGACY_BOOTSTRAP_TRAILERS = (
    # rules_qt (prebuilt Qt 6.8.3), multi-platform.
    _RULES_QT_BOOTSTRAP_TRAILER,
    # rules_qt (prebuilt Qt 6.8.3), linux_x86_64 only.
    _RULES_QT_BOOTSTRAP_TRAILER[: _RULES_QT_BOOTSTRAP_TRAILER.index("qt = use_extension")]
    + _SINGLE_PLATFORM_QT
    + _RULES_QT_BOOTSTRAP_TRAILER[_RULES_QT_BOOTSTRAP_TRAILER.index("\nregister_toolchains"):],
)

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
        # Every module depends on rosdistro, whether or not package.xml says
        # so. Callers normally supply its resolved pin (the .rcr.0 version,
        # same as every other RCR dep); fall back to the .rcr.0 tag otherwise.
        all_rcr.setdefault("rosdistro", f"{distro}.{date}.rcr.0")
        for dep_name in sorted(all_rcr.keys()):
            lines.append(f'bazel_dep(name = "{dep_name}", version = "{all_rcr[dep_name]}")\n')
        lines.append(BOOTSTRAP_TRAILER)
    return "".join(lines)


### Re-rendering existing MODULE.bazel files against the current template

_BAZEL_DEP_RE = re.compile(r'^bazel_dep\(\s*name\s*=\s*"([^"]+)"\s*,\s*version\s*=\s*"([^"]+)"\s*\)\s*$')
_MODULE_RE = re.compile(r'module\(\s*name\s*=\s*"([^"]+)"\s*,\s*version\s*=\s*"([^"]+)"')
_ROSDISTRO_VERSION_RE = re.compile(r"^([a-z]+)\.(\d{4}-\d{2}-\d{2})\.rcr\.\d+$")
BCR_SECTION = "# BCR dependencies"
RCR_SECTION = "# RCR Dependencies"
TRAILER_START = "# Setup Python"


@dataclasses.dataclass
class ParsedModule:
    """A bootstrap-shaped MODULE.bazel, pulled apart (see parse_module_dot_bazel)."""
    name: str
    version: str
    bcr_deps: Dict[str, str]
    rcr_deps: Dict[str, str]
    trailer_matches: bool
    trailer_is_legacy: bool
    unrecognized: List[str]

    @property
    def dropped_bcr_deps(self) -> Dict[str, str]:
        return {k: v for k, v in self.bcr_deps.items() if k not in BCR_DEPS}

    @property
    def stale_bcr_deps(self) -> Dict[str, str]:
        return {k: v for k, v in self.bcr_deps.items() if k in BCR_DEPS and v != BCR_DEPS[k]}

    @property
    def missing_bcr_deps(self) -> List[str]:
        return sorted(set(BCR_DEPS) - set(self.bcr_deps))

    @property
    def boilerplate_is_current(self) -> bool:
        return (
            self.bcr_deps == BCR_DEPS
            and self.trailer_matches
            and not self.unrecognized
        )


def parse_module_dot_bazel(text: str) -> ParsedModule:
    """
    Pull apart a MODULE.bazel produced by render_module_dot_bazel (any
    vintage of its template; see LEGACY_BOOTSTRAP_TRAILERS).  Raises ValueError if there is no module()
    block; anything else it doesn't understand is collected in
    `unrecognized` so callers can refuse to rewrite rather than guess.
    bazel_dep()s found *after* the trailer (older tooling appended RCR deps
    there) are treated as RCR deps.
    """
    m = _MODULE_RE.search(text)
    if not m:
        raise ValueError("no module(name=..., version=...) block")
    name, version = m.group(1), m.group(2)
    close = text.index("\n)\n", m.end()) + len("\n)\n")

    bcr: Dict[str, str] = {}
    rcr: Dict[str, str] = {}
    unrecognized: List[str] = []
    trailer_lines: List[str] = []
    section = None
    in_trailer = False
    for line in text[close:].split("\n"):
        stripped = line.strip()
        if in_trailer:
            dep = _BAZEL_DEP_RE.match(stripped)
            if dep:
                rcr[dep.group(1)] = dep.group(2)
            else:
                trailer_lines.append(line)
            continue
        if stripped == TRAILER_START:
            in_trailer = True
            trailer_lines.append(line)
            continue
        if not stripped:
            continue
        if stripped == BCR_SECTION:
            section = "bcr"
            continue
        if stripped == RCR_SECTION:
            section = "rcr"
            continue
        dep = _BAZEL_DEP_RE.match(stripped)
        if dep:
            (bcr if section == "bcr" else rcr)[dep.group(1)] = dep.group(2)
            continue
        unrecognized.append(stripped)

    trailer = "\n".join(trailer_lines).strip()
    trailer_matches = in_trailer and trailer == BOOTSTRAP_TRAILER.strip()
    trailer_is_legacy = in_trailer and any(trailer == t.strip() for t in LEGACY_BOOTSTRAP_TRAILERS)
    return ParsedModule(name, version, bcr, rcr, trailer_matches, trailer_is_legacy, unrecognized)


def refresh_module_dot_bazel(text: str, new_version: Optional[str] = None) -> Tuple[str, ParsedModule]:
    """
    Re-render an existing MODULE.bazel with today's BCR_DEPS and
    BOOTSTRAP_TRAILER, keeping its module() block (optionally with a new
    version) and its RCR bazel_dep pins exactly as they are.  Returns
    (new_text, parsed); new_text == text when the file is already current.
    Raises ValueError when the file can't be safely re-rendered: content
    the parser doesn't recognise, a hand-edited extension trailer, a
    custom-body module (rosdistro), or no rosdistro pin to derive the
    distro/date from.
    """
    parsed = parse_module_dot_bazel(text)
    if parsed.unrecognized:
        raise ValueError("unrecognized content: " + "; ".join(parsed.unrecognized[:3]))
    if not (parsed.trailer_matches or parsed.trailer_is_legacy):
        raise ValueError("module-extension trailer matches neither BOOTSTRAP_TRAILER nor a known legacy vintage")
    m = _ROSDISTRO_VERSION_RE.match(parsed.rcr_deps.get("rosdistro", ""))
    if not m:
        raise ValueError(f"no parseable rosdistro pin (got {parsed.rcr_deps.get('rosdistro')!r})")
    rendered = render_module_dot_bazel(
        parsed.name, new_version or parsed.version, parsed.rcr_deps, distro=m.group(1), date=m.group(2)
    )
    return rendered, parsed


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
    If this exact upstream version has already been bootstrapped in a
    prior run, return its latest existing .rcr.N form (see
    plan_existing_release for whether it can be reused as-is).
    """
    if not package_dir.exists():
        return None
    best = None
    best_patch = -1
    for item in package_dir.iterdir():
        if not item.is_dir():
            continue
        name = item.name
        if name.startswith(bare_version + ".rcr."):
            patch_num = int(name.split(".")[-1])
            if patch_num > best_patch:
                best, best_patch = name, patch_num
    return best


@dataclasses.dataclass
class ExistingReleasePlan:
    """
    What to do with a package whose upstream version was already
    bootstrapped in a prior run.  `pin` is the version this release should
    reference.  When `refresh_from` is set, `pin` is a brand-new .rcr.N+1
    directory that must be materialised as a copy of `refresh_from` with
    `module_dot_bazel` as its MODULE.bazel -- the existing version's BCR
    deps / module-extension boilerplate no longer match what a fresh
    bootstrap emits, and published versions are immutable, so the only way
    to bring it up to date is a new version.
    """
    pin: str
    refresh_from: Optional[str] = None
    module_dot_bazel: Optional[str] = None
    warning: Optional[str] = None


def plan_existing_release(package_dir: Path, existing: str) -> ExistingReleasePlan:
    """
    Decide whether `existing` (a modules/<pkg>/<existing>/ directory) can
    be pinned as-is or needs a boilerplate-refreshed successor.  A
    MODULE.bazel the parser can't safely re-render (hand-edited
    extensions, custom body) is reused as-is with a warning rather than
    guessed at.  RCR pins are deliberately left alone -- bumping those is
    the weekly rollup's job.
    """
    text = (package_dir / existing / "MODULE.bazel").read_text()
    new_version = bzlmod_lib.increment_version(existing)
    try:
        current, _ = refresh_module_dot_bazel(text)
    except ValueError as exc:
        return ExistingReleasePlan(pin=existing, warning=str(exc))
    if current == text:
        return ExistingReleasePlan(pin=existing)
    refreshed, _ = refresh_module_dot_bazel(text, new_version)
    return ExistingReleasePlan(pin=new_version, refresh_from=existing, module_dot_bazel=refreshed)


def materialize_refreshed_release(package_dir: Path, plan: ExistingReleasePlan, module_url: str) -> None:
    """
    Create modules/<pkg>/<plan.pin>/ as a copy of <plan.refresh_from>
    (source.json, patches/, overlay/) with the re-rendered MODULE.bazel,
    and register it in metadata.json.
    """
    assert plan.refresh_from and plan.module_dot_bazel
    old_dir = package_dir / plan.refresh_from
    new_dir = package_dir / plan.pin
    new_dir.mkdir(parents=True, exist_ok=False)
    (new_dir / "MODULE.bazel").write_text(plan.module_dot_bazel)
    shutil.copy2(old_dir / "source.json", new_dir / "source.json")
    for subdir in ("patches", "overlay"):
        if (old_dir / subdir).exists():
            shutil.copytree(old_dir / subdir, new_dir / subdir)
    bzlmod_lib.regenerate_integrity_hashes(new_dir)
    write_metadata_json_if_missing(package_dir, module_url, plan.pin)


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
        base = bzlmod_lib.get_base_version(item.name)
        parts = base.split(".")
        if len(parts) == 2 and parts[0] == distro:
            result.add(base)
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
    # (will need a fresh .rcr.0). Compute final pins for EVERY package up
    # front so bazel_dep entries can be written correctly in one pass,
    # without a second dependency-rewriting pass.
    final_pin: Dict[str, str] = {}
    needs_bootstrap: Dict[str, bool] = {}
    is_brand_new_package: Dict[str, bool] = {}
    refresh: Dict[str, ExistingReleasePlan] = {}
    for pkg_name, pkg_source in packages.items():
        pkg_dir = modules_dir / pkg_name
        is_brand_new_package[pkg_name] = not pkg_dir.exists()
        existing = find_existing_release(pkg_dir, pkg_source.version)
        if existing is not None:
            plan = plan_existing_release(pkg_dir, existing)
            final_pin[pkg_name] = plan.pin
            needs_bootstrap[pkg_name] = False
            if plan.refresh_from:
                refresh[pkg_name] = plan
            elif plan.warning:
                print(f"  ! {pkg_name}@{existing}: reusing as-is, can't refresh boilerplate: {plan.warning}",
                      file=sys.stderr)
        else:
            final_pin[pkg_name] = f"{pkg_source.version}.rcr.0"
            needs_bootstrap[pkg_name] = True

    fresh = [name for name, needed in needs_bootstrap.items() if needed]
    print(f"  {len(fresh)} package(s) need a fresh .rcr.0; "
          f"{len(refresh)} unchanged upstream but need their BCR deps / module extensions "
          f"refreshed; {len(packages) - len(fresh) - len(refresh)} reused as-is.")

    # Phase 2b: carried-forward versions whose boilerplate predates the
    # current template get a new .rcr.N+1 (same source/patches/overlay,
    # re-rendered MODULE.bazel) so that every version this release pins
    # declares the same BCR deps and module extensions as a fresh one.
    for pkg_name, plan in sorted(refresh.items()):
        print(f"  ~ {pkg_name}@{plan.pin} (boilerplate refresh of {plan.refresh_from})")
        if not dry_run:
            materialize_refreshed_release(modules_dir / pkg_name, plan, packages[pkg_name].url)

    # Phase 3: create 0.0.0 stubs + migrate to .rcr.0, for every package
    # that actually needs it.
    for pkg_name in fresh:
        pkg_source = packages[pkg_name]
        pkg_dir = modules_dir / pkg_name
        rcr_deps = {dep: final_pin[dep] for dep in filtered_deps[pkg_name]}
        if pkg_name != "rosdistro":
            rcr_deps["rosdistro"] = final_pin["rosdistro"]
        custom_body = ROSDISTRO_CUSTOM_BODY if pkg_name == "rosdistro" else None
        new_version = final_pin[pkg_name]

        print(f"  + {pkg_name}@{new_version}")
        if dry_run:
            continue

        source_json = compute_source_json(pkg_name, pkg_source, cache_dir)

        if is_brand_new_package[pkg_name]:
            stub_dir = pkg_dir / "0.0.0"
            stub_dir.mkdir(parents=True, exist_ok=True)
            (stub_dir / "MODULE.bazel").write_text(render_stub_module_dot_bazel(pkg_name))
            with open(stub_dir / "source.json", "w") as f:
                json.dump(source_json, f, indent=4)
                f.write("\n")
            write_metadata_json_if_missing(pkg_dir, pkg_source.url, "0.0.0")

        # Migrate: carry forward this package's own most recent patch set
        # (from any prior upstream version) onto the new .rcr.0 version.
        old_patched_version = find_candidate_patch_version(pkg_dir)
        new_dir = pkg_dir / new_version
        new_dir.mkdir(parents=True, exist_ok=True)
        (new_dir / "MODULE.bazel").write_text(
            render_module_dot_bazel(pkg_name, new_version, rcr_deps, distro, date, custom_body)
        )
        with open(new_dir / "source.json", "w") as f:
            json.dump(source_json, f, indent=4)
            f.write("\n")
        if old_patched_version is not None:
            for subdir in ("patches", "overlay"):
                src = pkg_dir / old_patched_version / subdir
                if src.exists():
                    shutil.copytree(src, new_dir / subdir)
            bzlmod_lib.regenerate_integrity_hashes(new_dir)
            print(f"    migrated patches/overlay from {pkg_name}@{old_patched_version}")
        write_metadata_json_if_missing(pkg_dir, pkg_source.url, new_version)

    print(f"Done with {distro}/{date}.")


def select_tags(new_dates: List[str], only_latest: bool) -> List[str]:
    """
    Narrows the oldest-first list of not-yet-bootstrapped tag dates to the
    ones a run should actually process. By default that's all of them (the
    nightly job's behaviour); with only_latest it's just the newest one, so
    a manual catch-up run after a gap can skip straight to the current tag
    instead of materializing every superseded-on-arrival intermediate
    release.
    """
    if only_latest and new_dates:
        return new_dates[-1:]
    return list(new_dates)


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap any new upstream ros/rosdistro tags for a distro."
    )
    parser.add_argument("--distro", required=True, help="ROS distro to scan, e.g. lyrical")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen, write nothing")
    parser.add_argument(
        "--only-latest", action="store_true",
        help="Bootstrap only the newest new tag, skipping any intermediate tags",
    )
    args = parser.parse_args()

    repo_root = Path(os.environ.get("BUILD_WORKSPACE_DIRECTORY", ".")).resolve()
    modules_dir = repo_root / "modules"
    cache_dir = repo_root / ".cache"

    bootstrapped = already_bootstrapped_dates(modules_dir, args.distro)
    new_dates = rosdistro_lib.list_new_tags(args.distro, bootstrapped)
    if not new_dates:
        print(f"Nothing to bootstrap -- {args.distro} has no new tags beyond {sorted(bootstrapped)}.")
        return

    selected = select_tags(new_dates, args.only_latest)
    if selected != new_dates:
        print(f"Found {len(new_dates)} new tag(s): {new_dates}; --only-latest selects {selected}")
    else:
        print(f"Found {len(new_dates)} new tag(s) to bootstrap: {new_dates}")
    for date in selected:
        bootstrap_one_tag(modules_dir, cache_dir, args.distro, date, args.dry_run)


if __name__ == "__main__":
    main()

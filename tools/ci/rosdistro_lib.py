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
Fetch and parse upstream ros/rosdistro release data directly -- no
rosdep/rosdistro/rosinstall_generator dependency. Those libraries exist
mainly to resolve historical dated releases through a distribution-cache
mechanism that has a known caching bug for exactly this use case; reading
distribution.yaml and each package's package.xml straight from the tag
sidesteps it entirely (see docs/source/design_choices.rst).
"""

import re
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from xml.etree import ElementTree

import requests
import yaml

# Packages that get "<distro>.<date>" as their version instead of their real
# upstream release version, so users can import them by release date.
DATE_VERSIONED_PACKAGES = {
    "rosdistro", "ros", "ros_core", "ros_base", "desktop", "desktop_full",
    "simulation", "perception",
}

# ROS packages whose name masks a BCR package.
IGNORED_PACKAGES = {"cyclonedds", "fastcdr", "fastdds"}

# Dependency names that can't be resolved to a ROS package or a Bazel dep
# and are skipped entirely (ported from the legacy rosdep-based pipeline's
# hand-tuned skip-list -- these are apt/system package names or packages
# with no Bazel equivalent, not something derivable from distribution.yaml).
FORBIDDEN_DEPS = {
    "python3-catkin-pkg-modules", "python3-vcstool", "python3-rospkg-modules",
    "python3-rosdistro-modules", "ros_ign_bridge", "ros_ign_gazebo",
    "action_tutorials_interfaces", "gazebo_ros_pkgs", "pybind11_json_vendor",
    "actionlib_msgs",
}

# Extra dependencies hand-added to make the IDL generator pipeline work in Bazel.
EXTRA_PACKAGE_DEPS = {
    "rosidl_generator_c": {"rosidl_runtime_c"},
    "rosidl_typesupport_cpp": {"rosidl_generator_cpp"},
    # The generated C++ FastRTPS typesupport calls the generated C FastRTPS
    # typesupport's has_buffer_fields_*() helper for the same interface.
    # Upstream CMake gets that target implicitly from the same
    # rosidl_generate_interfaces() call; our aspect needs the module visible.
    "rosidl_typesupport_fastrtps_cpp": {"rosidl_typesupport_fastrtps_c"},
    "rosidl_core_generators": {
        "rosidl_adapter", "rosidl_adapter_proto",
        "rosidl_generator_type_description",
        "rosidl_typesupport_protobuf_c", "rosidl_typesupport_protobuf_cpp",
    },
}

_PROTOBUF_TARBALL_URL = (
    "https://github.com/eclipse-ecal/rosidl_typesupport_protobuf/archive/"
    "e3de421144f1dd080f234a8a03a2de90bf31314f.tar.gz"
)
_PROTOBUF_DEFAULT_STRIP_PREFIX = (
    "rosidl_typesupport_protobuf-e3de421144f1dd080f234a8a03a2de90bf31314f"
)


@dataclass
class PackageSource:
    version: str
    url: str
    default_strip_prefix: str
    repo_owner: str = ""
    repo_name: str = ""
    tag: str = ""
    dependencies: Optional[Set[str]] = None


# The e-cal/rosidl_typesupport_protobuf project isn't part of any rosdistro
# release -- it enables ROS-message-to-.proto conversion and is hand-pinned
# to a specific upstream commit, with hand-specified dependencies (its
# package.xml files aren't fetched/parsed the way regular packages are).
EXTRA_PACKAGES: Dict[str, PackageSource] = {
    "rosidl_adapter_proto": PackageSource(
        version="1.0.0", url=_PROTOBUF_TARBALL_URL,
        default_strip_prefix=_PROTOBUF_DEFAULT_STRIP_PREFIX,
        dependencies={
            "ament_cmake_pytest", "ament_cmake", "rosidl_cli", "rosidl_cmake",
            "rosidl_parser", "rosidl_pycommon",
        },
    ),
    "rosidl_typesupport_protobuf": PackageSource(
        version="1.0.0", url=_PROTOBUF_TARBALL_URL,
        default_strip_prefix=_PROTOBUF_DEFAULT_STRIP_PREFIX,
        dependencies={
            "ament_cmake", "rosidl_generator_c", "rosidl_pycommon",
            "rosidl_runtime_c",
        },
    ),
    "rosidl_typesupport_protobuf_c": PackageSource(
        version="1.0.0", url=_PROTOBUF_TARBALL_URL,
        default_strip_prefix=_PROTOBUF_DEFAULT_STRIP_PREFIX,
        dependencies={
            "ament_cmake_gtest", "ament_cmake", "rmw", "rosidl_adapter_proto",
            "rosidl_cmake", "rosidl_generator_cpp", "rosidl_parser",
            "rosidl_pycommon", "rosidl_runtime_c", "rosidl_runtime_cpp",
            "rosidl_typesupport_interface", "rosidl_typesupport_protobuf",
            "rosidl_typesupport_introspection_cpp",
        },
    ),
    "rosidl_typesupport_protobuf_cpp": PackageSource(
        version="1.0.0", url=_PROTOBUF_TARBALL_URL,
        default_strip_prefix=_PROTOBUF_DEFAULT_STRIP_PREFIX,
        dependencies={
            "ament_cmake_gtest", "ament_cmake", "rmw", "rosidl_adapter_proto",
            "rosidl_cmake", "rosidl_generator_cpp", "rosidl_parser",
            "rosidl_pycommon", "rosidl_runtime_cpp",
            "rosidl_typesupport_interface", "rosidl_typesupport_protobuf",
        },
    ),
}


def compute_default_strip_prefix(repo_name: str, tag: str) -> str:
    """
    GitHub's own archive-generation convention: "{repo-name}-{tag, with
    every '/' replaced by '-'}". Correct as-is for archives with no
    per-package subdirectory (e.g. the ros/rosdistro archive itself, or any
    single-package -release repo); callers should override it with the
    actual containing directory of a matching package.xml when one is
    found inside the downloaded archive (see bootstrap_release.py).
    """
    return f"{repo_name}-{tag.replace('/', '-')}"


def _parse_github_owner_repo(repo_url: str) -> (str, str):
    stripped = repo_url.removesuffix(".git").rstrip("/")
    parts = stripped.split("/")
    return parts[-2], parts[-1]


def fetch_distribution_yaml(distro: str, date: str) -> dict:
    """
    Fetch and parse distribution.yaml for a specific dated tag directly
    from the official ros/rosdistro repo -- no rosdistro/rosinstall_generator
    library, no distribution-cache indirection.
    """
    url = f"https://raw.githubusercontent.com/ros/rosdistro/{distro}/{date}/{distro}/distribution.yaml"
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return yaml.safe_load(response.text)


def resolve_packages(distribution: dict, distro: str, date: str) -> Dict[str, PackageSource]:
    """
    Expand distribution.yaml's repositories map into a flat package name ->
    PackageSource map (one repo can produce several packages, all sharing
    the same upstream release version), applying the date-versioning
    override for meta-packages, plus the hardcoded extra packages.
    """
    packages: Dict[str, PackageSource] = dict(EXTRA_PACKAGES)
    for repo_name, repo_info in (distribution.get("repositories") or {}).items():
        release = repo_info.get("release")
        if not release:
            continue
        repo_url = release.get("url")
        upstream_version = release.get("version")
        tag_template = (release.get("tags") or {}).get("release")
        if not repo_url or not upstream_version or not tag_template:
            continue
        owner, bare_repo_name = _parse_github_owner_repo(repo_url)
        for pkg_name in release.get("packages") or [repo_name]:
            if pkg_name in IGNORED_PACKAGES:
                continue
            tag = tag_template.format(package=pkg_name, version=upstream_version)
            tarball_url = f"https://github.com/{owner}/{bare_repo_name}/archive/refs/tags/{tag}.tar.gz"
            final_version = (
                f"{distro}.{date}" if pkg_name in DATE_VERSIONED_PACKAGES else upstream_version
            )
            packages[pkg_name] = PackageSource(
                version=final_version,
                url=tarball_url,
                default_strip_prefix=compute_default_strip_prefix(bare_repo_name, tag),
                repo_owner=owner,
                repo_name=bare_repo_name,
                tag=tag,
            )
    return packages


# Every dependency tag defined by REP 149 (package.xml format 3), plus the
# legacy format-1 run_depend. doc_depend is included too, so the deps
# needed to eventually build package documentation from Bazel are declared
# up front. Dropping any of these silently produces a MODULE.bazel missing
# bazel_deps the package's BUILD files load -- e.g. every interface package
# declares rosidl_default_generators (and ament_cmake) as a
# buildtool_depend, not a build_depend.
PACKAGE_XML_DEPEND_TAGS = frozenset({
    "build_depend",
    "build_export_depend",
    "buildtool_depend",
    "buildtool_export_depend",
    "depend",
    "doc_depend",
    "exec_depend",
    "run_depend",
    "test_depend",
})


def parse_package_xml_dependencies(package_xml: str) -> Set[str]:
    """
    Returns every dependency name declared in a package.xml document via
    any of PACKAGE_XML_DEPEND_TAGS. Conditions (`condition="..."`
    attributes) are not evaluated -- a conditional dependency is kept, and
    like every other name here is expected to be filtered by the caller
    against the set of actually-resolved ROS packages.
    """
    root = ElementTree.fromstring(package_xml)
    return {el.text.strip() for el in root if el.tag in PACKAGE_XML_DEPEND_TAGS and el.text}


def fetch_package_xml_dependencies(pkg_source: PackageSource) -> Set[str]:
    """
    Fetch and parse a package's package.xml directly from its release tag,
    returning every declared dependency name (see
    parse_package_xml_dependencies). Callers are expected to filter this
    down to names that are themselves resolved ROS packages -- anything
    else (an apt/system dependency) is meaningless to Bazel and should be
    dropped, matching the legacy pipeline's behavior.
    """
    url = f"https://raw.githubusercontent.com/{pkg_source.repo_owner}/{pkg_source.repo_name}/{pkg_source.tag}/package.xml"
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return parse_package_xml_dependencies(response.text)



def list_new_tags(distro: str, already_bootstrapped: Set[str]) -> List[str]:
    """
    Returns dates (sorted oldest-first) for every "<distro>/<date>" tag on
    ros/rosdistro strictly newer than the latest already-bootstrapped date
    for this distro (already_bootstrapped is a set of "<distro>.<date>"
    strings, matching modules/ros/ directory names; ISO dates sort
    correctly as plain strings). Deliberately NOT "any date not already
    bootstrapped" -- a distro's history can have older tags that were
    intentionally skipped when it was first bootstrapped (e.g. this repo
    has never bootstrapped lyrical/2026-05-22, going straight to
    lyrical/2026-06-08), and re-processing those out of chronological
    order would create a confusing, superseded-on-arrival release row.
    """
    own_dates = [d.split(".", 1)[1] for d in already_bootstrapped if d.startswith(f"{distro}.")]
    latest_bootstrapped = max(own_dates) if own_dates else None

    result = subprocess.run(
        ["gh", "api", "repos/ros/rosdistro/tags", "--paginate", "-q", ".[].name"],
        check=True, capture_output=True, text=True,
    )
    pattern = re.compile(rf"^{re.escape(distro)}/(\d{{4}}-\d{{2}}-\d{{2}})$")
    dates = []
    for line in result.stdout.splitlines():
        match = pattern.match(line.strip())
        if match:
            date = match.group(1)
            if latest_bootstrapped is None or date > latest_bootstrapped:
                dates.append(date)
    dates.sort()
    return dates

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

import io
import re
import subprocess
import sys
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
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
    # Subdirectory (relative to the archive root) containing this package's
    # package.xml, when it's not at the archive root. Only ever set by the
    # no-official-release fallback (see resolve_unreleased_repo_packages) --
    # an officially-released package's archive is bloom-filtered so
    # package.xml always sits at the root already.
    package_xml_subdir: str = ""


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

    A repo whose 'release:' block is missing or incomplete (no url/version/
    tag template) falls back to resolve_unreleased_repo_packages instead of
    being silently dropped -- see that function's docstring for what it can
    and can't recover.
    """
    packages: Dict[str, PackageSource] = dict(EXTRA_PACKAGES)
    for repo_name, repo_info in (distribution.get("repositories") or {}).items():
        release = repo_info.get("release")
        if release:
            repo_url = release.get("url")
            upstream_version = release.get("version")
            tag_template = (release.get("tags") or {}).get("release")
            if repo_url and upstream_version and tag_template:
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
                continue
        packages.update(resolve_unreleased_repo_packages(repo_name, repo_info))
    return packages


_UPSTREAM_TAG_PATTERN = re.compile(r"^upstream/(\d+(?:\.\d+){1,3})$")


def _list_repo_tags(owner: str, repo: str) -> List[str]:
    """
    Every tag name on {owner}/{repo}, or [] if the repo doesn't exist, has
    no tags, or the API call otherwise fails -- callers treat "nothing
    found" as a normal, expected outcome (most repos probed this way won't
    have a '-release' companion at all), not an error worth surfacing.
    """
    result = subprocess.run(
        ["gh", "api", f"repos/{owner}/{repo}/tags", "--paginate", "-q", ".[].name"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _find_best_upstream_tag(
    owner: str, repo: str, alt_owner: Optional[str] = None
) -> Optional[Tuple[str, str, str]]:
    """
    Look for the highest-versioned 'upstream/X.Y.Z' tag on {owner}/{repo},
    then (if not found) on {alt_owner}/{repo}. Bloom writes an 'upstream/*'
    tag whenever it imports upstream source into a '-release' repo, which
    happens before (and independently of) an actual per-distro release --
    unlike a 'release/<distro>/<pkg>/X.Y.Z-N' tag, it carries no debian
    revision and isn't scoped to any particular distro. Returns
    (resolved_owner, repo, tag) for whichever owner had a match, or None.
    """
    for candidate_owner in [o for o in (owner, alt_owner) if o]:
        best: Optional[Tuple[Tuple[int, ...], str]] = None
        for tag in _list_repo_tags(candidate_owner, repo):
            match = _UPSTREAM_TAG_PATTERN.match(tag)
            if not match:
                continue
            key = tuple(int(p) for p in match.group(1).split("."))
            if best is None or key > best[0]:
                best = (key, tag)
        if best is not None:
            return candidate_owner, repo, best[1]
    return None


def discover_packages_in_archive(url: str) -> Dict[str, str]:
    """
    Download a source archive and return every ROS package it contains, as
    {package_name: strip_prefix} -- strip_prefix follows the same
    convention as compute_source_json in bootstrap_release.py: the full
    parent directory of that package's package.xml *within the downloaded
    tarball itself* ("" if package.xml sits at the tarball's absolute
    root). For a GitHub-generated archive this always includes the
    top-level "{repo}-{tag}" wrapper directory that every member is nested
    under -- callers that need a git-tree-relative path instead (e.g. to
    build a raw.githubusercontent.com URL) must strip that wrapper prefix
    back off; see resolve_unreleased_repo_packages. Used there because,
    unlike the normal release path, there's no 'packages:' list telling us
    what's inside a multi-package repo's archive -- the archive itself is
    the only source of truth.

    Only considers package.xml at the wrapper root or exactly one
    directory below it -- every real ROS package in this registry lives
    there. Anything deeper is almost always a vendored/third-party
    dependency bundled inside the repo's own source tree, which can carry
    its own unrelated package.xml: eCAL's upstream archive, for instance,
    has one at thirdparty/protobuf/php/ext/google/protobuf/package.xml
    declaring <name>protobuf</name>, which has nothing to do with the
    actual eCAL packages and would otherwise get "discovered" as one.
    """
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    discovered: Dict[str, str] = {}
    with tarfile.open(fileobj=io.BytesIO(response.content), mode="r:*") as tar:
        for member in tar.getmembers():
            if not member.name.endswith("package.xml"):
                continue
            parts = Path(member.name).parts
            # parts[0] is the wrapper directory, parts[-1] is "package.xml"
            # itself -- len(parts) 2 means the wrapper root, 3 means one
            # directory below it.
            if len(parts) > 3:
                continue
            fileobj = tar.extractfile(member)
            if fileobj is None:
                continue
            content = fileobj.read().decode("utf-8", errors="ignore")
            match = re.search(r"<name>\s*([^<\s]+)\s*</name>", content)
            if not match:
                continue
            parent = Path(member.name).parent.as_posix()
            discovered[match.group(1)] = "" if parent == "." else parent
    return discovered


def bcr_module_exists(name: str) -> bool:
    """
    True if `name` is a published Bazel Central Registry module (queries
    the live registry Bazel itself resolves against). Used to keep
    resolve_unreleased_repo_packages's archive scan from minting a package
    that shadows an unrelated BCR module of the same name -- see
    discover_packages_in_archive's docstring for the motivating example
    (a vendored third-party dependency's own package.xml, not a real
    package belonging to the repo being resolved). A network failure is
    treated as "not found" rather than raised -- this is a best-effort
    safety net, not something that should take down a whole bootstrap run
    over a transient error.
    """
    url = f"https://bcr.bazel.build/modules/{name}/metadata.json"
    try:
        response = requests.get(url, timeout=30)
    except requests.RequestException:
        return False
    return response.status_code == 200


def resolve_unreleased_repo_packages(repo_name: str, repo_info: dict) -> Dict[str, PackageSource]:
    """
    Fallback for a repo whose distribution.yaml entry can't produce a real
    release through the normal path in resolve_packages: either there's no
    'release:' block at all (never bloom-released into this distro), or
    there is one but it's missing its 'version' pin (bloom has released it,
    but the distribution.yaml PR registering that release hasn't landed).
    Recovers real version + dependency info straight from the package's
    GitHub '-release' companion repo's 'upstream/X.Y.Z' tag -- see
    _find_best_upstream_tag's docstring for why that's the right tag to
    look for here specifically. Every discovered name is checked against
    bcr_module_exists and silently dropped (with a warning) on a hit --
    unlike the primary path in resolve_packages, which only ever produces
    package names an upstream distribution.yaml maintainer chose, this
    fallback trusts an unreviewed archive scan (see
    discover_packages_in_archive), so it needs its own guard against
    minting a package that collides with an unrelated BCR module.

    Deliberately does NOT handle a package that's simply missing from an
    otherwise-complete 'release.packages' list (e.g. ros2_controllers no
    longer lists effort_controllers) -- a fully-resolved release with an
    explicit package list is a maintainer decision to exclude that package,
    not a data gap, and silently second-guessing it here would be a
    different, riskier kind of "fix" than recovering genuinely missing
    data. A repo entirely absent from distribution.yaml (not even a
    'source:' pointer) is likewise out of scope -- there's nothing here to
    hang a fallback off of; recovering it needs a cross-distro lookup, a
    different mechanism than this function provides.
    """
    release = repo_info.get("release") or {}
    source = repo_info.get("source") or {}
    release_url = release.get("url")
    source_url = source.get("url")

    if release_url:
        owner, repo = _parse_github_owner_repo(release_url)
        found = _find_best_upstream_tag(owner, repo, "ros2-gbp" if owner != "ros2-gbp" else None)
    elif source_url:
        owner, bare_repo_name = _parse_github_owner_repo(source_url)
        found = _find_best_upstream_tag(
            owner, f"{bare_repo_name}-release", "ros2-gbp" if owner != "ros2-gbp" else None
        )
    else:
        return {}

    if found is None:
        return {}
    found_owner, found_repo, tag = found
    version = tag.split("/", 1)[1]
    tarball_url = f"https://github.com/{found_owner}/{found_repo}/archive/refs/tags/{tag}.tar.gz"

    discovered = discover_packages_in_archive(tarball_url)
    # When distribution.yaml already names an explicit package list (true
    # for most of the missing-version case), trust it as a whitelist rather
    # than blindly accepting everything the archive scan turns up.
    allowed = set(release["packages"]) if release.get("packages") else None
    wrapper_dir = compute_default_strip_prefix(found_repo, tag)

    result: Dict[str, PackageSource] = {}
    for pkg_name, strip_prefix in discovered.items():
        if pkg_name in IGNORED_PACKAGES:
            continue
        if allowed is not None and pkg_name not in allowed:
            continue
        if bcr_module_exists(pkg_name):
            print(
                f"Warning: discovered package {pkg_name!r} in {found_owner}/{found_repo}@{tag} "
                "collides with an existing BCR module name -- skipping it.",
                file=sys.stderr,
            )
            continue
        # discover_packages_in_archive's strip_prefix is tarball-relative
        # (includes wrapper_dir); fetch_package_xml_dependencies needs a
        # git-tree-relative path instead (no wrapper) to build a
        # raw.githubusercontent.com URL.
        if strip_prefix == wrapper_dir:
            package_xml_subdir = ""
        elif strip_prefix.startswith(wrapper_dir + "/"):
            package_xml_subdir = strip_prefix[len(wrapper_dir) + 1:]
        else:
            package_xml_subdir = strip_prefix
        result[pkg_name] = PackageSource(
            version=version,
            url=tarball_url,
            default_strip_prefix=strip_prefix or wrapper_dir,
            repo_owner=found_owner,
            repo_name=found_repo,
            tag=tag,
            package_xml_subdir=package_xml_subdir,
        )
    return result


def fetch_package_xml_dependencies(pkg_source: PackageSource) -> Set[str]:
    """
    Fetch and parse a package's package.xml directly from its release tag,
    returning every declared dependency name (depend/build_depend/
    exec_depend/run_depend/test_depend). Callers are expected to filter
    this down to names that are themselves resolved ROS packages --
    anything else (an apt/system dependency) is meaningless to Bazel and
    should be dropped, matching the legacy pipeline's behavior.

    An officially-released package's archive is bloom-filtered so
    package.xml always sits at the tag's root; a package resolved via
    resolve_unreleased_repo_packages instead points at a whole-repo
    'upstream/*' archive, so package_xml_subdir locates it within that.
    """
    subdir = f"{pkg_source.package_xml_subdir}/" if pkg_source.package_xml_subdir else ""
    url = f"https://raw.githubusercontent.com/{pkg_source.repo_owner}/{pkg_source.repo_name}/{pkg_source.tag}/{subdir}package.xml"
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    root = ElementTree.fromstring(response.text)
    dep_tags = {"depend", "build_depend", "exec_depend", "run_depend", "test_depend"}
    return {el.text.strip() for el in root if el.tag in dep_tags and el.text}


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

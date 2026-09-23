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
Shared bzlmod/RCR primitives for the tools/ci scripts. Deliberately
independent of tools/bazelflore (see docs/source/design_choices.rst for
the versioning scheme these functions implement).
"""

import base64
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def get_copyright_header() -> str:
    return """# Copyright 2026 Open Source Robotics Foundation, Inc.
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


def parse_diff_status_file(file_path: Path) -> List[Tuple[str, str]]:
    """
    Parses the output of `git diff --name-status` (one "<status>\\t<path>"
    line per changed file) into a list of (status, path) tuples.
    """
    diffs = []
    try:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("\t", 1)
                if len(parts) == 2:
                    diffs.append((parts[0], parts[1]))
        return diffs
    except Exception as e:
        print(f"Error reading diff status file {file_path}: {e}", file=sys.stderr)
        sys.exit(1)


def scan_module_for_dependencies(
    module_dot_bazel: Path,
    modules_path: Path,
    include_bcr: bool = False,
    include_rcr: bool = True,
) -> Dict[str, str]:
    """
    Returns a dict of package name -> version for every bazel_dep() call in
    the given MODULE.bazel file.
    """
    packages = {}
    with open(module_dot_bazel, "r") as f:
        content = f.read()
    matches = re.findall(
        r'bazel_dep\(\s*name\s*=\s*"([^"]+)"\s*,\s*version\s*=\s*"([^"]+)"',
        content,
    )
    for name, version in matches:
        is_rcr_module = (modules_path / name).exists()
        if (include_rcr and is_rcr_module) or (include_bcr and not is_rcr_module):
            packages[name] = version
    return packages


def increment_version(version: str) -> str:
    """
    Increment the .rcr.N patch suffix of a version, e.g.
    "32.0.0-1.rcr.1" -> "32.0.0-1.rcr.2". If the version has no .rcr.N
    suffix yet, appends ".rcr.0".
    """
    version_parts = version.split(".")
    if len(version_parts) < 2:
        raise ValueError(f"Malformed version: {version}")
    if version_parts[-2] == "rcr":
        next_patch_version = int(version_parts[-1]) + 1
        return ".".join(version_parts[:-1] + [str(next_patch_version)])
    return f"{version}.rcr.0"


def version_sort_key(version: str) -> Tuple[str, int, int]:
    """
    Numeric-aware sort key for RCR version strings, so that e.g.
    "32.0.0-1.rcr.10" sorts after "32.0.0-1.rcr.2" (plain lexicographic
    sort would put "rcr.10" before "rcr.2"). Versions without a .rcr.N
    suffix sort before any .rcr.N variant of the same base version.
    """
    parts = version.split(".")
    if len(parts) >= 2 and parts[-2] == "rcr" and parts[-1].isdigit():
        return (".".join(parts[:-2]), 1, int(parts[-1]))
    return (version, 0, -1)


def read_metadata_json(metadata_json_path: Path) -> dict:
    """
    Read a package's metadata.json. Raises FileNotFoundError /
    json.JSONDecodeError if the file is missing or corrupt -- callers are
    expected to have already validated the package/module directory
    exists.
    """
    with open(metadata_json_path, "r") as f:
        return json.load(f)


def get_latest_non_yanked_version(metadata: dict) -> str:
    """
    Returns the latest (numeric-aware) version in metadata["versions"]
    that is not present in metadata["yanked_versions"].
    """
    yanked = metadata.get("yanked_versions", {})
    candidates = [v for v in metadata.get("versions", []) if v not in yanked]
    if not candidates:
        raise ValueError("No non-yanked versions found in metadata.json")
    return max(candidates, key=version_sort_key)


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


def get_latest_matching_patch_version(pinned_version: str, metadata: dict) -> str:
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
    return max(matching, key=version_sort_key)


def add_version_to_metadata_json(metadata_json_path: Path, package_version: str) -> None:
    """
    Append a new version to a package's metadata.json "versions" list (if
    not already present), keeping the list sorted in numeric-aware order.
    Raises if the file is missing or corrupt.
    """
    metadata = read_metadata_json(metadata_json_path)
    if package_version not in metadata["versions"]:
        metadata["versions"].append(package_version)
        metadata["versions"].sort(key=version_sort_key)
        with open(metadata_json_path, "w") as f:
            json.dump(metadata, f, indent=4)
            f.write("\n")


def calculate_integrity_hash_for_file(file_path: Path) -> str:
    """
    Calculate a bazel integrity hash ("sha256-<base64>") for a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return "sha256-" + base64.b64encode(sha256_hash.digest()).decode()


def hash_directory_tree(
    dir_path: Path, exclude_names: Tuple[str, ...] = ("MODULE.bazel", "MODULE.bazel.lock")
) -> Dict[str, str]:
    """
    Hashes every file under dir_path (recursively), keyed by its POSIX
    path relative to dir_path, skipping any file whose basename is in
    exclude_names. Used to snapshot a vendored module's tree right after
    vendoring (see //tools/ci:vendor_modules), and later to cheaply detect
    local edits against that snapshot without a network fetch (see
    //tools/ci:create_patch).
    """
    hashes = {}
    for file_path in sorted(dir_path.rglob("*")):
        if file_path.is_file() and file_path.name not in exclude_names:
            rel_path = file_path.relative_to(dir_path).as_posix()
            hashes[rel_path] = calculate_integrity_hash_for_file(file_path)
    return hashes


def regenerate_integrity_hashes(module_dir: Path) -> None:
    """
    Recompute source.json's "overlay"/"patches" integrity-hash dicts and
    "patch_strip" flag from whatever currently exists on disk under
    module_dir/overlay and module_dir/patches. Raises if source.json is
    missing or corrupt.
    """
    source_json_path = module_dir / "source.json"
    with open(source_json_path, "r") as f:
        source = json.load(f)

    source.pop("overlay", None)
    source.pop("patches", None)

    has_patches = False
    for name in ("overlay", "patches"):
        targ_dir = module_dir / name
        if targ_dir.exists():
            source[name] = {}
            for targ_file in sorted(targ_dir.rglob("*")):
                if targ_file.is_file() and targ_file.name != "MODULE.bazel.lock":
                    rel_path = targ_file.relative_to(targ_dir)
                    source[name][str(rel_path)] = calculate_integrity_hash_for_file(targ_file)
                    if name == "patches":
                        has_patches = True

    if has_patches:
        source["patch_strip"] = 1
    else:
        source.pop("patch_strip", None)

    with open(source_json_path, "w") as f:
        json.dump(source, f, indent=4)
        f.write("\n")


def patch_file_name_from_rel_path(rel_path: Path) -> str:
    """
    Convert a relative path to a patch file name, e.g. "src/foo.c" ->
    "src__foo__c.patch". Must stay identical to the legacy scheme -- it's
    already load-bearing in every existing patches/ directory in modules/.
    """
    path_file_name = str(rel_path).replace("/", "__").replace(".", "__")
    return path_file_name + ".patch"


def read_module_version(module_dot_bazel: Path, package_name: str) -> str:
    """
    Read the version a MODULE.bazel's own module(name=package_name, ...)
    declaration was resolved to. Used instead of scanning bazel_dep text in
    the root workspace, since bazel_dep text doesn't reflect
    single_version_override()s -- the vendored tree's own MODULE.bazel is
    the source of truth for what Bazel actually resolved.
    """
    content = module_dot_bazel.read_text()
    match = re.search(
        r'module\(\s*name\s*=\s*"' + re.escape(package_name) + r'"\s*,\s*version\s*=\s*"([^"]+)"',
        content,
    )
    if not match:
        raise RuntimeError(
            f"Could not find module(name={package_name!r}, ...) in {module_dot_bazel}"
        )
    return match.group(1)


def rewrite_module_version(content: str, package_name: str, new_version: str) -> str:
    """
    Rewrite the version field of a MODULE.bazel's own module(name=...,
    version=..., ...) declaration for package_name. Raises RuntimeError if
    no matching module() block is found -- refuses to silently no-op.
    """
    pattern = re.compile(
        r'(module\(\s*name\s*=\s*"' + re.escape(package_name) + r'"\s*,\s*version\s*=\s*")([^"]+)(")'
    )
    new_content, n = pattern.subn(
        lambda m: m.group(1) + new_version + m.group(3), content, count=1
    )
    if n == 0:
        raise RuntimeError(
            f"Expected a module(name={package_name!r}, ...) block, found none; "
            "refusing to silently skip."
        )
    return new_content


def rewrite_bazel_dep_version(content: str, dep_name: str, new_version: str) -> str:
    """
    Rewrite the version field of a specific bazel_dep(name=dep_name,
    version=...) line. Raises RuntimeError if no matching line is found --
    refuses to silently no-op (unlike the legacy exact-string-replace
    implementation this supersedes).
    """
    pattern = re.compile(
        r'(bazel_dep\(\s*name\s*=\s*"' + re.escape(dep_name) + r'"\s*,\s*version\s*=\s*")([^"]+)(")'
    )
    new_content, n = pattern.subn(
        lambda m: m.group(1) + new_version + m.group(3), content, count=1
    )
    if n == 0:
        raise RuntimeError(
            f"Expected a bazel_dep(name={dep_name!r}, ...) line, found none; "
            "refusing to silently skip (possible drift between metadata.json "
            "and MODULE.bazel)."
        )
    return new_content


def find_packages_with_newer_versions(
    current_map: Dict[str, str], modules_dir: Path
) -> Dict[str, str]:
    """
    Given a package -> pinned-version map, returns the subset of packages
    whose metadata.json lists a newer (numeric-aware, non-yanked) version
    than what's currently pinned.
    """
    result = {}
    for package_name, pinned_version in current_map.items():
        metadata_path = modules_dir / package_name / "metadata.json"
        if not metadata_path.exists():
            continue
        latest = get_latest_non_yanked_version(read_metadata_json(metadata_path))
        if version_sort_key(latest) != version_sort_key(pinned_version):
            result[package_name] = latest
    return result


def git_ref_exists(repo_root: Path, ref: str) -> bool:
    """
    True if `ref` resolves to a commit in the local repo at repo_root
    (does NOT fetch or otherwise consult a remote -- a local branch that
    hasn't been pulled recently can go stale, by design; see
    is_version_published).
    """
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        cwd=repo_root, capture_output=True,
    )
    return result.returncode == 0


def path_exists_at_git_ref(repo_root: Path, ref: str, rel_path: Path) -> bool:
    """
    True if rel_path (POSIX-relative to repo_root) exists as a blob at git
    ref `ref`. Raises RuntimeError if `ref` itself doesn't resolve locally
    -- fails closed rather than silently guessing "not published" (which
    would risk an unwarranted in-place overwrite of something that's
    actually immutable) or "published" (which would silently disable the
    overwrite-in-place feature entirely).
    """
    if not git_ref_exists(repo_root, ref):
        raise RuntimeError(
            f"git ref {ref!r} does not resolve in {repo_root} -- can't tell "
            "whether a version has already been published there. Make sure "
            f"the ref exists locally (e.g. `git fetch origin {ref}:{ref}`), "
            "or pass --base-ref to point at one that does."
        )
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{ref}:{rel_path.as_posix()}"],
        cwd=repo_root, capture_output=True,
    )
    return result.returncode == 0


def is_version_published(repo_root: Path, base_ref: str, module_dir: Path) -> bool:
    """
    True if module_dir (a modules/<package>/<version>/ directory, relative
    to repo_root) already exists at git ref base_ref -- i.e. this version
    has reached base_ref (typically "origin/main") and must be
    treated as immutable, rather than existing only on the current branch
    where it can still be safely amended in place. Checks module_dir's
    MODULE.bazel specifically, since git doesn't track empty directories
    and every version directory always has one.
    """
    rel_path = module_dir.relative_to(repo_root) / "MODULE.bazel"
    return path_exists_at_git_ref(repo_root, base_ref, rel_path)

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
Prints the package names a PR's diff newly adds a module version for, space
separated. Used by ci.yaml to also bazel build/test whatever package(s) a PR
actually touches -- a brand-new or freshly-patched package isn't necessarily
part of any of the six fixed distribution variants (ros_core, ros_base,
desktop, desktop_full, perception, simulation), so the variant build alone
can silently never exercise it at all.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

from tools.ci import bzlmod_lib
from tools.ci import module_diff


DISTRIBUTION_VARIANTS = {
    "ros",
    "ros_core",
    "ros_base",
    "desktop",
    "desktop_full",
    "perception",
    "simulation",
}


def find_changed_packages(diffs: List[Tuple[str, str]], target_dir: str) -> List[str]:
    """
    Deduplicated, sorted package names with at least one newly-added ("A"
    status) version directory under target_dir -- every package this repo's
    own patching model (setup-workspace/vendor-module/create-patch) could
    have touched, since a patch is always a brand-new version directory,
    never an edit to an existing one. Excludes distribution umbrella/variant
    modules which are already exercised by the matrix variant builds.
    """
    return sorted({
        package
        for package, _version in module_diff.find_new_module_versions(diffs, target_dir)
        if package not in DISTRIBUTION_VARIANTS
    })


def main():
    parser = argparse.ArgumentParser(
        description="Print the package names a PR's diff newly adds a module version for."
    )
    parser.add_argument(
        "--diff-status",
        required=True,
        type=Path,
        help="Path to the file containing git diff --name-status output",
    )
    parser.add_argument(
        "--directory",
        default="modules",
        help="Directory to scan for new module versions (e.g. modules or bcr_staging/modules)",
    )
    args = parser.parse_args()

    diffs = bzlmod_lib.parse_diff_status_file(args.diff_status)
    packages = find_changed_packages(diffs, args.directory)
    print(" ".join(packages))
    return 0


if __name__ == "__main__":
    sys.exit(main())

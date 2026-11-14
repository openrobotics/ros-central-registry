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
"""Run an auto_apms_behavior_tree_core CLI tool against an ament index.

Upstream's CMake runs these generators with the ament index of
auto_apms_behavior_tree_core already installed into the environment. Under
Bazel, genrule tools only see their own runfiles, so this wrapper carries the
needed ament index in *its* runfiles (via `data`) and exports that tree as
AMENT_PREFIX_PATH before exec'ing the real tool.

Usage: ament_prefix_wrapper <tool> [args...]
"""

import os
import sys


def _runfiles_main_dir():
    runfiles_dir = os.environ.get("RUNFILES_DIR")
    if not runfiles_dir:
        # This script lives at <runfiles>/<repo>/bazel/ament_prefix_wrapper.py.
        runfiles_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # ament_index symlinks are rooted at the main repository's runfiles dir.
    return os.path.join(runfiles_dir, "_main")


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage: ament_prefix_wrapper <tool> [args...]\n")
        return 2
    tool = os.path.abspath(sys.argv[1])
    env = dict(os.environ)
    prefix = _runfiles_main_dir()
    existing = env.get("AMENT_PREFIX_PATH")
    env["AMENT_PREFIX_PATH"] = prefix + (":" + existing if existing else "")
    # Let the tool resolve its own runfiles rather than the wrapper's.
    for var in ("RUNFILES_DIR", "RUNFILES_MANIFEST_FILE", "JAVA_RUNFILES"):
        env.pop(var, None)
    os.execve(tool, [tool] + sys.argv[2:], env)
    return 1


if __name__ == "__main__":
    sys.exit(main())

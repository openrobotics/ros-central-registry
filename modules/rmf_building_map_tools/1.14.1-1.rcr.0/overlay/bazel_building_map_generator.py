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
"""Hermetic build-time wrapper around building_map_generator.

Upstream resolves its world template and textures through
ament_index_python (share/rmf_building_map_tools/{templates,textures}) and
reads an optional model cache from ~/.pit_crew. Inside a Bazel action neither
an installed prefix nor a meaningful $HOME exists, so this wrapper:

  * builds a throwaway ament prefix that points at the runfiles copies of the
    templates and textures, and
  * points $HOME at an empty scratch directory so the output never depends on
    whatever model cache the build machine happens to have.

An optional leading --model_cache=PATH seeds the sandboxed model cache.
The next argument picks the upstream console script (building_map_generator
or building_crowdsim); the rest are forwarded unchanged.
"""

import os
import shutil
import sys
import tempfile

PACKAGE = "rmf_building_map_tools"


def _find_share_source():
    here = os.path.dirname(os.path.abspath(__file__))
    for root in (here, os.path.join(here, "..")):
        if os.path.isdir(os.path.join(root, "building_map_generator", "textures")):
            return os.path.realpath(root)
    raise RuntimeError("could not locate %s data files next to %s" % (PACKAGE, here))


def _make_prefix(scratch, src):
    share = os.path.join(scratch, "prefix", "share")
    marker_dir = os.path.join(share, "ament_index", "resource_index", "packages")
    os.makedirs(marker_dir)
    open(os.path.join(marker_dir, PACKAGE), "w").close()
    pkg_share = os.path.join(share, PACKAGE)
    os.makedirs(pkg_share)
    os.symlink(os.path.join(src, "building_map", "templates"), os.path.join(pkg_share, "templates"))
    os.symlink(
        os.path.join(src, "building_map_generator", "textures"), os.path.join(pkg_share, "textures")
    )
    return os.path.join(scratch, "prefix")


def main():
    scratch = tempfile.mkdtemp(prefix="building_map_generator.")
    os.environ["AMENT_PREFIX_PATH"] = _make_prefix(scratch, _find_share_source())
    home = os.path.join(scratch, "home")
    os.makedirs(home)
    os.environ["HOME"] = home

    # Optional checked-in stand-in for ~/.pit_crew/model_cache.json, which
    # upstream fills by downloading the Fuel model index
    # (building_map_model_downloader). Models listed there are emitted as
    # https://fuel.gazebosim.org URIs instead of model://.
    if len(sys.argv) > 1 and sys.argv[1].startswith("--model_cache="):
        cache = sys.argv.pop(1).split("=", 1)[1]
        os.makedirs(os.path.join(home, ".pit_crew"))
        shutil.copyfile(cache, os.path.join(home, ".pit_crew", "model_cache.json"))

    # First argument selects the upstream console script, mirroring
    # `ros2 run rmf_building_map_tools <tool> ...` in upstream CMake.
    tool = sys.argv.pop(1) if len(sys.argv) > 1 else ""
    if tool == "building_map_generator":
        from building_map_generator.building_map_generator import main as upstream_main
    elif tool == "building_crowdsim":
        from building_crowdsim.building_crowdsim import main as upstream_main
    else:
        sys.exit("usage: %s {building_map_generator,building_crowdsim} ARGS..." % sys.argv[0])

    sys.argv[0] = tool
    upstream_main()


if __name__ == "__main__":
    main()

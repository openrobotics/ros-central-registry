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

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.ci import rollup_patches


class TestFindCurrentRosVersion(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.ros_dir = self.tmp_dir / "ros"
        self.ros_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def make_release_dirs(self, names):
        for name in names:
            (self.ros_dir / name).mkdir()

    def test_finds_highest_patch(self):
        self.make_release_dirs([
            "lyrical.2026-06-08.rcr.0",
            "lyrical.2026-06-08.rcr.1",
            "lyrical.2026-06-08.rcr.9",
            "lyrical.2026-06-08.rcr.10",
        ])
        result = rollup_patches.find_current_ros_version(self.tmp_dir, "lyrical", "2026-06-08")
        self.assertEqual(result, "lyrical.2026-06-08.rcr.10")

    def test_ignores_other_distro_date_rows(self):
        self.make_release_dirs(["rolling.2026-01-21.rcr.5", "lyrical.2026-06-08.rcr.1"])
        result = rollup_patches.find_current_ros_version(self.tmp_dir, "lyrical", "2026-06-08")
        self.assertEqual(result, "lyrical.2026-06-08.rcr.1")

    def test_raises_if_none_found(self):
        with self.assertRaises(RuntimeError):
            rollup_patches.find_current_ros_version(self.tmp_dir, "lyrical", "2026-06-08")


class TestCheckNoYankedDependencies(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def write_metadata(self, package_name: str, yanked=None):
        package_dir = self.tmp_dir / package_name
        package_dir.mkdir()
        with open(package_dir / "metadata.json", "w") as f:
            json.dump({"versions": ["1.0.0"], "yanked_versions": yanked or {}}, f)

    def test_passes_when_nothing_yanked(self):
        self.write_metadata("rclcpp")
        rollup_patches.check_no_yanked_dependencies({"rclcpp": "1.0.0"}, self.tmp_dir)

    def test_raises_when_pinned_version_is_yanked(self):
        self.write_metadata("rclcpp", yanked={"1.0.0": "bad build"})
        with self.assertRaises(RuntimeError):
            rollup_patches.check_no_yanked_dependencies({"rclcpp": "1.0.0"}, self.tmp_dir)


class TestGetBaseVersion(unittest.TestCase):

    def test_rcr_versions(self):
        self.assertEqual(rollup_patches.get_base_version("1.0.0-1.rcr.1"), "1.0.0-1")
        self.assertEqual(rollup_patches.get_base_version("1.0.0.rcr.2"), "1.0.0")
        self.assertEqual(rollup_patches.get_base_version("lyrical.2026-06-08.rcr.1"), "lyrical.2026-06-08")

    def test_versions_without_rcr(self):
        self.assertEqual(rollup_patches.get_base_version("1.0.0"), "1.0.0")
        self.assertEqual(rollup_patches.get_base_version("lyrical.2026-06-08"), "lyrical.2026-06-08")


class TestGetLatestMatchingPatchVersion(unittest.TestCase):

    def test_selects_highest_matching_patch(self):
        metadata = {
            "versions": ["1.0.0.rcr.1", "1.0.0.rcr.2", "2.0.0.rcr.1"],
            "yanked_versions": {},
        }
        result = rollup_patches.get_latest_matching_patch_version("1.0.0.rcr.1", metadata)
        self.assertEqual(result, "1.0.0.rcr.2")

    def test_ignores_yanked_patch(self):
        metadata = {
            "versions": ["1.0.0.rcr.1", "1.0.0.rcr.2", "1.0.0.rcr.3"],
            "yanked_versions": {"1.0.0.rcr.3": "broken build"},
        }
        result = rollup_patches.get_latest_matching_patch_version("1.0.0.rcr.1", metadata)
        self.assertEqual(result, "1.0.0.rcr.2")

    def test_returns_pinned_if_no_newer_patch(self):
        metadata = {
            "versions": ["1.0.0.rcr.1"],
            "yanked_versions": {},
        }
        result = rollup_patches.get_latest_matching_patch_version("1.0.0.rcr.1", metadata)
        self.assertEqual(result, "1.0.0.rcr.1")


class TestRollupVariants(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.modules_dir = self.tmp_dir / "modules"
        self.modules_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_rollup_variants_end_to_end(self):
        # Create a package rclcpp with .rcr.1 and a newly published .rcr.2
        rclcpp_dir = self.modules_dir / "rclcpp"
        rclcpp_dir.mkdir()
        (rclcpp_dir / "32.0.0-1.rcr.1").mkdir()
        (rclcpp_dir / "32.0.0-1.rcr.2").mkdir()
        (rclcpp_dir / "metadata.json").write_text(json.dumps({
            "versions": ["32.0.0-1.rcr.1", "32.0.0-1.rcr.2"],
            "yanked_versions": {},
        }))

        # Create variant 'perception' and 'ros' at lyrical.2026-06-08.rcr.1
        for variant in ["ros", "perception"]:
            v_dir = self.modules_dir / variant
            v_dir.mkdir()
            (v_dir / "metadata.json").write_text(json.dumps({
                "versions": ["lyrical.2026-06-08.rcr.1"],
                "yanked_versions": {},
            }))
            ver_dir = v_dir / "lyrical.2026-06-08.rcr.1"
            ver_dir.mkdir()
            ver_dir.joinpath("MODULE.bazel").write_text(f"""module(
    name = "{variant}",
    version = "lyrical.2026-06-08.rcr.1",
)
bazel_dep(name = "rclcpp", version = "32.0.0-1.rcr.1")
""")

        new_ver = rollup_patches.rollup_variants(
            self.modules_dir, "lyrical", "2026-06-08", dry_run=False
        )
        self.assertEqual(new_ver, "lyrical.2026-06-08.rcr.2")

        # Verify perception was bumped and pins rclcpp@32.0.0-1.rcr.2
        p_module = (self.modules_dir / "perception" / "lyrical.2026-06-08.rcr.2" / "MODULE.bazel").read_text()
        self.assertIn('version = "lyrical.2026-06-08.rcr.2"', p_module)
        self.assertIn('bazel_dep(name = "rclcpp", version = "32.0.0-1.rcr.2")', p_module)

        # Verify rclcpp itself was NOT modified
        self.assertFalse((self.modules_dir / "rclcpp" / "32.0.0-1.rcr.3").exists())


if __name__ == "__main__":
    unittest.main()

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

import unittest

from tools.ci import changed_packages


class TestFindChangedPackages(unittest.TestCase):

    def test_deduplicates_and_sorts_package_names(self):
        diffs = [
            ("A", "modules/rclcpp/32.0.0-1.rcr.2/MODULE.bazel"),
            ("A", "modules/rclcpp/32.0.0-1.rcr.2/source.json"),
            ("A", "modules/ouster_ros/0.14.2-3.rcr.3/MODULE.bazel"),
            ("M", "modules/rclcpp/metadata.json"),
        ]
        self.assertEqual(
            changed_packages.find_changed_packages(diffs, "modules"),
            ["ouster_ros", "rclcpp"],
        )

    def test_ignores_modified_and_deleted_files(self):
        diffs = [
            ("M", "modules/rclcpp/32.0.0-1.rcr.1/MODULE.bazel"),
            ("D", "modules/old_pkg/1.0.0/MODULE.bazel"),
        ]
        self.assertEqual(changed_packages.find_changed_packages(diffs, "modules"), [])

    def test_ignores_other_directories(self):
        diffs = [("A", "bcr_staging/modules/foo/1.0.0/MODULE.bazel")]
        self.assertEqual(changed_packages.find_changed_packages(diffs, "modules"), [])

    def test_no_changes_returns_empty_list(self):
        self.assertEqual(changed_packages.find_changed_packages([], "modules"), [])

    def test_ignores_distribution_variants_and_ros(self):
        diffs = [
            ("A", "modules/ros/lyrical.2026-06-08.rcr.2/MODULE.bazel"),
            ("A", "modules/perception/lyrical.2026-06-08.rcr.2/MODULE.bazel"),
            ("A", "modules/desktop/lyrical.2026-06-08.rcr.2/MODULE.bazel"),
            ("A", "modules/rclcpp/32.0.0-1.rcr.2/MODULE.bazel"),
        ]
        self.assertEqual(
            changed_packages.find_changed_packages(diffs, "modules"),
            ["rclcpp"],
        )


if __name__ == "__main__":
    unittest.main()

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

import subprocess
import unittest

from tools.ci import rosdistro_lib


class TestListNewTags(unittest.TestCase):

    def _fake_run(self, tag_names):
        class _FakeResult:
            stdout = "\n".join(tag_names) + "\n"

        def _run(*args, **kwargs):
            return _FakeResult()
        return _run

    def test_only_returns_tags_newer_than_latest_bootstrapped(self):
        # lyrical/2026-05-22 predates the already-bootstrapped 2026-06-08
        # and was intentionally never bootstrapped -- must not resurface.
        tags = ["lyrical/2026-05-22", "lyrical/2026-06-08", "lyrical/2026-06-23", "rolling/2026-01-21"]
        original_run = subprocess.run
        rosdistro_lib.subprocess.run = self._fake_run(tags)
        try:
            result = rosdistro_lib.list_new_tags("lyrical", {"lyrical.2026-06-08"})
        finally:
            rosdistro_lib.subprocess.run = original_run
        self.assertEqual(result, ["2026-06-23"])

    def test_no_prior_bootstrap_returns_everything(self):
        tags = ["lyrical/2026-05-22", "lyrical/2026-06-08"]
        original_run = subprocess.run
        rosdistro_lib.subprocess.run = self._fake_run(tags)
        try:
            result = rosdistro_lib.list_new_tags("lyrical", set())
        finally:
            rosdistro_lib.subprocess.run = original_run
        self.assertEqual(result, ["2026-05-22", "2026-06-08"])


class TestComputeDefaultStripPrefix(unittest.TestCase):

    def test_replaces_slashes(self):
        self.assertEqual(
            rosdistro_lib.compute_default_strip_prefix("rcutils-release", "release/lyrical/rcutils/7.1.1-3"),
            "rcutils-release-release-lyrical-rcutils-7.1.1-3",
        )

    def test_ros_module_archive_shape(self):
        self.assertEqual(
            rosdistro_lib.compute_default_strip_prefix("rosdistro", "lyrical/2026-06-08"),
            "rosdistro-lyrical-2026-06-08",
        )


class TestResolvePackages(unittest.TestCase):

    def test_expands_multi_package_repo(self):
        distribution = {
            "repositories": {
                "rclcpp": {
                    "release": {
                        "url": "https://github.com/ros2-gbp/rclcpp-release.git",
                        "version": "32.0.0-1",
                        "packages": ["rclcpp", "rclcpp_action"],
                        "tags": {"release": "release/{package}/{version}"},
                    }
                },
            }
        }
        packages = rosdistro_lib.resolve_packages(distribution, "lyrical", "2026-06-08")
        self.assertIn("rclcpp", packages)
        self.assertIn("rclcpp_action", packages)
        self.assertEqual(packages["rclcpp"].version, "32.0.0-1")
        self.assertEqual(packages["rclcpp"].tag, "release/rclcpp/32.0.0-1")
        self.assertEqual(
            packages["rclcpp"].url,
            "https://github.com/ros2-gbp/rclcpp-release/archive/refs/tags/release/rclcpp/32.0.0-1.tar.gz",
        )

    def test_single_package_repo_defaults_name_to_repo_name(self):
        distribution = {
            "repositories": {
                "rcutils": {
                    "release": {
                        "url": "https://github.com/ros2-gbp/rcutils-release.git",
                        "version": "7.1.1-3",
                        "tags": {"release": "release/{package}/{version}"},
                    }
                },
            }
        }
        packages = rosdistro_lib.resolve_packages(distribution, "lyrical", "2026-06-08")
        self.assertIn("rcutils", packages)
        self.assertEqual(packages["rcutils"].version, "7.1.1-3")

    def test_date_versioned_meta_package_gets_distro_date_version(self):
        distribution = {
            "repositories": {
                "ros_core": {
                    "release": {
                        "url": "https://github.com/ros2-gbp/ros_core-release.git",
                        "version": "1.2.3-1",
                        "tags": {"release": "release/{package}/{version}"},
                    }
                },
            }
        }
        packages = rosdistro_lib.resolve_packages(distribution, "lyrical", "2026-06-08")
        self.assertEqual(packages["ros_core"].version, "lyrical.2026-06-08")

    def test_ignored_packages_are_skipped(self):
        distribution = {
            "repositories": {
                "cyclonedds": {
                    "release": {
                        "url": "https://github.com/ros2-gbp/cyclonedds-release.git",
                        "version": "1.0.0",
                        "tags": {"release": "release/{package}/{version}"},
                    }
                },
            }
        }
        packages = rosdistro_lib.resolve_packages(distribution, "lyrical", "2026-06-08")
        self.assertNotIn("cyclonedds", packages)

    def test_extra_packages_always_included(self):
        packages = rosdistro_lib.resolve_packages({"repositories": {}}, "lyrical", "2026-06-08")
        self.assertIn("rosidl_adapter_proto", packages)
        self.assertIn("rosidl_typesupport_protobuf", packages)

    def test_source_only_repo_without_release_is_skipped(self):
        distribution = {
            "repositories": {
                "some_doc_only_repo": {
                    "doc": {"type": "git", "url": "https://github.com/ros2/foo.git", "version": "lyrical"},
                },
            }
        }
        packages = rosdistro_lib.resolve_packages(distribution, "lyrical", "2026-06-08")
        self.assertNotIn("some_doc_only_repo", packages)


class TestFetchPackageXmlDependencies(unittest.TestCase):

    def test_parses_dependency_tags(self):
        pkg_source = rosdistro_lib.PackageSource(
            version="1.0.0", url="unused", default_strip_prefix="unused",
        )

        # Monkeypatch requests.get to avoid a real network call in this test.
        class _FakeResponse:
            text = (
                '<?xml version="1.0"?>'
                '<package format="2">'
                "<name>foo</name>"
                "<buildtool_depend>ament_cmake</buildtool_depend>"
                "<depend>rclcpp</depend>"
                "<build_depend>rcutils</build_depend>"
                "<exec_depend>rcutils</exec_depend>"
                "<test_depend>ament_lint_auto</test_depend>"
                "</package>"
            )

            def raise_for_status(self):
                pass

        original_get = rosdistro_lib.requests.get
        rosdistro_lib.requests.get = lambda *a, **k: _FakeResponse()
        try:
            deps = rosdistro_lib.fetch_package_xml_dependencies(pkg_source)
        finally:
            rosdistro_lib.requests.get = original_get

        # buildtool_depend must be kept: it's how every interface package
        # declares rosidl_default_generators / ament_cmake.
        self.assertEqual(deps, {"ament_cmake", "rclcpp", "rcutils", "ament_lint_auto"})


class TestParsePackageXmlDependencies(unittest.TestCase):

    def test_every_rep149_depend_tag_is_collected(self):
        xml = (
            '<?xml version="1.0"?>'
            '<package format="3">'
            "<name>foo</name>"
            "<buildtool_depend>ament_cmake</buildtool_depend>"
            "<buildtool_export_depend>ament_cmake_core</buildtool_export_depend>"
            "<build_depend>rcutils</build_depend>"
            "<build_export_depend>rcpputils</build_export_depend>"
            "<depend>rclcpp</depend>"
            "<exec_depend>rosidl_default_runtime</exec_depend>"
            "<run_depend>legacy_pkg</run_depend>"
            "<test_depend>ament_lint_auto</test_depend>"
            "<doc_depend>rosdoc2</doc_depend>"
            "</package>"
        )
        self.assertEqual(rosdistro_lib.parse_package_xml_dependencies(xml), {
            "ament_cmake", "ament_cmake_core", "rcutils", "rcpputils", "rclcpp",
            "rosidl_default_runtime", "legacy_pkg", "ament_lint_auto", "rosdoc2",
        })

    def test_non_depend_tags_are_ignored(self):
        xml = (
            '<package format="3">'
            "<name>foo</name>"
            "<version>1.0.0</version>"
            "<maintainer email=\"a@b.c\">A</maintainer>"
            "<license>Apache-2.0</license>"
            "<export><build_type>ament_cmake</build_type></export>"
            "</package>"
        )
        self.assertEqual(rosdistro_lib.parse_package_xml_dependencies(xml), set())

    def test_conditional_deps_are_kept_unevaluated(self):
        # Conditions aren't evaluated; callers filter against the resolved
        # package set, which drops ROS 1-only names like catkin anyway.
        xml = (
            '<package format="3">'
            "<name>foo</name>"
            '<buildtool_depend condition="$ROS_VERSION == 1">catkin</buildtool_depend>'
            '<buildtool_depend condition="$ROS_VERSION == 2">ament_cmake</buildtool_depend>'
            "</package>"
        )
        self.assertEqual(rosdistro_lib.parse_package_xml_dependencies(xml), {"catkin", "ament_cmake"})

    def test_whitespace_stripped_and_empty_skipped(self):
        xml = (
            '<package format="3">'
            "<name>foo</name>"
            "<depend>\n  rclcpp\n</depend>"
            "<depend></depend>"
            "</package>"
        )
        self.assertEqual(rosdistro_lib.parse_package_xml_dependencies(xml), {"rclcpp"})


if __name__ == "__main__":
    unittest.main()

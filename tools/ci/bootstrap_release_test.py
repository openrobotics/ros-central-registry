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

from tools.ci import bootstrap_release


class TestFindExistingRelease(unittest.TestCase):

    def setUp(self):
        self.package_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.package_dir)

    def test_returns_none_for_brand_new_package(self):
        self.assertIsNone(bootstrap_release.find_existing_release(self.package_dir, "1.0.0"))

    def test_finds_exact_bare_match(self):
        (self.package_dir / "1.0.0").mkdir()
        self.assertEqual(bootstrap_release.find_existing_release(self.package_dir, "1.0.0"), "1.0.0")

    def test_prefers_highest_patch_over_bare(self):
        (self.package_dir / "1.0.0").mkdir()
        (self.package_dir / "1.0.0.rcr.0").mkdir()
        (self.package_dir / "1.0.0.rcr.2").mkdir()
        (self.package_dir / "1.0.0.rcr.1").mkdir()
        self.assertEqual(bootstrap_release.find_existing_release(self.package_dir, "1.0.0"), "1.0.0.rcr.2")

    def test_ignores_unrelated_versions(self):
        (self.package_dir / "2.0.0").mkdir()
        (self.package_dir / "2.0.0.rcr.5").mkdir()
        self.assertIsNone(bootstrap_release.find_existing_release(self.package_dir, "1.0.0"))


class TestFindCandidatePatchVersion(unittest.TestCase):

    def setUp(self):
        self.package_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.package_dir)

    def test_returns_none_with_no_patches(self):
        (self.package_dir / "1.0.0").mkdir()
        self.assertIsNone(bootstrap_release.find_candidate_patch_version(self.package_dir))

    def test_finds_most_recent_across_versions(self):
        (self.package_dir / "1.0.0.rcr.0").mkdir()
        (self.package_dir / "1.0.0.rcr.1").mkdir()
        (self.package_dir / "2.0.0.rcr.0").mkdir()
        self.assertEqual(bootstrap_release.find_candidate_patch_version(self.package_dir), "2.0.0.rcr.0")


class TestAlreadyBootstrappedDates(unittest.TestCase):

    def setUp(self):
        self.modules_dir = Path(tempfile.mkdtemp())
        (self.modules_dir / "ros").mkdir()

    def tearDown(self):
        shutil.rmtree(self.modules_dir)

    def test_only_bare_two_part_names_match(self):
        for name in ["lyrical.2026-06-08", "lyrical.2026-06-08.rcr.0", "lyrical.2026-06-08.rcr.1", "rolling.2026-01-21"]:
            (self.modules_dir / "ros" / name).mkdir()
        result = bootstrap_release.already_bootstrapped_dates(self.modules_dir, "lyrical")
        self.assertEqual(result, {"lyrical.2026-06-08"})

    def test_missing_ros_dir_returns_empty(self):
        shutil.rmtree(self.modules_dir / "ros")
        self.assertEqual(bootstrap_release.already_bootstrapped_dates(self.modules_dir, "lyrical"), set())


class TestRenderModuleDotBazel(unittest.TestCase):

    def test_includes_bcr_and_rcr_deps_plus_forced_rosdistro(self):
        content = bootstrap_release.render_module_dot_bazel(
            "rclcpp", "32.0.0-1", {"rcutils": "7.1.1-3"}, "lyrical", "2026-06-23")
        self.assertIn('module(\n    name = "rclcpp",\n    version = "32.0.0-1",', content)
        self.assertIn('bazel_dep(name = "aspect_rules_py", version = "1.11.7")', content)
        self.assertIn('bazel_dep(name = "rcutils", version = "7.1.1-3")', content)
        self.assertIn('bazel_dep(name = "rosdistro", version = "lyrical.2026-06-23")', content)
        self.assertIn('pip_ros = use_extension("@rosdistro//python:defs.bzl", "pip_ros")', content)

    def test_custom_body_skips_generic_rcr_section(self):
        content = bootstrap_release.render_module_dot_bazel(
            "rosdistro", "lyrical.2026-06-23", {}, "lyrical", "2026-06-23",
            custom_body=bootstrap_release.ROSDISTRO_CUSTOM_BODY)
        self.assertNotIn("# RCR Dependencies", content)
        self.assertIn('bazel_dep(name = "assimp", version = "6.0.3")', content)
        self.assertIn('hub_name = "pip_ros"', content)

    def test_trailing_register_toolchains_is_buildifier_formatted(self):
        # buildifier requires a blank line before a bare statement that
        # follows a use_repo(...) call -- regression test for a bug where
        # every bootstrapped MODULE.bazel failed lint (see git history).
        for content in (
                bootstrap_release.render_module_dot_bazel(
                    "rclcpp", "32.0.0-1", {}, "lyrical", "2026-06-23"),
                bootstrap_release.render_module_dot_bazel(
                    "rosdistro", "lyrical.2026-06-23", {}, "lyrical", "2026-06-23",
                    custom_body=bootstrap_release.ROSDISTRO_CUSTOM_BODY)):
            self.assertIn('use_repo(qt, "qt_linux_x86_64")\n\nregister_toolchains("@rules_qt//tools:all")', content)


class TestRenderStubModuleDotBazel(unittest.TestCase):

    def test_matches_real_stub_shape(self):
        content = bootstrap_release.render_stub_module_dot_bazel("rclcpp")
        self.assertIn('module(\n    name = "rclcpp",\n    version = "0.0.0",\n    bazel_compatibility = [">=7.2.1"],\n)\n', content)
        self.assertNotIn("bazel_dep", content)


class TestRenderBoilerplateOverlayBuildBazel(unittest.TestCase):

    def test_ament_package_deps_include_rcr_deps_and_rosdistro_sorted(self):
        content = bootstrap_release.render_boilerplate_overlay_build_bazel(
            {"ament_cmake": "2.8.7-3.rcr.1", "ament_lint_auto": "0.20.6-1.rcr.1"}
        )
        self.assertIn('load("@rosdistro//ament:defs.bzl", "ament_package")', content)
        self.assertIn('package(default_visibility = ["//visibility:public"])', content)
        self.assertIn('name = "ament_package"', content)
        self.assertIn('package_xml = "package.xml"', content)
        # Sorted alphabetically, matching every hand-written overlay/BUILD.bazel.
        self.assertIn(
            '    deps = [\n'
            '        "@ament_cmake//:ament_package",\n'
            '        "@ament_lint_auto//:ament_package",\n'
            '        "@rosdistro//:ament_package",\n'
            '    ],\n',
            content,
        )

    def test_rosdistro_always_included_even_with_no_rcr_deps(self):
        content = bootstrap_release.render_boilerplate_overlay_build_bazel({})
        self.assertIn('"@rosdistro//:ament_package"', content)

    def test_no_duplicate_rosdistro_entry_if_already_a_dep(self):
        content = bootstrap_release.render_boilerplate_overlay_build_bazel(
            {"rosdistro": "lyrical.2026-06-08.rcr.1"}
        )
        self.assertEqual(content.count('"@rosdistro//:ament_package"'), 1)


class TestDeriveHomepage(unittest.TestCase):

    def test_truncates_github_url_to_owner_repo(self):
        self.assertEqual(
            bootstrap_release.derive_homepage(
                "https://github.com/ros2-gbp/rcutils-release/archive/refs/tags/release/lyrical/rcutils/7.1.1-3.tar.gz"),
            "https://github.com/ros2-gbp/rcutils-release",
        )

    def test_non_github_url_passthrough(self):
        url = "https://example.com/foo.tar.gz"
        self.assertEqual(bootstrap_release.derive_homepage(url), url)


class TestWriteMetadataJsonIfMissing(unittest.TestCase):

    def setUp(self):
        self.pkg_dir = Path(tempfile.mkdtemp()) / "some_pkg"

    def tearDown(self):
        shutil.rmtree(self.pkg_dir.parent)

    def test_creates_fresh_metadata(self):
        bootstrap_release.write_metadata_json_if_missing(
            self.pkg_dir, "https://github.com/ros2-gbp/foo-release/archive/x.tar.gz", "1.0.0")
        with open(self.pkg_dir / "metadata.json") as f:
            metadata = json.load(f)
        self.assertEqual(metadata["versions"], ["1.0.0"])
        self.assertEqual(metadata["homepage"], "https://github.com/ros2-gbp/foo-release")
        self.assertEqual(metadata["yanked_versions"], {})

    def test_appends_to_existing_metadata(self):
        self.pkg_dir.mkdir(parents=True)
        with open(self.pkg_dir / "metadata.json", "w") as f:
            json.dump({"homepage": "x", "maintainers": [], "versions": ["1.0.0"], "yanked_versions": {}}, f)
        bootstrap_release.write_metadata_json_if_missing(self.pkg_dir, "unused", "2.0.0")
        with open(self.pkg_dir / "metadata.json") as f:
            metadata = json.load(f)
        self.assertEqual(metadata["versions"], ["1.0.0", "2.0.0"])


if __name__ == "__main__":
    unittest.main()

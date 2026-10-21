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

    def test_ignores_bare_match_without_rcr_suffix(self):
        (self.package_dir / "1.0.0").mkdir()
        self.assertIsNone(bootstrap_release.find_existing_release(self.package_dir, "1.0.0"))

    def test_prefers_highest_patch(self):
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

    def test_extracts_dates_from_rcr_versions(self):
        for name in ["0.0.0", "lyrical.2026-06-08.rcr.0", "lyrical.2026-06-08.rcr.1", "lyrical.2026-10-05.rcr.0", "rolling.2026-01-21.rcr.0"]:
            (self.modules_dir / "ros" / name).mkdir()
        result = bootstrap_release.already_bootstrapped_dates(self.modules_dir, "lyrical")
        self.assertEqual(result, {"lyrical.2026-06-08", "lyrical.2026-10-05"})

    def test_missing_ros_dir_returns_empty(self):
        shutil.rmtree(self.modules_dir / "ros")
        self.assertEqual(bootstrap_release.already_bootstrapped_dates(self.modules_dir, "lyrical"), set())


class TestRenderModuleDotBazel(unittest.TestCase):

    def test_includes_bcr_and_rcr_deps_plus_forced_rosdistro(self):
        content = bootstrap_release.render_module_dot_bazel(
            "rclcpp", "32.0.0-1.rcr.0", {"rcutils": "7.1.1-3.rcr.0"}, "lyrical", "2026-06-23")
        self.assertIn('module(\n    name = "rclcpp",\n    version = "32.0.0-1.rcr.0",', content)
        self.assertIn('bazel_dep(name = "rules_python", version = "2.4.1")', content)
        self.assertIn('bazel_dep(name = "rcutils", version = "7.1.1-3.rcr.0")', content)
        self.assertIn('bazel_dep(name = "rosdistro", version = "lyrical.2026-06-23.rcr.0")', content)
        self.assertIn('pip_ros = use_extension("@rosdistro//python:defs.bzl", "pip_ros")', content)

    def test_explicit_rosdistro_pin_overrides_default_fallback(self):
        content = bootstrap_release.render_module_dot_bazel(
            "rclcpp", "32.0.0-1.rcr.0", {"rosdistro": "lyrical.2026-06-23.rcr.1"}, "lyrical", "2026-06-23")
        self.assertIn('bazel_dep(name = "rosdistro", version = "lyrical.2026-06-23.rcr.1")', content)
        self.assertEqual(content.count('name = "rosdistro"'), 1)


    def test_custom_body_skips_generic_rcr_section(self):
        content = bootstrap_release.render_module_dot_bazel(
            "rosdistro", "lyrical.2026-06-23", {}, "lyrical", "2026-06-23",
            custom_body=bootstrap_release.ROSDISTRO_CUSTOM_BODY)
        self.assertNotIn("# RCR Dependencies", content)
        self.assertIn('bazel_dep(name = "assimp", version = "6.0.3")', content)
        self.assertIn('hub_name = "pip_ros"', content)

    def test_rules_qt_is_replaced_by_from_source_qt(self):
        for content in (
                bootstrap_release.render_module_dot_bazel(
                    "rclcpp", "32.0.0-1", {}, "lyrical", "2026-06-23"),
                bootstrap_release.render_module_dot_bazel(
                    "rosdistro", "lyrical.2026-06-23", {}, "lyrical", "2026-06-23",
                    custom_body=bootstrap_release.ROSDISTRO_CUSTOM_BODY)):
            self.assertNotIn("rules_qt", content)
            self.assertNotIn("qt.install(", content)
            for name in bootstrap_release.QT_MODULES:
                self.assertIn(
                    f'bazel_dep(name = "{name}", version = "{bootstrap_release.QT_VERSION}")',
                    content,
                )
            # No trailing blank line (buildifier).
            self.assertTrue(content.endswith(")\n"), content[-80:])


class TestSelectTags(unittest.TestCase):

    DATES = ["2026-06-23", "2026-08-07", "2026-10-05"]

    def test_default_keeps_every_tag_in_order(self):
        self.assertEqual(bootstrap_release.select_tags(self.DATES, only_latest=False), self.DATES)

    def test_only_latest_keeps_newest(self):
        self.assertEqual(bootstrap_release.select_tags(self.DATES, only_latest=True), ["2026-10-05"])

    def test_only_latest_on_empty_is_empty(self):
        self.assertEqual(bootstrap_release.select_tags([], only_latest=True), [])


class TestRenderStubModuleDotBazel(unittest.TestCase):

    def test_matches_real_stub_shape(self):
        content = bootstrap_release.render_stub_module_dot_bazel("rclcpp")
        self.assertIn('module(\n    name = "rclcpp",\n    version = "0.0.0",\n    bazel_compatibility = [">=7.2.1"],\n)\n', content)
        self.assertNotIn("bazel_dep", content)


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


RCR_PINS = {"rclcpp": "32.0.0-1.rcr.0", "rosdistro": "lyrical.2026-10-05.rcr.0"}


def _legacy_module(version: str = "1.2.3-1.rcr.2") -> str:
    """A MODULE.bazel as an older bootstrap would have rendered it."""
    return (
        bootstrap_release.bzlmod_lib.get_copyright_header()
        + "# ROS package information\n"
        + f'module(\n    name = "foo",\n    version = "{version}",\n    bazel_compatibility = [">=7.2.1"],\n)\n'
        + "\n# BCR dependencies\n"
        + 'bazel_dep(name = "aspect_rules_py", version = "1.11.7")\n'
        + 'bazel_dep(name = "bazel_skylib", version = "1.9.0")\n'
        + 'bazel_dep(name = "rules_rust", version = "0.71.3")\n'
        + "\n# RCR Dependencies\n"
        + 'bazel_dep(name = "rclcpp", version = "32.0.0-1.rcr.0")\n'
        + 'bazel_dep(name = "rosdistro", version = "lyrical.2026-10-05.rcr.0")\n'
        + bootstrap_release.LEGACY_BOOTSTRAP_TRAILERS[0]
        + '\nbazel_dep(name = "launch_ros", version = "0.29.9-1.rcr.0")\n'
    )


class TestParseAndRefreshModuleDotBazel(unittest.TestCase):
    def test_fresh_module_is_current_and_roundtrips(self):
        fresh = bootstrap_release.render_module_dot_bazel("foo", "1.2.3-1.rcr.0", RCR_PINS, "lyrical", "2026-10-05")
        parsed = bootstrap_release.parse_module_dot_bazel(fresh)
        self.assertTrue(parsed.boilerplate_is_current)
        self.assertEqual(parsed.rcr_deps, RCR_PINS)
        self.assertEqual(bootstrap_release.refresh_module_dot_bazel(fresh)[0], fresh)

    def test_legacy_module_is_rerendered_keeping_rcr_pins(self):
        new_text, parsed = bootstrap_release.refresh_module_dot_bazel(_legacy_module())
        self.assertFalse(parsed.boilerplate_is_current)
        self.assertEqual(parsed.dropped_bcr_deps, {"aspect_rules_py": "1.11.7", "rules_rust": "0.71.3"})
        self.assertEqual(parsed.stale_bcr_deps, {"bazel_skylib": "1.9.0"})
        self.assertIn("rules_cc", parsed.missing_bcr_deps)
        # The dep appended after the trailer is folded back into the RCR block.
        self.assertEqual(parsed.rcr_deps, dict(RCR_PINS, launch_ros="0.29.9-1.rcr.0"))
        self.assertEqual(
            new_text,
            bootstrap_release.render_module_dot_bazel("foo", "1.2.3-1.rcr.2", parsed.rcr_deps, "lyrical", "2026-10-05"),
        )
        self.assertNotIn("aspect_rules_py", new_text)

    def test_new_version_override(self):
        new_text, _ = bootstrap_release.refresh_module_dot_bazel(_legacy_module(), new_version="1.2.3-1.rcr.3")
        self.assertIn('version = "1.2.3-1.rcr.3"', new_text)

    def test_refuses_unrecognized_content(self):
        text = _legacy_module().replace("# RCR Dependencies\n", '# RCR Dependencies\nlocal_path_override(module_name = "x", path = "y")\n')
        with self.assertRaisesRegex(ValueError, "unrecognized"):
            bootstrap_release.refresh_module_dot_bazel(text)

    def test_refuses_hand_edited_trailer(self):
        text = _legacy_module().replace('version = "6.8.3"', 'version = "6.9.0"')
        with self.assertRaisesRegex(ValueError, "trailer"):
            bootstrap_release.refresh_module_dot_bazel(text)

    def test_known_legacy_trailer_is_rerendered(self):
        text = _legacy_module()
        for legacy in bootstrap_release.LEGACY_BOOTSTRAP_TRAILERS:
            old = text.replace(bootstrap_release.LEGACY_BOOTSTRAP_TRAILERS[0], legacy)
            parsed = bootstrap_release.parse_module_dot_bazel(old)
            self.assertFalse(parsed.trailer_matches)
            self.assertTrue(parsed.trailer_is_legacy)
            new_text, _ = bootstrap_release.refresh_module_dot_bazel(old)
            self.assertIn(bootstrap_release.BOOTSTRAP_TRAILER, new_text)
            self.assertNotIn('os = "linux",', new_text)
            self.assertNotIn("rules_qt", new_text)

    def test_refuses_custom_body(self):
        text = bootstrap_release.render_module_dot_bazel(
            "rosdistro", "lyrical.2026-10-05.rcr.0", {}, "lyrical", "2026-10-05",
            custom_body=bootstrap_release.ROSDISTRO_CUSTOM_BODY)
        with self.assertRaises(ValueError):
            bootstrap_release.refresh_module_dot_bazel(text)


class TestPlanExistingRelease(unittest.TestCase):
    def setUp(self):
        self.pkg_dir = Path(tempfile.mkdtemp()) / "foo"
        (self.pkg_dir / "1.2.3-1.rcr.2" / "overlay").mkdir(parents=True)
        (self.pkg_dir / "1.2.3-1.rcr.2" / "overlay" / "BUILD.bazel").write_text("# build\n")
        (self.pkg_dir / "1.2.3-1.rcr.2" / "source.json").write_text(
            json.dumps({"integrity": "sha256-x", "url": "u", "strip_prefix": "p", "overlay": {"BUILD.bazel": "stale"}}))
        with open(self.pkg_dir / "metadata.json", "w") as f:
            json.dump({"homepage": "x", "maintainers": [], "versions": ["1.2.3-1.rcr.2"], "yanked_versions": {}}, f)

    def tearDown(self):
        shutil.rmtree(self.pkg_dir.parent)

    def _write_module(self, text: str) -> None:
        (self.pkg_dir / "1.2.3-1.rcr.2" / "MODULE.bazel").write_text(text)

    def test_current_boilerplate_is_reused_as_is(self):
        self._write_module(bootstrap_release.render_module_dot_bazel("foo", "1.2.3-1.rcr.2", RCR_PINS, "lyrical", "2026-10-05"))
        plan = bootstrap_release.plan_existing_release(self.pkg_dir, "1.2.3-1.rcr.2")
        self.assertEqual(plan, bootstrap_release.ExistingReleasePlan(pin="1.2.3-1.rcr.2"))

    def test_stale_boilerplate_plans_a_refreshed_successor(self):
        self._write_module(_legacy_module())
        plan = bootstrap_release.plan_existing_release(self.pkg_dir, "1.2.3-1.rcr.2")
        self.assertEqual(plan.pin, "1.2.3-1.rcr.3")
        self.assertEqual(plan.refresh_from, "1.2.3-1.rcr.2")
        self.assertIsNone(plan.warning)
        self.assertIn('version = "1.2.3-1.rcr.3"', plan.module_dot_bazel)
        self.assertNotIn("aspect_rules_py", plan.module_dot_bazel)
        # RCR pins are carried over untouched (bumping them is the rollup's job).
        self.assertIn('bazel_dep(name = "rclcpp", version = "32.0.0-1.rcr.0")', plan.module_dot_bazel)
        self.assertIn('bazel_dep(name = "launch_ros", version = "0.29.9-1.rcr.0")', plan.module_dot_bazel)

    def test_unparseable_module_is_reused_with_warning(self):
        self._write_module(_legacy_module().replace('version = "6.8.3"', 'version = "6.9.0"'))
        plan = bootstrap_release.plan_existing_release(self.pkg_dir, "1.2.3-1.rcr.2")
        self.assertEqual(plan.pin, "1.2.3-1.rcr.2")
        self.assertIsNone(plan.refresh_from)
        self.assertIn("trailer", plan.warning)

    def test_materialize_copies_everything_and_rehashes(self):
        self._write_module(_legacy_module())
        plan = bootstrap_release.plan_existing_release(self.pkg_dir, "1.2.3-1.rcr.2")
        bootstrap_release.materialize_refreshed_release(self.pkg_dir, plan, "https://github.com/ros2-gbp/foo-release/x.tar.gz")
        new_dir = self.pkg_dir / "1.2.3-1.rcr.3"
        self.assertEqual((new_dir / "MODULE.bazel").read_text(), plan.module_dot_bazel)
        self.assertEqual((new_dir / "overlay" / "BUILD.bazel").read_text(), "# build\n")
        source = json.loads((new_dir / "source.json").read_text())
        self.assertEqual(source["integrity"], "sha256-x")
        self.assertEqual(
            source["overlay"]["BUILD.bazel"],
            bootstrap_release.bzlmod_lib.calculate_integrity_hash_for_file(new_dir / "overlay" / "BUILD.bazel"),
        )
        with open(self.pkg_dir / "metadata.json") as f:
            self.assertEqual(json.load(f)["versions"], ["1.2.3-1.rcr.2", "1.2.3-1.rcr.3"])
        # The old version is untouched.
        self.assertEqual((self.pkg_dir / "1.2.3-1.rcr.2" / "MODULE.bazel").read_text(), _legacy_module())
        # And a second plan against the new version is a no-op reuse.
        self.assertEqual(bootstrap_release.plan_existing_release(self.pkg_dir, "1.2.3-1.rcr.3"),
                         bootstrap_release.ExistingReleasePlan(pin="1.2.3-1.rcr.3"))


if __name__ == "__main__":
    unittest.main()

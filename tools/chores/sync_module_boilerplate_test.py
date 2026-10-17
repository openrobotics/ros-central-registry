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
import tempfile
import unittest
from pathlib import Path

from tools.chores import sync_module_boilerplate as sync
from tools.ci import bootstrap_release
from tools.ci import bzlmod_lib

RCR_DEPS = {"rclcpp": "32.0.0-1.rcr.0", "rosdistro": "lyrical.2026-10-05.rcr.0"}
FRESH = bootstrap_release.render_module_dot_bazel("foo", "1.2.3-1.rcr.0", RCR_DEPS, "lyrical", "2026-10-05")

LEGACY = (
    bzlmod_lib.get_copyright_header()
    + """# ROS package information
module(
    name = "foo",
    version = "1.2.3-1.rcr.2",
    bazel_compatibility = [">=7.2.1"],
)

# BCR dependencies
bazel_dep(name = "aspect_rules_py", version = "1.11.7")
bazel_dep(name = "bazel_skylib", version = "1.9.0")
bazel_dep(name = "rules_python", version = "2.2.0")
bazel_dep(name = "rules_rust", version = "0.71.3")

# RCR Dependencies
bazel_dep(name = "rclcpp", version = "32.0.0-1.rcr.0")
bazel_dep(name = "rosdistro", version = "lyrical.2026-10-05.rcr.0")
"""
    + bootstrap_release.BOOTSTRAP_TRAILER
    + """
bazel_dep(name = "launch_ros", version = "0.29.9-1.rcr.0")
"""
)


class ParseModuleDotBazelTest(unittest.TestCase):
    def test_fresh_module_roundtrips_unchanged(self):
        new_text, parsed = sync.sync_module_dot_bazel_text(FRESH)
        self.assertEqual(new_text, FRESH)
        self.assertEqual(parsed.rcr_deps, RCR_DEPS)
        self.assertEqual(parsed.bcr_deps, bootstrap_release.BCR_DEPS)
        self.assertFalse(parsed.dropped_bcr_deps)
        self.assertFalse(parsed.stale_bcr_deps)
        self.assertFalse(parsed.missing_bcr_deps)

    def test_legacy_module_is_normalised(self):
        new_text, parsed = sync.sync_module_dot_bazel_text(LEGACY)
        self.assertEqual(parsed.dropped_bcr_deps, {"aspect_rules_py": "1.11.7", "rules_rust": "0.71.3"})
        self.assertEqual(parsed.stale_bcr_deps, {"bazel_skylib": "1.9.0", "rules_python": "2.2.0"})
        self.assertIn("rules_cc", parsed.missing_bcr_deps)
        # The dep appended after the trailer is folded into the RCR block.
        self.assertEqual(parsed.rcr_deps, dict(RCR_DEPS, launch_ros="0.29.9-1.rcr.0"))
        expected = bootstrap_release.render_module_dot_bazel(
            "foo", "1.2.3-1.rcr.2", parsed.rcr_deps, "lyrical", "2026-10-05"
        )
        self.assertEqual(new_text, expected)
        self.assertNotIn("aspect_rules_py", new_text)
        self.assertNotIn("rules_rust", new_text)
        self.assertEqual(new_text.count(bootstrap_release.BOOTSTRAP_TRAILER), 1)
        # Idempotent.
        self.assertEqual(sync.sync_module_dot_bazel_text(new_text)[0], new_text)

    def test_unrecognized_content_is_refused(self):
        text = FRESH.replace("# RCR Dependencies\n", '# RCR Dependencies\nlocal_path_override(module_name = "x", path = "y")\n')
        with self.assertRaisesRegex(ValueError, "unrecognized content"):
            sync.sync_module_dot_bazel_text(text)

    def test_custom_trailer_is_refused(self):
        text = FRESH + '\nfoo = use_extension("@foo//:ext.bzl", "foo")\nuse_repo(foo, "bar")\n'
        with self.assertRaisesRegex(ValueError, "trailer"):
            sync.sync_module_dot_bazel_text(text)

    def test_missing_rosdistro_pin_is_refused(self):
        text = FRESH.replace('bazel_dep(name = "rosdistro", version = "lyrical.2026-10-05.rcr.0")\n', "")
        with self.assertRaisesRegex(ValueError, "rosdistro"):
            sync.sync_module_dot_bazel_text(text)

    def test_no_module_block(self):
        with self.assertRaises(ValueError):
            sync.parse_module_dot_bazel("# nothing here\n")


class MigrateLoadsTest(unittest.TestCase):
    def test_simple_rewrite(self):
        text = 'load("@aspect_rules_py//py:defs.bzl", "py_binary", "py_library")\n\npy_library(name = "x")\n'
        new, unsupported = sync.migrate_loads(text)
        self.assertEqual(new, 'load("@rules_python//python:defs.bzl", "py_binary", "py_library")\n\npy_library(name = "x")\n')
        self.assertEqual(unsupported, [])

    def test_alias_and_content_between_loads_preserved(self):
        text = (
            'load("@aspect_rules_py//py:defs.bzl", _py_test = "py_test")\n'
            "# Some comment that someone put between the loads\n"
            'load("@rules_license//rules:license.bzl", "license")\n'
        )
        new, unsupported = sync.migrate_loads(text)
        self.assertEqual(
            new,
            'load("@rules_python//python:defs.bzl", _py_test = "py_test")\n'
            "# Some comment that someone put between the loads\n"
            'load("@rules_license//rules:license.bzl", "license")\n',
        )
        self.assertEqual(unsupported, [])

    def test_leading_loads_before_copyright_moved_after_header(self):
        text = (
            'load("@aspect_rules_py//py:defs.bzl", _py_test = "py_test")\n'
            "# Copyright 2026 Open Source Robotics Foundation, Inc.\n"
            "#\n"
            '# Licensed under the Apache License, Version 2.0 (the "License");\n\n'
            'load("@rules_license//rules:license.bzl", "license")\n'
        )
        new, unsupported = sync.migrate_loads(text)
        self.assertEqual(
            new,
            "# Copyright 2026 Open Source Robotics Foundation, Inc.\n"
            "#\n"
            '# Licensed under the Apache License, Version 2.0 (the "License");\n\n'
            'load("@rules_python//python:defs.bzl", _py_test = "py_test")\n'
            'load("@rules_license//rules:license.bzl", "license")\n',
        )
        self.assertEqual(unsupported, [])

    def test_merges_into_existing_rules_python_load(self):
        text = (
            'load("@aspect_rules_py//py:defs.bzl", "py_binary")\n'
            'load("@rules_license//rules:license.bzl", "license")\n'
            'load("@rules_python//python:defs.bzl", "py_library")\n'
        )
        new, _ = sync.migrate_loads(text)
        self.assertEqual(
            new,
            'load("@rules_license//rules:license.bzl", "license")\n'
            'load("@rules_python//python:defs.bzl", "py_binary", "py_library")\n',
        )

    def test_unsupported_symbols_stay_on_old_label(self):
        text = 'load("@aspect_rules_py//py:defs.bzl", "py_image_layer", "py_library")\n'
        new, unsupported = sync.migrate_loads(text)
        self.assertEqual(
            new,
            'load("@rules_python//python:defs.bzl", "py_library")\n'
            'load("@aspect_rules_py//py:defs.bzl", "py_image_layer")\n',
        )
        self.assertEqual(unsupported, ["py_image_layer"])

    def test_multiline_load(self):
        text = 'load(\n    "@aspect_rules_py//py:defs.bzl",\n    "py_binary",\n    "py_test",\n)\n'
        new, _ = sync.migrate_loads(text)
        self.assertEqual(new, 'load("@rules_python//python:defs.bzl", "py_binary", "py_test")\n')

    def test_untouched_when_nothing_to_migrate(self):
        text = 'load("@rules_python//python:defs.bzl", "py_library")\n'
        self.assertEqual(sync.migrate_loads(text), (text, []))


class FindMainLessExecutablesTest(unittest.TestCase):
    def test_flags_only_targets_rules_python_cannot_infer(self):
        text = """
py_binary(
    name = "ok_named",
    srcs = ["pkg/ok_named.py"],
)

py_binary(
    name = "has_main",
    srcs = ["pkg/entry.py"],
    main = "pkg/entry.py",
)

py_test(
    name = "needs_review",
    srcs = ["test/test_something.py"],
    deps = [":lib"],
)

py_library(
    name = "lib",
    srcs = ["lib.py"],
)
"""
        self.assertEqual(sync.find_main_less_executables(text), ["needs_review"])


class SyncVersionDirTest(unittest.TestCase):
    def _make_version_dir(self, root: Path, build_text: str) -> Path:
        version_dir = root / "modules" / "foo" / "1.2.3-1.rcr.2"
        (version_dir / "overlay").mkdir(parents=True)
        (version_dir / "MODULE.bazel").write_text(LEGACY)
        (version_dir / "overlay" / "BUILD.bazel").write_text(build_text)
        (version_dir / "source.json").write_text(json.dumps({"integrity": "x", "url": "u", "overlay": {"BUILD.bazel": "stale"}}))
        return version_dir

    def test_dry_run_reports_but_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = 'load("@aspect_rules_py//py:defs.bzl", "py_library")\n'
            version_dir = self._make_version_dir(Path(tmp), build)
            report = sync.sync_version_dir(version_dir, dry_run=True, buildifier=None)
            self.assertTrue(report.module_changed)
            self.assertEqual([p.name for p in report.overlay_changed], ["BUILD.bazel"])
            self.assertEqual((version_dir / "MODULE.bazel").read_text(), LEGACY)
            self.assertEqual((version_dir / "overlay" / "BUILD.bazel").read_text(), build)
            self.assertEqual(json.loads((version_dir / "source.json").read_text())["overlay"]["BUILD.bazel"], "stale")

    def test_writes_and_rehashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = 'load("@aspect_rules_py//py:defs.bzl", "py_library")\n'
            version_dir = self._make_version_dir(Path(tmp), build)
            report = sync.sync_version_dir(version_dir, dry_run=False, buildifier=None)
            self.assertTrue(report.changed)
            self.assertNotIn("aspect_rules_py", (version_dir / "MODULE.bazel").read_text())
            new_build = (version_dir / "overlay" / "BUILD.bazel").read_text()
            self.assertEqual(new_build, 'load("@rules_python//python:defs.bzl", "py_library")\n')
            source = json.loads((version_dir / "source.json").read_text())
            self.assertEqual(
                source["overlay"]["BUILD.bazel"],
                bzlmod_lib.calculate_integrity_hash_for_file(version_dir / "overlay" / "BUILD.bazel"),
            )
            # Second pass is a no-op.
            again = sync.sync_version_dir(version_dir, dry_run=False, buildifier=None)
            self.assertFalse(again.changed)

    def test_unrecognized_module_is_skipped_entirely(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = 'load("@aspect_rules_py//py:defs.bzl", "py_library")\n'
            version_dir = self._make_version_dir(Path(tmp), build)
            (version_dir / "MODULE.bazel").write_text(FRESH + "\nweird_call()\n")
            report = sync.sync_version_dir(version_dir, dry_run=False, buildifier=None)
            self.assertIn("MODULE.bazel: ", report.skipped)
            self.assertFalse(report.changed)
            self.assertEqual((version_dir / "overlay" / "BUILD.bazel").read_text(), build)


class DiscoverVersionDirsTest(unittest.TestCase):
    def test_skips_stubs_and_rosdistro(self):
        with tempfile.TemporaryDirectory() as tmp:
            modules = Path(tmp)
            for rel in ("foo/0.0.0", "foo/1.0.0-1.rcr.1", "rosdistro/lyrical.2026-10-05.rcr.0", "bar/2.0.0-1.rcr.0"):
                (modules / rel).mkdir(parents=True)
                (modules / rel / "MODULE.bazel").write_text("")
            found = [p.relative_to(modules).as_posix() for p in sync.discover_version_dirs(modules, [])]
            self.assertEqual(found, ["bar/2.0.0-1.rcr.0", "foo/1.0.0-1.rcr.1"])
            found = [p.relative_to(modules).as_posix() for p in sync.discover_version_dirs(modules, ["foo"])]
            self.assertEqual(found, ["foo/1.0.0-1.rcr.1"])


class PublishedVersionDirsTest(unittest.TestCase):
    def test_only_committed_versions_count(self):
        import subprocess

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            git = lambda *a: subprocess.run(["git", *a], cwd=root, check=True, capture_output=True)  # noqa: E731
            git("init", "-q", "-b", "main")
            git("config", "user.email", "t@example.com")
            git("config", "user.name", "t")
            for rel in ("modules/foo/1.0.0-1.rcr.0/MODULE.bazel", "modules/foo/metadata.json", "modules/bar/2.0.0-1.rcr.0/overlay/BUILD.bazel"):
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_text("")
            git("add", ".")
            git("commit", "-q", "-m", "init")
            # Branch-only version: on disk, not committed.
            (root / "modules/foo/1.0.0-1.rcr.1").mkdir()
            (root / "modules/foo/1.0.0-1.rcr.1/MODULE.bazel").write_text("")

            published = sync.published_version_dirs(root, "main", root / "modules")
            # bar/2.0.0-1.rcr.0 has no MODULE.bazel committed, so it doesn't count.
            self.assertEqual(published, {Path("modules/foo/1.0.0-1.rcr.0")})
            with self.assertRaises(RuntimeError):
                sync.published_version_dirs(root, "no-such-ref", root / "modules")


if __name__ == "__main__":
    unittest.main()

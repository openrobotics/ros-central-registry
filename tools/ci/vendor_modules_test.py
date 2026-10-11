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
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.ci import bzlmod_lib
from tools.ci import vendor_modules


class TestParseModuleTokens(unittest.TestCase):

    def test_multiple_separate_arguments_pass_through(self):
        result = vendor_modules.parse_module_tokens(
            ["rclcpp", "rclcpp_action", "rclcpp_lifecycle"])
        self.assertEqual(result, ["rclcpp", "rclcpp_action", "rclcpp_lifecycle"])

    def test_single_space_separated_string_is_split(self):
        result = vendor_modules.parse_module_tokens(
            ["rclcpp rclcpp_action rclcpp_lifecycle"])
        self.assertEqual(result, ["rclcpp", "rclcpp_action", "rclcpp_lifecycle"])

    def test_comma_separated_string_is_split(self):
        result = vendor_modules.parse_module_tokens(
            ["rclcpp, rclcpp_action,rclcpp_lifecycle"])
        self.assertEqual(result, ["rclcpp", "rclcpp_action", "rclcpp_lifecycle"])

    def test_ignores_blank_tokens(self):
        result = vendor_modules.parse_module_tokens(["  rclcpp   ", ""])
        self.assertEqual(result, ["rclcpp"])


class TestClearVendoredModule(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = Path(tempfile.mkdtemp())
        (self.workspace_dir / "vendor").mkdir()

    def tearDown(self):
        shutil.rmtree(self.workspace_dir)

    def test_removes_tree_and_marker(self):
        vendor = self.workspace_dir / "vendor"
        (vendor / "rclcpp+" / "src").mkdir(parents=True)
        (vendor / "rclcpp+" / "src" / "a.cpp").write_text("x")
        (vendor / "@rclcpp+.marker").write_text("hash")
        (vendor / "other+").mkdir()
        self.assertTrue(vendor_modules.clear_vendored_module(self.workspace_dir, "rclcpp"))
        self.assertFalse((vendor / "rclcpp+").exists())
        self.assertFalse((vendor / "@rclcpp+.marker").exists())
        # Unrelated modules are untouched.
        self.assertTrue((vendor / "other+").exists())

    def test_noop_when_not_vendored(self):
        self.assertFalse(vendor_modules.clear_vendored_module(self.workspace_dir, "rclcpp"))


class TestModulesForVariant(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.workspace_dir)

    def write_variant_file(self, key: str, packages):
        (self.workspace_dir / f"ros-{key}.txt").write_text(
            "\n".join(f"@{p}//..." for p in packages))

    def test_reads_bare_module_names_from_target_pattern_file(self):
        self.write_variant_file("core", ["rcutils", "rclcpp"])
        result = vendor_modules.modules_for_variant(self.workspace_dir, "ros_core")
        self.assertEqual(result, ["rcutils", "rclcpp"])

    def test_desktop_full_maps_to_its_own_file(self):
        self.write_variant_file("desktop_full", ["rviz2"])
        result = vendor_modules.modules_for_variant(self.workspace_dir, "desktop_full")
        self.assertEqual(result, ["rviz2"])

    def test_missing_variant_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            vendor_modules.modules_for_variant(self.workspace_dir, "simulation")


class TestResolveModules(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.workspace_dir)

    def write_variant_file(self, key: str, packages):
        (self.workspace_dir / f"ros-{key}.txt").write_text(
            "\n".join(f"@{p}//..." for p in packages))

    def test_explicit_modules_only(self):
        result = vendor_modules.resolve_modules(
            ["rclcpp", "rclcpp_action"], [], False, self.workspace_dir, {"rclcpp", "rclcpp_action"})
        self.assertEqual(result, ["rclcpp", "rclcpp_action"])

    def test_variant_expands_to_its_packages(self):
        self.write_variant_file("core", ["rcutils", "rclcpp"])
        result = vendor_modules.resolve_modules(
            [], ["ros_core"], False, self.workspace_dir, {"rcutils", "rclcpp"})
        self.assertEqual(result, ["rcutils", "rclcpp"])

    def test_explicit_modules_and_variant_are_combined_and_deduped(self):
        self.write_variant_file("core", ["rcutils", "rclcpp"])
        result = vendor_modules.resolve_modules(
            ["rclcpp"], ["ros_core"], False, self.workspace_dir, {"rcutils", "rclcpp"})
        # "rclcpp" only appears once even though it's in both sources, and
        # the explicitly requested module keeps its earlier position.
        self.assertEqual(result, ["rclcpp", "rcutils"])

    def test_all_overrides_everything_else_and_returns_sorted_declared(self):
        result = vendor_modules.resolve_modules(
            ["ignored"], ["ros_core"], True, self.workspace_dir, {"rclcpp", "rcutils"})
        self.assertEqual(result, ["rclcpp", "rcutils"])


class TestDeclaredModuleNames(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.modules_dir = self.tmp_dir / "modules"
        (self.modules_dir / "rclcpp").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_includes_both_rcr_and_bcr_deps(self):
        module_dot_bazel = self.tmp_dir / "MODULE.bazel"
        module_dot_bazel.write_text(
            'bazel_dep(name = "rclcpp", version = "1.0.0")\n'
            'bazel_dep(name = "rules_cc", version = "0.2.22")\n')
        result = vendor_modules.declared_module_names(module_dot_bazel, self.modules_dir)
        self.assertEqual(result, {"rclcpp", "rules_cc"})


class TestEnsureVendorDirFlag(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.bazelrc = self.tmp_dir / ".bazelrc"

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_appends_flag_when_missing(self):
        self.bazelrc.write_text("common --foo=bar\n")
        vendor_modules.ensure_vendor_dir_flag(self.bazelrc)
        self.assertIn(vendor_modules.VENDOR_DIR_RC_LINE, self.bazelrc.read_text())

    def test_does_not_duplicate_existing_flag(self):
        self.bazelrc.write_text(f"common --foo=bar\n{vendor_modules.VENDOR_DIR_RC_LINE}\n")
        vendor_modules.ensure_vendor_dir_flag(self.bazelrc)
        content = self.bazelrc.read_text()
        self.assertEqual(content.count(vendor_modules.VENDOR_DIR_RC_LINE), 1)


class TestWriteVendorManifest(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = Path(tempfile.mkdtemp())
        self.vendor_module_dir = self.workspace_dir / "vendor" / "rclcpp+"
        self.vendor_module_dir.mkdir(parents=True)
        (self.vendor_module_dir / "MODULE.bazel").write_text('module(name = "rclcpp")\n')
        (self.vendor_module_dir / "src.c").write_text("hello\n")

    def tearDown(self):
        shutil.rmtree(self.workspace_dir)

    def test_writes_manifest_matching_hash_directory_tree(self):
        vendor_modules.write_vendor_manifest(self.workspace_dir, "rclcpp")
        manifest_path = (
            self.workspace_dir / vendor_modules.VENDOR_MANIFEST_DIR_NAME / "rclcpp.json")
        with open(manifest_path) as f:
            manifest = json.load(f)
        self.assertEqual(manifest, bzlmod_lib.hash_directory_tree(self.vendor_module_dir))
        self.assertNotIn("MODULE.bazel", manifest)

    def test_overwrites_stale_manifest_on_rerun(self):
        vendor_modules.write_vendor_manifest(self.workspace_dir, "rclcpp")
        (self.vendor_module_dir / "src.c").write_text("edited\n")
        vendor_modules.write_vendor_manifest(self.workspace_dir, "rclcpp")
        manifest_path = (
            self.workspace_dir / vendor_modules.VENDOR_MANIFEST_DIR_NAME / "rclcpp.json")
        with open(manifest_path) as f:
            manifest = json.load(f)
        self.assertEqual(manifest, bzlmod_lib.hash_directory_tree(self.vendor_module_dir))


class TestWritePackageManifest(unittest.TestCase):

    def setUp(self):
        self.workspace_root = Path(tempfile.mkdtemp())
        self.modules_dir = self.workspace_root / "modules"
        self.module_dir = self.modules_dir / "rclcpp" / "1.0.0"
        self.module_dir.mkdir(parents=True)
        (self.module_dir / "MODULE.bazel").write_text(
            'module(\n    name = "rclcpp",\n    version = "1.0.0",\n)\n')
        (self.module_dir / "source.json").write_text('{"url": "..."}\n')
        self.target_workspace = self.workspace_root / "workspace"
        self.target_workspace.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.workspace_root)

    def test_writes_manifest_including_module_bazel(self):
        vendor_modules.write_package_manifest(self.target_workspace, self.modules_dir, "rclcpp", "1.0.0")
        manifest_path = (
            self.target_workspace / vendor_modules.PACKAGE_MANIFEST_DIR_NAME / "rclcpp.json")
        with open(manifest_path) as f:
            manifest = json.load(f)
        self.assertEqual(manifest["version"], "1.0.0")
        self.assertEqual(
            manifest["hashes"], bzlmod_lib.hash_directory_tree(self.module_dir, exclude_names=()))
        # Unlike write_vendor_manifest, MODULE.bazel IS included here --
        # drift there is exactly what this manifest exists to catch.
        self.assertIn("MODULE.bazel", manifest["hashes"])

    def test_overwrites_stale_manifest_on_rerun(self):
        vendor_modules.write_package_manifest(self.target_workspace, self.modules_dir, "rclcpp", "1.0.0")
        (self.module_dir / "source.json").write_text('{"url": "changed"}\n')
        vendor_modules.write_package_manifest(self.target_workspace, self.modules_dir, "rclcpp", "1.0.0")
        manifest_path = (
            self.target_workspace / vendor_modules.PACKAGE_MANIFEST_DIR_NAME / "rclcpp.json")
        with open(manifest_path) as f:
            manifest = json.load(f)
        self.assertEqual(
            manifest["hashes"], bzlmod_lib.hash_directory_tree(self.module_dir, exclude_names=()))


class TestWriteVendorSnapshot(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = Path(tempfile.mkdtemp())
        self.vendor_module_dir = self.workspace_dir / "vendor" / "rclcpp+"
        self.vendor_module_dir.mkdir(parents=True)
        (self.vendor_module_dir / "src.c").write_text("hello\n")

    def tearDown(self):
        shutil.rmtree(self.workspace_dir)

    def test_copies_full_content(self):
        vendor_modules.write_vendor_snapshot(self.workspace_dir, "rclcpp")
        snapshot = self.workspace_dir / vendor_modules.VENDOR_SNAPSHOT_DIR_NAME / "rclcpp+"
        self.assertEqual((snapshot / "src.c").read_text(), "hello\n")

    def test_later_edits_do_not_affect_the_snapshot(self):
        vendor_modules.write_vendor_snapshot(self.workspace_dir, "rclcpp")
        (self.vendor_module_dir / "src.c").write_text("edited\n")
        snapshot = self.workspace_dir / vendor_modules.VENDOR_SNAPSHOT_DIR_NAME / "rclcpp+"
        self.assertEqual((snapshot / "src.c").read_text(), "hello\n")

    def test_rerun_replaces_rather_than_merges(self):
        vendor_modules.write_vendor_snapshot(self.workspace_dir, "rclcpp")
        (self.vendor_module_dir / "src.c").write_text("edited\n")
        (self.vendor_module_dir / "new_file.h").write_text("new\n")
        vendor_modules.write_vendor_snapshot(self.workspace_dir, "rclcpp")
        snapshot = self.workspace_dir / vendor_modules.VENDOR_SNAPSHOT_DIR_NAME / "rclcpp+"
        self.assertEqual((snapshot / "src.c").read_text(), "edited\n")
        self.assertEqual((snapshot / "new_file.h").read_text(), "new\n")


class TestMain(unittest.TestCase):
    """
    End-to-end coverage of main()'s argument handling, exercised against a
    throwaway workspace directory rather than a real Bazel invocation.
    """

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.workspace_root = self.tmp_dir / "repo"
        self.modules_dir = self.workspace_root / "modules"
        self.target_workspace = self.workspace_root / "workspace"
        for name in ["rclcpp", "rclcpp_action", "rclcpp_lifecycle", "rcutils"]:
            version_dir = self.modules_dir / name / "1.0.0"
            version_dir.mkdir(parents=True)
            (version_dir / "MODULE.bazel").write_text(
                f'module(\n    name = "{name}",\n    version = "1.0.0",\n)\n')
        self.target_workspace.mkdir(parents=True)
        (self.target_workspace / "MODULE.bazel").write_text(
            'bazel_dep(name = "rclcpp", version = "1.0.0")\n'
            'bazel_dep(name = "rclcpp_action", version = "1.0.0")\n'
            'bazel_dep(name = "rclcpp_lifecycle", version = "1.0.0")\n'
            'bazel_dep(name = "rcutils", version = "1.0.0")\n')
        (self.target_workspace / ".bazelrc").write_text("common --foo=bar\n")
        (self.target_workspace / "ros-core.txt").write_text(
            "@rcutils//...\n@rclcpp//...\n")

        self.env_patch = {"BUILD_WORKSPACE_DIRECTORY": str(self.workspace_root)}
        self.original_environ = dict(__import__("os").environ)
        __import__("os").environ.update(self.env_patch)

        self.recorded_cmds = []
        self.original_run = subprocess.run

        def _fake_run(cmd, cwd=None, check=None):
            self.recorded_cmds.append(cmd)
            # Simulate what a real "bazel vendor" would materialize, so the
            # post-vendor manifest-writing steps have something to hash.
            for arg in cmd:
                if arg.startswith("--repo=@"):
                    name = arg[len("--repo=@"):]
                    module_dir = self.target_workspace / "vendor" / f"{name}+"
                    module_dir.mkdir(parents=True, exist_ok=True)
                    (module_dir / "MODULE.bazel").write_text(
                        f'module(\n    name = "{name}",\n    version = "1.0.0",\n)\n')
                    (module_dir / "src.c").write_text("hello\n")

            class _FakeResult:
                returncode = 0
            return _FakeResult()

        vendor_modules.subprocess.run = _fake_run

    def tearDown(self):
        import os
        os.environ.clear()
        os.environ.update(self.original_environ)
        vendor_modules.subprocess.run = self.original_run
        shutil.rmtree(self.tmp_dir)

    def run_main(self, argv):
        original_argv = sys.argv
        sys.argv = ["vendor_modules.py"] + argv
        try:
            vendor_modules.main()
        finally:
            sys.argv = original_argv

    def test_multiple_modules_as_separate_arguments(self):
        self.run_main(["rclcpp", "rclcpp_action", "rclcpp_lifecycle"])
        self.assertEqual(len(self.recorded_cmds), 1)
        repos = [a for a in self.recorded_cmds[0] if a.startswith("--repo=")]
        self.assertEqual(
            repos,
            ["--repo=@rclcpp", "--repo=@rclcpp_action", "--repo=@rclcpp_lifecycle"])
        self.assertTrue(
            (self.target_workspace / vendor_modules.PACKAGE_MANIFEST_DIR_NAME / "rclcpp.json").exists())
        self.assertTrue(
            (self.target_workspace / vendor_modules.VENDOR_SNAPSHOT_DIR_NAME / "rclcpp+" / "src.c").exists())

    def test_multiple_modules_as_single_quoted_string(self):
        self.run_main(["rclcpp rclcpp_action rclcpp_lifecycle"])
        repos = [a for a in self.recorded_cmds[0] if a.startswith("--repo=")]
        self.assertEqual(
            repos,
            ["--repo=@rclcpp", "--repo=@rclcpp_action", "--repo=@rclcpp_lifecycle"])

    def test_variant_flag_vendors_its_packages(self):
        self.run_main(["--variant", "ros_core"])
        repos = [a for a in self.recorded_cmds[0] if a.startswith("--repo=")]
        self.assertEqual(repos, ["--repo=@rcutils", "--repo=@rclcpp"])

    def test_all_flag_vendors_every_declared_module(self):
        self.run_main(["--all"])
        repos = {a for a in self.recorded_cmds[0] if a.startswith("--repo=")}
        self.assertEqual(
            repos,
            {"--repo=@rclcpp", "--repo=@rclcpp_action", "--repo=@rclcpp_lifecycle", "--repo=@rcutils"})

    def test_all_combined_with_modules_is_rejected(self):
        with self.assertRaises(SystemExit):
            self.run_main(["--all", "rclcpp"])
        self.assertEqual(self.recorded_cmds, [])

    def test_no_arguments_is_rejected(self):
        with self.assertRaises(SystemExit):
            self.run_main([])
        self.assertEqual(self.recorded_cmds, [])

    def test_unknown_module_is_rejected(self):
        with self.assertRaises(SystemExit):
            self.run_main(["not_a_real_module"])
        self.assertEqual(self.recorded_cmds, [])

    def test_unknown_variant_choice_is_rejected(self):
        with self.assertRaises(SystemExit):
            self.run_main(["--variant", "not_a_real_variant"])
        self.assertEqual(self.recorded_cmds, [])


if __name__ == "__main__":
    unittest.main()

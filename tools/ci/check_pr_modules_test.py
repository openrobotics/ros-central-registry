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
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tools.ci import check_pr_modules
from tools.ci.check_pr_modules import check_violations

class TestCheckPrModules(unittest.TestCase):

    def setUp(self):
        # Create temp directories for old metadata files and current workspace files
        self.old_dir = Path(tempfile.mkdtemp())
        self.work_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        # Clean up temp directories
        shutil.rmtree(self.old_dir)
        shutil.rmtree(self.work_dir)

    def write_json(self, base_dir: Path, rel_path: str, data: dict):
        path = base_dir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f)

    def test_allowed_adds_modules(self):
        # Adding new files (status A) under modules/ is allowed
        diffs = [
            ("A", "modules/new_module/metadata.json"),
            ("A", "modules/new_module/1.0.0/MODULE.bazel"),
            ("A", "modules/new_module/1.0.0/source.json"),
        ]
        violations = check_violations(diffs, self.old_dir, self.work_dir, "modules")
        self.assertEqual(violations, [])

    def test_allowed_adds_bcr_staging(self):
        # Adding new files (status A) under bcr_staging/modules/ is allowed
        diffs = [
            ("A", "bcr_staging/modules/new_module/metadata.json"),
            ("A", "bcr_staging/modules/new_module/1.0.0/MODULE.bazel"),
            ("A", "bcr_staging/modules/new_module/1.0.0/source.json"),
        ]
        violations = check_violations(diffs, self.old_dir, self.work_dir, "bcr_staging/modules")
        self.assertEqual(violations, [])

    def test_deleted_file_forbidden(self):
        # Deleting existing files under modules/ is forbidden
        diffs = [
            ("D", "modules/existing_module/1.0.0/MODULE.bazel")
        ]
        violations = check_violations(diffs, self.old_dir, self.work_dir, "modules")
        self.assertIn("Deleted file in modules/: modules/existing_module/1.0.0/MODULE.bazel", violations)

    def test_renamed_file_forbidden(self):
        # Renaming existing files under modules/ is forbidden
        diffs = [
            ("R100", "modules/existing_module/1.0.0/MODULE.bazel")
        ]
        violations = check_violations(diffs, self.old_dir, self.work_dir, "modules")
        self.assertIn("Renamed file in modules/: modules/existing_module/1.0.0/MODULE.bazel", violations)

    def test_modified_non_metadata_forbidden(self):
        # Modifying non-metadata.json/MODULE.bazel files is forbidden
        diffs = [
            ("M", "modules/existing_module/1.0.0/source.json")
        ]
        violations = check_violations(diffs, self.old_dir, self.work_dir, "modules")
        self.assertIn("Modified existing file (only metadata.json and MODULE.bazel files can be modified): modules/existing_module/1.0.0/source.json", violations)

    def test_modified_metadata_allowed_add_version(self):
        # Modifying metadata.json to add a new version is allowed
        rel_path = "modules/existing_module/metadata.json"
        
        # Base metadata has version "1.0.0"
        self.write_json(self.old_dir, rel_path, {"versions": ["1.0.0"], "yanked_versions": {}})
        # Working metadata has "1.0.0" and "1.1.0"
        self.write_json(self.work_dir, rel_path, {"versions": ["1.0.0", "1.1.0"], "yanked_versions": {}})

        diffs = [("M", rel_path)]
        violations = check_violations(diffs, self.old_dir, self.work_dir, "modules")
        self.assertEqual(violations, [])

    def test_modified_metadata_removed_version_forbidden(self):
        # Modifying metadata.json and removing a version without yanking is forbidden
        rel_path = "modules/existing_module/metadata.json"
        
        # Base metadata has versions "1.0.0" and "1.1.0"
        self.write_json(self.old_dir, rel_path, {"versions": ["1.0.0", "1.1.0"], "yanked_versions": {}})
        # Working metadata removes "1.0.0" without yanking it
        self.write_json(self.work_dir, rel_path, {"versions": ["1.1.0"], "yanked_versions": {}})

        diffs = [("M", rel_path)]
        violations = check_violations(diffs, self.old_dir, self.work_dir, "modules")
        self.assertIn("Version '1.0.0' was removed from 'versions' in modules/existing_module/metadata.json but was not added to 'yanked_versions'.", violations)

    def test_modified_metadata_yanked_version_allowed(self):
        # Modifying metadata.json and moving a version to yanked_versions is allowed
        rel_path = "modules/existing_module/metadata.json"
        
        # Base metadata has versions "1.0.0" and "1.1.0"
        self.write_json(self.old_dir, rel_path, {"versions": ["1.0.0", "1.1.0"], "yanked_versions": {}})
        # Working metadata removes "1.0.0" from versions and adds it to yanked_versions
        self.write_json(self.work_dir, rel_path, {"versions": ["1.1.0"], "yanked_versions": {"1.0.0": "security flaw"}})

        diffs = [("M", rel_path)]
        violations = check_violations(diffs, self.old_dir, self.work_dir, "modules")
        self.assertEqual(violations, [])

    def test_bcr_staging_rules(self):
        # Test that same rules apply under bcr_staging/modules directory
        rel_path = "bcr_staging/modules/existing_module/metadata.json"
        
        self.write_json(self.old_dir, rel_path, {"versions": ["1.0.0"], "yanked_versions": {}})
        self.write_json(self.work_dir, rel_path, {"versions": ["1.1.0"], "yanked_versions": {}})

        diffs = [("M", rel_path)]
        violations = check_violations(diffs, self.old_dir, self.work_dir, "bcr_staging/modules")
        self.assertIn("Version '1.0.0' was removed from 'versions' in bcr_staging/modules/existing_module/metadata.json but was not added to 'yanked_versions'.", violations)

    def write_text(self, base_dir: Path, rel_path: str, content: str):
        path = base_dir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def test_modified_module_bazel_bump_version_allowed(self):
        rel_path = "modules/existing_module/1.0.0/MODULE.bazel"
        old_content = """module(
    name = "existing_module",
    version = "1.0.0-1.rcr.1",
)
bazel_dep(name = "some_dep", version = "1.2.3")
"""
        new_content = """module(
    name = "existing_module",
    version = "1.0.0-1.rcr.2",
)
bazel_dep(name = "some_dep", version = "1.2.3")
"""
        self.write_text(self.old_dir, rel_path, old_content)
        self.write_text(self.work_dir, rel_path, new_content)

        diffs = [("M", rel_path)]
        violations = check_violations(diffs, self.old_dir, self.work_dir, "modules")
        self.assertEqual(violations, [])

    def test_modified_module_bazel_other_edits_forbidden(self):
        rel_path = "modules/existing_module/1.0.0/MODULE.bazel"
        old_content = """module(
    name = "existing_module",
    version = "1.0.0-1.rcr.1",
)
bazel_dep(name = "some_dep", version = "1.2.3")
"""
        # Change a dependency version, even if version field is bumped correctly
        new_content = """module(
    name = "existing_module",
    version = "1.0.0-1.rcr.2",
)
bazel_dep(name = "some_dep", version = "1.2.4")
"""
        self.write_text(self.old_dir, rel_path, old_content)
        self.write_text(self.work_dir, rel_path, new_content)

        diffs = [("M", rel_path)]
        violations = check_violations(diffs, self.old_dir, self.work_dir, "modules")
        self.assertIn("MODULE.bazel has modifications other than the version bump: modules/existing_module/1.0.0/MODULE.bazel", violations)

    def test_modified_module_bazel_wrong_version_forbidden(self):
        rel_path = "modules/existing_module/1.0.0/MODULE.bazel"
        old_content = """module(
    name = "existing_module",
    version = "1.0.0-1.rcr.1",
)
"""
        # Change version field but not to the correct next patch version
        new_content = """module(
    name = "existing_module",
    version = "1.0.0-1.rcr.3",
)
"""
        self.write_text(self.old_dir, rel_path, old_content)
        self.write_text(self.work_dir, rel_path, new_content)

        diffs = [("M", rel_path)]
        violations = check_violations(diffs, self.old_dir, self.work_dir, "modules")
        self.assertIn("MODULE.bazel version was changed from '1.0.0-1.rcr.1' to '1.0.0-1.rcr.3', but it should have been incremented to '1.0.0-1.rcr.2'.", violations)

    def test_modified_module_bazel_rosdistro_allowed(self):
        rel_path = "modules/rosdistro/lyrical.2026-06-08.rcr.1/MODULE.bazel"
        old_content = """module(
    name = "rosdistro",
    version = "lyrical.2026-06-08.rcr.1",
)
bazel_dep(name = "some_dep", version = "1.2.3")
"""
        # Rosdistro can have any edits (e.g. adding dependencies, changing version, etc.)
        new_content = """module(
    name = "rosdistro",
    version = "lyrical.2026-06-08.rcr.1",
)
bazel_dep(name = "some_dep", version = "1.2.4")
bazel_dep(name = "new_dep", version = "2.0.0")
"""
        self.write_text(self.old_dir, rel_path, old_content)
        self.write_text(self.work_dir, rel_path, new_content)

        diffs = [("M", rel_path)]
        violations = check_violations(diffs, self.old_dir, self.work_dir, "modules")
        self.assertEqual(violations, [])

    def test_source_json_integrity_valid(self):
        # Valid source.json matching overlay and patches files passes
        overlay_file = self.work_dir / "modules/my_module/1.0.0/overlay/BUILD.bazel"
        overlay_file.parent.mkdir(parents=True, exist_ok=True)
        overlay_file.write_text("# BUILD.bazel content\n")

        patch_file = self.work_dir / "modules/my_module/1.0.0/patches/fix.patch"
        patch_file.parent.mkdir(parents=True, exist_ok=True)
        patch_file.write_text("--- a/foo\n+++ b/foo\n")

        from tools.ci.bzlmod_lib import calculate_integrity_hash_for_file
        source_data = {
            "url": "https://example.com/archive.tar.gz",
            "integrity": "sha256-dummy",
            "overlay": {
                "BUILD.bazel": calculate_integrity_hash_for_file(overlay_file),
            },
            "patches": {
                "fix.patch": calculate_integrity_hash_for_file(patch_file),
            },
        }
        self.write_json(self.work_dir, "modules/my_module/1.0.0/source.json", source_data)

        diffs = [
            ("A", "modules/my_module/1.0.0/MODULE.bazel"),
            ("A", "modules/my_module/1.0.0/source.json"),
            ("A", "modules/my_module/1.0.0/overlay/BUILD.bazel"),
            ("A", "modules/my_module/1.0.0/patches/fix.patch"),
        ]
        violations = check_violations(diffs, self.old_dir, self.work_dir, "modules")
        self.assertEqual(violations, [])

    def test_source_json_missing_when_overlay_exists(self):
        # Missing source.json when overlay exists fails
        overlay_file = self.work_dir / "modules/my_module/1.0.0/overlay/BUILD.bazel"
        overlay_file.parent.mkdir(parents=True, exist_ok=True)
        overlay_file.write_text("# BUILD.bazel\n")

        diffs = [
            ("A", "modules/my_module/1.0.0/overlay/BUILD.bazel"),
        ]
        violations = check_violations(diffs, self.old_dir, self.work_dir, "modules")
        self.assertIn("Missing source.json in modules/my_module/1.0.0", violations)

    def test_source_json_overlay_hash_mismatch(self):
        # Mismatch in overlay file hash fails with clear violation
        overlay_file = self.work_dir / "modules/my_module/1.0.0/overlay/BUILD.bazel"
        overlay_file.parent.mkdir(parents=True, exist_ok=True)
        overlay_file.write_text("# Updated BUILD.bazel content\n")

        source_data = {
            "url": "https://example.com/archive.tar.gz",
            "integrity": "sha256-dummy",
            "overlay": {
                "BUILD.bazel": "sha256-stalehash1234567890=",
            },
        }
        self.write_json(self.work_dir, "modules/my_module/1.0.0/source.json", source_data)

        diffs = [
            ("A", "modules/my_module/1.0.0/overlay/BUILD.bazel"),
            ("A", "modules/my_module/1.0.0/source.json"),
        ]
        violations = check_violations(diffs, self.old_dir, self.work_dir, "modules")
        self.assertTrue(any("Integrity mismatch for overlay 'BUILD.bazel'" in v for v in violations))

    def test_source_json_undeclared_overlay_file(self):
        # Overlay file exists on disk but is not declared in source.json
        overlay_file = self.work_dir / "modules/my_module/1.0.0/overlay/BUILD.bazel"
        overlay_file.parent.mkdir(parents=True, exist_ok=True)
        overlay_file.write_text("# BUILD.bazel\n")

        source_data = {
            "url": "https://example.com/archive.tar.gz",
            "integrity": "sha256-dummy",
            "overlay": {},
        }
        self.write_json(self.work_dir, "modules/my_module/1.0.0/source.json", source_data)

        diffs = [
            ("A", "modules/my_module/1.0.0/overlay/BUILD.bazel"),
            ("A", "modules/my_module/1.0.0/source.json"),
        ]
        violations = check_violations(diffs, self.old_dir, self.work_dir, "modules")
        self.assertIn("File 'BUILD.bazel' exists in modules/my_module/1.0.0/overlay but is missing from source.json overlay list", violations)

    def test_source_json_missing_overlay_file_on_disk(self):
        # source.json declares an overlay file that does not exist on disk
        source_data = {
            "url": "https://example.com/archive.tar.gz",
            "integrity": "sha256-dummy",
            "overlay": {
                "nonexistent.bazel": "sha256-dummyhash=",
            },
        }
        self.write_json(self.work_dir, "modules/my_module/1.0.0/source.json", source_data)

        diffs = [
            ("A", "modules/my_module/1.0.0/source.json"),
        ]
        violations = check_violations(diffs, self.old_dir, self.work_dir, "modules")
        self.assertIn("Overlay file 'nonexistent.bazel' declared in modules/my_module/1.0.0/source.json does not exist on disk", violations)

    def test_inter_module_dependency_mismatch_fails(self):
        # Both pkg_a and pkg_b are updated in the PR, but pkg_a references an older version of pkg_b
        pkg_a_module = (
            'module(\n'
            '    name = "pkg_a",\n'
            '    version = "1.0.0.rcr.2",\n'
            ')\n'
            'bazel_dep(name = "pkg_b", version = "2.0.0.rcr.0")\n'
        )
        pkg_b_module = (
            'module(\n'
            '    name = "pkg_b",\n'
            '    version = "2.0.0.rcr.1",\n'
            ')\n'
        )
        self.write_text(self.work_dir, "modules/pkg_a/1.0.0.rcr.2/MODULE.bazel", pkg_a_module)
        self.write_text(self.work_dir, "modules/pkg_b/2.0.0.rcr.1/MODULE.bazel", pkg_b_module)

        diffs = [
            ("A", "modules/pkg_a/1.0.0.rcr.2/MODULE.bazel"),
            ("A", "modules/pkg_b/2.0.0.rcr.1/MODULE.bazel"),
        ]
        violations = check_violations(diffs, self.old_dir, self.work_dir, "modules")
        self.assertTrue(any("All inter-module references between modules updated in a PR must be bumped consistently" in v for v in violations))

    def test_inter_module_dependency_consistent_passes(self):
        # Both pkg_a and pkg_b are updated in the PR, and pkg_a references the updated version of pkg_b
        pkg_a_module = (
            'module(\n'
            '    name = "pkg_a",\n'
            '    version = "1.0.0.rcr.2",\n'
            ')\n'
            'bazel_dep(name = "pkg_b", version = "2.0.0.rcr.1")\n'
        )
        pkg_b_module = (
            'module(\n'
            '    name = "pkg_b",\n'
            '    version = "2.0.0.rcr.1",\n'
            ')\n'
        )
        self.write_text(self.work_dir, "modules/pkg_a/1.0.0.rcr.2/MODULE.bazel", pkg_a_module)
        self.write_text(self.work_dir, "modules/pkg_b/2.0.0.rcr.1/MODULE.bazel", pkg_b_module)

        diffs = [
            ("A", "modules/pkg_a/1.0.0.rcr.2/MODULE.bazel"),
            ("A", "modules/pkg_b/2.0.0.rcr.1/MODULE.bazel"),
        ]
        violations = check_violations(diffs, self.old_dir, self.work_dir, "modules")
        self.assertEqual(violations, [])


class TestMain(unittest.TestCase):
    """
    Exercises main() end-to-end, including its resolution of the actual
    working directory -- the piece check_violations()/check_metadata_json()
    unit tests above can't cover, since they're always handed an explicit
    working_dir rather than going through main()'s own resolution logic.
    """

    def setUp(self):
        # Simulates the real git checkout (what BUILD_WORKSPACE_DIRECTORY
        # should point at).
        self.workspace_root = Path(tempfile.mkdtemp())
        # Simulates Bazel's exec root: some unrelated directory that
        # `bazel run` actually sets as the child process's cwd.
        self.unrelated_cwd = Path(tempfile.mkdtemp())
        self.old_metadata_dir = Path(tempfile.mkdtemp())
        self.args_dir = Path(tempfile.mkdtemp())
        self.diff_status_path = self.args_dir / "diff_status.txt"

        self.original_environ = dict(os.environ)
        self.original_argv = sys.argv
        self.original_cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self.original_cwd)
        os.environ.clear()
        os.environ.update(self.original_environ)
        sys.argv = self.original_argv
        shutil.rmtree(self.workspace_root)
        shutil.rmtree(self.unrelated_cwd)
        shutil.rmtree(self.old_metadata_dir)
        shutil.rmtree(self.args_dir)

    def write_json(self, base_dir: Path, rel_path: str, data: dict):
        path = base_dir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f)

    def run_main(self) -> int:
        sys.argv = [
            "check_pr_modules.py",
            "--diff-status", str(self.diff_status_path),
            "--old-metadata-dir", str(self.old_metadata_dir),
            "--directory", "modules",
        ]
        with self.assertRaises(SystemExit) as cm:
            check_pr_modules.main()
        return cm.exception.code

    def test_modified_metadata_resolved_via_build_workspace_directory(self):
        # Regression test for the bug fixed in main(): under `bazel run`,
        # the child process's cwd is Bazel's exec root, not the real git
        # checkout, so a legitimately-modified metadata.json must still be
        # found via BUILD_WORKSPACE_DIRECTORY rather than bare Path(".").
        rel_path = "modules/existing_module/metadata.json"
        self.write_json(self.old_metadata_dir, rel_path, {"versions": ["1.0.0"], "yanked_versions": {}})
        self.write_json(self.workspace_root, rel_path, {"versions": ["1.0.0", "1.1.0"], "yanked_versions": {}})
        self.diff_status_path.write_text(f"M\t{rel_path}\n")

        os.chdir(self.unrelated_cwd)
        os.environ["BUILD_WORKSPACE_DIRECTORY"] = str(self.workspace_root)

        self.assertEqual(self.run_main(), 0)

    def test_modified_metadata_not_found_without_build_workspace_directory(self):
        # Characterizes the failure mode this env var exists to avoid: if
        # it's unset (or wrong) and the cwd isn't the real checkout, the
        # modified metadata.json can't be found and is (mis)reported as a
        # violation, even though the change itself is legitimate.
        rel_path = "modules/existing_module/metadata.json"
        self.write_json(self.old_metadata_dir, rel_path, {"versions": ["1.0.0"], "yanked_versions": {}})
        self.write_json(self.workspace_root, rel_path, {"versions": ["1.0.0", "1.1.0"], "yanked_versions": {}})
        self.diff_status_path.write_text(f"M\t{rel_path}\n")

        os.chdir(self.unrelated_cwd)
        os.environ.pop("BUILD_WORKSPACE_DIRECTORY", None)

        self.assertEqual(self.run_main(), 1)

    def test_falls_back_to_cwd_when_env_var_unset(self):
        # When invoked directly (e.g. `python3 tools/ci/check_pr_modules.py`
        # outside of `bazel run`), there's no BUILD_WORKSPACE_DIRECTORY --
        # main() should fall back to the process's actual cwd, which is
        # correct in that case since there's no exec-root indirection.
        rel_path = "modules/existing_module/metadata.json"
        self.write_json(self.old_metadata_dir, rel_path, {"versions": ["1.0.0"], "yanked_versions": {}})
        self.write_json(self.workspace_root, rel_path, {"versions": ["1.0.0", "1.1.0"], "yanked_versions": {}})
        self.diff_status_path.write_text(f"M\t{rel_path}\n")

        os.chdir(self.workspace_root)
        os.environ.pop("BUILD_WORKSPACE_DIRECTORY", None)

        self.assertEqual(self.run_main(), 0)

    def test_no_violations_exits_zero_and_violations_exit_one(self):
        diffs_path_content = "D\tmodules/existing_module/1.0.0/MODULE.bazel\n"
        self.diff_status_path.write_text(diffs_path_content)

        os.chdir(self.workspace_root)
        os.environ["BUILD_WORKSPACE_DIRECTORY"] = str(self.workspace_root)

        self.assertEqual(self.run_main(), 1)


if __name__ == "__main__":
    unittest.main()

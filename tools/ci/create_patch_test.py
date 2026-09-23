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

import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

from tools.ci import bzlmod_lib
from tools.ci import create_patch
from tools.ci import vendor_modules


def _run_git(repo_root: Path, args) -> None:
    subprocess.run(["git"] + args, cwd=repo_root, check=True, capture_output=True)


def _init_git_repo_with_published_modules(repo_root: Path) -> None:
    """
    Initializes repo_root as a git repo (branch "main") and commits
    whatever's under modules/ as the "published" baseline -- so
    compute_rollup's default base_ref="main" treats every version present
    at setUp time as already-published (preserving existing tests'
    increment-mode expectations), while versions added later in a test
    body remain branch-only/uncommitted and thus overwrite-in-place
    candidates.
    """
    _run_git(repo_root, ["init", "-q", "-b", "main"])
    _run_git(repo_root, ["config", "user.email", "test@example.com"])
    _run_git(repo_root, ["config", "user.name", "Test"])
    _run_git(repo_root, ["add", "modules"])
    _run_git(repo_root, ["commit", "-q", "-m", "publish initial modules/"])


class TestFetchRawUpstream(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def make_archive(self, strip_prefix: str, files: dict) -> Path:
        src_dir = self.tmp_dir / "src" / strip_prefix
        for rel_path, content in files.items():
            path = src_dir / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        archive_path = self.tmp_dir / "archive.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tf:
            tf.add(src_dir, arcname=strip_prefix)
        return archive_path

    def test_fetches_verifies_and_extracts(self):
        archive_path = self.make_archive("pkg-1.0.0", {"src/foo.c": "int main() {}\n"})
        digest = base64.b64encode(hashlib.sha256(archive_path.read_bytes()).digest()).decode()
        source_json_path = self.tmp_dir / "source.json"
        with open(source_json_path, "w") as f:
            json.dump({
                "url": archive_path.as_uri(),
                "strip_prefix": "pkg-1.0.0",
                "integrity": f"sha256-{digest}",
            }, f)

        dest_dir = self.tmp_dir / "dest"
        create_patch.fetch_raw_upstream(source_json_path, dest_dir)
        self.assertEqual((dest_dir / "src" / "foo.c").read_text(), "int main() {}\n")

    def test_raises_on_integrity_mismatch(self):
        archive_path = self.make_archive("pkg-1.0.0", {"src/foo.c": "content\n"})
        source_json_path = self.tmp_dir / "source.json"
        with open(source_json_path, "w") as f:
            json.dump({
                "url": archive_path.as_uri(),
                "strip_prefix": "pkg-1.0.0",
                "integrity": "sha256-wrongdigest==",
            }, f)

        with self.assertRaises(RuntimeError):
            create_patch.fetch_raw_upstream(source_json_path, self.tmp_dir / "dest")


class TestReadModuleVersion(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_reads_version(self):
        module_file = self.tmp_dir / "MODULE.bazel"
        module_file.write_text(
            'module(\n    name = "rclcpp",\n    version = "32.0.0-1.rcr.1",\n)\n'
        )
        self.assertEqual(create_patch.read_module_version(module_file, "rclcpp"), "32.0.0-1.rcr.1")

    def test_raises_if_not_found(self):
        module_file = self.tmp_dir / "MODULE.bazel"
        module_file.write_text('module(\n    name = "other",\n    version = "1.0.0",\n)\n')
        with self.assertRaises(RuntimeError):
            create_patch.read_module_version(module_file, "rclcpp")


class TestDiffModuleSource(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.pristine_dir = self.tmp_dir / "pristine"
        self.edited_dir = self.tmp_dir / "edited"
        self.pristine_dir.mkdir()
        self.edited_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_unchanged_file_produces_no_diff(self):
        (self.pristine_dir / "src.c").write_text("hello\n")
        (self.edited_dir / "src.c").write_text("hello\n")
        patches, overlays = create_patch.diff_module_source(self.pristine_dir, self.edited_dir)
        self.assertEqual(patches, {})
        self.assertEqual(overlays, {})

    def test_changed_file_produces_patch(self):
        (self.pristine_dir / "src.c").write_text("hello\n")
        (self.edited_dir / "src.c").write_text("goodbye\n")
        patches, overlays = create_patch.diff_module_source(self.pristine_dir, self.edited_dir)
        self.assertIn("src__c.patch", patches)
        self.assertIn("-hello", patches["src__c.patch"])
        self.assertIn("+goodbye", patches["src__c.patch"])
        self.assertEqual(overlays, {})

    def test_new_file_produces_overlay(self):
        (self.edited_dir / "new_file.h").write_text("new content\n")
        patches, overlays = create_patch.diff_module_source(self.pristine_dir, self.edited_dir)
        self.assertEqual(patches, {})
        self.assertEqual(overlays, {"new_file.h": "new content\n"})

    def test_deleted_file_produces_deletion_patch(self):
        (self.pristine_dir / "gone.c").write_text("bye\n")
        patches, overlays = create_patch.diff_module_source(self.pristine_dir, self.edited_dir)
        self.assertIn("gone__c.patch", patches)
        self.assertIn("-bye", patches["gone__c.patch"])
        self.assertEqual(overlays, {})

    def test_module_bazel_is_never_diffed(self):
        (self.pristine_dir / "MODULE.bazel").write_text("old\n")
        (self.edited_dir / "MODULE.bazel").write_text("new\n")
        patches, overlays = create_patch.diff_module_source(self.pristine_dir, self.edited_dir)
        self.assertEqual(patches, {})
        self.assertEqual(overlays, {})

    def test_module_bazel_lock_is_never_diffed(self):
        (self.pristine_dir / "MODULE.bazel.lock").write_text("old\n")
        (self.edited_dir / "MODULE.bazel.lock").write_text("new\n")
        patches, overlays = create_patch.diff_module_source(self.pristine_dir, self.edited_dir)
        self.assertEqual(patches, {})
        self.assertEqual(overlays, {})

    def test_diff_files_without_trailing_newline(self):
        (self.pristine_dir / "file.h").write_text("#include <a.h>\n}")
        (self.edited_dir / "file.h").write_text("#include <a.h>\n#include <b.h>\n}")
        patches, overlays = create_patch.diff_module_source(self.pristine_dir, self.edited_dir)
        self.assertIn("file__h.patch", patches)
        self.assertNotIn("-}+}", patches["file__h.patch"])
        self.assertIn("+#include <b.h>\n", patches["file__h.patch"])


class TestLoadExistingPatchesAndOverlays(unittest.TestCase):

    def setUp(self):
        self.module_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.module_dir)

    def test_loads_referenced_files(self):
        (self.module_dir / "patches").mkdir()
        (self.module_dir / "patches" / "foo.patch").write_text("diff content\n")
        (self.module_dir / "overlay").mkdir()
        (self.module_dir / "overlay" / "bar.h").write_text("overlay content\n")
        with open(self.module_dir / "source.json", "w") as f:
            json.dump({
                "patches": {"foo.patch": "sha256-fake"},
                "overlay": {"bar.h": "sha256-fake"},
            }, f)
        patches, overlays = create_patch.load_existing_patches_and_overlays(self.module_dir)
        self.assertEqual(patches, {"foo.patch": "diff content\n"})
        self.assertEqual(overlays, {"bar.h": "overlay content\n"})


class TestDiscoverVendoredModules(unittest.TestCase):

    def setUp(self):
        self.workspace_root = Path(tempfile.mkdtemp())
        self.modules_dir = self.workspace_root / "modules"
        self.target_workspace = self.workspace_root / "workspace"
        for name in ["rclcpp", "rcutils"]:
            (self.modules_dir / name).mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.workspace_root)

    def test_lists_vendored_modules_stripping_plus_suffix(self):
        (self.target_workspace / "vendor" / "rclcpp+").mkdir(parents=True)
        (self.target_workspace / "vendor" / "rcutils+").mkdir(parents=True)
        result = create_patch.discover_vendored_modules(self.target_workspace, self.modules_dir)
        self.assertEqual(result, ["rclcpp", "rcutils"])

    def test_ignores_entries_without_a_declared_module(self):
        (self.target_workspace / "vendor" / "rclcpp+").mkdir(parents=True)
        (self.target_workspace / "vendor" / "some_bcr_only_dep+").mkdir(parents=True)
        result = create_patch.discover_vendored_modules(self.target_workspace, self.modules_dir)
        self.assertEqual(result, ["rclcpp"])

    def test_missing_vendor_dir_returns_empty(self):
        result = create_patch.discover_vendored_modules(self.target_workspace, self.modules_dir)
        self.assertEqual(result, [])


class TestModuleHasLocalEdits(unittest.TestCase):

    def setUp(self):
        self.target_workspace = Path(tempfile.mkdtemp())
        self.vendor_module_dir = self.target_workspace / "vendor" / "rclcpp+"
        self.vendor_module_dir.mkdir(parents=True)
        (self.vendor_module_dir / "src.c").write_text("hello\n")

    def tearDown(self):
        shutil.rmtree(self.target_workspace)

    def write_manifest(self, hashes: dict):
        manifest_dir = self.target_workspace / vendor_modules.VENDOR_MANIFEST_DIR_NAME
        manifest_dir.mkdir(parents=True, exist_ok=True)
        with open(manifest_dir / "rclcpp.json", "w") as f:
            json.dump(hashes, f)

    def test_no_manifest_is_conservatively_treated_as_edited(self):
        self.assertTrue(create_patch.module_has_local_edits(self.target_workspace, "rclcpp"))

    def test_matching_manifest_means_no_edits(self):
        self.write_manifest(bzlmod_lib.hash_directory_tree(self.vendor_module_dir))
        self.assertFalse(create_patch.module_has_local_edits(self.target_workspace, "rclcpp"))

    def test_edited_file_is_detected(self):
        self.write_manifest(bzlmod_lib.hash_directory_tree(self.vendor_module_dir))
        (self.vendor_module_dir / "src.c").write_text("edited\n")
        self.assertTrue(create_patch.module_has_local_edits(self.target_workspace, "rclcpp"))


class _RollupFixtureTestCase(unittest.TestCase):
    """
    Shared fixture: a workspace with a single vendored module ("rclcpp",
    published at 1.0.0) whose vendored tree has been locally edited, plus
    the raw-upstream archive (served over a file:// URL, same trick as
    TestFetchRawUpstream) needed to diff against it without real network
    access.
    """

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.workspace_root = self.tmp_dir / "repo"
        self.modules_dir = self.workspace_root / "modules"
        self.target_workspace = self.workspace_root / "workspace"
        (self.target_workspace / "vendor").mkdir(parents=True)
        (self.target_workspace / "MODULE.bazel").write_text("")

        module_dir = self.modules_dir / "rclcpp"
        self.version_dir = module_dir / "1.0.0"
        self.version_dir.mkdir(parents=True)
        with open(module_dir / "metadata.json", "w") as f:
            json.dump({"versions": ["1.0.0"], "yanked_versions": {}}, f)
        (self.version_dir / "MODULE.bazel").write_text(
            'module(\n    name = "rclcpp",\n    version = "1.0.0",\n)\n')

        archive_path = self._make_archive("rclcpp-1.0.0", {"src.c": "original\n"})
        digest = base64.b64encode(hashlib.sha256(archive_path.read_bytes()).digest()).decode()
        with open(self.version_dir / "source.json", "w") as f:
            json.dump({
                "url": archive_path.as_uri(),
                "strip_prefix": "rclcpp-1.0.0",
                "integrity": f"sha256-{digest}",
            }, f)

        self.vendor_module_dir = self.target_workspace / "vendor" / "rclcpp+"
        self.vendor_module_dir.mkdir(parents=True)
        (self.vendor_module_dir / "MODULE.bazel").write_text(
            'module(\n    name = "rclcpp",\n    version = "1.0.0",\n)\n')
        (self.vendor_module_dir / "src.c").write_text("edited\n")

        _init_git_repo_with_published_modules(self.workspace_root)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def _make_archive(self, strip_prefix: str, files: dict) -> Path:
        src_dir = self.tmp_dir / "archive_src" / strip_prefix
        for rel_path, content in files.items():
            path = src_dir / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        archive_path = self.tmp_dir / f"{strip_prefix}.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tf:
            tf.add(src_dir, arcname=strip_prefix)
        return archive_path


class TestComputeRollupAndApply(_RollupFixtureTestCase):

    def test_detects_change_and_computes_new_version(self):
        rollup = create_patch.compute_rollup(
            "rclcpp", self.modules_dir, self.target_workspace, self.workspace_root)
        self.assertTrue(rollup.changed)
        self.assertEqual(rollup.current_version, "1.0.0")
        self.assertEqual(rollup.new_version, "1.0.0.rcr.0")
        self.assertIn("src__c.patch", rollup.new_patches)

    def test_no_local_edit_means_unchanged(self):
        (self.vendor_module_dir / "src.c").write_text("original\n")
        rollup = create_patch.compute_rollup(
            "rclcpp", self.modules_dir, self.target_workspace, self.workspace_root)
        self.assertFalse(rollup.changed)

    def test_missing_vendor_dir_raises(self):
        shutil.rmtree(self.vendor_module_dir)
        with self.assertRaises(RuntimeError):
            create_patch.compute_rollup(
                "rclcpp", self.modules_dir, self.target_workspace, self.workspace_root)

    def test_stale_workspace_raises(self):
        # A newer patch has already been published since this workspace
        # was set up -- the workspace is stale and must not be rolled up.
        (self.modules_dir / "rclcpp" / "1.0.0.rcr.5").mkdir()
        with open(self.modules_dir / "rclcpp" / "metadata.json", "w") as f:
            json.dump({"versions": ["1.0.0", "1.0.0.rcr.5"], "yanked_versions": {}}, f)
        with self.assertRaises(RuntimeError):
            create_patch.compute_rollup(
                "rclcpp", self.modules_dir, self.target_workspace, self.workspace_root)

    def test_apply_rollup_writes_new_version_and_updates_metadata(self):
        rollup = create_patch.compute_rollup(
            "rclcpp", self.modules_dir, self.target_workspace, self.workspace_root)
        create_patch.apply_rollup(rollup, self.modules_dir / "rclcpp" / "metadata.json")

        new_dir = self.modules_dir / "rclcpp" / "1.0.0.rcr.0"
        self.assertEqual(
            (new_dir / "patches" / "src__c.patch").read_text(),
            rollup.new_patches["src__c.patch"])
        self.assertIn('version = "1.0.0.rcr.0"', (new_dir / "MODULE.bazel").read_text())
        with open(self.modules_dir / "rclcpp" / "metadata.json") as f:
            metadata = json.load(f)
        self.assertEqual(metadata["versions"], ["1.0.0", "1.0.0.rcr.0"])


class TestComputeRollupOverwriteInPlace(_RollupFixtureTestCase):
    """
    Covers a version that only exists on the current branch (never
    committed to "main"): compute_rollup should amend it in place instead
    of incrementing to yet another new version.
    """

    def setUp(self):
        super().setUp()
        # Simulate a prior create_patch run that already amended rclcpp to
        # 1.0.0.rcr.0 on this branch, uncommitted -- current_version
        # resolves to it, and it should be safe to overwrite in place
        # rather than incrementing to 1.0.0.rcr.1.
        self.branch_version = "1.0.0.rcr.0"
        self.branch_version_dir = self.modules_dir / "rclcpp" / self.branch_version
        shutil.copytree(self.version_dir, self.branch_version_dir)
        (self.branch_version_dir / "MODULE.bazel").write_text(
            f'module(\n    name = "rclcpp",\n    version = "{self.branch_version}",\n)\n')
        with open(self.modules_dir / "rclcpp" / "metadata.json", "w") as f:
            json.dump({"versions": ["1.0.0", self.branch_version], "yanked_versions": {}}, f)

        (self.vendor_module_dir / "MODULE.bazel").write_text(
            f'module(\n    name = "rclcpp",\n    version = "{self.branch_version}",\n)\n')

        vendor_modules.write_package_manifest(
            self.target_workspace, self.modules_dir, "rclcpp", self.branch_version)

    def test_overwrites_in_place_instead_of_incrementing(self):
        rollup = create_patch.compute_rollup(
            "rclcpp", self.modules_dir, self.target_workspace, self.workspace_root)
        self.assertTrue(rollup.overwrite_in_place)
        self.assertEqual(rollup.current_version, self.branch_version)
        self.assertEqual(rollup.new_version, self.branch_version)
        self.assertEqual(rollup.new_module_dir, rollup.current_module_dir)

    def test_apply_rollup_overwrites_existing_dir_in_place(self):
        rollup = create_patch.compute_rollup(
            "rclcpp", self.modules_dir, self.target_workspace, self.workspace_root)
        create_patch.apply_rollup(rollup, self.modules_dir / "rclcpp" / "metadata.json")

        self.assertEqual(
            (self.branch_version_dir / "patches" / "src__c.patch").read_text(),
            rollup.new_patches["src__c.patch"])
        self.assertIn(
            f'version = "{self.branch_version}"',
            (self.branch_version_dir / "MODULE.bazel").read_text())
        with open(self.modules_dir / "rclcpp" / "metadata.json") as f:
            metadata = json.load(f)
        # Idempotent -- the version was already listed, no duplicate entry.
        self.assertEqual(metadata["versions"], ["1.0.0", self.branch_version])
        # No stray extra version got minted alongside it.
        self.assertFalse((self.modules_dir / "rclcpp" / "1.0.0.rcr.1").exists())

    def test_drift_since_vendoring_is_refused(self):
        # Something (e.g. a concurrent git pull/checkout) changed the
        # packaged directory after this workspace vendored it.
        (self.branch_version_dir / "extra_file.txt").write_text("surprise\n")
        with self.assertRaises(RuntimeError):
            create_patch.compute_rollup(
                "rclcpp", self.modules_dir, self.target_workspace, self.workspace_root)

    def test_missing_package_manifest_is_refused(self):
        manifest_path = (
            self.target_workspace / vendor_modules.PACKAGE_MANIFEST_DIR_NAME / "rclcpp.json")
        manifest_path.unlink()
        with self.assertRaises(RuntimeError):
            create_patch.compute_rollup(
                "rclcpp", self.modules_dir, self.target_workspace, self.workspace_root)


class TestMainAutoDetect(_RollupFixtureTestCase):

    def setUp(self):
        super().setUp()
        self.original_environ = dict(os.environ)
        os.environ["BUILD_WORKSPACE_DIRECTORY"] = str(self.workspace_root)
        self.original_argv = sys.argv

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.original_environ)
        sys.argv = self.original_argv
        if "input" in vars(create_patch):
            del create_patch.input
        super().tearDown()

    def run_main(self, argv):
        sys.argv = ["create_patch.py"] + argv
        create_patch.main()

    def new_version_dir(self) -> Path:
        return self.modules_dir / "rclcpp" / "1.0.0.rcr.0"

    def test_confirm_yes_rolls_up_detected_module(self):
        create_patch.input = lambda prompt="": "y"
        self.run_main([])
        self.assertTrue(self.new_version_dir().exists())

    def test_confirm_no_aborts_without_writing(self):
        create_patch.input = lambda prompt="": "n"
        self.run_main([])
        self.assertFalse(self.new_version_dir().exists())

    def test_yes_flag_skips_the_prompt(self):
        def _boom(prompt=""):
            raise AssertionError("should not prompt when --yes is passed")
        create_patch.input = _boom
        self.run_main(["--yes"])
        self.assertTrue(self.new_version_dir().exists())

    def test_dry_run_does_not_prompt_or_write(self):
        def _boom(prompt=""):
            raise AssertionError("should not prompt during --dry-run")
        create_patch.input = _boom
        self.run_main(["--dry-run"])
        self.assertFalse(self.new_version_dir().exists())

    def test_no_edits_means_no_prompt_and_nothing_to_roll_up(self):
        (self.vendor_module_dir / "src.c").write_text("original\n")

        def _boom(prompt=""):
            raise AssertionError("should not prompt when nothing changed")
        create_patch.input = _boom
        self.run_main([])
        self.assertFalse(self.new_version_dir().exists())

    def test_explicit_module_argument_bypasses_auto_detect_and_prompt(self):
        def _boom(prompt=""):
            raise AssertionError("explicit module should never prompt")
        create_patch.input = _boom
        self.run_main(["rclcpp"])
        self.assertTrue(self.new_version_dir().exists())

    def test_base_ref_flag_changes_publish_decision(self):
        # An empty branch where rclcpp@1.0.0 was never committed -- against
        # that ref, 1.0.0 looks branch-only, so create_patch should amend
        # it in place rather than incrementing to 1.0.0.rcr.0. Built via
        # plumbing commands (commit-tree/update-ref) rather than a real
        # checkout, so the current branch's working tree/index are never
        # touched.
        empty_tree_sha = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
        commit_result = subprocess.run(
            ["git", "commit-tree", empty_tree_sha, "-m", "empty"],
            cwd=self.workspace_root, check=True, capture_output=True, text=True,
        )
        _run_git(
            self.workspace_root,
            ["update-ref", "refs/heads/empty-branch", commit_result.stdout.strip()],
        )
        vendor_modules.write_package_manifest(
            self.target_workspace, self.modules_dir, "rclcpp", "1.0.0")

        create_patch.input = lambda prompt="": "y"
        self.run_main(["--base-ref", "empty-branch"])

        self.assertFalse(self.new_version_dir().exists())
        self.assertTrue((self.version_dir / "patches" / "src__c.patch").exists())


class TestRosdistroMODULEBazelRollup(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.workspace_root = self.tmp_dir / "repo"
        self.modules_dir = self.workspace_root / "modules"
        self.target_workspace = self.workspace_root / "workspace"
        (self.target_workspace / "vendor").mkdir(parents=True)
        (self.target_workspace / "MODULE.bazel").write_text("")

        module_dir = self.modules_dir / "rosdistro"
        self.version_dir = module_dir / "lyrical.2026-06-08.rcr.1"
        self.version_dir.mkdir(parents=True)
        with open(module_dir / "metadata.json", "w") as f:
            json.dump({"versions": ["lyrical.2026-06-08.rcr.1"], "yanked_versions": {}}, f)
        
        self.old_module_content = (
            'module(\n'
            '    name = "rosdistro",\n'
            '    version = "lyrical.2026-06-08.rcr.1",\n'
            ')\n'
            'bazel_dep(name = "old_dep", version = "1.0.0")\n'
        )
        (self.version_dir / "MODULE.bazel").write_text(self.old_module_content)

        # source.json has to exist for compute_rollup to load pristine/raw-upstream
        # even though we don't have diffs.
        archive_src = self.tmp_dir / "archive_src" / "rosdistro-lyrical-2026-06-08"
        archive_src.mkdir(parents=True)
        (archive_src / "dummy.txt").write_text("hello\n")
        archive_path = self.tmp_dir / "rosdistro.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tf:
            tf.add(archive_src, arcname="rosdistro-lyrical-2026-06-08")
        
        digest = base64.b64encode(hashlib.sha256(archive_path.read_bytes()).digest()).decode()
        with open(self.version_dir / "source.json", "w") as f:
            json.dump({
                "url": archive_path.as_uri(),
                "strip_prefix": "rosdistro-lyrical-2026-06-08",
                "integrity": f"sha256-{digest}",
            }, f)

        self.vendor_module_dir = self.target_workspace / "vendor" / "rosdistro+"
        self.vendor_module_dir.mkdir(parents=True)
        # In vendor_module_dir, write the dummy.txt as well so no diffs in source files
        (self.vendor_module_dir / "dummy.txt").write_text("hello\n")

        _init_git_repo_with_published_modules(self.workspace_root)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_rosdistro_module_bazel_edits_detected_and_applied(self):
        # Developer edits MODULE.bazel in vendored tree (adds a new dependency)
        new_module_content = (
            'module(\n'
            '    name = "rosdistro",\n'
            '    version = "lyrical.2026-06-08.rcr.1",\n'
            ')\n'
            'bazel_dep(name = "old_dep", version = "1.0.0")\n'
            'bazel_dep(name = "new_dep", version = "2.0.0")\n'
        )
        (self.vendor_module_dir / "MODULE.bazel").write_text(new_module_content)

        rollup = create_patch.compute_rollup(
            "rosdistro", self.modules_dir, self.target_workspace, self.workspace_root)
        self.assertTrue(rollup.changed)
        self.assertEqual(rollup.current_version, "lyrical.2026-06-08.rcr.1")
        self.assertEqual(rollup.new_version, "lyrical.2026-06-08.rcr.2")

        create_patch.apply_rollup(rollup, self.modules_dir / "rosdistro" / "metadata.json")

        new_dir = self.modules_dir / "rosdistro" / "lyrical.2026-06-08.rcr.2"
        self.assertTrue(new_dir.exists())
        
        # Verify the new MODULE.bazel has the developer's modifications AND the correct new version
        new_content = (new_dir / "MODULE.bazel").read_text()
        self.assertIn('version = "lyrical.2026-06-08.rcr.2"', new_content)
        self.assertIn('bazel_dep(name = "new_dep", version = "2.0.0")', new_content)


class TestRosdistroOverwriteInPlace(unittest.TestCase):
    """
    Covers the overwrite-in-place path for rosdistro specifically: its
    version is branch-only (never committed to "main"), so create_patch
    should amend modules/rosdistro/<version>/MODULE.bazel in place rather
    than incrementing to a new version.
    """

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.workspace_root = self.tmp_dir / "repo"
        self.modules_dir = self.workspace_root / "modules"
        self.target_workspace = self.workspace_root / "workspace"
        (self.target_workspace / "vendor").mkdir(parents=True)
        (self.target_workspace / "MODULE.bazel").write_text("")

        # git repo exists, but rosdistro's version is never committed to
        # main -- it's branch-only.
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        _run_git(self.workspace_root, ["init", "-q", "-b", "main"])
        _run_git(self.workspace_root, ["config", "user.email", "test@example.com"])
        _run_git(self.workspace_root, ["config", "user.name", "Test"])
        (self.workspace_root / "README.md").write_text("placeholder\n")
        _run_git(self.workspace_root, ["add", "README.md"])
        _run_git(self.workspace_root, ["commit", "-q", "-m", "initial commit"])

        module_dir = self.modules_dir / "rosdistro"
        self.version_dir = module_dir / "lyrical.2026-06-08.rcr.2"
        self.version_dir.mkdir(parents=True)
        with open(module_dir / "metadata.json", "w") as f:
            json.dump({"versions": ["lyrical.2026-06-08.rcr.2"], "yanked_versions": {}}, f)

        self.old_module_content = (
            'module(\n'
            '    name = "rosdistro",\n'
            '    version = "lyrical.2026-06-08.rcr.2",\n'
            ')\n'
            'bazel_dep(name = "old_dep", version = "1.0.0")\n'
        )
        (self.version_dir / "MODULE.bazel").write_text(self.old_module_content)

        archive_src = self.tmp_dir / "archive_src" / "rosdistro-lyrical-2026-06-08"
        archive_src.mkdir(parents=True)
        (archive_src / "dummy.txt").write_text("hello\n")
        archive_path = self.tmp_dir / "rosdistro.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tf:
            tf.add(archive_src, arcname="rosdistro-lyrical-2026-06-08")
        digest = base64.b64encode(hashlib.sha256(archive_path.read_bytes()).digest()).decode()
        with open(self.version_dir / "source.json", "w") as f:
            json.dump({
                "url": archive_path.as_uri(),
                "strip_prefix": "rosdistro-lyrical-2026-06-08",
                "integrity": f"sha256-{digest}",
            }, f)

        self.vendor_module_dir = self.target_workspace / "vendor" / "rosdistro+"
        self.vendor_module_dir.mkdir(parents=True)
        (self.vendor_module_dir / "dummy.txt").write_text("hello\n")
        (self.vendor_module_dir / "MODULE.bazel").write_text(self.old_module_content)

        vendor_modules.write_package_manifest(
            self.target_workspace, self.modules_dir, "rosdistro", "lyrical.2026-06-08.rcr.2")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_amends_rosdistro_module_bazel_in_place(self):
        new_module_content = (
            'module(\n'
            '    name = "rosdistro",\n'
            '    version = "lyrical.2026-06-08.rcr.2",\n'
            ')\n'
            'bazel_dep(name = "old_dep", version = "1.0.0")\n'
            'bazel_dep(name = "new_dep", version = "2.0.0")\n'
        )
        (self.vendor_module_dir / "MODULE.bazel").write_text(new_module_content)

        rollup = create_patch.compute_rollup(
            "rosdistro", self.modules_dir, self.target_workspace, self.workspace_root)
        self.assertTrue(rollup.overwrite_in_place)
        self.assertEqual(rollup.new_version, "lyrical.2026-06-08.rcr.2")

        create_patch.apply_rollup(rollup, self.modules_dir / "rosdistro" / "metadata.json")

        # Still the SAME directory -- no lyrical.2026-06-08.rcr.3 was minted.
        self.assertFalse((self.modules_dir / "rosdistro" / "lyrical.2026-06-08.rcr.3").exists())
        new_content = (self.version_dir / "MODULE.bazel").read_text()
        self.assertIn('version = "lyrical.2026-06-08.rcr.2"', new_content)
        self.assertIn('bazel_dep(name = "new_dep", version = "2.0.0")', new_content)


class TestApplyRollupInterModuleBumps(_RollupFixtureTestCase):

    def setUp(self):
        super().setUp()
        rcutils_dir = self.modules_dir / "rcutils"
        (rcutils_dir / "1.0.0").mkdir(parents=True)
        (rcutils_dir / "1.0.0" / "MODULE.bazel").write_text('module(name = "rcutils", version = "1.0.0")\n')
        with open(rcutils_dir / "metadata.json", "w") as f:
            json.dump({"versions": ["1.0.0", "1.0.0.rcr.1"], "yanked_versions": {}}, f)

        module_content = (
            'module(\n'
            '    name = "rclcpp",\n'
            '    version = "1.0.0",\n'
            ')\n'
            'bazel_dep(name = "rcutils", version = "1.0.0")\n'
        )
        (self.version_dir / "MODULE.bazel").write_text(module_content)
        (self.vendor_module_dir / "MODULE.bazel").write_text(module_content)

    def test_apply_rollup_bumps_dep_from_batch_versions(self):
        rollup = create_patch.compute_rollup(
            "rclcpp", self.modules_dir, self.target_workspace, self.workspace_root
        )
        create_patch.apply_rollup(
            rollup,
            self.modules_dir / "rclcpp" / "metadata.json",
            updated_versions={"rcutils": "1.0.0.rcr.2"},
        )
        new_dir = self.modules_dir / "rclcpp" / "1.0.0.rcr.0"
        content = (new_dir / "MODULE.bazel").read_text()
        self.assertIn('bazel_dep(name = "rcutils", version = "1.0.0.rcr.2")', content)

    def test_apply_rollup_bumps_dep_from_metadata_json(self):
        rollup = create_patch.compute_rollup(
            "rclcpp", self.modules_dir, self.target_workspace, self.workspace_root
        )
        create_patch.apply_rollup(
            rollup,
            self.modules_dir / "rclcpp" / "metadata.json",
        )
        new_dir = self.modules_dir / "rclcpp" / "1.0.0.rcr.0"
        content = (new_dir / "MODULE.bazel").read_text()
        self.assertIn('bazel_dep(name = "rcutils", version = "1.0.0.rcr.1")', content)


if __name__ == "__main__":
    unittest.main()

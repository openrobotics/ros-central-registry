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

import shutil
import tempfile
import unittest
from pathlib import Path

from tools.ci import setup_workspace


class TestRenderBazelrc(unittest.TestCase):

    def test_cache_write_off_by_default(self):
        content = setup_workspace.render_bazelrc("lyrical", "", "/tmp")
        self.assertNotIn("--remote_upload_local_results=true", content)
        self.assertNotIn("--google_default_credentials", content)
        # The safe, credential-free performance flags are always present.
        self.assertIn("common:ci --http_timeout_scaling=3.0", content)

    def test_cache_write_enabled_opt_in(self):
        content = setup_workspace.render_bazelrc("lyrical", "", "/tmp", remote_cache_write=True)
        self.assertIn("common:ci --remote_upload_local_results=true", content)
        self.assertIn("common:ci --google_default_credentials", content)


class TestLlvmPatches(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo_root = self.tmp / "repo"
        self.workspace = self.tmp / "workspace"
        self.src_dir = self.repo_root / setup_workspace.LLVM_PATCHES_SOURCE_DIR
        self.src_dir.mkdir(parents=True)
        for name, _ in setup_workspace.LLVM_PATCHES:
            (self.src_dir / name).write_text(f"--- {name}\n")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_render_llvm_override_lists_every_patch_with_explanation(self):
        content = setup_workspace.render_llvm_override("0.8.24")
        self.assertIn('module_name = "llvm"', content)
        self.assertIn('version = "0.8.24"', content)
        self.assertIn("patch_strip = 1", content)
        for name, explanation in setup_workspace.LLVM_PATCHES:
            self.assertIn(f'"//{setup_workspace.WORKSPACE_PATCHES_DIR}:{name}",', content)
            # Every explanation line is emitted as a comment.
            for line in explanation.splitlines():
                self.assertIn(f"# {line}", content)

    def test_copy_llvm_patches_copies_all_listed_files(self):
        written = setup_workspace.copy_llvm_patches(self.repo_root, self.workspace)
        expected_dir = self.workspace / setup_workspace.WORKSPACE_PATCHES_DIR
        self.assertEqual(
            sorted(p.name for p in written),
            sorted(name for name, _ in setup_workspace.LLVM_PATCHES),
        )
        for name, _ in setup_workspace.LLVM_PATCHES:
            dst = expected_dir / name
            self.assertTrue(dst.is_file())
            self.assertEqual(dst.read_text(), f"--- {name}\n")

    def test_copy_llvm_patches_raises_when_a_patch_is_missing(self):
        missing = setup_workspace.LLVM_PATCHES[0][0]
        (self.src_dir / missing).unlink()
        with self.assertRaises(FileNotFoundError) as ctx:
            setup_workspace.copy_llvm_patches(self.repo_root, self.workspace)
        self.assertIn(missing, str(ctx.exception))

    def test_render_patches_build_file_exports_each_file(self):
        content = setup_workspace.render_patches_build_file(["fmt.patch", "a.patch"])
        self.assertIn("exports_files([", content)
        self.assertIn('    "fmt.patch",', content)
        self.assertIn('    "a.patch",', content)

    def test_checked_in_patches_match_manifest(self):
        # Guard against LLVM_PATCHES drifting from tools/ci/patches/llvm/.
        real_root = Path(__file__).parents[2]
        real_dir = real_root / setup_workspace.LLVM_PATCHES_SOURCE_DIR
        if not real_dir.is_dir():
            self.skipTest(f"{real_dir} not available in this test environment")
        on_disk = sorted(p.name for p in real_dir.glob("*.patch"))
        listed = sorted(name for name, _ in setup_workspace.LLVM_PATCHES)
        self.assertEqual(on_disk, listed)


class TestCalculatePackagesForVariant(unittest.TestCase):

    def setUp(self):
        self.module_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.module_dir)

    def write_module_bazel(self, name: str, version: str, deps=None):
        pkg_dir = self.module_dir / name / version
        pkg_dir.mkdir(parents=True)
        content = f'module(name = "{name}", version = "{version}")\n'
        for dep_name, dep_version in (deps or []):
            content += f'bazel_dep(name = "{dep_name}", version = "{dep_version}")\n'
        (pkg_dir / "MODULE.bazel").write_text(content)

    def test_collects_transitive_dependencies(self):
        self.write_module_bazel("pkg_a", "1.0.0", deps=[("pkg_b", "2.0.0")])
        self.write_module_bazel("pkg_b", "2.0.0", deps=[("pkg_c", "3.0.0")])
        self.write_module_bazel("pkg_c", "3.0.0")
        result = setup_workspace.calculate_packages_for_variant(
            self.module_dir, "pkg_a", "1.0.0")
        self.assertEqual(result, ["pkg_a", "pkg_b", "pkg_c"])

    def test_diamond_dependency_is_only_visited_once(self):
        self.write_module_bazel(
            "pkg_a", "1.0.0", deps=[("pkg_b", "1.0.0"), ("pkg_c", "1.0.0")])
        self.write_module_bazel("pkg_b", "1.0.0", deps=[("pkg_d", "1.0.0")])
        self.write_module_bazel("pkg_c", "1.0.0", deps=[("pkg_d", "1.0.0")])
        self.write_module_bazel("pkg_d", "1.0.0")
        result = setup_workspace.calculate_packages_for_variant(
            self.module_dir, "pkg_a", "1.0.0")
        self.assertEqual(result, ["pkg_a", "pkg_b", "pkg_c", "pkg_d"])

    def test_rosdistro_is_always_discarded(self):
        self.write_module_bazel(
            "pkg_a", "1.0.0", deps=[("rosdistro", "lyrical.2026-06-08")])
        result = setup_workspace.calculate_packages_for_variant(
            self.module_dir, "pkg_a", "1.0.0")
        self.assertEqual(result, ["pkg_a"])

    def test_dependency_with_missing_module_file_is_not_traversed_further(self):
        self.write_module_bazel(
            "pkg_a", "1.0.0", deps=[("pkg_missing", "9.9.9")])
        result = setup_workspace.calculate_packages_for_variant(
            self.module_dir, "pkg_a", "1.0.0")
        # pkg_missing has no MODULE.bazel on disk, so it's never queued and
        # never shows up as a collected package.
        self.assertEqual(result, ["pkg_a"])

    def test_start_module_with_missing_file_returns_only_itself(self):
        result = setup_workspace.calculate_packages_for_variant(
            self.module_dir, "pkg_a", "1.0.0")
        self.assertEqual(result, ["pkg_a"])


if __name__ == "__main__":
    unittest.main()

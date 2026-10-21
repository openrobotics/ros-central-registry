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

    def test_cxx23_and_per_file_exceptions(self):
        content = setup_workspace.render_bazelrc("lyrical", "", "/tmp")
        self.assertIn("build --cxxopt=-std=c++23", content)
        self.assertIn("build --host_cxxopt=-std=c++23", content)
        self.assertIn("WARNING: PER-FILE C++ STANDARD EXCEPTIONS", content)
        self.assertIn("build --per_file_copt=external/.*fastdds.*@-std=c++17", content)
        self.assertIn("build --per_file_copt=external/.*popf.*@-std=c++17", content)


class TestPlatforms(unittest.TestCase):

    def test_platforms_build_pins_glibc_2_34(self):
        content = setup_workspace.render_platforms_build_file()
        self.assertTrue(content.startswith("# Copyright"))
        self.assertIn('name = "linux",', content)
        self.assertIn('"@llvm//constraints/libc:gnu.2.34",', content)
        self.assertIn('parents = ["@platforms//host"],', content)

    def test_bazelrc_selects_platform_on_linux(self):
        content = setup_workspace.render_bazelrc("lyrical", "", "/tmp")
        self.assertIn(
            f"build:linux --platforms=//{setup_workspace.WORKSPACE_PLATFORMS_DIR}:linux",
            content,
        )
        self.assertIn("common --enable_platform_specific_config", content)


class TestRenderUnderlayBuildFile(unittest.TestCase):

    def test_one_underlay_per_variant(self):
        content = setup_workspace.render_underlay_build_file(["core", "desktop_full"])
        self.assertIn('load("@rosdistro//ament:defs.bzl", "ament_underlay")', content)
        self.assertIn('name = "core",', content)
        self.assertIn('deps = ["@ros_core//:ament_package"],', content)
        self.assertIn('name = "desktop_full",', content)
        self.assertIn('deps = ["@desktop_full//:ament_package"],', content)
        self.assertEqual(content.count("ament_underlay("), 2)

    def test_no_variants_only_loads(self):
        content = setup_workspace.render_underlay_build_file([])
        self.assertNotIn("ament_underlay(", content)

    def test_skips_all_variant(self):
        content = setup_workspace.render_underlay_build_file(["all", "core"])
        self.assertNotIn('name = "all",', content)
        self.assertIn('name = "core",', content)
        self.assertEqual(content.count("ament_underlay("), 1)


class TestModuleOverrides(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo_root = self.tmp / "repo"
        self.workspace = self.tmp / "workspace"
        self.src_dir = self.repo_root / setup_workspace.PATCHES_SOURCE_DIR
        for rel in setup_workspace.override_patch_paths():
            (self.src_dir / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.src_dir / rel).write_text(f"--- {rel}\n")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_render_module_override_lists_every_patch_with_explanation(self):
        for override in setup_workspace.MODULE_OVERRIDES:
            content = setup_workspace.render_module_override(override)
            dep = f'bazel_dep(name = "{override.module}", version = "{override.version}")'
            if override.declare_dep:
                self.assertIn(dep, content)
            else:
                self.assertNotIn(dep, content)
            self.assertIn(f'module_name = "{override.module}"', content)
            self.assertIn(f'version = "{override.version}"', content)
            self.assertIn("patch_strip = 1", content)
            for line in override.reason.splitlines():
                self.assertIn(f"# {line}", content)
            for name, explanation in override.patches:
                self.assertIn(
                    f'"//{setup_workspace.WORKSPACE_PATCHES_DIR}:{override.module}/{name}",',
                    content,
                )
                for line in explanation.splitlines():
                    self.assertIn(f"# {line}", content)

    def test_render_module_overrides_includes_extra_pins(self):
        content = setup_workspace.render_module_overrides()
        for name, version in setup_workspace.EXTRA_ROOT_PINS:
            self.assertIn(f'bazel_dep(name = "{name}", version = "{version}")', content)
        self.assertEqual(
            content.count("single_version_override("),
            len(setup_workspace.MODULE_OVERRIDES),
        )

    def test_render_qt_deps_pins_every_module(self):
        content = setup_workspace.render_qt_deps()
        for name in setup_workspace.QT_MODULES:
            self.assertIn(
                f'bazel_dep(name = "{name}", version = "{setup_workspace.QT_VERSION}")',
                content,
            )
        self.assertNotIn("rules_qt", content)

    def test_copy_override_patches_copies_all_listed_files(self):
        written = setup_workspace.copy_override_patches(self.repo_root, self.workspace)
        expected_dir = self.workspace / setup_workspace.WORKSPACE_PATCHES_DIR
        self.assertEqual(
            sorted(str(p.relative_to(expected_dir)) for p in written),
            sorted(setup_workspace.override_patch_paths()),
        )
        for rel in setup_workspace.override_patch_paths():
            dst = expected_dir / rel
            self.assertTrue(dst.is_file())
            self.assertEqual(dst.read_text(), f"--- {rel}\n")

    def test_copy_override_patches_raises_when_a_patch_is_missing(self):
        missing = setup_workspace.override_patch_paths()[0]
        (self.src_dir / missing).unlink()
        with self.assertRaises(FileNotFoundError) as ctx:
            setup_workspace.copy_override_patches(self.repo_root, self.workspace)
        self.assertIn(missing, str(ctx.exception))

    def test_render_patches_build_file_exports_each_file(self):
        content = setup_workspace.render_patches_build_file(["fmt.patch", "llvm/a.patch"])
        self.assertIn("exports_files([", content)
        self.assertIn('    "fmt.patch",', content)
        self.assertIn('    "llvm/a.patch",', content)

    def test_checked_in_patches_match_manifest(self):
        # Guard against MODULE_OVERRIDES drifting from tools/ci/patches/.
        real_root = Path(__file__).parents[2]
        real_dir = real_root / setup_workspace.PATCHES_SOURCE_DIR
        if not real_dir.is_dir():
            self.skipTest(f"{real_dir} not available in this test environment")
        on_disk = sorted(
            str(p.relative_to(real_dir)) for p in real_dir.glob("*/*.patch")
        )
        listed = sorted(setup_workspace.override_patch_paths())
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

    def test_ros_is_always_discarded(self):
        self.write_module_bazel(
            "ros",
            "lyrical.2026-06-08",
            deps=[("pkg_a", "1.0.0"), ("rosdistro", "lyrical.2026-06-08")],
        )
        self.write_module_bazel("pkg_a", "1.0.0")
        result = setup_workspace.calculate_packages_for_variant(
            self.module_dir, "ros", "lyrical.2026-06-08")
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

    def test_uses_overridden_versions_during_traversal(self):
        # pkg_a@1.0.0 depends on pkg_b@1.0.0 (which had a dep on pkg_old),
        # but pkg_b is overridden to 1.0.1 (which dropped pkg_old and added pkg_new).
        self.write_module_bazel("pkg_a", "1.0.0", deps=[("pkg_b", "1.0.0")])
        self.write_module_bazel("pkg_b", "1.0.0", deps=[("pkg_old", "1.0.0")])
        self.write_module_bazel("pkg_b", "1.0.1", deps=[("pkg_new", "1.0.0")])
        self.write_module_bazel("pkg_old", "1.0.0")
        self.write_module_bazel("pkg_new", "1.0.0")
        result = setup_workspace.calculate_packages_for_variant(
            self.module_dir, "pkg_a", "1.0.0", overrides={"pkg_b": "1.0.1"}
        )
        self.assertEqual(result, ["pkg_a", "pkg_b", "pkg_new"])

    def test_allowed_packages_skips_removed_dependencies(self):
        self.write_module_bazel(
            "pkg_a", "1.0.0", deps=[("pkg_b", "1.0.0"), ("pkg_removed", "1.0.0")]
        )
        self.write_module_bazel("pkg_b", "1.0.0")
        self.write_module_bazel("pkg_removed", "1.0.0")
        result = setup_workspace.calculate_packages_for_variant(
            self.module_dir, "pkg_a", "1.0.0", allowed_packages={"pkg_a", "pkg_b"}
        )
        self.assertEqual(result, ["pkg_a", "pkg_b"])


if __name__ == "__main__":
    unittest.main()


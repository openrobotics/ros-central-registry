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
        self.assertIn("common:ci --repo_contents_cache=", content)

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

    def test_macos_test_sandbox_options(self):
        content = setup_workspace.render_bazelrc("lyrical", "", "/tmp")
        self.assertIn("test --sandbox_default_allow_network=false", content)
        self.assertIn("test:macos --local_test_jobs=1", content)
        self.assertIn("test:macos --strategy=TestRunner=standalone", content)

    def test_runfile_links_disabled_everywhere(self):
        content = setup_workspace.render_bazelrc("lyrical", "", "/tmp")
        self.assertIn("common --nobuild_runfile_links\n", content)
        self.assertNotIn("common:ci --nobuild_runfile_links", content)

    def test_action_env_pinned_across_bazel_versions(self):
        content = setup_workspace.render_bazelrc("lyrical", "", "/tmp")
        self.assertIn("common --action_env=LC_CTYPE=C.UTF-8", content)
        self.assertIn("common --host_action_env=LC_CTYPE=C.UTF-8", content)
        for os_name in ("linux", "macos"):
            self.assertIn(
                f"common:{os_name} --action_env=PATH=/bin:/usr/bin:/usr/local/bin", content
            )
            self.assertIn(
                f"common:{os_name} --host_action_env=PATH=/bin:/usr/bin:/usr/local/bin", content
            )

    def test_ci_memory_options(self):
        content = setup_workspace.render_bazelrc("lyrical", "", "/tmp")
        self.assertIn("startup --host_jvm_args=-XX:MaxRAMPercentage=50.0", content)
        self.assertIn("build:ci --jobs=4", content)
        self.assertIn("build:ci --discard_analysis_cache", content)

    def test_portable_and_sanitizer_configs(self):
        content = setup_workspace.render_bazelrc("lyrical", "", "/tmp")
        self.assertIn("build:portable --@rosdistro//:rmw=rmw_cyclonedds_cpp", content)
        self.assertIn("build:portable --dynamic_mode=off", content)
        self.assertIn("build:portable --per_file_copt=\\.pb\\.cc$@-O3", content)
        for san in ("asan", "msan", "tsan", "ubsan", "rtsan"):
            self.assertIn(f"common:{san} --@llvm//config:{san}", content)
            self.assertIn(f"test:{san} --test_tag_filters=-no{san}", content)
        self.assertIn("common:fuzztest --config=asan", content)


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


class TestRenderBazelignore(unittest.TestCase):

    def test_ignores_internal_tooling_and_runtime_dirs(self):
        content = setup_workspace.render_bazelignore()
        lines = content.splitlines()
        self.assertEqual(
            lines,
            [
                ".package_manifest",
                ".pristine_upstream",
                ".rebase_conflicts",
                ".ros",
                ".vendor_manifest",
                ".vendor_snapshot",
            ],
        )
        self.assertTrue(content.endswith("\n"))


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

    def test_all_variant_renders_as_ros_underlay(self):
        content = setup_workspace.render_underlay_build_file(["all", "core"])
        self.assertNotIn('name = "all",', content)
        self.assertIn('name = "ros",', content)
        self.assertIn('deps = ["@ros//:ament_package"],', content)
        self.assertIn('name = "core",', content)
        self.assertEqual(content.count("ament_underlay("), 2)


class TestQtDeps(unittest.TestCase):

    def test_render_qt_deps_pins_every_module(self):
        content = setup_workspace.render_qt_deps()
        for name in setup_workspace.QT_MODULES:
            self.assertIn(
                f'bazel_dep(name = "{name}", version = "{setup_workspace.QT_VERSION}")',
                content,
            )
        self.assertNotIn("rules_qt", content)


class TestCuda(unittest.TestCase):

    def test_render_cuda_toolkit_configures_redist_in_root(self):
        content = setup_workspace.render_cuda_toolkit()
        self.assertIn('use_extension("@rules_cuda//cuda:extensions.bzl", "toolchain")', content)
        self.assertIn(f'version = "{setup_workspace.CUDA_REDIST_VERSION}"', content)
        self.assertIn('cuda.toolkit(name = "cuda")', content)
        self.assertIn('use_repo(cuda, "cuda")', content)
        for component in setup_workspace.CUDA_REDIST_COMPONENTS:
            self.assertIn(f'"{component}",', content)

    def test_cuda_is_opt_in(self):
        content = setup_workspace.render_bazelrc("lyrical", "", "/tmp")
        self.assertIn("build --@rules_cuda//cuda:enable=False", content)
        self.assertIn("build:cuda --@rules_cuda//cuda:enable=True", content)
        self.assertIn("build:cuda --@rules_cuda//cuda:archs=sm_90", content)
        self.assertIn("build:cuda --@rules_cuda//cuda:copts=--cuda-include-ptx=sm_90", content)
        self.assertIn("build --@rules_cuda//cuda:compiler=clang", content)


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


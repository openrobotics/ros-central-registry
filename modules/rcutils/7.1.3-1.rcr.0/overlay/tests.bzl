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

"""Generates rcutils' test/test_*.{cpp,c} cc_test targets."""

load("@rosdistro//cc:defs.bzl", "ros_local_defines")
load("@rules_cc//cc:defs.bzl", "cc_binary", "cc_test")
load("@rules_shell//shell:sh_test.bzl", "sh_test")

def rcutils_cc_tests(tests, memory_tools_tests):
    """Generates rcutils' test/test_*.{cpp,c} cc_test targets.

    Tests named in memory_tools_tests exercise osrf_testing_tools_cpp's
    memory-tools interposition checks and need to share the exact loaded
    :memory_tools_interpose instance (not a separately linked static copy)
    -- see the comment on memory_tools_wrapper_script.sh for why that means
    running through a wrapper rather than being a plain cc_test.

    Args:
        tests: dict of (name, src) -> env, as in rcutils' BUILD.bazel.
        memory_tools_tests: names (a subset of tests' keys) that need
            osrf_testing_tools_cpp's memory-tools interposition.
    """
    for (name, src), env in tests.items():
        needs_memory_tools = name in memory_tools_tests

        # Skip test_time on macOS because mimick's clock_gettime mocking crashes on ARM64 macOS due to system protection.
        target_compatible_with = select({
            "@platforms//os:osx": ["@platforms//:incompatible"],
            "//conditions:default": [],
        }) if name == "test_time" else []

        common_kwargs = dict(
            srcs = [
                "test/allocator_testing_utils.h",
                "test/dummy_shared_library/dummy_shared_library.h",
                "test/locate_test_assets.h",
                "test/mocking_utils/filesystem.hpp",
                "test/mocking_utils/patch.hpp",
                "test/mocking_utils/remove_noexcept.hpp",
                "test/time_bomb_allocator_testing_utils.h",
            ] + ["test/{}".format(src)],
            data = [
                "test/dummy_folder/dummy.dummy",
                "test/dummy_folder_with_subdir/dummy-subfolder/dummy-subfolder/dummy.dummy",
                "test/dummy_folder_with_subdir/dummy-subfolder/dummy.dummy",
                "test/dummy_folder_with_subdir/dummy.dummy",
                "test/dummy_readable_file.txt",
                "test/dummy_readable_writable_file.txt",
                "test/dummy_shared_library/dummy_shared_library.c",
                "test/dummy_shared_library/dummy_shared_library.h",
            ] + [":file_with_space"],
            dynamic_deps = [":rcutils"] + (
                ["@osrf_testing_tools_cpp//:memory_tools_interpose"] if needs_memory_tools else []
            ),
            env = {} if needs_memory_tools else env,
            local_defines = ros_local_defines() + [
                # GitHub Actions runners restrict what /tmp can be used for.
                # $(TMPDIR) is a Make variable set via --define=TMPDIR=...
                # (see workspace/.bazelrc and tools/ci/setup_workspace.py),
                # resolved from $RUNNER_TEMP/$TMPDIR with a /tmp fallback for
                # local use.
                "BUILD_DIR=\\\"$(TMPDIR)\\\"",
            ],
            target_compatible_with = target_compatible_with,
            deps = [
                ":rcutils_library",
                "@rosdistro//cc:googletest",
                "@osrf_testing_tools_cpp//:memory_tools",
                "@rosdistro//cc:mimick",
                "@rules_cc//cc/runfiles",
            ],
        )

        if needs_memory_tools:
            cc_binary(
                name = name + "_bin",
                testonly = True,
                tags = ["manual"],
                **common_kwargs
            )
        else:
            cc_test(
                name = name,
                **common_kwargs
            )

        if needs_memory_tools:
            sh_test(
                name = name,
                srcs = [":memory_tools_wrapper"],
                args = [
                    "$(rlocationpath :{}_bin)".format(name),
                    "$(rlocationpath @osrf_testing_tools_cpp//:memory_tools_interpose)",
                ],
                data = [
                    ":{}_bin".format(name),
                    "@bazel_tools//tools/bash/runfiles",
                    "@osrf_testing_tools_cpp//:memory_tools_interpose",
                ],
                env = env,
                target_compatible_with = target_compatible_with,
            )

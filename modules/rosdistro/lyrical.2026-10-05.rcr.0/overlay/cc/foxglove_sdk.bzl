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

"""Fetches the prebuilt foxglove-sdk C++ dist consumed by foxglove_bridge.

Upstream's CMakeLists.txt pulls this same release zip via FetchContent and
compiles its C++ wrapper sources (foxglove-sdkConfig.cmake's
foxglove_sdk_add_cpp_library()) against the prebuilt Rust/C libfoxglove.{a,so}.
This mirrors only the (SHARED wrapper, REMOTE_ACCESS=OFF) combination that
foxglove_bridge actually uses: the wrapper statically bundles libfoxglove.a
(the non-remote-access static lib), so consumers link one shared library and
never see the Rust static lib on their own link line.
"""

_VERSION = "0.25.1"

_ARCH_MAP = {
    "amd64": "x86_64",
    "x86_64": "x86_64",
    "arm64": "aarch64",
    "aarch64": "aarch64",
}

# Mirrors the two platforms upstream's CMakeLists.txt itself supports (it hard
# errors on anything else).
_PLATFORMS = {
    ("linux", "x86_64"): struct(
        triple = "x86_64-unknown-linux-gnu",
        sha256 = "0b9d348df3a8e98d2c2cee2360cc9f52e83bb3445044debd771d1b46dc358be4",
    ),
    ("linux", "aarch64"): struct(
        triple = "aarch64-unknown-linux-gnu",
        sha256 = "c70e35c78f0e37f3ba8d0251cd31f353bb10b1fd106200dc6c5f409ed4df1918",
    ),
    ("darwin", "x86_64"): struct(
        triple = "x86_64-apple-darwin",
        sha256 = "3531502efd958be3f9dca06a099c167512dd3006b98ac3eecf8250d376eaa16b",
    ),
    ("darwin", "aarch64"): struct(
        triple = "aarch64-apple-darwin",
        sha256 = "c9dfa5061d72795af2620c2840a85e695b9dacce19475eaec8caf0102c4940ef",
    ),
}

# Single source of truth for the wrapper source filenames is
# foxglove-sources.cmake in the dist; hardcoded here since we only need the
# non-remote-access set (excludes remote_access.cpp) and the dist has no
# machine-readable manifest to read at extraction time.
_WRAPPER_SOURCES = [
    "src/callback_forwarders.cpp",
    "src/channel.cpp",
    "src/connection_graph.cpp",
    "src/context.cpp",
    "src/error.cpp",
    "src/fetch_asset.cpp",
    "src/foxglove.cpp",
    "src/mcap.cpp",
    "src/messages.cpp",
    "src/parameter.cpp",
    "src/parameter_handler.cpp",
    "src/service.cpp",
    "src/system_info.cpp",
    "src/websocket.cpp",
]

_BUILD_FILE_TEMPLATE = """\
load("@rules_cc//cc:defs.bzl", "cc_import", "cc_library")

package(default_visibility = ["//visibility:public"])

# The non-remote-access static Rust/C library (libfoxglove.a). The dist also
# ships libfoxglove.so / libfoxglove.dylib (the remote-access cdylib), which
# no consumer here uses, so it's left unwrapped.
cc_import(
    name = "static",
    static_library = "lib/libfoxglove.a",
)

# The dist ships C++ wrapper *sources* (not a prebuilt C++ lib) -- consumers
# compile them against their own toolchain. Headers are SYSTEM (external repo
# headers are treated as -isystem automatically), so -Wall/-Wextra/-Werror
# consumers don't get warnings from them.
cc_library(
    name = "cpp_wrapper",
    srcs = {srcs} + glob(["src/*.hpp"]),
    hdrs = glob([
        "include/**/*.hpp",
        "include/**/*.h",
    ]),
    copts = ["-std=c++17"],
    includes = ["include"],
    linkopts = select({{
        "@platforms//os:linux": [
            # The Rust standard library needs these directly on older glibc
            # (< 2.34), where they're separate libraries -- see the dist's own
            # foxglove-static-platform-links.cmake for the same set.
            "-lpthread",
            "-ldl",
            "-lm",
        ],
        "@platforms//os:macos": [
            "-Wl,-framework,CoreFoundation",
            "-Wl,-framework,Security",
        ],
        "//conditions:default": [],
    }}),
    deps = [":static"],
)
"""

def _foxglove_sdk_repository_impl(repository_ctx):
    os_name = repository_ctx.os.name.lower()
    if "linux" in os_name:
        os_key = "linux"
    elif "mac" in os_name or "darwin" in os_name:
        os_key = "darwin"
    else:
        fail((
            "foxglove-sdk prebuilt dist v{} is only published for Linux and macOS " +
            "(x86_64/aarch64); host OS is '{}'."
        ).format(_VERSION, os_name))

    arch = _ARCH_MAP.get(repository_ctx.os.arch, repository_ctx.os.arch)
    platform_key = (os_key, arch)
    if platform_key not in _PLATFORMS:
        fail((
            "foxglove-sdk prebuilt dist v{} has no build for {}/{}."
        ).format(_VERSION, os_key, arch))

    platform = _PLATFORMS[platform_key]
    url = (
        "https://github.com/foxglove/foxglove-sdk/releases/download/" +
        "sdk%2Fv{v}/foxglove-v{v}-cpp-{triple}.zip"
    ).format(v = _VERSION, triple = platform.triple)

    repository_ctx.download_and_extract(
        url = url,
        sha256 = platform.sha256,
        stripPrefix = "foxglove",
    )
    repository_ctx.file(
        "BUILD.bazel",
        _BUILD_FILE_TEMPLATE.format(srcs = repr(_WRAPPER_SOURCES)),
    )

foxglove_sdk_repository = repository_rule(
    implementation = _foxglove_sdk_repository_impl,
    doc = "Fetches the prebuilt foxglove-sdk C++ dist for the host platform.",
)

def _foxglove_sdk_extension_impl(_module_ctx):
    foxglove_sdk_repository(name = "foxglove_sdk")

foxglove_sdk = module_extension(
    implementation = _foxglove_sdk_extension_impl,
    doc = "Registers the @foxglove_sdk repo used by rosdistro's cc:foxglove_sdk target.",
)

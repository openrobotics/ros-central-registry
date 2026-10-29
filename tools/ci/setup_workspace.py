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

"""
Setup a Bazel workspace for testing ROS distributions in CI.
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List

from tools.ci.bzlmod_lib import scan_module_for_dependencies
from tools.ci.bzlmod_lib import find_packages_with_newer_versions

VARIANTS = {
    "all": "ros",
    "core": "ros_core",
    "base": "ros_base",
    "desktop": "desktop",
    "desktop_full": "desktop_full",
    "perception": "perception",
    "simulation": "simulation",
}

# LLVM release the hermetic toolchain's libc++/compiler-rt sources are pinned
# to (via llvm.version(...) in the generated MODULE.bazel). Newer libc++
# releases (23.x) dropped transitive standard-library includes that several
# BCR modules we can't patch from rosdistro (fastdds, uncrustify, ...) still
# rely on, so hold at 21.x -- the line hermetic-llvm's (now upstreamed)
# llvm21_third_party_zstd fix targets.
LLVM_VERSION = "21.1.8"


# From-source Qt 6 modules (staged under bcr_staging/modules/, served via the
# bcr_staging registry -- see BAZELRC_TEMPLATE). These replace the prebuilt
# rules_qt binaries.
QT_VERSION = "6.10.2.rcr.0"
QT_MODULES = (
    "qt",
    "qtbase",
    "qtsvg",
    "qtlanguageserver",
    "qtimageformats",
    "qtshadertools",
    "qtdeclarative",
    "qtwebsockets",
    "qtwebchannel",
    "qthttpserver",
    "qtnetworkauth",
    "qtserialport",
    "qtserialbus",
    "qtsensors",
    "qt5compat",
    "qtcharts",
    "qtpositioning",
    "qtlocation",
    "qtconnectivity",
    "qtlottie",
    "qtquicktimeline",
    "qtvirtualkeyboard",
    "qtremoteobjects",
    "qtscxml",
    "qtquick3d",
    "qtquick3dphysics",
    "qtgraphs",
    "qtdatavis3d",
    "qt3d",
    "qtmultimedia",
    "qtspeech",
    "qtwayland",
    "qtwebview",
    "qtgrpc",
    "qttools",
    "qttranslations",
)


def render_qt_deps() -> str:
    """bazel_dep lines for every from-source Qt module."""
    return "".join(
        f'bazel_dep(name = "{name}", version = "{QT_VERSION}")\n' for name in QT_MODULES
    )


# Hermetic CUDA toolkit for @libtorch's (opt-in) CUDA backend and the
# cuda_buffer* packages. rules_cuda only honours cuda.toolkit() and
# cuda.redist_json() tags from the root module, so they can't live in
# rosdistro's MODULE.bazel. The staged rules_cuda (bcr_staging/modules/
# rules_cuda/*/patches/multiplatform_redist.patch) makes this a no-op on macOS
# hosts and maps linux-arm64 to NVIDIA's linux-sbsa redist. Only the redist
# index is fetched eagerly; component archives are fetched lazily, i.e. only
# by builds that use --config=cuda.
CUDA_REDIST_VERSION = "12.8.1"
CUDA_REDIST_COMPONENTS = (
    "cccl",
    "cublas",
    "cudart",
    "cufft",
    "cupti",
    "curand",
    "cusolver",
    "cusparse",
    "nvcc",
    "nvjitlink",
    "nvml",
    "nvrtc",
    "nvtx",
)


def render_cuda_toolkit() -> str:
    """Root-module rules_cuda configuration (see CUDA_REDIST_VERSION)."""
    components = "".join(f'        "{c}",\n' for c in CUDA_REDIST_COMPONENTS)
    return (
        "# Hermetic CUDA toolkit (see tools/ci/setup_workspace.py:CUDA_REDIST_VERSION).\n"
        "# Unused unless a build passes --config=cuda.\n"
        'cuda = use_extension("@rules_cuda//cuda:extensions.bzl", "toolchain")\n'
        "cuda.redist_json(\n"
        '    name = "rules_cuda_redist_json",\n'
        "    components = [\n"
        f"{components}"
        "    ],\n"
        f'    version = "{CUDA_REDIST_VERSION}",\n'
        ")\n"
        'cuda.toolkit(name = "cuda")\n'
        'use_repo(cuda, "cuda")\n'
    )


BAZELRC_TEMPLATE = """# Copyright 2026 Open Source Robotics Foundation, Inc.
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

## STARTUP OPTIONS

# Raise the JVM heap limit from the default 25% of physical RAM (4 GB on
# 16 GB GitHub Actions runners), which is too small to hold the Skyframe
# graph when analyzing large target sets across the distribution.
startup --host_jvm_args=-XX:MaxRAMPercentage=50.0

## COMMON OPTIONS

# This suppresses warnings that bazel emits when two dependencies rely
# on different versions of a single module. This is what allows us to
# load 0.0.0 versions of RCR package and have bazel resolve the correct
# package for the ROS distribution we are using.
common --check_direct_dependencies=off

# This tells Bazel to look locally for RCR modules at the root of this
# project, additional "staged" BCR modules in the bcr_staging folder
# in this workspace, and ultimately at the BCR for the rest.
common --registry=file:///%workspace%/..             \\
       --registry=file:///%workspace%/../bcr_staging \\
       --registry=https://bcr.bazel.build

# If a "vendor" folder is present (see //tools/ci:vendor_modules), read
# vendored module sources from it instead of fetching/extracting them,
# so in-place edits to vendored modules are picked up by the build.
common --vendor_dir=vendor

# This provides read-only access to a shared Bazel remote cache offered
# by Intrinsic. It helps speed up fresh checkouts from upstream.
common --remote_cache=https://storage.googleapis.com/intrinsic-opensource-buildcache
common --remote_upload_local_results=false
common --remote_cache_compression=true

# Critical ROS environment variables needed at test-time.
common --test_env=ROS_DISTRO="{distro}"
common --test_env=ROS_HOME=".ros"
common --test_env=RMW_IMPLEMENTATION="rmw_fastrtps_cpp"
common --test_env=LD_LIBRARY_PATH=lib
common --test_env=DYLD_LIBRARY_PATH=lib
common --test_env=TMPDIR={tmpdir}
common --test_env=QT_QPA_PLATFORM="offscreen"

# Critical ROS environment variables needed at run-time.
common --run_env=ROS_DISTRO="{distro}"
common --run_env=ROS_HOME=".ros"
common --run_env=RMW_IMPLEMENTATION="rmw_fastrtps_cpp"
common --run_env=LD_LIBRARY_PATH=lib
common --run_env=DYLD_LIBRARY_PATH=lib
common --run_env=TMPDIR={tmpdir}
common:linux --run_env=QT_QPA_PLATFORM="xcb"
common:macos --run_env=QT_QPA_PLATFORM="cocoa"
common:windows --run_env=QT_QPA_PLATFORM="windows"

# Propagate select X11 variables through to the test sandbox, so that
# any test that uses the display has access to it.
common --test_env=DISPLAY
common --test_env=XAUTHORITY
common --test_env=WAYLAND_DISPLAY

# Without a console (as under Bazel on Windows) Qt routes qDebug/QTest output
# to OutputDebugString, leaving test.log empty. Force it to stderr/stdout.
common --test_env=QT_FORCE_STDERR_LOGGING=1

# Our approach to message generation works on a per-message dependency
# chain. We need to be able to merge messages into 
common --incompatible_default_to_explicit_init_py

# This restricts the environment variables available to build actions, 
# keeping the build environment more hermetic.
common --incompatible_strict_action_env

# Use a shared cache for bazel builds, which speeds up CI builds.
common --remote_cache=https://storage.googleapis.com/intrinsic-opensource-buildcache
common --remote_cache_compression=true
common --remote_upload_local_results=false

# Don't build runfiles symlink trees for every binary; Bazel still creates
# them when a target is run or tested. Applied everywhere (not just CI):
# the ament_index-shaped runfiles trees are large, and building one per
# binary consumes a lot of inodes for no benefit until the target is run.
common --nobuild_runfile_links

# CI specific performance/reliability tweaks -- safe to use anywhere,
# require no credentials (this is what forks get; see cache_write_config
# below for the part that isn't safe on a fork).
common:ci --http_timeout_scaling=3.0
common:ci --experimental_repository_downloader_retries=10
common:ci --repo_contents_cache=
common:ci --remote_cache_compression=false
common:ci --ui_event_filters=-INFO,-DEBUG
{cache_write_config}

# We support the following variants of ROS distributions. This allows you
# to build or test the entire variant with a --config flag.
{variants}

# Automatically pick configurations for the platform running bazel.
# For example, macos on macos, linux on linux, etc.
common --enable_platform_specific_config

# Stop the profiler from being fatal — even with less build pressure,
# a resource issue shouldn't take down the whole bazel command.
common --noexperimental_collect_system_network_usage

## BUILD OPTIONS

# Just a small amount of compiler optimization leads to signficantly faster
# simulation speeds. Do not remove this unless you absolutely need to.
build --@llvm//config:fastbuild_optimization_mode=O1

# Ensure that we always download all outputs, including the shared libraries
# that are required at runtime for dlopen() calls.
build --remote_download_outputs=all

# Some packages bake a scratch-directory path into compiled test binaries via
# local_defines (e.g. rcutils' BUILD_DIR), which --test_env/--run_env can't
# reach since it's resolved at compile time, not test run-time. Expose the
# same caller-resolved TMPDIR (see above) as a Make variable so those
# local_defines/env attributes can pick it up via $(TMPDIR) substitution.
build --define=TMPDIR={tmpdir}

# Ensure that we use toolchains_llvm instead of the host toolchain.
build --repo_env="BAZEL_DO_NOT_DETECT_CPP_TOOLCHAIN=1"

# Ignore any host-level pip configurations and pull public python dependencies.
build --repo_env="PIP_CONFIG_FILE=/dev/null"

# Our bazel distribution provides conversion utilities for transforming
# ROS messages to .proto files. This prevent protobuf from trying to
# recompile itself in response to environment changes.
build --@protobuf//bazel/toolchains:prefer_prebuilt_protoc

# This tells our hermetic LLVM compiler to stub some GCC functions that
# are used in several places around the ROS Bazel workspace/
build --@llvm//config:experimental_stub_libgcc_s=True

# The workspace builds all C++ universally as C++23 to guarantee a uniform
# language standard and prevent C++ standard-level ABI incompatibilities across
# targets. Set the language standard once for every C++ compile, in both the
# target and exec (host tool) configurations. NEVER specify `-std=c++*` in
# per-target `copts` or `cxxopts` inside `BUILD.bazel` files.
build --cxxopt=-std=c++23
build --host_cxxopt=-std=c++23

# ==============================================================================
# WARNING: PER-FILE C++ STANDARD EXCEPTIONS
# ==============================================================================
# Mixing C++ standards across translation units risks subtle ODR and ABI
# incompatibilities. Do NOT add entries here unless an upstream or third-party
# package uses language or standard-library constructs that were hard-removed in
# C++20/C++23 and cannot be cleanly patched in source. Every exception below
# MUST document the exact symbol/construct and reason it cannot compile as C++23:
#
# 1. @fastdds (eProsima Fast-DDS 3.4.2):
#    Reason: `include/fastdds/utils/collections/impl/node-sizes/FixedSizeQueue.hpp`
#    invokes `std::allocator<T>::construct()` and `std::allocator<T>::destroy()`,
#    which were deprecated in C++17 and removed in C++20 (`libc++` gates them
#    strictly behind `#if _LIBCPP_STD_VER <= 17`).
build --per_file_copt=external/.*fastdds.*@-std=c++17
build --host_per_file_copt=external/.*fastdds.*@-std=c++17
#
# 2. @popf (POPF PDDL planner 0.0.20):
#    Reason: Legacy 2010 C++98/03 codebase (`src/VALfiles/`, `src/popf/`) that
#    heavily relies on `std::auto_ptr`, `std::unary_function`, `std::binary_function`,
#    `std::bind1st`, `std::bind2nd`, `std::ptr_fun`, and `std::mem_fun`, which
#    were removed from `<functional>`/`<memory>` in C++17/C++20.
build --per_file_copt=external/.*popf.*@-std=c++17
build --host_per_file_copt=external/.*popf.*@-std=c++17
#
# 3. @gz-sim (Gazebo Sim 10.5.0):
#    Reason: 31 system plugin headers (`src/systems/*/*.hh`) declare inline
#    `~Plugin() override = default;` while holding `std::unique_ptr<PluginPrivate>`
#    to an incomplete forward-declared PIMPL class. In C++23 (`P2273R3`),
#    `std::unique_ptr::~unique_ptr()` became `constexpr`, forcing eager template
#    instantiation of `std::default_delete<PluginPrivate>` at the class definition
#    point and failing `static_assert(sizeof(_Tp) >= 0)`.
build --per_file_copt=external/.*gz-sim.*@-std=c++20
build --host_per_file_copt=external/.*gz-sim.*@-std=c++20
#
# 4. @libtorch (PyTorch 2.14.1, bcr_staging):
#    Reason: upstream builds with CMAKE_CXX_STANDARD 20 and the staged module
#    reproduces that with LIBTORCH_COPTS = ["-std=gnu++20"] on every @libtorch
#    target (overlay/libtorch_config.bzl), which wins over --cxxopt above.
#    Consumers that only include torch headers (e.g. torch_conversions) still
#    compile as C++23 against the same libc++, so no ABI split.
# ==============================================================================

# ==============================================================================
# GPU / CUDA (opt-in: --config=cuda)
# ==============================================================================
# The default distribution build is CPU-only: @libtorch//:torch degrades to its
# CPU backend and the Linux-only cuda_buffer* packages are skipped as
# incompatible. --config=cuda compiles CUDA with the hermetic @llvm Clang (not
# nvcc) against the hash-pinned CUDA redistributables configured in
# MODULE.bazel (see tools/ci/setup_workspace.py:CUDA_REDIST_VERSION). No GPU or
# driver is needed to build; binaries dlopen libcuda.so.1 at run time.
build --repo_env=CUDA_COMPILER_USE_CC_TOOLCHAIN=true
build --@rules_cuda//cuda:compiler=clang
build --@rules_cuda//cuda:enable=False
build:cuda --@rules_cuda//cuda:enable=True
# The CUDA headers reject libc++ on x86 (crt/host_defines.h) unless this is
# defined; the whole stack is Clang + libc++, so there is no ABI mix.
build:cuda --@rules_cuda//cuda:copts=-D_ALLOW_UNSUPPORTED_LIBCPP
# Clang can't detect the CUDA version from the nvcc redist (no cuda.h there),
# so pin CUDA 12.8's PTX ISA (8.7). Update together with CUDA_REDIST_VERSION.
build:cuda --@rules_cuda//cuda:copts=--cuda-feature=+ptx87
build:cuda --@rules_cuda//cuda:copts=-Wno-unknown-cuda-version
# Hopper (sm_90) cubins plus sm_90 PTX for newer GPUs to JIT. Override
# --@rules_cuda//cuda:archs in user.bazelrc for your own GPU (e.g. sm_89), or
# list several (sm_80;sm_86;sm_89;sm_90) for a portable build.
build:cuda --@rules_cuda//cuda:archs=sm_90
build:cuda --@rules_cuda//cuda:copts=--no-cuda-include-ptx=all
build:cuda --@rules_cuda//cuda:copts=--cuda-include-ptx=sm_90
build:cuda --@rules_cuda//cuda:copts=-Xcuda-fatbinary
build:cuda --@rules_cuda//cuda:copts=--compress-all
# ==============================================================================

# rules_bison and rules_m4 ship a gnulib Windows configuration written for MSVC
# (#pragma include_alias, mode_t/pid_t/ssize_t/off_t macro overrides, and
# omitted C99 extern-inline instantiation units). When cross-compiling Linux
# targets (xkbcommon) from a Windows host, bison and m4 are compiled for the
# Windows exec platform with MinGW clang; pass the flags needed for gnulib's
# MSVC config to compile and link under MinGW clang.
build:windows --host_per_file_copt=external/rules_(bison|m4)[^/]*/.*@-fms-extensions,-D_MODE_T_,-D_PID_T_,-D_SSIZE_T_DEFINED,-D_GL_M4_SYS_TYPES_H,-D_GL_EXTERN_INLINE_STDHEADER_BUG
build:windows --per_file_copt=external/rules_(bison|m4)[^/]*/.*@-fms-extensions,-D_MODE_T_,-D_PID_T_,-D_SSIZE_T_DEFINED,-D_GL_M4_SYS_TYPES_H,-D_GL_EXTERN_INLINE_STDHEADER_BUG

# ld64's two-level namespace requires every undefined symbol in a .dylib to
# be resolvable among the libraries passed directly to its link command.
# Our rosidl-generated cc_shared_library targets commonly need symbols from
# libraries that are several dynamic_deps hops away, which the ELF loader on
# Linux resolves transitively at process load time with no issue. On Darwin
# we fall back to flat-namespace symbol lookup at load time instead.
build:macos --linkopt=-Wl,-undefined,dynamic_lookup
build:macos --host_linkopt=-Wl,-undefined,dynamic_lookup

# Native Linux builds target glibc 2.34 on the host's CPU (see
# platforms/BUILD.bazel). An unpinned Linux build carries
# `libc:unconstrained`, which the @llvm toolchain maps to its 2.28 floor --
# too old for the from-source Qt modules. macOS and Windows need no pin.
build:linux --platforms=//platforms:linux
# Tests run on the first execution platform matching *all* of the target
# platform's constraints (@bazel_tools//tools/test:default_test_toolchain_type).
# The auto-detected host platform doesn't carry the libc:gnu.2.34 pin, so
# without this every test fails with "No matching toolchain found".
build:linux --extra_execution_platforms=//platforms:linux

# Our hermetic macOS toolchain passes clang's SDK header search path via
# "-isysroot <execroot-relative path>" (see the `llvm` module's
# toolchain/args/macos:macos_sdk_sysroot, which needs -isysroot specifically
# so Clang's Darwin driver resolves framework headers -- it checks -isysroot
# before --sysroot). That relative path only resolves when the compiler's
# current directory is the exec root. Cargo build scripts run with their
# current directory changed to CARGO_MANIFEST_DIR instead, so any cc-rs
# invocation that inherits these flags (e.g. the `ring` crate's build script,
# used by zenoh's TLS transport) fails with "file not found" for SDK headers
# like TargetConditionals.h. rules_rust/rules_rs have a purpose-built escape
# hatch for exactly this: symlink the exec root's top-level entries into
# CARGO_MANIFEST_DIR so exec-root-relative paths keep resolving.
build:macos --@@rules_rs++rules_rust+rules_rust//cargo/settings:experimental_symlink_execroot=true

# The Apple SDK framework directories contain module.modulemap files that
# activate Clang's implicit module system once a Frameworks directory is in
# scope (as it now implicitly is, via --sysroot). Libraries like abseil-cpp
# include CoreFoundation headers without declaring a module dependency, which
# the module system rejects. -fno-implicit-module-maps is a clang driver flag
# (not a cc1 flag); pass it directly without -Xclang.
build:macos --copt=-fno-implicit-module-maps
build:macos --host_copt=-fno-implicit-module-maps

# Apple SDK framework headers use the CF_ENUM() macro, which expands to a forward
# enum declaration inside a typedef -- a Clang extension that Clang supports but
# warns about starting with Clang 22 (-Welaborated-enum-base). Suppress it so
# CoreFoundation/CFBase.h and friends compile cleanly with the hermetic toolchain.
build:macos --copt=-Wno-elaborated-enum-base
build:macos --host_copt=-Wno-elaborated-enum-base

# Pin the action environment that --incompatible_strict_action_env produces.
# Bazel 10 changed its defaults (LC_CTYPE=C.UTF-8 on all OSes, plus
# PATH=/bin:/usr/bin:/sbin:/usr/sbin vs. /bin:/usr/bin:/usr/local/bin on Unix
# in Bazel 9). The environment is part of every action's cache key, so without
# this pin the 9.x and last_rc CI jobs cannot share a disk cache. Exec-config
# (tool) actions take --host_action_env, so pin both.
common --action_env=LC_CTYPE=C.UTF-8
common --host_action_env=LC_CTYPE=C.UTF-8
common:linux --action_env=PATH=/bin:/usr/bin:/usr/local/bin
common:linux --host_action_env=PATH=/bin:/usr/bin:/usr/local/bin
common:macos --action_env=PATH=/bin:/usr/bin:/usr/local/bin
common:macos --host_action_env=PATH=/bin:/usr/bin:/usr/local/bin

# Fix memory pressure in CI workers, which leads to OOM errors.
build:ci --jobs=4
build:ci --discard_analysis_cache

## TEST OPTIONS

# This restricts our test sandboxes from accessing the network, which is
# important if you want to prevent destructive interference between tests.
# Note: this only applies to developer builds because github runners are
#       in proceswrapper-sandbox and run 1 test at a time.
test --sandbox_default_allow_network=false

# Without linux-sandbox's isolated loopback namespace, CycloneDDS on macOS
# selects en0 over lo0 and sees IFF_MULTICAST on lo0, so it tries UDP multicast
# discovery (blocked on macOS CI VMs) instead of its automatic loopback unicast
# fallback. Pin CycloneDDS to 127.0.0.1 with multicast="false" so q_init.c
# applies the same loopback unicast peer discovery as inside linux-sandbox.
# The whole flag is single-quoted: .bazelrc lines are shell-tokenized, so the
# unquoted space inside <NetworkInterface ...> would otherwise split it and
# leak "address=..." / "multicast=..." onto the command line as target patterns.
test:macos '--test_env=CYCLONEDDS_URI=<CycloneDDS><Domain><General><Interfaces><NetworkInterface address="127.0.0.1" multicast="false"/></Interfaces></General></Domain></CycloneDDS>'

# Don't allow a flaky test to fail the entire run.
test:ci --flaky_test_attempts=3

# Limit local test concurrency on CI to prevent resource starvation, as
# well as destructive interference between tests.
test:ci --local_test_jobs=1
test:ci --test_strategy=exclusive
test:ci --strategy=TestRunner=standalone

## STATIC compilation

build:portable --@rosdistro//:rmw=rmw_cyclonedds_cpp
build:portable -c opt
build:portable --dynamic_mode=off
build:portable --strip=always
build:portable --copt=-Oz
build:portable --copt=-ffunction-sections
build:portable --copt=-fdata-sections
build:portable --copt=-fno-asynchronous-unwind-tables
build:portable --features=no_gdb_index
build:portable --features=thin_lto
build:portable --per_file_copt=\\.pb\\.cc$@-O3

## SANITIZER OPTIONS

# Address sanitizer
common:asan --strip=never
common:asan --@llvm//config:asan
common:asan --copt -O0
common:asan --copt -g
common:asan --copt -fno-omit-frame-pointer
test:asan --test_tag_filters=-noasan

# Memory sanitizer
common:msan --strip=never
common:msan --@llvm//config:msan
common:msan --copt -O0
common:msan --copt -g
common:msan --copt -fno-omit-frame-pointer
test:msan --test_tag_filters=-nomsan

# Thread sanitizer
common:tsan --strip=never
common:tsan --@llvm//config:tsan
common:tsan --copt -O0
common:tsan --copt -g
common:tsan --copt -fno-omit-frame-pointer
test:tsan --test_tag_filters=-notsan

# Undefined Behavior sanitizer
common:ubsan --strip=never
common:ubsan --@llvm//config:ubsan
common:ubsan --copt -O0
common:ubsan --copt -g
common:ubsan --copt -fno-omit-frame-pointer
test:ubsan --test_tag_filters=-noubsan

# Real-time sanitizer
common:rtsan --strip=never
common:rtsan --@llvm//config:rtsan
common:rtsan --copt -O0
common:rtsan --copt -g
common:rtsan --copt -fno-omit-frame-pointer
test:rtsan --test_tag_filters=-nortsan

# Fuzzing
common:fuzztest --config=asan
common:fuzztest --config=ubsan
common:fuzztest --dynamic_mode=off
common:fuzztest --copt=-fsanitize-coverage=inline-8bit-counters,trace-cmp,pc-table
common:fuzztest --@llvm//config:sanitizer_strip_foreign_source_paths
test:fuzztest --test_tag_filters=-nofuzztest
"""


def render_bazelrc(distro: str, variants: str, tmpdir: str, remote_cache_write: bool = False) -> str:
    """
    Fill in BAZELRC_TEMPLATE. remote_cache_write gates the two flags that
    require GCP credentials (--remote_upload_local_results=true and
    --google_default_credentials) -- see --remote-cache-write's help text.
    """
    cache_write_config = (
        "common:ci --remote_upload_local_results=true\n"
        "common:ci --google_default_credentials"
    ) if remote_cache_write else ""
    return BAZELRC_TEMPLATE.format(
        distro=distro, variants=variants, tmpdir=tmpdir, cache_write_config=cache_write_config
    )


def get_copyright_header() -> str:
    return """# Copyright 2026 Open Source Robotics Foundation, Inc.
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
"""

# Directory (and package) of the generated workspace holding PLATFORMS_BUILD.
WORKSPACE_PLATFORMS_DIR = "platforms"

PLATFORMS_BUILD = """# Native Linux platform.
#
# Inherits the auto-detected OS/CPU from @platforms//host (so one target covers
# both amd64 and arm64) and pins the glibc version. Without this, an unpinned
# Linux build carries `libc:unconstrained`, which the @llvm toolchain maps to
# its 2.28 floor, and the from-source Qt modules need newer glibc symbols.
# Selected via `build:linux --platforms=//platforms:linux` in .bazelrc
# (auto-applied on Linux by --enable_platform_specific_config); it is
# equivalent to @llvm//platforms:linux_<host-arch>_gnu.2.34.
#
# macOS and Windows need no counterpart: all other @llvm constraint settings
# have defaults, so @platforms//host already resolves correctly there.

platform(
    name = "linux",
    constraint_values = [
        "@llvm//constraints/libc:gnu.2.34",
    ],
    parents = ["@platforms//host"],
    visibility = ["//visibility:public"],
)
"""


def render_platforms_build_file() -> str:
    """BUILD.bazel content for <workspace>/platforms/ (glibc-pinned Linux)."""
    return get_copyright_header() + "\n" + PLATFORMS_BUILD


# Internal tooling and runtime directories under <workspace>/ that are not
# Bazel packages (snapshots/manifests from vendor_modules, create_patch, and
# rebase_module, plus ROS_HOME). Listing them in .bazelignore keeps `bazel
# query //...` and IDE Bazel extensions from trying to parse BUILD.bazel files
# inside vendored/upstream snapshots as main-workspace packages.
BAZELIGNORE_DIRS = (
    ".package_manifest",
    ".pristine_upstream",
    ".rebase_conflicts",
    ".ros",
    ".vendor_manifest",
    ".vendor_snapshot",
)


def render_bazelignore() -> str:
    """Content for <workspace>/.bazelignore."""
    return "\n".join(BAZELIGNORE_DIRS) + "\n"


def render_underlay_build_file(variant_names: List[str]) -> str:
    """BUILD.bazel content declaring one `ament_underlay` tarball per variant.

    `bazel build //:desktop_full` (etc.) produces `<variant>.tar.gz`: an
    isolated-layout ROS underlay containing `<pkg>/{bin,lib,include,share}` for
    every package reachable from the variant's `:ament_package`.
    """
    lines = [
        'load("@rosdistro//ament:defs.bzl", "ament_underlay")',
        "",
        'package(default_visibility = ["//visibility:public"])',
        "",
    ]
    underlays = sorted(
        ("ros" if name == "all" else name, VARIANTS.get(name, name))
        for name in variant_names
    )
    for target_name, package in underlays:
        lines += [
            "ament_underlay(",
            f'    name = "{target_name}",',
            f'    deps = ["@{package}//:ament_package"],',
            ")",
            "",
        ]
    return "\n".join(lines)


def calculate_packages_for_variant(
    module_dir: Path,
    start_name: str,
    start_version: str,
    overrides: Dict[str, str] | None = None,
    allowed_packages: set | None = None,
) -> List[str]:
    """
    Performs a BFS traversal starting from the given module name and version to collect
    all transitive dependencies. If `overrides` is provided, uses the overridden
    version of any package in the traversal rather than the older version
    pinned in a parent's MODULE.bazel. If `allowed_packages` is provided,
    skips any dependency not in that set (e.g. a package removed from the
    distro that an un-updated downstream package still references).
    """
    overrides = overrides or {}
    effective_start_version = overrides.get(start_name, start_version)
    visited = set()
    queue = [(start_name, module_dir / start_name / effective_start_version / 'MODULE.bazel')]
    while queue:
        current_name, current_file = queue.pop(0)
        if current_name in visited:
            continue
        visited.add(current_name)
        if not current_file.exists():
            continue
        with open(current_file, "r") as f:
            content = f.read()
            deps = re.findall(
                r'bazel_dep\(name\s*=\s*"([^"]+)"\s*,\s*version\s*=\s*"([^"]+)"\)',
                content,
            )
            for next_name, next_version in deps:
                if allowed_packages is not None and next_name not in allowed_packages:
                    continue
                effective_next_version = overrides.get(next_name, next_version)
                next_file = module_dir / next_name / effective_next_version / 'MODULE.bazel'
                if next_file.exists():
                    if next_name not in visited:
                        queue.append((next_name, next_file))
    visited.discard("ros")
    visited.discard("rosdistro")
    return sorted(list(visited))

def main():
    parser = argparse.ArgumentParser(
        description="Setup a Bazel workspace for testing ROS distributions in CI."
    )
    parser.add_argument(
        "--release",
        required=True,
        help="Bazel 'ros' module release version, e.g. lyrical.2026-06-08.rcr.1",
    )
    parser.add_argument(
        "--workspace-dir",
        type=Path,
        default=Path("workspace"),
        help="Directory to create the workspace in",
    )
    parser.add_argument(
        "--tmpdir",
        default="",
        help="Directory to pin TMPDIR to for build/test/run actions, e.g. "
             "$RUNNER_TEMP. Falls back to $TMPDIR, then /tmp, if not given.",
    )
    parser.add_argument(
        "--remote-cache-write",
        action="store_true",
        help="Enable writing to the shared remote build cache under "
             "--config ci (requires GCP credentials for the "
             "intrinsic-opensource-buildcache bucket, e.g. via "
             "google-github-actions/auth in the upstream repo's own CI). "
             "Leave this off anywhere else -- forks don't have those "
             "credentials, and attempting to write without them fails the "
             "build rather than just skipping the write. The default "
             "(non-ci) config already gives every caller anonymous "
             "read-only access to the cache, so this only affects writes.",
    )
    args = parser.parse_args()

    tmpdir = args.tmpdir or os.environ.get("TMPDIR") or "/tmp"

    # Locate directories
    workspace_root = Path(
        os.environ.get("BUILD_WORKSPACE_DIRECTORY", ".")
    ).resolve()
    modules_dir = workspace_root / "modules"
    ros_module_dir = modules_dir / "ros" / args.release

    if not ros_module_dir.exists():
        print(f"Error: ROS release module path {ros_module_dir} does not exist.", file=sys.stderr)
        sys.exit(1)

    # Scan release for dependencies
    print(f"Scanning ROS release '{args.release}' for packages...")
    packages = scan_module_for_dependencies(
        ros_module_dir / "MODULE.bazel", modules_dir
    )
    # Add ros and rosdistro to match the behavior of workspace_setup.py
    packages.setdefault("ros", args.release)
    packages.setdefault("rosdistro", args.release)
    print(f"Found {len(packages)} RCR packages in release.")

    # Some packages may already have a newer patch published (e.g. a
    # developer's create_patch PR merged since this release was cut) than
    # what this release pins. Override those to the latest available
    # version so this workspace is never stale -- this is what keeps
    # concurrent per-package patches from colliding on the same next
    # version number (see docs/source/design_choices.rst).
    override_candidates = {k: v for k, v in packages.items() if k not in ("ros")}
    overrides = find_packages_with_newer_versions(override_candidates, modules_dir)
    for name, latest_version in sorted(overrides.items()):
        print(
            f"OVERRIDE: {name} pinned at {packages[name]} by release "
            f"{args.release}, but a newer patch {latest_version} already "
            f"exists -- overriding workspace to use it."
        )
    if overrides:
        print(f"Overrode {len(overrides)} package(s) to newer available patches.")

    # Detect variants
    allowed_packages = set(packages.keys())
    variants: Dict[str, List[str]] = {}
    for variant_name, variant_package in VARIANTS.items():
        if variant_package not in packages:
            print(f"Warning: Variant package {variant_package} not found in release.")
            continue
        variants[variant_name] = calculate_packages_for_variant(
            modules_dir,
            variant_package,
            packages[variant_package],
            overrides=overrides,
            allowed_packages=allowed_packages,
        )
        print(f"  {variant_name}: {len(variants[variant_name])} packages")

    # Create workspace directory
    target_workspace = (workspace_root / args.workspace_dir).resolve()
    target_workspace.mkdir(parents=True, exist_ok=True)
    print(f"Creating workspace at {target_workspace}...")

    # Write BUILD.bazel
    with open(target_workspace / "BUILD.bazel", "w") as f:
        f.write(get_copyright_header())
        f.write(render_underlay_build_file(sorted(variants.keys())))

    # Write platforms/ (glibc-pinned Linux platform, see PLATFORMS_BUILD).
    platforms_dir = target_workspace / WORKSPACE_PLATFORMS_DIR
    platforms_dir.mkdir(parents=True, exist_ok=True)
    with open(platforms_dir / "BUILD.bazel", "w") as f:
        f.write(render_platforms_build_file())

    # Write ros-<variant>.txt files
    for variant_name, variant_packages in variants.items():
        with open(target_workspace / f"ros-{variant_name}.txt", "w") as f:
            f.write("\n".join([f"@{p}//..." for p in variant_packages]))

    # Write MODULE.bazel
    with open(target_workspace / "MODULE.bazel", "w") as f:
        f.write(get_copyright_header())
        f.write("""module(
    name = "rcr-workspace",
)

# BCR deps

bazel_dep(name = "llvm", version = "0.8.25.rcr.0")
bazel_dep(name = "platforms", version = "1.1.0")
bazel_dep(name = "protobuf", version = "36.2")
bazel_dep(name = "rules_cc", version = "0.2.26.rcr.0")
bazel_dep(name = "rules_cuda", version = "0.3.0.rcr.0")
bazel_dep(name = "rules_go", version = "0.60.0")
bazel_dep(name = "rules_python", version = "2.4.5")
bazel_dep(name = "rules_rs", version = "0.1.0")
bazel_dep(name = "rules_shell", version = "0.8.0")

# Patched third-party modules (zlib_shared, LINKABLE_MORE_THAN_ONCE tags, the
# hermetic LLVM fixes, Windows/MinGW and macOS fixes, ...) are staged under
# bcr_staging/modules/ and pinned by rosdistro's MODULE.bazel, so every
# consumer -- not just this generated root -- picks them up. Do not add
# single_version_override patches here: they only apply to the root module.

## QT DEPS (from source, see tools/ci/setup_workspace.py:QT_MODULES)

""")
        f.write(render_qt_deps())
        f.write("""
## RCR deps

""")
        f.write(f'bazel_dep(name = "ros", version = "{args.release}")\n\n')
        for name in sorted(packages.keys()):
            if name != "ros":
                f.write(f'bazel_dep(name = "{name}", version = "{packages[name]}")\n')

        if overrides:
            f.write("\n## OVERRIDES (packages with newer patches than the pinned release)\n\n")
            for name in sorted(overrides.keys()):
                f.write(
                    f'single_version_override(module_name = "{name}", '
                    f'version = "{overrides[name]}")\n'
                )

        f.write("""
## BOOTSTRAP

# Register our hermetic compiler (clang)
register_toolchains("@llvm//toolchain:all")

# Extend the hermetic macOS SDK sysroot (@llvm//extensions:osx.bzl) with the
# frameworks our dependencies needed on OSX.
# WebKit and JavaScriptCore (QtWebView's macOS plugin) are symlinks into
# System/Cryptexes/OS in the macOS 26 SDK; the staged llvm module's
# osx_cryptex_frameworks.patch (bcr_staging/modules/llvm/*/patches/)
# extracts the link targets too, so they resolve (the darwin sandbox rejects
# dangling links whenever macOS is the execution platform).
osx = use_extension("@llvm//extensions:osx.bzl", "osx")
osx.frameworks(
    names = [
        "AVFAudio",
        "AVFoundation",
        "AVRouting",
        "Accelerate",
        "AppKit",
        "ApplicationServices",
        "AudioToolbox",
        "AudioUnit",
        "CFNetwork",
        "Carbon",
        "CloudKit",
        "Cocoa",
        "ColorSync",
        "CoreAudio",
        "CoreAudioTypes",
        "CoreBluetooth",
        "CoreData",
        "CoreFoundation",
        "CoreGraphics",
        "CoreHaptics",
        "CoreImage",
        "CoreLocation",
        "CoreMIDI",
        "CoreMedia",
        "CoreServices",
        "CoreText",
        "CoreVideo",
        "DiskArbitration",
        "FontServices",
        "ForceFeedback",
        "Foundation",
        "GameController",
        "IOBluetooth",
        "IOKit",
        "IOSurface",
        "JavaScriptCore",
        "ImageIO",
        "Kernel",
        "MediaToolbox",
        "Metal",
        "MetalKit",
        "ModelIO",
        "Network",
        "OSLog",
        "OpenGL",
        "PCSC",
        "PrintCore",
        "QuartzCore",
        "Security",
        "Symbols",
        "SystemConfiguration",
        "UniformTypeIdentifiers",
        "VideoToolbox",
        "WebKit",
        "_LocationEssentials",
    ],
)

# QtPrintSupport on macOS (qcocoaprintdevice.mm) uses the CUPS PPD API and
# links -lcups; libcups.tbd is not in the default minimal sysroot.
osx.libraries(names = ["libcups"])

# Python configuration

PYTHON_VERSIONS = ["3.11", "3.12", "3.13", "3.14"]
DEFAULT_PYTHON_VERSION = "3.12"

python = use_extension("@rules_python//python/extensions:python.bzl", "python")
[
    python.toolchain(
        is_default = v == DEFAULT_PYTHON_VERSION,
        python_version = v,
    )
    for v in PYTHON_VERSIONS
]

uv = use_extension("@rules_python//python/uv:uv.bzl", "uv")
uv.configure(version = "0.9.7")

# C++ configuration

llvm = use_extension("@llvm//extensions:llvm.bzl", "llvm")
""")
        f.write(
            "# Pin the LLVM release used for libc++/compiler-rt sources (see\n"
            "# tools/ci/setup_workspace.py:LLVM_VERSION for why this is held back).\n"
            f'llvm.version(llvm_version = "{LLVM_VERSION}")\n'
        )
        f.write("""
# Backends built into the from-source `@llvm-project` overlay (libclang for
# qttools' lupdate/qdoc). The prebuilt cross-compiler always has every
# backend, so this does not limit which `--platforms` we can target.
llvm.configure(
    targets = [
        "AArch64",
        "X86",
    ],
)
use_repo(llvm, "llvm-project")

""")
        f.write(render_cuda_toolkit())
        f.write("""
# Rust configuration

rs_toolchains = use_extension("@rules_rs//rs/toolchains:module_extension.bzl", "toolchains")
rs_toolchains.toolchain(
    edition = "2021",
    version = "1.93.0",
)
use_repo(rs_toolchains, "default_rust_toolchains")

register_toolchains(
    "@default_rust_toolchains//...",
)
""")

    # Write .bazelrc
    distro = args.release.split(".")[0]
    variants = "\n".join(
        f"common:{variant_name} --target_pattern_file=ros-{variant_name}.txt"
        for variant_name in VARIANTS
    )
    with open(target_workspace / ".bazelrc", "w") as f:
        f.write(render_bazelrc(distro, variants, tmpdir, args.remote_cache_write))

    # Write .bazelignore
    with open(target_workspace / ".bazelignore", "w") as f:
        f.write(render_bazelignore())

    print("Workspace setup complete.")

if __name__ == "__main__":
    main()

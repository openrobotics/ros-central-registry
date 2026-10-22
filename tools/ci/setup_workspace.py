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
import dataclasses
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

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
# rely on, so hold at 21.x -- the same line the llvm21_third_party_zstd patch
# below targets.
LLVM_VERSION = "21.1.8"

# Where third-party override patches are kept in this repo, relative to the
# repo root. Each module's patches live in their own subdirectory
# (tools/ci/patches/<module>/<file>.patch).
PATCHES_SOURCE_DIR = Path("tools") / "ci" / "patches"

# Subdirectory of the generated workspace that patches are copied into,
# preserving the <module>/<file>.patch layout.
WORKSPACE_PATCHES_DIR = "patches"


@dataclasses.dataclass(frozen=True)
class ModuleOverride:
    """
    A third-party BCR module the generated root MODULE.bazel pins with a
    bazel_dep + single_version_override, applying patches from
    tools/ci/patches/<module>/. `reason` is emitted as a comment above the
    bazel_dep; each patch's explanation is emitted above its label.
    """
    module: str
    version: str
    reason: str
    patches: Tuple[Tuple[str, str], ...]
    # False when the generated MODULE.bazel already declares the bazel_dep
    # elsewhere (e.g. rules_cc in the "BCR deps" block).
    declare_dep: bool = True


# single_version_override only takes effect in the root module, so every
# patch needed to build the from-source Qt modules (see QT_MODULES) and the
# hermetic toolchain has to be re-declared in each generated workspace.
MODULE_OVERRIDES = (
    ModuleOverride(
        module="llvm",
        version="0.8.24",
        reason=(
            "Pin the hermetic LLVM toolchain module and carry a handful of\n"
            "not-yet-released upstream fixes against it."
        ),
        patches=(
            (
                "fastbuild_compile_flags.patch",
                "Adds --@llvm//config:fastbuild_optimization_mode=<O0|O1|O2|O3|Og|Os|Oz>\n"
                "to pick the optimization level of `-c fastbuild` builds (default O0),\n"
                "giving feature parity with toolchains_llvm.\n"
                "See: https://github.com/hermeticbuild/hermetic-llvm/pull/802",
            ),
            (
                "header_search_paths.patch",
                "Fixes a bug that causes several BCR package headers to be shadowed by\n"
                "LLVM headers.\n"
                "See: https://github.com/hermeticbuild/hermetic-llvm/pull/806",
            ),
            (
                "msan_libcxx.patch",
                "Forces libc++ and libc++-abi to be compiled with msan support when using\n"
                "@llvm//config:msan (MSan requires an instrumented C++ standard library),\n"
                "following the existing inherit_asan pattern.\n"
                "See: https://github.com/hermeticbuild/hermetic-llvm/pull/803",
            ),
            (
                "stage0_object_reset.patch",
                "Makes the cc_stage0_object transition reset user copt/cxxopt/conlyopt/\n"
                "linkopt (as configure_builder_for_runtimes already does for the other\n"
                "runtimes) and the fuzzer/profile settings it forgot, so crtbegin.o/\n"
                "crtend.o never carry -fsanitize-coverage instrumentation into every\n"
                "shared library.\n"
                "See: https://github.com/hermeticbuild/hermetic-llvm/pull/815",
            ),
            (
                "llvm21_third_party_zstd.patch",
                "Backports @llvm-project//third-party:BUILD.bazel (llvm_enable_zstd) to\n"
                "LLVM 21.x so sanitizer symbolizer transitions work.\n"
                "See: https://github.com/hermeticbuild/hermetic-llvm/pull/805",
            ),
            (
                "asan_runtime.patch",
                "Applies the (already declared) ASAN_CFLAGS and UBSAN_STANDALONE_CFLAGS to\n"
                "the asan / ubsan_standalone runtimes so they are built with -fno-rtti\n"
                "-fno-exceptions like upstream CMake does. Without it the runtimes\n"
                "reference __cxa_begin_catch / __gxx_personality_v0 / _Unwind_Resume and\n"
                "plain-C links (e.g. CMake's compiler check in rules_foreign_cc) fail.\n"
                "See: https://github.com/hermeticbuild/hermetic-llvm/pull/813",
            ),
            (
                "sanitizer_runtime_libunwind.patch",
                "Makes sanitizer_common_symbolizer depend on libunwind on Linux. The\n"
                "toolchain links with --unwindlib=none and only hands libunwind to C++\n"
                "links, so a C link against a sanitizer runtime otherwise lacks\n"
                "_Unwind_Backtrace / _Unwind_GetIP.\n"
                "See: https://github.com/hermeticbuild/hermetic-llvm/pull/814",
            ),
            (
                "sanitizer_strip_foreign_source_paths.patch",
                "Adds the opt-in @llvm//config:sanitizer_strip_foreign_source_paths flag.\n"
                "When set, compile command lines exported to foreign build systems (no\n"
                "`source_file` variable: rules_foreign_cc, rules_rust cargo_build_script)\n"
                "strip source paths from UBSan locations and disable ASan global metadata,\n"
                "so code compiled with absolute paths does not embed the build root.\n"
                "See: https://github.com/hermeticbuild/hermetic-llvm/pull/816",
            ),
            (
                "windows_compiler_param_file.patch",
                "Makes the compiler_param_file feature available for every target, since\n"
                "CreateProcessW's 32767-char command line limit depends on the execution\n"
                "platform: cross-compiling from a Windows host needs @params files too.",
            ),
            (
                "windows_pkg_dir_symlinks.patch",
                "Repairs macOS SDK framework directory symlinks that libarchive extracts\n"
                "as file symlinks on Windows hosts.",
            ),
            (
                "runtime_library_search_directories_dedup.patch",
                "Only emits the toolchain's $ORIGIN/@loader_path rpaths for cc_test links;\n"
                "rules_cc already emits them for every other link, so doing it twice\n"
                "produces duplicate -rpath entries (ld64.lld warns about these).",
            ),
            (
                "mingw_def_extra_tokens.patch",
                "Passes -Wno-extra-tokens when preprocessing MinGW .def templates.",
            ),
            (
                "osx_cryptex_frameworks.patch",
                "Extracts System/Cryptexes/OS framework targets (e.g. WebKit,\n"
                "JavaScriptCore in the macOS 26 SDK) so their symlinks resolve.",
            ),
        ),
    ),
    ModuleOverride(
        module="rules_cc",
        version="0.2.26",
        reason=(
            "Lets @rules_cc//cc/runfiles be linked into more than one shared\n"
            "library: @qtbase//:core_shared embeds (and exports) it, and so do\n"
            "ROS shared libraries such as rclcpp via ament_index_cpp, which would\n"
            "otherwise fail cc_shared_library's link-once check in every binary\n"
            "that uses both Qt and ROS."
        ),
        patches=(
            (
                "runfiles_linkable_more_than_once.patch",
                'Tags cc/runfiles:runfiles with "LINKABLE_MORE_THAN_ONCE".',
            ),
        ),
        declare_dep=False,
    ),
    ModuleOverride(
        module="freetype",
        version="2.14.1.bcr.1",
        reason=(
            "Linked statically into both the from-source Qt shared libraries and\n"
            "ROS / third-party shared libraries (e.g. ogre's OgreOverlay); tagging it\n"
            "LINKABLE_MORE_THAN_ONCE keeps cc_shared_library's link-once check\n"
            "from rejecting every binary that loads both."
        ),
        patches=(
            ("linkable_more_than_once.patch", 'Tags the library "LINKABLE_MORE_THAN_ONCE".'),
        ),
    ),
    ModuleOverride(
        module="libpng",
        version="1.6.58.bcr.1",
        reason=(
            "Linked statically into both the from-source Qt shared libraries and\n"
            "ROS / third-party shared libraries (e.g. opencv, graphicsmagick); tagging it\n"
            "LINKABLE_MORE_THAN_ONCE keeps cc_shared_library's link-once check\n"
            "from rejecting every binary that loads both."
        ),
        patches=(
            ("linkable_more_than_once.patch", 'Tags the library "LINKABLE_MORE_THAN_ONCE".'),
        ),
    ),
    ModuleOverride(
        module="zlib",
        version="1.3.2.bcr.2",
        reason=(
            "Adds @zlib//:zlib_shared, a cc_shared_library exporting the whole zlib API.\n"
            "Qt's libraries (and any other cc_shared_library in the same process, e.g.\n"
            "downstream ROS libraries) depend on it via `dynamic_deps`, so exactly one\n"
            "copy of zlib is linked without tagging `:z` LINKABLE_MORE_THAN_ONCE.\n"
            "Intended for upstreaming to the BCR zlib module."
        ),
        patches=(("zlib_shared.patch", "Adds the @zlib//:zlib_shared cc_shared_library."),),
    ),
    ModuleOverride(
        module="systemd",
        version="260.1.bcr.2",
        reason=(
            "The BCR module's hand-curated config.h hard-codes HAVE_EPOLL_PWAIT2=1,\n"
            "but epoll_pwait2() only appeared in glibc 2.35 and the hermetic toolchain\n"
            "targets glibc 2.34 headers (see build:linux in .bazelrc), so\n"
            "sd-event.c fails to compile with an implicit declaration error."
        ),
        patches=(
            (
                "glibc_2_34_epoll_pwait2.patch",
                "Sets HAVE_EPOLL_PWAIT2=0 so sd-event.c uses its built-in epoll_wait()\n"
                "fallback, upstream's own behavior on libcs older than 2.35.",
            ),
        ),
    ),
    ModuleOverride(
        module="libjpeg_turbo",
        version="3.1.3.bcr.4",
        reason=(
            "Its Windows x86_64 copts are MSVC-only (/Ox, -wd4996), which breaks MinGW\n"
            "(x86_64-w64-windows-gnu) targets. Intended for upstreaming to the BCR module."
        ),
        patches=(("mingw_copts.patch", "Selects the Windows copts by compiler instead of by OS."),),
    ),
    ModuleOverride(
        module="ffmpeg",
        version="7.1.1.bcr.beta.13",
        reason="Pulled in by the from-source Qt modules (qtmultimedia).",
        patches=(
            (
                "sysctl.patch",
                "Detects sysctl() with a header-aware link check instead of\n"
                "AC_CHECK_FUNC, which misdetects it where <sys/sysctl.h> is absent.",
            ),
        ),
    ),
    ModuleOverride(
        module="openssl",
        version="3.5.8.bcr.0",
        reason="Pulled in by qtbase (QtNetwork TLS backend).",
        patches=(
            (
                "perlasm_gnu_section_syntax.patch",
                "Always emits GNU .section syntax: the $gnuas probe shells out with Unix\n"
                "redirections that fail under cmd.exe, selecting the Solaris syntax\n"
                "clang rejects on a Windows execution platform.",
            ),
            (
                "windows_clang.patch",
                "Lets OpenSSL's Perl code generation run on a Windows execution\n"
                "platform (exports VERSION.dat, per-config configdata.pm, ...).",
            ),
        ),
    ),
    ModuleOverride(
        module="libexpat",
        version="2.7.1.bcr.1",
        reason=(
            "Not a direct dependency (wayland -> libexpat), but overridden to add a\n"
            "Windows branch to its config header. wayland-scanner (and so libexpat)\n"
            "is built for the execution platform, which is Windows when\n"
            "cross-compiling a Linux target from a Windows host."
        ),
        patches=(("windows.patch", "Adds a MinGW/Windows branch to expat's config header."),),
    ),
    ModuleOverride(
        module="rules_perl",
        version="1.1.2",
        reason=(
            "Not a direct dependency (openssl -> rules_perl), but overridden to add a\n"
            "windows/arm64 Perl toolchain so OpenSSL's Perl code generation works\n"
            "when the execution platform is windows_arm64."
        ),
        patches=(
            (
                "windows_arm64_emulated_x86_64.patch",
                "Registers x86_64 Strawberry Perl for windows/arm64 (runs emulated).",
            ),
        ),
    ),
    ModuleOverride(
        module="ogre-next",
        version="2.3.3.bcr.6",
        reason="Pulled in by rosdistro (gz-rendering).",
        patches=(
            (
                "cxx23_string_nullptr.patch",
                "Replaces `return 0;` with `return \"\";` in GLSLShader::getShaderTypeLabel,\n"
                "since `std::basic_string(std::nullptr_t)` is deleted in C++23.",
            ),
        ),
    ),
    ModuleOverride(
        module="uncrustify",
        version="0.82.0",
        reason="Pulled in by rosdistro (ament_uncrustify / uncrustify_vendor).",
        patches=(
            (
                "missing_algorithm_include.patch",
                "Adds missing `#include <algorithm>` in `src/output.cpp` and `src/sorting.cpp`.",
            ),
        ),
    ),
    ModuleOverride(
        module="rules_cc_autoconf",
        version="0.27.0",
        reason=(
            "Not a direct dependency: pulled in by ffmpeg/xkbcommon/dbus/libusb/libzip/sdl2,...\n"
            "Pinned because < 0.27.0 fails to compile its config checker with libc++ on a\n"
            "Windows host (std::ifstream from std::wstring), and patched so macOS's\n"
            "`-Wl,-undefined,dynamic_lookup` linkopt does not make every `AC_CHECK_FUNC`\n"
            "link probe succeed unconditionally."
        ),
        patches=(
            (
                "macos_strip_dynamic_lookup.patch",
                "Strips `-Wl,-undefined,dynamic_lookup` from `ctx.fragments.cpp.linkopts`\n"
                "when constructing autoconf link check flags.",
            ),
        ),
    ),
)

# Plain (unpatched) version pins added to the generated root MODULE.bazel.
EXTRA_ROOT_PINS = ()


# From-source Qt 6 modules (staged under bcr_staging/modules/, served via the
# bcr_staging registry -- see BAZELRC_TEMPLATE). These replace the prebuilt
# rules_qt binaries.
QT_VERSION = "6.10.2"
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


def override_patch_paths() -> List[str]:
    """Every override patch as a <module>/<file> path, in declaration order."""
    return [f"{o.module}/{name}" for o in MODULE_OVERRIDES for name, _ in o.patches]


def copy_override_patches(repo_root: Path, target_workspace: Path) -> List[Path]:
    """
    Copy every patch listed in MODULE_OVERRIDES from
    repo_root/tools/ci/patches/<module>/ into <target_workspace>/patches/<module>/.
    Returns the destination paths. Raises FileNotFoundError if a listed patch
    is missing from the repo.
    """
    src_root = repo_root / PATCHES_SOURCE_DIR
    dst_root = target_workspace / WORKSPACE_PATCHES_DIR
    written: List[Path] = []
    for rel in override_patch_paths():
        src = src_root / rel
        if not src.is_file():
            raise FileNotFoundError(f"override patch {src} listed in MODULE_OVERRIDES does not exist")
        dst = dst_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        written.append(dst)
    return written


def render_patches_build_file(patch_paths: List[str]) -> str:
    """BUILD.bazel content for <workspace>/patches/ exporting the given files."""
    lines = [get_copyright_header().rstrip("\n"), "", "exports_files(["]
    lines += [f'    "{name}",' for name in patch_paths]
    lines += ["])"]
    return "\n".join(lines) + "\n"


def render_module_override(override: ModuleOverride) -> str:
    """
    MODULE.bazel snippet declaring a bazel_dep on one overridden module and
    pinning + patching it via single_version_override.
    """
    out = [f"# {line}" for line in override.reason.splitlines()]
    if override.declare_dep:
        out.append(f'bazel_dep(name = "{override.module}", version = "{override.version}")')
    out += [
        "single_version_override(",
        f'    module_name = "{override.module}",',
        "    patch_strip = 1,",
        "    patches = [",
    ]
    for filename, explanation in override.patches:
        for line in explanation.splitlines():
            out.append(f"        # {line}")
        out.append(f'        "//{WORKSPACE_PATCHES_DIR}:{override.module}/{filename}",')
    out += [
        "    ],",
        f'    version = "{override.version}",',
        ")",
    ]
    return "\n".join(out) + "\n"


def render_module_overrides() -> str:
    """All MODULE_OVERRIDES plus EXTRA_ROOT_PINS, separated by blank lines."""
    blocks = [render_module_override(o) for o in MODULE_OVERRIDES]
    blocks.append("".join(
        f'bazel_dep(name = "{name}", version = "{version}")\n'
        for name, version in EXTRA_ROOT_PINS
    ))
    return "\n".join(blocks)


def render_qt_deps() -> str:
    """bazel_dep lines for every from-source Qt module."""
    return "".join(
        f'bazel_dep(name = "{name}", version = "{QT_VERSION}")\n' for name in QT_MODULES
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

# CI specific performance/reliability tweaks -- safe to use anywhere,
# require no credentials (this is what forks get; see cache_write_config
# below for the part that isn't safe on a fork).
common:ci --http_timeout_scaling=3.0
common:ci --experimental_repository_downloader_retries=10
common:ci --remote_cache_compression=false
common:ci --nobuild_runfile_links
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

# Fix memory pressure in CI workers, which leads to OOM errors.
build:ci --jobs=4

## TEST OPTIONS

# This restricts our test sandboxes from accessing the network, which is
# important if you want to prevent destructive interference between tests.
# Note: this only applies to developer builds because github runners are
#       in proceswrapper-sandbox and run 1 test at a time.
test --sandbox_default_allow_network=false

# Unlike linux-sandbox (which creates an isolated CLONE_NEWNET loopback
# namespace per test), darwin-sandbox blocks all network and POSIX SHM IPC
# with sandbox-exec '(deny network*)' / '(deny default)', which breaks DDS
# participant discovery and shared-memory transport. Run tests standalone one
# at a time on macOS, matching the CI configuration below.
test:macos --local_test_jobs=1
test:macos --strategy=TestRunner=standalone

# Don't allow a flaky test to fail the entire run.
test:ci --flaky_test_attempts=3

# Limit local test concurrency on CI to prevent resource starvation, as
# well as destructive interference between tests.
test:ci --local_test_jobs=1
test:ci --test_strategy=exclusive
test:ci --strategy=TestRunner=standalone
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
    for name in variant_names:
        if name == "all":
            continue
        package = VARIANTS[name]
        lines += [
            "ament_underlay(",
            f'    name = "{name}",',
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

    # Write patches/ (fmt + MODULE_OVERRIDES) with an exports_files BUILD.bazel.
    patches_dir = target_workspace / WORKSPACE_PATCHES_DIR
    patches_dir.mkdir(parents=True, exist_ok=True)
    with open(patches_dir / "fmt.patch", "w") as f:
        f.write("""diff -urN a/BUILD.bazel b/BUILD.bazel
--- a/BUILD.bazel\t2026-08-20 00:00:00.000000000 +0000
+++ b/BUILD.bazel\t2026-08-20 00:00:00.000000000 +0000
@@ -19,6 +19,7 @@
         "src/format.cc",
         "src/os.cc",
     ],
+    tags = ["LINKABLE_MORE_THAN_ONCE"],
     hdrs = glob([
         "include/fmt/*.h",
     ]),
""")
    try:
        copy_override_patches(workspace_root, target_workspace)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    with open(patches_dir / "BUILD.bazel", "w") as f:
        f.write(render_patches_build_file(["fmt.patch"] + override_patch_paths()))

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

bazel_dep(name = "platforms", version = "1.1.0")
bazel_dep(name = "protobuf", version = "36.2")
bazel_dep(name = "rules_cc", version = "0.2.26")
bazel_dep(name = "rules_go", version = "0.60.0")
bazel_dep(name = "rules_python", version = "2.4.1")
bazel_dep(name = "rules_rs", version = "0.1.0")
bazel_dep(name = "rules_shell", version = "0.8.0")

## PATCHED BCR DEPS (see tools/ci/setup_workspace.py:MODULE_OVERRIDES)

""")
        f.write(render_module_overrides())
        f.write("""
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
# System/Cryptexes/OS in the macOS 26 SDK; patches/llvm/osx_cryptex_frameworks.patch
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

# Patch fmt to bypass duplicate linking check
single_version_override(
    module_name = "fmt",
    patch_strip = 1,
    patches = ["//patches:fmt.patch"],
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

    print("Workspace setup complete.")

if __name__ == "__main__":
    main()

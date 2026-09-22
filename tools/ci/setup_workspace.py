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
    "core": "ros_core",
    "base": "ros_base",
    "desktop": "desktop",
    "desktop_full": "desktop_full",
    "perception": "perception",
    "simulation": "simulation",
}

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

# Critical ROS environment variables needed at run-time.
common --run_env=ROS_DISTRO="{distro}"
common --run_env=ROS_HOME=".ros"
common --run_env=RMW_IMPLEMENTATION="rmw_fastrtps_cpp"
common --run_env=LD_LIBRARY_PATH=lib
common --run_env=DYLD_LIBRARY_PATH=lib
common --run_env=TMPDIR={tmpdir}

# Propagate select X11 variables through to the test sandbox, so that
# any test that uses the display has access to it.
common --test_env=DISPLAY
common --test_env=XAUTHORITY
common --test_env=WAYLAND_DISPLAY

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

# ld64's two-level namespace requires every undefined symbol in a .dylib to
# be resolvable among the libraries passed directly to its link command.
# Our rosidl-generated cc_shared_library targets commonly need symbols from
# libraries that are several dynamic_deps hops away, which the ELF loader on
# Linux resolves transitively at process load time with no issue. On Darwin
# we fall back to flat-namespace symbol lookup at load time instead.
build:macos --linkopt=-Wl,-undefined,dynamic_lookup
build:macos --host_linkopt=-Wl,-undefined,dynamic_lookup

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

def calculate_packages_for_variant(
    module_dir: Path, start_name: str, start_version: str
) -> List[str]:
    """
    Performs a BFS traversal starting from the given module name and version to collect
    all transitive dependencies.
    """
    visited = set()
    queue = [(start_name, module_dir / start_name / start_version / 'MODULE.bazel')]
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
                next_file = module_dir / next_name / next_version / 'MODULE.bazel'
                if next_file.exists():
                    if next_name not in visited:
                        queue.append((next_name, next_file))
    visited.discard("rosdistro")
    return sorted(list(visited))

def main():
    parser = argparse.ArgumentParser(
        description="Setup a Bazel workspace for testing ROS distributions in CI."
    )
    parser.add_argument(
        "--release",
        required=True,
        help="Bazel 'ros' module release version, e.g. lyrical.2026-06-08.rcr.2",
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
    packages["ros"] = args.release
    packages["rosdistro"] = args.release
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
    variants: Dict[str, List[str]] = {}
    for variant_name, variant_package in VARIANTS.items():
        if variant_package not in packages:
            print(f"Warning: Variant package {variant_package} not found in release.")
            continue
        variants[variant_name] = calculate_packages_for_variant(
            modules_dir, variant_package, packages[variant_package]
        )
        print(f"  {variant_name}: {len(variants[variant_name])} packages")

    # Create workspace directory
    target_workspace = (workspace_root / args.workspace_dir).resolve()
    target_workspace.mkdir(parents=True, exist_ok=True)
    print(f"Creating workspace at {target_workspace}...")

    # Write BUILD.bazel
    with open(target_workspace / "BUILD.bazel", "w") as f:
        f.write(get_copyright_header())

    # Write fmt.patch
    with open(target_workspace / "fmt.patch", "w") as f:
        f.write("""diff -urN a/BUILD.bazel b/BUILD.bazel
--- a/BUILD.bazel	2026-08-20 00:00:00.000000000 +0000
+++ b/BUILD.bazel	2026-08-20 00:00:00.000000000 +0000
@@ -19,6 +19,7 @@
         "src/format.cc",
         "src/os.cc",
     ],
+    tags = ["LINKABLE_MORE_THAN_ONCE"],
     hdrs = glob([
         "include/fmt/*.h",
     ]),
""")

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

bazel_dep(name = "aspect_rules_py", version = "1.11.7")
bazel_dep(name = "llvm", version = "0.8.17")
bazel_dep(name = "platforms", version = "1.1.0")
bazel_dep(name = "protobuf", version = "35.1")
bazel_dep(name = "rules_cc", version = "0.2.22")
bazel_dep(name = "rules_go", version = "0.60.0")
bazel_dep(name = "rules_python", version = "1.9.2")
bazel_dep(name = "rules_qt", version = "0.0.7")
bazel_dep(name = "rules_rs", version = "0.0.111")
bazel_dep(name = "rules_shell", version = "0.8.0")

# There is a large design change in rules_python 2.x, and some versions don't
# support 3.14. So let's stick with the older version for now. This forces
# the 1.9.2 version even if other packages in ROS specify a newer version.
single_version_override(
    module_name = "rules_python",
    version = "1.9.2"
)

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
        "CFNetwork",
        "Carbon",
        "CloudKit",
        "Cocoa",
        "ColorSync",
        "CoreAudio",
        "CoreAudioTypes",
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
        "IOKit",
        "IOSurface",
        "ImageIO",
        "Kernel",
        "MediaToolbox",
        "Metal",
        "MetalKit",
        "OSLog",
        "OpenGL",
        "PrintCore",
        "QuartzCore",
        "Security",
        "Symbols",
        "SystemConfiguration",
        "UniformTypeIdentifiers",
        "_LocationEssentials",
    ],
)

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
use_repo(llvm, "llvm-project")

qt = use_extension("@rules_qt//extension:qt.bzl", "fetch")
qt.install(
    name = "qt_linux_x86_64",
    build_file = "@rules_qt//extension:qt/6.8.3/linux_x86_64.BUILD",
    os = "linux_x86_64",
    version = "6.8.3",
)
qt.install(
    name = "qt_linux_aarch64",
    build_file = "@rules_qt//extension:qt/6.8.3/linux_aarch64.BUILD",
    os = "linux_aarch64",
    version = "6.8.3",
)
qt.install(
    name = "qt_mac_aarch64",
    build_file = "@rules_qt//extension:qt/6.8.3/mac_aarch64.BUILD",
    os = "macos",
    version = "6.8.3",
)
qt.install(
    name = "qt_mac_x86_64",
    build_file = "@rules_qt//extension:qt/6.8.3/mac_aarch64.BUILD",
    os = "macos",
    version = "6.8.3",
)
qt.install(
    name = "qt_windows_x86_64",
    build_file = "@rules_qt//extension:qt/6.8.3/windows_x86_64.BUILD",
    os = "windows",
    version = "6.8.3",
    windows_architecture = "win64_msvc2022",
)
use_repo(qt, "qt_linux_aarch64", "qt_linux_x86_64", "qt_mac_aarch64", "qt_mac_x86_64", "qt_windows_x86_64")

register_toolchains("@rules_qt//tools:all")

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
    patches = ["//:fmt.patch"],
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

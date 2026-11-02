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

"""vendor_install_tree: lay out a cc_library the way ament_vendor() installs it.

ament_cmake_vendor_package builds the vendored project with CMake and installs
it under `opt/<vendor_pkg>/{include,lib}` inside the vendor package's own
prefix. Here the same third-party library already exists as a Bazel target
(wired through @rosdistro//cc), so this rule maps that target's public headers
and library artifacts onto the same `opt/<vendor_pkg>/` layout and exposes the
result as rules_pkg's PackageFilesInfo, ready for ament_package(install = ...).
"""

load("@rules_cc//cc/common:cc_info.bzl", "CcInfo")
load("@rules_pkg//pkg:providers.bzl", "PackageFilesInfo")

def _include_relative(path):
    """external/foo+/include/bar/baz.h -> bar/baz.h (path after the last include/)."""
    parts = path.split("/")
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] == "include":
            return "/".join(parts[i + 1:])
    return parts[-1]

def _vendor_install_tree_impl(ctx):
    prefix = ctx.attr.prefix.strip("/")
    dest_src_map = {}
    for target in ctx.attr.deps:
        cc_info = target[CcInfo]
        comp = cc_info.compilation_context
        headers = comp.headers.to_list() if ctx.attr.transitive else comp.direct_public_headers
        for h in headers:
            dest_src_map[prefix + "/include/" + _include_relative(h.path)] = h
        for linker_input in cc_info.linking_context.linker_inputs.to_list():
            for lib in linker_input.libraries:
                for f in [lib.static_library, lib.pic_static_library, lib.dynamic_library]:
                    if f != None and f.basename.startswith("lib"):
                        dest_src_map[prefix + "/lib/" + f.basename] = f
    return [
        DefaultInfo(files = depset(dest_src_map.values())),
        PackageFilesInfo(dest_src_map = dest_src_map, attributes = {}),
    ]

vendor_install_tree = rule(
    implementation = _vendor_install_tree_impl,
    attrs = {
        "deps": attr.label_list(providers = [CcInfo], mandatory = True, doc = "cc targets backing the vendored project."),
        "prefix": attr.string(mandatory = True, doc = "Install prefix inside the package, e.g. opt/mimick_vendor."),
        "transitive": attr.bool(default = False, doc = "Also install headers/libraries of transitive cc deps (e.g. zenoh-c under zenoh-cpp)."),
    },
)

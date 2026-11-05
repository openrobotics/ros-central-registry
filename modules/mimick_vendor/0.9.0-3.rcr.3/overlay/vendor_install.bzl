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

load("@rules_cc//cc/common:cc_info.bzl", "CcInfo")
load("@rules_pkg//pkg:providers.bzl", "PackageFilesInfo")

def _include_relative(path):
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
                f = lib.static_library or lib.pic_static_library
                if f != None and f.basename.startswith("lib"):
                    name = f.basename.replace(".pic.a", ".a")
                    dest_src_map[prefix + "/lib/" + name] = f
    return [
        DefaultInfo(files = depset(dest_src_map.values())),
        PackageFilesInfo(dest_src_map = dest_src_map, attributes = {}),
    ]

vendor_install_tree = rule(
    implementation = _vendor_install_tree_impl,
    attrs = {
        "deps": attr.label_list(providers = [CcInfo], mandatory = True),
        "prefix": attr.string(mandatory = True),
        "transitive": attr.bool(default = False),
    },
)

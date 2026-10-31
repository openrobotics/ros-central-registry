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

"""Install-tree helper for osqp_vendor.

Upstream builds osqp with ExternalProject and installs the resulting tree
(include/osqp, include/qdldl, lib/libosqp.so, lib/libosqpstatic.a) into the
package prefix. Here osqp comes from the BCR module wrapped by
@rosdistro//cc:osqp_library; this rule maps that target's public headers and
static archives onto the same layout.
"""

load("@rules_cc//cc/common:cc_info.bzl", "CcInfo")
load("@rules_pkg//pkg:providers.bzl", "PackageFilesInfo")

def _osqp_install_tree_impl(ctx):
    cc_info = ctx.attr.dep[CcInfo]
    dest_src_map = {}
    for h in cc_info.compilation_context.headers.to_list():
        path = h.path
        if "/include/public/" in path or path.endswith("/include/private/osqp_configure.h"):
            dest_src_map["include/osqp/" + h.basename] = h
        elif "/qdldl+/include/" in path:
            dest_src_map["include/qdldl/" + h.basename] = h
    for linker_input in cc_info.linking_context.linker_inputs.to_list():
        for lib in linker_input.libraries:
            f = lib.static_library or lib.pic_static_library
            if f != None and f.basename in ("libosqp.a", "libosqp.pic.a"):
                dest_src_map["lib/libosqpstatic.a"] = f
    return [
        DefaultInfo(files = depset(dest_src_map.values())),
        PackageFilesInfo(dest_src_map = dest_src_map, attributes = {}),
    ]

osqp_install_tree = rule(
    implementation = _osqp_install_tree_impl,
    attrs = {
        "dep": attr.label(providers = [CcInfo], mandatory = True),
    },
)

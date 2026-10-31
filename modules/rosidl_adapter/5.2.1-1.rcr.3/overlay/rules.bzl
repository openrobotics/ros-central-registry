# Copyright 2025 Open Source Robotics Foundation, Inc.
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

load("@rules_cc//cc:defs.bzl", "CcInfo")
load(":aspects.bzl", "rosidl_adapter_aspect")
load(":types.bzl", "RosIdlInfo", "RosInterfaceInfo")

def _ros_interface_impl(ctx):
    return [
        RosInterfaceInfo(
            src = ctx.file.src,
            package = ctx.attr.package,
        ),
        # Deliberately empty: the generated code is attached by the rosidl
        # aspects (see rosidl_core_generators' rosidl_cc_aspect). Advertising
        # CcInfo makes every interface a node in the dependency graph that
        # cc_shared_library and cc_binary(dynamic_deps = ...) walk to decide
        # what is linked statically and what comes from a dynamic_dep, so an
        # interface package's `:cc_shared` target can stand in for its
        # generated code exactly like any other cc_shared_library.
        CcInfo(),
    ]

_ros_interface_rule = rule(
    implementation = _ros_interface_impl,
    attrs = {
        "src": attr.label(
            allow_single_file = [
                ".action",
                ".idl",
                ".msg",
                ".srv",
            ],
        ),
        "package": attr.string(mandatory = True),
        "deps": attr.label_list(providers = [RosInterfaceInfo]),
    },
    provides = [RosInterfaceInfo, CcInfo],
)

def ros_interface(name, src = None, package = None, deps = []):
    return _ros_interface_rule(
        name = name,
        src = src,
        package = package if package else native.module_name(),
        deps = deps,
    )

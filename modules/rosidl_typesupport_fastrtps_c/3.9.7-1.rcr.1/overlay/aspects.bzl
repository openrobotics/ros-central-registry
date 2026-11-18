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

load("@rosidl_generator_c//:defs.bzl", "RosCBindingsInfo")
load("@rosidl_pycommon//:defs.bzl", "ROSIDL_COMMON_ATTRS", "RosIdlInfo", "RosInterfaceInfo", "generate_compilation_information", "generate_sources", "rosidl_static_typesupport")
load("@rules_cc//cc:defs.bzl", "CcInfo")
load("@rules_cc//cc:find_cc_toolchain.bzl", "use_cc_toolchain")
load(":types.bzl", "RosCTypesupportFastRTPSInfo")

def _rosidl_typesupport_fastrtps_c_aspect_impl(target, ctx):
    hdrs, srcs, include_dirs = generate_sources(
        target = target,
        ctx = ctx,
        executable = ctx.executable._c_typesupport_fastrtps_generator,
        mnemonic = "CTypeSupportFastRTPSGeneration",
        input_idls = [target[RosIdlInfo].idl],
        input_templates = ctx.attr._c_typesupport_fastrtps_templates[DefaultInfo].files.to_list(),
        input_templates_dir = ctx.attr._c_typesupport_fastrtps_templates[DefaultInfo].files.to_list()[0].dirname,
        templates_hdrs = ["detail/{}__rosidl_typesupport_fastrtps_c.h"],
        templates_srcs = ["detail/{}__rosidl_typesupport_fastrtps_c.cpp"],
        template_visibility_control = ctx.file._c_typesupport_fastrtps_visibility_template,
        debug = True,
    )

    # rosidl_typesupport_fastrtps_c_library (and the rosidl_typesupport_fastrtps_cpp
    # runtime library, whose message_type_support.h / buffer_serialization.hpp
    # the generated C typesupport includes -- upstream CMake links
    # rosidl_typesupport_fastrtps_cpp::rosidl_typesupport_fastrtps_cpp into the
    # generated target too) are only needed for their headers here -- linking
    # them in statically would duplicate their global state into every
    # message's typesupport fragment. Route them through
    # header_only_deps so the package shared library links
    # against the single canonical shared libraries instead. See
    # generate_compilation_information's docstring.
    #
    # Note: this aspect deliberately does NOT depend on the generated C++
    # typesupport for the same interface (RosCcTypesupportFastRTPSInfo); the
    # C++ typesupport depends on *this* aspect's output (has_buffer_fields_*),
    # so doing so would be a cycle.
    header_only_deps = [dep[CcInfo] for dep in ctx.attr._c_deps if CcInfo in dep]

    deps = [target[RosCBindingsInfo].cc_info]
    for dep in ctx.rule.attr.deps:
        if RosCTypesupportFastRTPSInfo in dep:
            deps.append(dep[RosCTypesupportFastRTPSInfo].cc_info)

    package_name = target[RosIdlInfo].package_name
    info = generate_compilation_information(
        ctx = ctx,
        name = "{}__{}__{}__rosidl_typesupport_fastrtps_c".format(
            target[RosIdlInfo].package_name,
            target[RosIdlInfo].interface_type,
            target[RosIdlInfo].interface_code,
        ),
        hdrs = hdrs,
        srcs = srcs,
        deps = deps,
        header_only_deps = header_only_deps,
        include_dirs = include_dirs,
        local_defines = ["ROSIDL_TYPESUPPORT_FASTRTPS_C_BUILDING_DLL_" + package_name],
        alwayslink = rosidl_static_typesupport(ctx),
    )

    return [
        RosCTypesupportFastRTPSInfo(
            cc_info = info.cc_info,
            static_library = info.static_library,
        ),
    ]

rosidl_typesupport_fastrtps_c_aspect = aspect(
    implementation = _rosidl_typesupport_fastrtps_c_aspect_impl,
    toolchains = use_cc_toolchain(),
    attr_aspects = ["deps"],
    fragments = ["cpp"],
    attrs = {
        "_c_typesupport_fastrtps_generator": attr.label(
            default = Label("@rosidl_typesupport_fastrtps_c//:cli"),
            executable = True,
            cfg = "exec",
        ),
        "_c_typesupport_fastrtps_templates": attr.label(
            default = Label("@rosidl_typesupport_fastrtps_c//:interface_templates"),
        ),
        "_c_typesupport_fastrtps_visibility_template": attr.label(
            default = Label("@rosidl_typesupport_fastrtps_c//:resource/rosidl_typesupport_fastrtps_c__visibility_control.h.in"),
            allow_single_file = True,
        ),
        "_c_deps": attr.label_list(
            default = [
                Label("@rosidl_typesupport_fastrtps_c//:rosidl_typesupport_fastrtps_c_library"),
                Label("@rosidl_typesupport_fastrtps_cpp//:rosidl_typesupport_fastrtps_cpp_library"),
            ],
            providers = [CcInfo],
        ),
    } | ROSIDL_COMMON_ATTRS,
    required_providers = [RosInterfaceInfo],
    required_aspect_providers = [
        [RosIdlInfo],
        [RosCBindingsInfo],
    ],
    provides = [RosCTypesupportFastRTPSInfo],
)

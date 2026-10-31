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

load("@rosidl_generator_cpp//:defs.bzl", "RosCcBindingsInfo")
load("@rosidl_pycommon//:defs.bzl", "ROSIDL_COMMON_ATTRS", "RosIdlInfo", "RosInterfaceInfo", "generate_compilation_information", "generate_sources", "rosidl_static_typesupport")

# Load from types.bzl (not defs.bzl) to avoid a .bzl load cycle: fastrtps_c's
# own aspects.bzl loads this package's defs.bzl for RosCcTypesupportFastRTPSInfo.
load("@rosidl_typesupport_fastrtps_c//:types.bzl", "RosCTypesupportFastRTPSInfo")
load("@rules_cc//cc:defs.bzl", "CcInfo")
load("@rules_cc//cc:find_cc_toolchain.bzl", "use_cc_toolchain")
load(":types.bzl", "RosCcTypesupportFastRTPSInfo")

def _rosidl_typesupport_fastrtps_cpp_aspect_impl(target, ctx):
    hdrs, srcs, include_dirs = generate_sources(
        target = target,
        ctx = ctx,
        executable = ctx.executable._cc_typesupport_fastrtps_generator,
        mnemonic = "CcTypeSupportFastRTPSGeneration",
        input_idls = [target[RosIdlInfo].idl],
        input_templates = ctx.attr._cc_typesupport_fastrtps_templates[DefaultInfo].files.to_list(),
        input_templates_dir = ctx.attr._cc_typesupport_fastrtps_templates[DefaultInfo].files.to_list()[0].dirname,
        templates_hdrs = ["detail/{}__rosidl_typesupport_fastrtps_cpp.hpp"],
        templates_srcs = ["detail/{}__rosidl_typesupport_fastrtps_cpp.cpp"],
        template_visibility_control = ctx.file._cc_typesupport_fastrtps_visibility_template,
    )

    # rosidl_typesupport_fastrtps_cpp_library is only needed for its
    # headers here -- linking it in statically would duplicate its global
    # state into every message's typesupport fragment. Route it through
    # header_only_deps so the package shared library links
    # against the single canonical shared library instead. See
    # generate_compilation_information's docstring.
    header_only_deps = [dep[CcInfo] for dep in ctx.attr._cc_deps if CcInfo in dep]

    # The generated C++ typesupport delegates transitive Buffer-field
    # detection (has_buffer_fields_*()) to the generated C typesupport for
    # the same interface, mirroring upstream CMake's PRIVATE link against
    # ${target}__rosidl_typesupport_fastrtps_c. Compile against its headers
    # and link its per-interface library in.
    deps = [target[RosCcBindingsInfo].cc_info, target[RosCTypesupportFastRTPSInfo].cc_info]
    for dep in ctx.rule.attr.deps:
        if RosCcTypesupportFastRTPSInfo in dep:
            deps.append(dep[RosCcTypesupportFastRTPSInfo].cc_info)

    package_name = target[RosIdlInfo].package_name
    info = generate_compilation_information(
        ctx = ctx,
        name = "{}__{}__{}__rosidl_typesupport_fastrtps_cpp".format(
            target[RosIdlInfo].package_name,
            target[RosIdlInfo].interface_type,
            target[RosIdlInfo].interface_code,
        ),
        hdrs = hdrs,
        srcs = srcs,
        deps = deps,
        header_only_deps = header_only_deps,
        include_dirs = include_dirs,
        local_defines = ["ROSIDL_TYPESUPPORT_FASTRTPS_CPP_BUILDING_DLL_" + package_name],
        alwayslink = rosidl_static_typesupport(ctx),
    )

    return [
        RosCcTypesupportFastRTPSInfo(
            cc_info = info.cc_info,
            static_library = info.static_library,
        ),
    ]

rosidl_typesupport_fastrtps_cpp_aspect = aspect(
    implementation = _rosidl_typesupport_fastrtps_cpp_aspect_impl,
    toolchains = use_cc_toolchain(),
    attr_aspects = ["deps"],
    fragments = ["cpp"],
    attrs = {
        "_cc_typesupport_fastrtps_generator": attr.label(
            default = Label("@rosidl_typesupport_fastrtps_cpp//:cli"),
            executable = True,
            cfg = "exec",
        ),
        "_cc_typesupport_fastrtps_templates": attr.label(
            default = Label("@rosidl_typesupport_fastrtps_cpp//:interface_templates"),
        ),
        "_cc_typesupport_fastrtps_visibility_template": attr.label(
            default = Label("@rosidl_typesupport_fastrtps_cpp//:resource/rosidl_typesupport_fastrtps_cpp__visibility_control.h.in"),
            allow_single_file = True,
        ),
        "_cc_deps": attr.label_list(
            default = [
                Label("@rosidl_typesupport_fastrtps_cpp//:rosidl_typesupport_fastrtps_cpp_library"),
            ],
            providers = [CcInfo],
        ),
    } | ROSIDL_COMMON_ATTRS,
    required_providers = [RosInterfaceInfo],
    required_aspect_providers = [
        [RosIdlInfo],
        #[RosTypeDescriptionInfo],
        [RosCcBindingsInfo],
        [RosCTypesupportFastRTPSInfo],
    ],
    provides = [RosCcTypesupportFastRTPSInfo],
)

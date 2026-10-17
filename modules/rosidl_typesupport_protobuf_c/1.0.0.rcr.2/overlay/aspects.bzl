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

load("@rosidl_adapter//:tools.bzl", "generate_compilation_information", "generate_sources")
load("@rosidl_adapter//:types.bzl", "RosIdlInfo")
load("@rosidl_adapter_proto//:types.bzl", "RosProtoInfo")
load("@rosidl_cmake//:types.bzl", "RosInterfaceInfo")
load("@rosidl_generator_c//:types.bzl", "RosCBindingsInfo")
load("@rosidl_generator_cpp//:types.bzl", "RosCcBindingsInfo")
load("@rosidl_generator_type_description//:types.bzl", "RosTypeDescriptionInfo")
load("@rules_cc//cc:defs.bzl", "CcInfo", "cc_common")
load("@rules_cc//cc:find_cc_toolchain.bzl", "find_cc_toolchain", "use_cc_toolchain")
load("@rules_cc//cc/common:cc_shared_library_info.bzl", "CcSharedLibraryInfo")
load(":types.bzl", "RosCTypesupportProtobufInfo")

def _rosidl_typesupport_protobuf_c_aspect_impl(target, ctx):
    hdrs, srcs, include_dirs = generate_sources(
        target = target,
        ctx = ctx,
        executable = ctx.executable._c_typesupport_protobuf_generator,
        mnemonic = "CTypeSupportProtobufGeneration",
        input_idls = [target[RosIdlInfo].idl],
        input_type_descriptions = target[RosTypeDescriptionInfo].jsons.to_list(),
        input_templates = ctx.attr._c_typesupport_protobuf_templates[DefaultInfo].files.to_list(),
        templates_hdrs = ["{}__rosidl_typesupport_protobuf_c.hpp"],
        templates_srcs = ["{}__rosidl_typesupport_protobuf_c.cpp"],
        template_visibility_control = ctx.file._c_typesupport_protobuf_visibility_template,
    )

    # rosidl_typesupport_protobuf_c_library is only needed for its headers
    # here -- linking it in statically would duplicate its global state
    # into every message's typesupport fragment. Route it through
    # header_only_deps/dynamic_dep_linker_inputs so every fragment links
    # against the single canonical shared library instead. See
    # generate_compilation_information's docstring.
    header_only_deps = [dep[CcInfo] for dep in ctx.attr._c_deps if CcInfo in dep]

    deps = [
        target[RosProtoInfo].cc_info,
        target[RosCBindingsInfo].cc_info,
        target[RosCcBindingsInfo].cc_info,
    ]
    for dep in ctx.rule.attr.deps:
        if RosCTypesupportProtobufInfo in dep:
            deps.append(dep[RosCTypesupportProtobufInfo].cc_info)

    cc_info, dynamic_library = generate_compilation_information(
        ctx = ctx,
        name = "{}__{}__{}__rosidl_typesupport_protobuf_c".format(
            target[RosIdlInfo].package_name,
            target[RosIdlInfo].interface_type,
            target[RosIdlInfo].interface_code,
        ),
        hdrs = hdrs,
        srcs = srcs,
        deps = deps,
        header_only_deps = header_only_deps,
        dynamic_dep_linker_inputs = [ctx.attr._cc_shared_dep[CcSharedLibraryInfo].linker_input],
        include_dirs = include_dirs,
    )

    return [
        RosCTypesupportProtobufInfo(
            cc_info = cc_info,
            dynamic_libraries = depset(
                direct = [dynamic_library],
                transitive = [
                    dep[RosCTypesupportProtobufInfo].dynamic_libraries
                    for dep in ctx.rule.attr.deps
                    if RosCTypesupportProtobufInfo in dep
                ],
            ),
            linker_inputs = cc_info.linking_context.linker_inputs,
        ),
    ]

rosidl_typesupport_protobuf_c_aspect = aspect(
    implementation = _rosidl_typesupport_protobuf_c_aspect_impl,
    toolchains = use_cc_toolchain(),
    attr_aspects = ["deps"],
    fragments = ["cpp"],
    attrs = {
        "_c_typesupport_protobuf_generator": attr.label(
            default = Label("@rosidl_typesupport_protobuf_c//:cli"),
            executable = True,
            cfg = "exec",
        ),
        "_c_typesupport_protobuf_templates": attr.label(
            default = Label("@rosidl_typesupport_protobuf_c//:interface_templates"),
        ),
        "_c_typesupport_protobuf_visibility_template": attr.label(
            default = Label("@rosidl_typesupport_protobuf_c//:resource/rosidl_typesupport_protobuf_c__visibility_control.h.in"),
            allow_single_file = True,
        ),
        "_c_deps": attr.label_list(
            default = [
                Label("@rosidl_typesupport_protobuf_c//:rosidl_typesupport_protobuf_c_library"),
            ],
            providers = [CcInfo],
        ),
        "_cc_shared_dep": attr.label(
            default = Label("@rosidl_typesupport_protobuf_c//:rosidl_typesupport_protobuf_c"),
        ),
    },
    required_providers = [RosInterfaceInfo],
    required_aspect_providers = [
        [RosIdlInfo],
        [RosProtoInfo],
        [RosTypeDescriptionInfo],
        [RosCBindingsInfo],
        [RosCcBindingsInfo],
    ],
    provides = [RosCTypesupportProtobufInfo],
)

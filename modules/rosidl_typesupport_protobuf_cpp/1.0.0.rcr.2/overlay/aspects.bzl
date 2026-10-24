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

load("@rosidl_adapter_proto//:types.bzl", "RosProtoInfo")
load("@rosidl_generator_cpp//:types.bzl", "RosCcBindingsInfo")
load("@rosidl_pycommon//:defs.bzl", "RosIdlInfo", "RosInterfaceInfo", "generate_compilation_information", "generate_sources")
load("@rules_cc//cc:defs.bzl", "CcInfo", "cc_common")
load("@rules_cc//cc:find_cc_toolchain.bzl", "find_cc_toolchain", "use_cc_toolchain")
load("@rules_cc//cc/common:cc_shared_library_info.bzl", "CcSharedLibraryInfo")
load(":types.bzl", "RosCcTypesupportProtobufInfo")

def _rosidl_typesupport_protobuf_cpp_aspect_impl(target, ctx):
    hdrs, srcs, include_dirs = generate_sources(
        target = target,
        ctx = ctx,
        executable = ctx.executable._cc_typesupport_protobuf_generator,
        mnemonic = "CcTypeSupportProtobufGeneration",
        input_idls = [target[RosIdlInfo].idl],
        input_templates = ctx.attr._cc_typesupport_protobuf_templates[DefaultInfo].files.to_list(),
        input_templates_dir = ctx.attr._cc_typesupport_protobuf_templates[DefaultInfo].files.to_list()[0].dirname,
        templates_hdrs = [
            "{}__rosidl_typesupport_protobuf_cpp.hpp",
            "{}__typeadapter_protobuf_cpp.hpp",
        ],
        templates_srcs = ["detail/{}__rosidl_typesupport_protobuf_cpp.cpp"],
        template_visibility_control = ctx.file._cc_typesupport_protobuf_visibility_template,
    )

    # rosidl_typesupport_protobuf_cpp_library is only needed for its
    # headers here -- linking it in statically would duplicate its global
    # state into every message's typesupport fragment. Route it through
    # header_only_deps/dynamic_dep_linker_inputs so every fragment links
    # against the single canonical shared library instead. See
    # generate_compilation_information's docstring.
    header_only_deps = [dep[CcInfo] for dep in ctx.attr._cc_deps if CcInfo in dep]

    deps = [target[RosCcBindingsInfo].cc_info, target[RosProtoInfo].cc_info]
    for dep in ctx.rule.attr.deps:
        if RosCcTypesupportProtobufInfo in dep:
            deps.append(dep[RosCcTypesupportProtobufInfo].cc_info)

    cc_info, dynamic_libraries = generate_compilation_information(
        ctx = ctx,
        name = "{}__{}__{}__rosidl_typesupport_protobuf_cpp".format(
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
        RosCcTypesupportProtobufInfo(
            cc_info = cc_info,
            dynamic_libraries = depset(
                direct = dynamic_libraries,
                transitive = [
                    dep[RosCcTypesupportProtobufInfo].dynamic_libraries
                    for dep in ctx.rule.attr.deps
                    if RosCcTypesupportProtobufInfo in dep
                ],
            ),
            linker_inputs = cc_info.linking_context.linker_inputs,
        ),
    ]

rosidl_typesupport_protobuf_cpp_aspect = aspect(
    implementation = _rosidl_typesupport_protobuf_cpp_aspect_impl,
    toolchains = use_cc_toolchain(),
    attr_aspects = ["deps"],
    fragments = ["cpp"],
    attrs = {
        "_cc_typesupport_protobuf_generator": attr.label(
            default = Label("@rosidl_typesupport_protobuf_cpp//:cli"),
            executable = True,
            cfg = "exec",
        ),
        "_cc_typesupport_protobuf_templates": attr.label(
            default = Label("@rosidl_typesupport_protobuf_cpp//:interface_templates"),
        ),
        "_cc_typesupport_protobuf_visibility_template": attr.label(
            default = Label("@rosidl_typesupport_protobuf_cpp//:resource/rosidl_typesupport_protobuf_cpp__visibility_control.h.in"),
            allow_single_file = True,
        ),
        "_cc_deps": attr.label_list(
            default = [
                Label("@rosidl_typesupport_protobuf_cpp//:rosidl_typesupport_protobuf_cpp_library"),
            ],
            providers = [CcInfo],
        ),
        "_cc_shared_dep": attr.label(
            default = Label("@rosidl_typesupport_protobuf_cpp//:rosidl_typesupport_protobuf_cpp"),
        ),
    },
    required_providers = [RosInterfaceInfo],
    required_aspect_providers = [
        [RosIdlInfo],
        [RosProtoInfo],
        [RosCcBindingsInfo],
    ],
    provides = [RosCcTypesupportProtobufInfo],
)

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
load("@rosidl_pycommon//:defs.bzl", "RosIdlInfo", "RosInterfaceInfo", "generate_compilation_information", "generate_sources")
load("@rules_cc//cc:defs.bzl", "CcInfo")
load("@rules_cc//cc:find_cc_toolchain.bzl", "use_cc_toolchain")
load("@rules_cc//cc/common:cc_shared_library_info.bzl", "CcSharedLibraryInfo")
load(":types.bzl", "RosCTypesupportInfo")

def _rosidl_typesupport_c_aspect_impl(target, ctx):
    hdrs, srcs, include_dirs = generate_sources(
        target = target,
        ctx = ctx,
        executable = ctx.executable._c_typesupport_generator,
        mnemonic = "CTypeSupportGeneration",
        input_idls = [target[RosIdlInfo].idl],
        input_templates = ctx.attr._c_typesupport_templates[DefaultInfo].files.to_list(),
        input_templates_dir = ctx.attr._c_typesupport_templates[DefaultInfo].files.to_list()[0].dirname,
        templates_hdrs = [],
        templates_srcs = ["detail/{}__rosidl_typesupport_c.cpp"],
        additional = [
            "--typesupports",
            "rosidl_typesupport_fastrtps_cpp",
            "rosidl_typesupport_fastrtps_c",
            "rosidl_typesupport_introspection_c",
        ],
    )

    # rosidl_typesupport_c_library is only needed for its headers here --
    # linking it in statically would duplicate its global state (e.g. the
    # typesupport_identifier constant, and transitively rcutils' error
    # state) into every message's typesupport fragment. Route it through
    # header_only_deps/dynamic_dep_linker_inputs so every fragment links
    # against the single canonical @rosidl_typesupport_c//:rosidl_typesupport_c
    # shared library instead. See generate_compilation_information's
    # docstring.
    header_only_deps = [dep[CcInfo] for dep in ctx.attr._c_deps if CcInfo in dep]

    deps = [target[RosCBindingsInfo].cc_info]
    for dep in ctx.rule.attr.deps:
        if RosCTypesupportInfo in dep:
            deps.append(dep[RosCTypesupportInfo].cc_info)

    cc_info, dynamic_libraries = generate_compilation_information(
        ctx = ctx,
        name = "{}__{}__{}__rosidl_typesupport_c".format(
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
        RosCTypesupportInfo(
            cc_info = cc_info,
            dynamic_libraries = depset(
                direct = dynamic_libraries,
                transitive = [
                    dep[RosCTypesupportInfo].dynamic_libraries
                    for dep in ctx.rule.attr.deps
                    if RosCTypesupportInfo in dep
                ],
            ),
        ),
    ]

rosidl_typesupport_c_aspect = aspect(
    implementation = _rosidl_typesupport_c_aspect_impl,
    toolchains = use_cc_toolchain(),
    attr_aspects = ["deps"],
    fragments = ["cpp"],
    attrs = {
        "_c_typesupport_generator": attr.label(
            default = Label("@rosidl_typesupport_c//:cli"),
            executable = True,
            cfg = "exec",
        ),
        "_c_typesupport_templates": attr.label(
            default = Label("@rosidl_typesupport_c//:interface_templates"),
        ),
        "_c_deps": attr.label_list(
            default = [
                Label("@rosidl_typesupport_c//:rosidl_typesupport_c_library"),
            ],
            providers = [CcInfo],
        ),
        "_cc_shared_dep": attr.label(
            default = Label("@rosidl_typesupport_c//:transitive_dynamic_deps"),
        ),
    },
    required_providers = [RosInterfaceInfo],
    required_aspect_providers = [
        [RosIdlInfo],
        [RosCBindingsInfo],
    ],
    provides = [RosCTypesupportInfo],
)

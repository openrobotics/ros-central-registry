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
load("@rosidl_generator_type_description//:defs.bzl", "RosTypeDescriptionInfo")
load("@rosidl_parser//:defs.bzl", "ROSIDL_COMMON_ATTRS", "RosIdlInfo", "generate_compilation_information", "generate_sources", "rosidl_static_typesupport")
load("@rosidl_pycommon//:defs.bzl", "RosInterfaceInfo")
load("@rules_cc//cc:defs.bzl", "CcInfo")
load("@rules_cc//cc:find_cc_toolchain.bzl", "use_cc_toolchain")
load(":types.bzl", "RosCcBindingsInfo")

def _rosidl_generator_cpp_aspect_impl(target, ctx):
    hdrs, srcs, include_dirs = generate_sources(
        target = target,
        ctx = ctx,
        executable = ctx.executable._cc_generator,
        mnemonic = "CcGeneration",
        input_idls = [target[RosIdlInfo].idl],
        input_type_descriptions = target[RosTypeDescriptionInfo].jsons.to_list(),
        input_templates = ctx.attr._cc_templates[DefaultInfo].files.to_list(),
        input_templates_dir = ctx.attr._cc_templates[DefaultInfo].files.to_list()[0].dirname,
        templates_hdrs = [
            "{}.hpp",
            "detail/{}__builder.hpp",
            "detail/{}__struct.hpp",
            "detail/{}__traits.hpp",
            "detail/{}__type_support.hpp",
        ],
        templates_srcs = [],
        template_visibility_control = ctx.file._cc_visibility_template,
    )

    # rosidl_runtime_cpp_library is only needed for its headers here --
    # even though it has no sources of its own, it statically depends on
    # rosidl_runtime_c_library (and transitively rcutils_library), so
    # linking it in here would duplicate that global state into every
    # message's C++ bindings fragment. Route it through header_only_deps
    # so the package shared library links against the single canonical
    # @rosidl_runtime_cpp//:rosidl_runtime_cpp shared library instead. See generate_compilation_information's docstring.
    header_only_deps = [dep[CcInfo] for dep in ctx.attr._cc_deps if CcInfo in dep]

    deps = [target[RosCBindingsInfo].cc_info]
    for dep in ctx.rule.attr.deps:
        if RosCcBindingsInfo in dep:
            deps.append(dep[RosCcBindingsInfo].cc_info)

    # Assemble the CcInfo provider.
    package_name = target[RosIdlInfo].package_name
    info = generate_compilation_information(
        ctx = ctx,
        name = "{}__{}__{}__rosidl_generator_cpp".format(
            target[RosIdlInfo].package_name,
            target[RosIdlInfo].interface_type,
            target[RosIdlInfo].interface_code,
        ),
        hdrs = hdrs,
        srcs = srcs,
        deps = deps,
        header_only_deps = header_only_deps,
        include_dirs = include_dirs,
        local_defines = [],
        alwayslink = rosidl_static_typesupport(ctx),
    )

    # Return the CcInfo wrapped in a RosCBindingsInfo provider.
    return [
        RosCcBindingsInfo(
            cc_info = info.cc_info,
            static_library = info.static_library,
        ),
    ]

rosidl_generator_cpp_aspect = aspect(
    implementation = _rosidl_generator_cpp_aspect_impl,
    toolchains = use_cc_toolchain(),
    attr_aspects = ["deps"],
    fragments = ["cpp"],
    attrs = {
        "_cc_generator": attr.label(
            default = Label("//:cli"),
            executable = True,
            cfg = "exec",
        ),
        "_cc_templates": attr.label(
            default = Label("//:interface_templates"),
        ),
        "_cc_visibility_template": attr.label(
            default = Label("//:resource/rosidl_generator_cpp__visibility_control.hpp.in"),
            allow_single_file = True,
        ),
        "_cc_deps": attr.label_list(
            default = [
                Label("@rosidl_runtime_cpp//:rosidl_runtime_cpp_library"),
            ],
            providers = [CcInfo],
        ),
    } | ROSIDL_COMMON_ATTRS,
    required_providers = [RosInterfaceInfo],
    required_aspect_providers = [
        [RosIdlInfo],
        [RosTypeDescriptionInfo],
        [RosCBindingsInfo],
    ],
    provides = [RosCcBindingsInfo],
)

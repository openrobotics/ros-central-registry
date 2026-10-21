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

load("@rosidl_generator_type_description//:defs.bzl", "RosTypeDescriptionInfo")
load("@rosidl_parser//:defs.bzl", "RosIdlInfo", "RosInterfaceInfo", "generate_compilation_information", "generate_sources")
load("@rules_cc//cc:defs.bzl", "CcInfo")
load("@rules_cc//cc:find_cc_toolchain.bzl", "use_cc_toolchain")
load("@rules_cc//cc/common:cc_shared_library_info.bzl", "CcSharedLibraryInfo")
load(":types.bzl", "RosCBindingsInfo")

def _rosidl_generator_c_aspect_impl(target, ctx):
    hdrs, srcs, include_dirs = generate_sources(
        target = target,
        ctx = ctx,
        executable = ctx.executable._c_generator,
        mnemonic = "CGeneration",
        input_idls = [target[RosIdlInfo].idl],
        input_type_descriptions = target[RosTypeDescriptionInfo].jsons.to_list(),
        input_templates = ctx.attr._c_templates[DefaultInfo].files.to_list(),
        input_templates_dir = ctx.attr._c_templates[DefaultInfo].files.to_list()[0].dirname,
        templates_hdrs = [
            "{}.h",
            "detail/{}__functions.h",
            "detail/{}__struct.h",
            "detail/{}__type_support.h",
        ],
        templates_srcs = [
            "detail/{}__description.c",
            "detail/{}__functions.c",
            "detail/{}__type_support.c",
        ],
        template_visibility_control = ctx.file._c_visibility_template,
    )

    # rosidl_runtime_c_library is only needed for its headers here --
    # linking it in statically would duplicate its global state (and
    # transitively rcutils' error state, since rosidl_runtime_c_library
    # itself statically depends on rcutils_library) into every message's
    # C bindings fragment. Route it through header_only_deps/
    # dynamic_dep_linker_inputs so every fragment links against the single
    # canonical @rosidl_runtime_c//:rosidl_runtime_c shared library
    # instead. See generate_compilation_information's docstring.
    header_only_deps = [dep[CcInfo] for dep in ctx.attr._c_deps if CcInfo in dep]

    deps = []
    for dep in ctx.rule.attr.deps:
        if RosCBindingsInfo in dep:
            deps.append(dep[RosCBindingsInfo].cc_info)

    # Assemble the CcInfo provider.
    cc_info, dynamic_libraries = generate_compilation_information(
        ctx = ctx,
        name = "{}__{}__{}__rosidl_generator_c".format(
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

    # Return the CcInfo wrapped in a RosCBindingsInfo provider.
    return [
        RosCBindingsInfo(
            cc_info = cc_info,
            dynamic_libraries = depset(
                direct = dynamic_libraries,
                transitive = [
                    dep[RosCBindingsInfo].dynamic_libraries
                    for dep in ctx.rule.attr.deps
                    if RosCBindingsInfo in dep
                ],
            ),
        ),
    ]

rosidl_generator_c_aspect = aspect(
    implementation = _rosidl_generator_c_aspect_impl,
    toolchains = use_cc_toolchain(),
    attr_aspects = ["deps"],
    fragments = ["cpp"],
    attrs = {
        "_c_generator": attr.label(
            default = Label("@rosidl_generator_c//:cli"),
            executable = True,
            cfg = "exec",
        ),
        "_c_templates": attr.label(
            default = Label("@rosidl_generator_c//:interface_templates"),
        ),
        "_c_visibility_template": attr.label(
            default = Label("@rosidl_generator_c//:resource/rosidl_generator_c__visibility_control.h.in"),
            allow_single_file = True,
        ),
        "_c_deps": attr.label_list(
            default = [
                Label("@rosidl_runtime_c//:rosidl_runtime_c_library"),
            ],
            providers = [CcInfo],
        ),
        "_cc_shared_dep": attr.label(
            # On Windows a DLL may not carry undefined symbols, so each fragment
            # must link the *full* transitive shared-library closure it uses --
            # not just rosidl_runtime_c but also its dependencies (rcutils,
            # rosidl_typesupport_interface, ...), which the generated C bindings
            # call into directly. transitive_dynamic_deps collects that closure;
            # linking against just @rosidl_runtime_c//:rosidl_runtime_c leaves
            # e.g. rcutils_get_default_allocator undefined at link time. On Linux
            # this attribute is unused (fragments statically bundle their deps)
            # and on Darwin the extra DLLs are harmless.
            default = Label("@rosidl_runtime_c//:transitive_dynamic_deps"),
        ),
    },
    required_providers = [RosInterfaceInfo],
    required_aspect_providers = [
        [RosIdlInfo],
        [RosTypeDescriptionInfo],
    ],
    provides = [RosCBindingsInfo],
)

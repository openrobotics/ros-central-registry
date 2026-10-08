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

load("@bazel_skylib//lib:paths.bzl", "paths")
load("@rosdistro//rust:defs.bzl", "CrateInfo")
load("@rosidl_generator_c//:defs.bzl", "RosCBindingsInfo")
load("@rosidl_parser//:defs.bzl", "RosIdlInfo", "RosInterfaceInfo", "generate_compilation_information", "generate_sources")
load("@rosidl_typesupport_c//:defs.bzl", "RosCTypesupportInfo")
load("@rules_cc//cc:defs.bzl", "CcInfo")
load(":types.bzl", "RosRsBindingsInfo")

def _rosidl_generator_rs_aspect_impl(target, ctx):
    # Generate source files
    lib_files, rs_files, _ = generate_sources(
        target = target,
        ctx = ctx,
        executable = ctx.executable._rs_generator,
        mnemonic = "RustGeneration",
        input_idls = [target[RosIdlInfo].idl],
        input_templates = ctx.attr._rs_templates[DefaultInfo].files.to_list(),
        input_templates_dir = ctx.attr._rs_templates[DefaultInfo].files.to_list()[0].dirname,
        templates_hdrs = ["rust/src/" + target[RosIdlInfo].interface_type + "/{}.lib.rs"],
        templates_srcs = ["rust/src/" + target[RosIdlInfo].interface_type + "/{}.rs"],
        additional = ["--typesupport-impls=rosidl_typesupport_c"],
        debug = True,
    )

    if not rs_files:
        fail("No Rust files generated for target " + target.label.name)

    # Collect dependencies
    deps = []
    for dep in ctx.rule.attr.deps:
        if CrateInfo in dep:
            deps.append(dep[CrateInfo])

    # Construct CrateInfo
    crate_info = CrateInfo(
        name = target[RosIdlInfo].package_name + "_" + target[RosIdlInfo].interface_name,
        type = "lib",
        root = lib_files[0],
        srcs = lib_files + rs_files,
        deps = deps,
        proc_macro_deps = [],
        aliases = {},
        edition = "2021",
    )

    # Return the CrateInfo wrapped in a RosRsBindingsInfo provider.
    return [
        RosRsBindingsInfo(
            crate_info = crate_info,
            rs_files = rs_files + lib_files,
        ),
    ]

rosidl_generator_rs_aspect = aspect(
    implementation = _rosidl_generator_rs_aspect_impl,
    attr_aspects = ["deps"],
    attrs = {
        #########################################################################
        # Code generation #######################################################
        #########################################################################
        "_rs_generator": attr.label(
            default = Label("//:cli"),
            executable = True,
            cfg = "exec",
        ),
        "_rs_templates": attr.label(
            default = Label("//:interface_templates"),
        ),
        #########################################################################
        # Dependencies ##########################################################
        #########################################################################
        # "_cc_deps": attr.label_list(
        #     default = [
        #         Label("//:numpy_headers"),
        #     ],
        #     providers = [CcInfo],
        # ),
    },
    required_providers = [RosInterfaceInfo],
    required_aspect_providers = [
        [RosIdlInfo],
    ],
    provides = [RosRsBindingsInfo],
)

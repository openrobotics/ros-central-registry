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
load("@rosidl_generator_c//:defs.bzl", "RosCBindingsInfo")
load("@rosidl_parser//:defs.bzl", "ROSIDL_COMMON_ATTRS", "RosIdlInfo", "RosInterfaceInfo", "generate_compilation_information", "generate_sources")
load("@rosidl_typesupport_c//:defs.bzl", "RosCTypesupportInfo")
load("@rules_cc//cc:defs.bzl", "CcInfo")
load(":types.bzl", "RosPyBindingsInfo")

def _rosidl_generator_py_aspect_impl(target, ctx):
    # Generate source files
    py_files, srcs, _ = generate_sources(
        target = target,
        ctx = ctx,
        executable = ctx.executable._py_generator,
        mnemonic = "PyGeneration",
        input_idls = [target[RosIdlInfo].idl],
        input_templates = ctx.attr._py_templates[DefaultInfo].files.to_list(),
        input_templates_dir = ctx.attr._py_templates[DefaultInfo].files.to_list()[0].dirname,
        templates_hdrs = ["_{}.py", "_{}.__init__.py"],
        templates_srcs = ["_{}_s.c", "_{}_s.ep.rosidl_typesupport_c.c"],
        additional = ["--typesupport-impls=rosidl_typesupport_c"],
    )

    # Unpack the generated python files - there are two files per message. One is the
    # python interface, the other is the module initialization file (__init__.py).
    py_interface_file, _ = py_files[0], py_files[1]

    # The extension module calls into this interface's C bindings and C
    # typesupport, and into the extension modules of nested interfaces
    # (their <type>__convert_from_py/_to_py are called by symbol). Only the
    # static archive is built here; py_ros_library links the module itself,
    # against the package's lib<pkg>__rosidl_generator_c/typesupport_c.so
    # and the nested interfaces' modules.
    deps = [target[RosCBindingsInfo].cc_info, target[RosCTypesupportInfo].cc_info]
    dep_labels = []
    for dep in ctx.rule.attr.deps:
        if RosPyBindingsInfo in dep:
            deps.append(dep[RosPyBindingsInfo].cc_info)
            dep_labels.append(dep.label)

    # numpy is header-only here; the extension module resolves the Python C
    # API from the interpreter that loads it.
    header_only_deps = [dep[CcInfo] for dep in ctx.attr._cc_deps if CcInfo in dep]

    info = generate_compilation_information(
        ctx = ctx,
        name = "{p}/{t}/{p}__{t}__{n}_s__rosidl_typesupport_c".format(
            p = target[RosIdlInfo].package_name,
            t = target[RosIdlInfo].interface_type,
            n = target[RosIdlInfo].interface_code,
        ),
        hdrs = [],
        srcs = srcs,
        deps = deps,
        header_only_deps = header_only_deps,
        include_dirs = [],
    )
    module_name = "{p}__{t}__{n}_s__rosidl_typesupport_c".format(
        p = target[RosIdlInfo].package_name,
        t = target[RosIdlInfo].interface_type,
        n = target[RosIdlInfo].interface_code,
    )

    # We need the import path relative to the runfiles root, and this is different
    # depending on whether the target is in the main workspace or an external one.
    if target.label.workspace_root:
        import_path = paths.join(
            target.label.workspace_root.removeprefix("external/"),
            target.label.package,
        )
    else:
        import_path = paths.join("_main", target.label.package)

    # Return the depset of python interfaces and extension modules. These will be
    # aggregated by the rule and placed in the runfile path as needed.
    return [
        RosPyBindingsInfo(
            cc_info = info.cc_info,
            static_library = info.static_library,
            module_name = module_name,
            module_package = target.label.package,
            dep_labels = dep_labels,
            transitive_sources = depset(
                direct = [py_interface_file],
                transitive = [
                    dep[RosPyBindingsInfo].transitive_sources
                    for dep in ctx.rule.attr.deps
                    if RosPyBindingsInfo in dep
                ],
            ),
            imports = depset(
                direct = [import_path],
                transitive = [
                    dep[RosPyBindingsInfo].imports
                    for dep in ctx.rule.attr.deps
                    if RosPyBindingsInfo in dep
                ],
            ),
            sources = depset(direct = srcs),
        ),
    ]

rosidl_generator_py_aspect = aspect(
    implementation = _rosidl_generator_py_aspect_impl,
    toolchains = ["@rules_cc//cc:toolchain_type"],
    attr_aspects = ["deps"],
    fragments = ["cpp"],
    attrs = {
        #########################################################################
        # Code generation #######################################################
        #########################################################################
        "_py_generator": attr.label(
            default = Label("//:cli"),
            executable = True,
            cfg = "exec",
        ),
        "_py_templates": attr.label(
            default = Label("//:interface_templates"),
        ),
        #########################################################################
        # Dependencies ##########################################################
        #########################################################################
        "_cc_deps": attr.label_list(
            default = [
                Label("//:numpy_headers"),
            ],
            providers = [CcInfo],
        ),
    } | ROSIDL_COMMON_ATTRS,
    required_providers = [RosInterfaceInfo],
    required_aspect_providers = [
        [RosIdlInfo],
        [RosCBindingsInfo],
        [RosCTypesupportInfo],
    ],
    provides = [RosPyBindingsInfo],
)

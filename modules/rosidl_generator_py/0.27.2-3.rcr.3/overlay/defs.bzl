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

load("@rosidl_generator_c//:defs.bzl", "rosidl_generator_c_aspect", "rosidl_generator_type_description_aspect")
load("@rosidl_generator_cpp//:defs.bzl", "rosidl_generator_cpp_aspect")
load("@rosidl_parser//:defs.bzl", "RosInterfaceInfo", "rosidl_adapter_aspect")
load("@rosidl_typesupport_c//:defs.bzl", "RosCTypesupportInfo", "rosidl_typesupport_c_aspect")
load("@rosidl_typesupport_fastrtps_c//:defs.bzl", "RosCTypesupportFastRTPSInfo", "rosidl_typesupport_fastrtps_c_aspect")
load("@rosidl_typesupport_introspection_c//:defs.bzl", "RosCTypesupportIntrospectionInfo", "rosidl_typesupport_introspection_c_aspect")
load("@rules_cc//cc:defs.bzl", "CcInfo", "cc_common")
load("@rules_cc//cc:find_cc_toolchain.bzl", "find_cc_toolchain", "use_cc_toolchain")
load("@rules_python//python:defs.bzl", "PyInfo")
load("@rules_python//python/api:api.bzl", "py_common")
load(":aspects.bzl", _rosidl_generator_py_aspect = "rosidl_generator_py_aspect")
load(":types.bzl", _RosPyBindingsInfo = "RosPyBindingsInfo")

# Types
RosPyBindingsInfo = _RosPyBindingsInfo

# Aspects
rosidl_generator_py_aspect = _rosidl_generator_py_aspect

def _extract_information(deps, providers):
    direct_cc_infos = []
    direct_libraries = []
    for dep in deps:
        for provider in providers:
            if provider in dep:
                direct_cc_infos.append(dep[provider].cc_info)
                direct_libraries.append(dep[provider].dynamic_libraries)
    return direct_cc_infos, direct_libraries

def _create_dynamic_linking_context(ctx, transitive_libraries):
    cc_toolchain = find_cc_toolchain(ctx)
    feature_configuration = cc_common.configure_features(
        ctx = ctx,
        cc_toolchain = cc_toolchain,
        requested_features = ctx.features,
        unsupported_features = ctx.disabled_features,
    )
    libraries_to_link = []
    for file in depset(transitive = transitive_libraries).to_list():
        libraries_to_link.append(
            cc_common.create_library_to_link(
                actions = ctx.actions,
                feature_configuration = feature_configuration,
                cc_toolchain = cc_toolchain,
                dynamic_library = file,
            ),
        )
    return cc_common.create_linking_context(
        linker_inputs = depset([
            cc_common.create_linker_input(
                owner = ctx.label,
                libraries = depset(direct = libraries_to_link),
            ),
        ]),
    )

def _py_ros_library_rule_impl(ctx):
    direct_cc_infos, direct_libraries = _extract_information(ctx.attr.deps, [
        RosCTypesupportIntrospectionInfo,
        RosCTypesupportFastRTPSInfo,
        RosCTypesupportInfo,
    ])
    dynamic_linking_context = _create_dynamic_linking_context(ctx, direct_libraries)
    cc_info = cc_common.merge_cc_infos(
        direct_cc_infos = [
            cc_common.merge_cc_infos(direct_cc_infos = direct_cc_infos),
            CcInfo(linking_context = dynamic_linking_context),
        ],
    )
    symlinks = {}
    for file in depset(transitive = direct_libraries).to_list():
        symlinks["lib/" + file.basename] = file
    runfiles = ctx.runfiles(
        symlinks = symlinks,
        transitive_files = depset(transitive = direct_libraries),
    )
    for dep in ctx.attr._py_deps:
        if DefaultInfo in dep:
            runfiles = runfiles.merge(dep[DefaultInfo].default_runfiles)
    for dep in ctx.attr.deps:
        if DefaultInfo in dep:
            runfiles = runfiles.merge(dep[DefaultInfo].default_runfiles)

    default_info = DefaultInfo(
        files = depset(transitive = direct_libraries),
        runfiles = runfiles,
    )
    rosidl_py_info = PyInfo(
        imports = depset(
            transitive = [
                dep[_RosPyBindingsInfo].imports
                for dep in ctx.attr.deps
                if _RosPyBindingsInfo in dep
            ],
        ),
        transitive_sources = depset(
            transitive = [
                dep[_RosPyBindingsInfo].transitive_sources
                for dep in ctx.attr.deps
                if _RosPyBindingsInfo in dep
            ],
        ),
    )

    py_info = py_common.get(ctx).merge_py_infos(
        direct = [rosidl_py_info],
        transitive = [
            dep[PyInfo]
            for dep in ctx.attr._py_deps
            if PyInfo in dep
        ],
    )

    return [py_info, cc_info, default_info]

py_ros_library = rule(
    implementation = _py_ros_library_rule_impl,
    toolchains = use_cc_toolchain(),
    fragments = ["cpp"],
    attrs = {
        "deps": attr.label_list(
            aspects = [
                rosidl_adapter_aspect,
                rosidl_generator_type_description_aspect,
                rosidl_generator_c_aspect,
                rosidl_generator_cpp_aspect,
                rosidl_typesupport_introspection_c_aspect,
                rosidl_typesupport_fastrtps_c_aspect,
                rosidl_typesupport_c_aspect,
                _rosidl_generator_py_aspect,
            ],
            providers = [RosInterfaceInfo],
            allow_files = False,
        ),
        "_py_deps": attr.label_list(
            default = [
                Label("//:rosidl_generator_py"),
            ],
            providers = [PyInfo],
        ),
    } | py_common.API_ATTRS,
    provides = [PyInfo, CcInfo, DefaultInfo],
)

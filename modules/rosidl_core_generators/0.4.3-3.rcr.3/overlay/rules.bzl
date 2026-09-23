# Copyright 2026 Open Source Robotics Foundation, Inc.
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
"""Starlark rules for compiling ROS message generator libraries."""

load("@protobuf//bazel/common:proto_info.bzl", "ProtoInfo")
load("@rosidl_adapter//:defs.bzl", "RosInterfaceInfo", "rosidl_adapter_aspect")
load("@rosidl_adapter_proto//:defs.bzl", "RosProtoInfo", "merge_proto_infos", "rosidl_adapter_proto_aspect")
load("@rosidl_generator_c//:defs.bzl", "rosidl_generator_c_aspect", "rosidl_generator_type_description_aspect")
load("@rosidl_generator_cpp//:defs.bzl", "rosidl_generator_cpp_aspect")
load("@rosidl_generator_py//:defs.bzl", "RosPyBindingsInfo", "rosidl_generator_py_aspect")
load("@rosidl_generator_rs//:defs.bzl", "RosRsBindingsInfo", "rosidl_generator_rs_aspect")
load("@rosidl_typesupport_c//:defs.bzl", "RosCTypesupportInfo", "rosidl_typesupport_c_aspect")
load("@rosidl_typesupport_cpp//:defs.bzl", "RosCcTypesupportInfo", "rosidl_typesupport_cpp_aspect")
load("@rosidl_typesupport_fastrtps_c//:defs.bzl", "RosCTypesupportFastRTPSInfo", "rosidl_typesupport_fastrtps_c_aspect")
load("@rosidl_typesupport_fastrtps_cpp//:defs.bzl", "RosCcTypesupportFastRTPSInfo", "rosidl_typesupport_fastrtps_cpp_aspect")
load("@rosidl_typesupport_introspection_c//:defs.bzl", "RosCTypesupportIntrospectionInfo", "rosidl_typesupport_introspection_c_aspect")
load("@rosidl_typesupport_introspection_cpp//:defs.bzl", "RosCcTypesupportIntrospectionInfo", "rosidl_typesupport_introspection_cpp_aspect")
load("@rosidl_typesupport_protobuf_cpp//:defs.bzl", "RosCcTypesupportProtobufInfo", "rosidl_typesupport_protobuf_cpp_aspect")
load("@rules_cc//cc:defs.bzl", "CcInfo", "cc_common")
load("@rules_cc//cc:find_cc_toolchain.bzl", "find_cc_toolchain", "use_cc_toolchain")
load("@rules_python//python:defs.bzl", "PyInfo")
load("@rules_python//python/api:api.bzl", "py_common")
load("@rules_rust//rust:rust_common.bzl", "CrateInfo")

def _extract_information(deps, providers):
    """Extract a list of cc_info from providers"""
    direct_cc_infos = []
    direct_libraries = []
    for dep in deps:
        for provider in providers:
            if provider in dep:
                direct_cc_infos.append(dep[provider].cc_info)
                direct_libraries.append(dep[provider].dynamic_libraries)
    return direct_cc_infos, direct_libraries

def _create_dynamic_linking_context(ctx, transitive_libraries):
    """Create a linking context with the given dynamic libraries."""
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

def _force_alwayslink(ctx, direct_cc_infos):
    cc_toolchain = find_cc_toolchain(ctx)
    feature_configuration = cc_common.configure_features(
        ctx = ctx,
        cc_toolchain = cc_toolchain,
        requested_features = ctx.features,
        unsupported_features = ctx.disabled_features,
    )
    is_windows = "windows" in cc_toolchain.target_gnu_system_name or "mingw" in cc_toolchain.target_gnu_system_name
    is_darwin = "apple" in cc_toolchain.target_gnu_system_name

    merged_cc_info = cc_common.merge_cc_infos(direct_cc_infos = direct_cc_infos)
    new_linker_inputs = []
    for linker_input in merged_cc_info.linking_context.linker_inputs.to_list():
        new_libraries = []
        for lib in linker_input.libraries:
            if not lib.static_library and not lib.pic_static_library:
                if lib.dynamic_library or lib.interface_library:
                    new_libraries.append(lib)
                    continue
                fail("Library %s lacks a static archive; cannot statically link typesupport" % lib)
            new_libraries.append(
                cc_common.create_library_to_link(
                    actions = ctx.actions,
                    feature_configuration = feature_configuration,
                    cc_toolchain = cc_toolchain,
                    static_library = lib.static_library,
                    pic_static_library = lib.pic_static_library,
                    alwayslink = True,
                ),
            )

        user_link_flags = list(linker_input.user_link_flags)
        if not is_windows and not is_darwin:
            if "-rdynamic" not in user_link_flags:
                user_link_flags.append("-rdynamic")

        new_linker_inputs.append(
            cc_common.create_linker_input(
                owner = linker_input.owner,
                libraries = depset(new_libraries),
                user_link_flags = depset(user_link_flags),
                additional_inputs = depset(linker_input.additional_inputs),
            ),
        )
    return CcInfo(
        compilation_context = merged_cc_info.compilation_context,
        linking_context = cc_common.create_linking_context(
            linker_inputs = depset(new_linker_inputs),
        ),
    )

# IDL files

def _ros_library(ctx):
    default_info = DefaultInfo(
        files = depset(transitive = [dep[DefaultInfo].files for dep in ctx.attr.deps]),
    )
    return [default_info]

ros_library = rule(
    implementation = _ros_library,
    attrs = {
        "deps": attr.label_list(
            aspects = [rosidl_adapter_aspect],
            providers = [RosInterfaceInfo],
            allow_files = False,
        ),
    },
    provides = [DefaultInfo],
)

# Protobuf

def _cc_proto_ros_library(ctx):
    proto_info, _ = merge_proto_infos(
        ctx = ctx,
        name = ctx.label.name,
        deps = ctx.attr.deps,
    )
    direct_cc_infos, direct_libraries = _extract_information(ctx.attr.deps, [
        RosCcTypesupportIntrospectionInfo,
        RosCcTypesupportFastRTPSInfo,
        RosCcTypesupportProtobufInfo,
        RosCcTypesupportInfo,
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
    default_info = DefaultInfo(
        files = depset(transitive = direct_libraries),
        runfiles = ctx.runfiles(
            symlinks = symlinks,
            transitive_files = depset(transitive = direct_libraries),
        ),
    )
    return [proto_info, cc_info, default_info]

cc_proto_ros_library = rule(
    implementation = _cc_proto_ros_library,
    toolchains = use_cc_toolchain() + ["@protobuf//bazel/private:proto_toolchain_type"],
    fragments = ["proto", "cpp"],
    attrs = {
        "deps": attr.label_list(
            aspects = [
                # Adapters
                rosidl_adapter_aspect,
                rosidl_adapter_proto_aspect,
                # Type descriptions
                rosidl_generator_type_description_aspect,
                # Bindings
                rosidl_generator_c_aspect,
                rosidl_generator_cpp_aspect,
                # Typesupports
                rosidl_typesupport_introspection_cpp_aspect,
                rosidl_typesupport_fastrtps_cpp_aspect,
                rosidl_typesupport_protobuf_cpp_aspect,
                rosidl_typesupport_cpp_aspect,
            ],
            providers = [RosInterfaceInfo],
            allow_files = False,
        ),
    },
    provides = [ProtoInfo, CcInfo, DefaultInfo],
)

def _proto_ros_library(ctx):
    proto_info, _ = merge_proto_infos(
        ctx = ctx,
        name = ctx.label.name,
        deps = ctx.attr.deps,
    )
    proto_files = depset(
        transitive = [
            dep[RosProtoInfo].protos
            for dep in ctx.attr.deps
            if RosProtoInfo in dep
        ],
    )
    default_info = DefaultInfo(files = proto_files)
    return [proto_info, default_info]

proto_ros_library = rule(
    implementation = _proto_ros_library,
    toolchains = ["@protobuf//bazel/private:proto_toolchain_type"],
    fragments = ["proto"],
    attrs = {
        "deps": attr.label_list(
            aspects = [
                rosidl_adapter_aspect,
                rosidl_adapter_proto_aspect,
            ],
            providers = [RosInterfaceInfo],
            allow_files = False,
        ),
    },
    provides = [ProtoInfo, DefaultInfo],
)

# C

def _c_ros_library(ctx):
    direct_cc_infos, direct_libraries = _extract_information(ctx.attr.deps, [
        RosCTypesupportIntrospectionInfo,
        RosCTypesupportFastRTPSInfo,
        RosCcTypesupportFastRTPSInfo,
        RosCTypesupportInfo,
    ])
    dynamic_mode_val = ctx.fragments.cpp.dynamic_mode()
    dynamic_mode_off = dynamic_mode_val.lower() == "off"
    if ctx.attr.alwayslink or dynamic_mode_off:
        cc_info = _force_alwayslink(ctx, direct_cc_infos)
        default_info = DefaultInfo(
            files = depset(),
            runfiles = ctx.runfiles(),
        )
    else:
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
        default_info = DefaultInfo(
            files = depset(transitive = direct_libraries),
            runfiles = ctx.runfiles(
                symlinks = symlinks,
                transitive_files = depset(transitive = direct_libraries),
            ),
        )
    return [cc_info, default_info]

c_ros_library = rule(
    implementation = _c_ros_library,
    toolchains = use_cc_toolchain(),
    fragments = ["cpp"],
    attrs = {
        "deps": attr.label_list(
            aspects = [
                # Adapters
                rosidl_adapter_aspect,
                rosidl_generator_type_description_aspect,
                # Bindings
                rosidl_generator_c_aspect,
                rosidl_generator_cpp_aspect,
                # Typesupports
                rosidl_typesupport_introspection_c_aspect,
                rosidl_typesupport_fastrtps_cpp_aspect,
                rosidl_typesupport_fastrtps_c_aspect,
                rosidl_typesupport_c_aspect,
            ],
            providers = [RosInterfaceInfo],
            allow_files = False,
        ),
        "alwayslink": attr.bool(default = False),
    },
    provides = [CcInfo, DefaultInfo],
)

# C++

def _cc_ros_library(ctx):
    direct_cc_infos, direct_libraries = _extract_information(ctx.attr.deps, [
        RosCcTypesupportIntrospectionInfo,
        RosCcTypesupportFastRTPSInfo,
        RosCcTypesupportInfo,
    ])
    dynamic_mode_val = ctx.fragments.cpp.dynamic_mode()
    dynamic_mode_off = dynamic_mode_val.lower() == "off"
    if ctx.attr.alwayslink or dynamic_mode_off:
        cc_info = _force_alwayslink(ctx, direct_cc_infos)
        default_info = DefaultInfo(
            files = depset(),
            runfiles = ctx.runfiles(),
        )
    else:
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
        default_info = DefaultInfo(
            files = depset(transitive = direct_libraries),
            runfiles = ctx.runfiles(
                symlinks = symlinks,
                transitive_files = depset(transitive = direct_libraries),
            ),
        )
    return [cc_info, default_info]

cc_ros_library = rule(
    implementation = _cc_ros_library,
    toolchains = use_cc_toolchain(),
    fragments = ["cpp"],
    attrs = {
        "deps": attr.label_list(
            aspects = [
                # Adapters
                rosidl_adapter_aspect,
                rosidl_generator_type_description_aspect,
                # Bindings
                rosidl_generator_c_aspect,
                rosidl_generator_cpp_aspect,
                # Typesupports
                rosidl_typesupport_introspection_cpp_aspect,
                rosidl_typesupport_fastrtps_cpp_aspect,
                rosidl_typesupport_cpp_aspect,
            ],
            providers = [RosInterfaceInfo],
            allow_files = False,
        ),
        "alwayslink": attr.bool(default = False),
    },
    provides = [CcInfo, DefaultInfo],
)

# Python

def _py_ros_library_rule_impl(ctx):
    direct_cc_infos, direct_libraries = _extract_information(ctx.attr.deps, [
        RosCcTypesupportFastRTPSInfo,
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
                dep[RosPyBindingsInfo].imports
                for dep in ctx.attr.deps
                if RosPyBindingsInfo in dep
            ],
        ),
        transitive_sources = depset(
            transitive = [
                dep[RosPyBindingsInfo].transitive_sources
                for dep in ctx.attr.deps
                if RosPyBindingsInfo in dep
            ],
        ),
    )

    # Merge py_info structs.
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
                # Adapters
                rosidl_adapter_aspect,
                rosidl_generator_type_description_aspect,
                # Generators
                rosidl_generator_c_aspect,
                rosidl_generator_cpp_aspect,
                # Typesupports
                rosidl_typesupport_introspection_c_aspect,
                rosidl_typesupport_fastrtps_cpp_aspect,
                rosidl_typesupport_fastrtps_c_aspect,
                rosidl_typesupport_c_aspect,
                # Python
                rosidl_generator_py_aspect,
            ],
            providers = [RosInterfaceInfo],
            allow_files = False,
        ),
        "_py_deps": attr.label_list(
            default = [
                Label("@rosidl_generator_py"),
            ],
            providers = [PyInfo],
        ),
    } | py_common.API_ATTRS,
    provides = [PyInfo, CcInfo, DefaultInfo],
)

# Rust

def _rs_ros_library_rule_impl(ctx):
    # Extract the shared object files for each typesupport.
    _, direct_libraries = _extract_information(ctx.attr.deps, [
        RosCcTypesupportFastRTPSInfo,
        RosCTypesupportIntrospectionInfo,
        RosCTypesupportFastRTPSInfo,
        RosCTypesupportInfo,
    ])

    # Crate dependencies.
    deps = []
    for dep in ctx.attr.deps:
        if RosRsBindingsInfo in dep:
            deps.append(dep[RosRsBindingsInfo].crate_info)

    # Generate a dummy lib.rs
    lib_rs = ctx.actions.declare_file(ctx.label.name + "_lib.rs")
    ctx.actions.write(
        output = lib_rs,
        content = "// Generated by rs_ros_library\n",
    )

    # Merge everything into a CrateInfo for consumption by the callee.
    crate_info = CrateInfo(
        name = ctx.label.name,
        type = "lib",
        root = lib_rs,
        srcs = [lib_rs],
        deps = deps,
        proc_macro_deps = [],
        aliases = {},
        edition = "2021",
    )

    # Dynamically-loaded typesupports are included as runfiles.
    symlinks = {}
    for file in depset(transitive = direct_libraries).to_list():
        symlinks["lib/" + file.basename] = file
    default_info = DefaultInfo(
        files = depset(transitive = direct_libraries),
        runfiles = ctx.runfiles(
            symlinks = symlinks,
            transitive_files = depset(transitive = direct_libraries),
        ),
    )
    return [crate_info, default_info]

rs_ros_library = rule(
    implementation = _rs_ros_library_rule_impl,
    attrs = {
        "deps": attr.label_list(
            aspects = [
                # Adapters
                rosidl_adapter_aspect,
                rosidl_generator_type_description_aspect,
                # Generators
                rosidl_generator_c_aspect,
                rosidl_generator_cpp_aspect,
                # Typesupports
                rosidl_typesupport_introspection_c_aspect,
                rosidl_typesupport_fastrtps_cpp_aspect,
                rosidl_typesupport_fastrtps_c_aspect,
                rosidl_typesupport_c_aspect,
                # Rust
                rosidl_generator_rs_aspect,
            ],
            providers = [RosInterfaceInfo],
            allow_files = False,
        ),
    },
    provides = [DefaultInfo, CrateInfo],
)

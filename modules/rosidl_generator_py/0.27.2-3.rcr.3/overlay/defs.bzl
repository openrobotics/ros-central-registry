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

load("@rosidl_generator_c//:defs.bzl", "RosCBindingsInfo", "rosidl_generator_c_aspect", "rosidl_generator_type_description_aspect")
load("@rosidl_generator_cpp//:defs.bzl", "rosidl_generator_cpp_aspect")
load("@rosidl_parser//:defs.bzl", "ROSIDL_COMMON_ATTRS", "RosInterfaceInfo", "rosidl_adapter_aspect", "rosidl_link_shared_library", "rosidl_runtime_dynamic_libraries")
load("@rosidl_typesupport_c//:defs.bzl", "RosCTypesupportInfo", "rosidl_typesupport_c_aspect")
load("@rosidl_typesupport_fastrtps_c//:defs.bzl", "rosidl_typesupport_fastrtps_c_aspect")
load("@rosidl_typesupport_introspection_c//:defs.bzl", "rosidl_typesupport_introspection_c_aspect")
load("@rules_cc//cc:find_cc_toolchain.bzl", "use_cc_toolchain")
load("@rules_cc//cc/common:cc_shared_library_info.bzl", "CcSharedLibraryInfo")
load("@rules_python//python:defs.bzl", "PyInfo")
load("@rules_python//python/api:api.bzl", "py_common")
load(":aspects.bzl", _rosidl_generator_py_aspect = "rosidl_generator_py_aspect")
load(":types.bzl", _RosPyBindingsInfo = "RosPyBindingsInfo")

# Types
RosPyBindingsInfo = _RosPyBindingsInfo

# Aspects
rosidl_generator_py_aspect = _rosidl_generator_py_aspect

# ---------------------------------------------------------------------------
# Test-only py_ros_library
# ---------------------------------------------------------------------------
#
# rosidl_core_generators (which owns the real `py_ros_library`) depends on
# this package, so this package's own test interfaces cannot use it. This
# minimal stand-in links the test package's C bindings and C typesupport
# into one shared library each (like cc_ros_shared_library does per kind)
# and each interface's extension module against them; the dependency
# packages' modules are never needed because the test interfaces only nest
# each other.

def _dependencies_first(items, dep_labels):
    ordered = []
    done = {}
    for _ in range(len(items)):
        for label, item in items:
            if label in done:
                continue
            if all([dep in done or dep not in dict(items) for dep in dep_labels[label]]):
                ordered.append((label, item))
                done[label] = True
    if len(ordered) != len(items):
        fail("cyclic interface dependencies among {}".format([label for label, _ in items]))
    return ordered

def _test_py_ros_library_impl(ctx):
    package_name = ctx.label.repo_name.removesuffix("+")
    runtime_inputs = [dep[CcSharedLibraryInfo].linker_input for dep in ctx.attr._runtime_shared_deps]
    package_inputs = []
    package_files = []
    for name, provider in (("rosidl_generator_c", RosCBindingsInfo), ("rosidl_typesupport_c", RosCTypesupportInfo)):
        archives = [dep[provider].static_library for dep in ctx.attr.deps if provider in dep and dep[provider].static_library]
        linked = rosidl_link_shared_library(
            ctx,
            name = "{}__{}".format(package_name, name),
            static_libraries = archives,
            linker_inputs = package_inputs + runtime_inputs,
            symlink_dir = "rosidl_" + package_name,
        )
        package_inputs.append(linked.linker_input)
        package_files.append(linked.file)

    items = [(str(dep.label), dep[RosPyBindingsInfo]) for dep in ctx.attr.deps if RosPyBindingsInfo in dep]
    dep_labels = {label: [str(dep_label) for dep_label in info.dep_labels] for label, info in items}
    modules = {}
    module_files = []
    for label, info in _dependencies_first(items, dep_labels):
        if not info.static_library:
            continue
        nested = [modules[dep_label] for dep_label in dep_labels[label] if dep_label in modules]
        linked = rosidl_link_shared_library(
            ctx,
            name = info.module_name,
            static_libraries = [info.static_library],
            linker_inputs = package_inputs + nested + runtime_inputs,
            output_name = info.module_package + "/" + info.module_name + ".so",
            allow_undefined_symbols = True,
            symlink_dir = "rosidl_" + package_name,
        )
        modules[label] = linked.linker_input
        module_files.append(linked.file)

    solib_files = []
    for linker_input in package_inputs + modules.values():
        for library in linker_input.libraries:
            if library.dynamic_library:
                solib_files.append(library.dynamic_library)
    symlinks = {"lib/" + f.basename: f for f in package_files}
    runfiles = ctx.runfiles(
        symlinks = symlinks,
        transitive_files = depset(
            package_files + module_files + solib_files + rosidl_runtime_dynamic_libraries(ctx),
            transitive = [dep[DefaultInfo].files for dep in ctx.attr._runtime_shared_deps],
        ),
    )
    for dep in ctx.attr._py_deps:
        runfiles = runfiles.merge(dep[DefaultInfo].default_runfiles)

    rosidl_py_info = PyInfo(
        imports = depset(transitive = [info.imports for _, info in items]),
        transitive_sources = depset(module_files, transitive = [info.transitive_sources for _, info in items]),
    )
    py_info = py_common.get(ctx).merge_py_infos(
        direct = [rosidl_py_info],
        transitive = [dep[PyInfo] for dep in ctx.attr._py_deps if PyInfo in dep],
    )
    return [
        py_info,
        DefaultInfo(files = depset(module_files), runfiles = runfiles),
    ]

py_ros_library = rule(
    implementation = _test_py_ros_library_impl,
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
        "_runtime_shared_deps": attr.label_list(
            default = [Label("@rosidl_typesupport_c//:transitive_dynamic_deps")],
            providers = [CcSharedLibraryInfo],
        ),
    } | ROSIDL_COMMON_ATTRS | py_common.API_ATTRS,
    provides = [PyInfo, DefaultInfo],
)

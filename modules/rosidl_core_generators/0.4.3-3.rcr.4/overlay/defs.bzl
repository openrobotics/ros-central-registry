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
"""Starlark rules for generating ROS interface code and bindings."""

load("@rosdistro//ament:defs.bzl", "ament_index", "ament_package")
load(
    "@rosidl_cmake//:defs.bzl",
    _RosInterfaceInfo = "RosInterfaceInfo",
    _ros_interface = "ros_interface",
)
load("@rules_cc//cc:defs.bzl", "cc_library")
load(
    ":install.bzl",
    _BUNDLE_LIB_DEPS = "BUNDLE_LIB_DEPS",
    _LIBRARY_KINDS = "LIBRARY_KINDS",
    _PY_TYPESUPPORTS = "PY_TYPESUPPORTS",
    _RosidlBundledLibraryInfo = "RosidlBundledLibraryInfo",
    _kind_closure = "kind_closure",
    _rosidl_bundled_library = "rosidl_bundled_library",
    _rosidl_bundled_python_module = "rosidl_bundled_python_module",
    _rosidl_cmake_exports = "rosidl_cmake_exports",
    _rosidl_install = "rosidl_install",
    _rosidl_skip_install = "rosidl_skip_install",
)
load(
    ":rules.bzl",
    _c_ros_library = "c_ros_library",
    _cc_proto_ros_library = "cc_proto_ros_library",
    _cc_ros_library = "cc_ros_library",
    _proto_ros_library = "proto_ros_library",
    _py_ros_library = "py_ros_library",
    _ros_library = "ros_library",
    _rs_ros_library = "rs_ros_library",
)

# Foundational provider for ROS interfaces.
RosInterfaceInfo = _RosInterfaceInfo

# Root rule for declaring interfaces.
ros_interface = _ros_interface

# Generates type description .json and .msg definition files.
ros_library = _ros_library

# Generates .proto files for ros interfaces.
proto_ros_library = _proto_ros_library

# Generates .proto files and C++ bindings for ros interfaces.
cc_proto_ros_library = _cc_proto_ros_library

# Language bindings.
c_ros_library = _c_ros_library
cc_ros_library = _cc_ros_library
py_ros_library = _py_ros_library
rs_ros_library = _rs_ros_library

# Install layout (what colcon installs): one library per typesupport kind.
RosidlBundledLibraryInfo = _RosidlBundledLibraryInfo
rosidl_bundled_library = _rosidl_bundled_library
rosidl_bundled_python_module = _rosidl_bundled_python_module
rosidl_cmake_exports = _rosidl_cmake_exports
rosidl_install = _rosidl_install
rosidl_skip_install = _rosidl_skip_install

# Runtime shared libraries each bundled lib<pkg>__<kind> links against, and
# the other kinds of the same package it depends on.
_BUNDLE_DYNAMIC_DEPS = {
    "rosidl_generator_c": [Label("@rosidl_generator_c//:runtime_dynamic_deps")],
    "rosidl_generator_py": [Label("@rosidl_generator_c//:runtime_dynamic_deps")],
    "rosidl_typesupport_c": [Label("@rosidl_typesupport_c//:transitive_dynamic_deps")],
    "rosidl_typesupport_cpp": [Label("@rosidl_typesupport_cpp//:transitive_dynamic_deps")],
    "rosidl_typesupport_fastrtps_c": [Label("@rosidl_typesupport_fastrtps_c//:transitive_dynamic_deps")],
    "rosidl_typesupport_fastrtps_cpp": [Label("@rosidl_typesupport_fastrtps_cpp//:transitive_dynamic_deps")],
    "rosidl_typesupport_introspection_c": [Label("@rosidl_typesupport_introspection_c//:transitive_dynamic_deps")],
    "rosidl_typesupport_introspection_cpp": [Label("@rosidl_typesupport_introspection_cpp//:transitive_dynamic_deps")],
}

def _bundle_dynamic_deps(kind):
    """Runtime libraries for `kind` and every kind it links against.

    The private copies of dependency packages' sibling kinds a bundle links
    (see rosidl_bundled_library) need those kinds' runtime libraries too.
    """
    labels = []
    for k in _kind_closure(kind):
        for label in _BUNDLE_DYNAMIC_DEPS.get(k, []):
            if label not in labels:
                labels.append(label)
    return labels

# Libraries ament_cmake_export_libraries lists for an interface package (the
# remaining ones are installed, but only exported as CMake targets).
_EXPORTED_LIBRARY_KINDS = ["rosidl_generator_c", "rosidl_typesupport_c", "rosidl_typesupport_cpp"]

# Python typesupport module -> bundled libraries it links against.
_PY_MODULE_LIB_DEPS = {
    "rosidl_typesupport_c": ["rosidl_generator_py", "rosidl_typesupport_c", "rosidl_generator_c"],
    "rosidl_typesupport_fastrtps_c": ["rosidl_typesupport_fastrtps_c", "rosidl_generator_c"],
    "rosidl_typesupport_introspection_c": ["rosidl_typesupport_introspection_c", "rosidl_generator_c"],
}

def core_generators(package_xml, name = None, export_name = None, deps = [], hdrs = [], includes = [], data = [], alwayslink = None):
    """Generate core interface targets

    Besides the language binding targets (`:c`, `:cc`, `:py`, `:rs`) consumed
    by other Bazel targets, it declares what `colcon` would install for this
    package, to be referenced from the package's `ament_package` (see
    `rosidl_ament_package`, which wires them up):

    - `:<pkg>__<kind>` for every typesupport kind: the single
      lib<pkg>__<kind>.so bundling all interfaces of this package.
    - `:rosidl_libraries`: the bundled libraries ament_cmake_export_libraries
      lists (pass as `libraries`).
    - `:rosidl_install`: headers, python modules, interface files, the
      remaining libraries and rosidl's cmake extras (pass as `install`).
    - `:rosidl_cmake`: the cmake extras to list in <pkg>Config.cmake (pass as
      `cmake`).

    `rosidl_ament_package` additionally declares the CMake export sets (one
    per typesupport kind) and passes them as `cmake_exports`.

    Args:
        package_xml: required package.xml file
        name: optional macro name
        export_name: optional export name
        deps: list of dependencies for this target collection.
        hdrs: extra headers
        includes: extra includes
        data: extra data
        alwayslink: optional boolean to force alwayslink behavior
    """

    if alwayslink == None:
        alwayslink = select({
            "@rosdistro//:rmw_dynamic": False,
            "//conditions:default": True,
        })

    package_name = export_name if export_name else native.module_name()

    # C bindings:
    # ----------
    # This is a rule that returns a CcInfo with compile context that sets up the consumer
    # to link against shared libraries available at runtime. It includes a DefaultInfo
    # containing all shared libraries for the whole dep chain of messages.
    c_ros_library(
        name = "c_internal",
        alwayslink = alwayslink,
        deps = deps,
    )
    cc_library(
        name = "c",
        hdrs = hdrs,
        includes = includes,
        deps = [":c_internal"],
    )

    # C++ bindings:
    # ------------
    # This is a rule that returns a CcInfo with compile context that sets up the consumer
    # to link against shared libraries available at runtime. It includes a DefaultInfo
    # containing all shared libraries for the whole dep chain of messages.
    cc_ros_library(
        name = "cc_internal",
        alwayslink = alwayslink,
        deps = deps,
    )
    cc_library(
        name = "cc",
        hdrs = hdrs,
        includes = includes,
        deps = [":cc_internal"],
    )

    # Python bindings:
    # ---------------
    # This is a rule that returns a PyInfo with python context that sets up the consumer
    # to link against shared libraries available at runtime. It includes a DefaultInfo
    # containing all shared libraries for the whole dep chain of messages.
    py_ros_library(
        name = "py",
        deps = deps,
    )

    # Rust bindings:
    # ---------------
    # This is a rule that returns a PyInfo with python context that sets up the consumer
    # to link against shared libraries available at runtime. It includes a DefaultInfo
    # containing all shared libraries for the whole dep chain of messages.
    rs_ros_library(
        name = "rs",
        deps = deps,
    )

    # Message data
    # ------------
    # This is a simple rule that collects the IDLs definition files into an ament_index
    # for the calling context, so that they may be queried at runtime.
    ros_library(
        name = "idl",
        deps = deps,
    )

    # Protobuf files:
    # ---------------
    # This is a simple rule that collects the .proto files.
    cc_proto_ros_library(
        name = "proto",
        deps = deps,
    )

    ament_index(
        name = "ament_index",
        package_xml = package_xml,
        export_name = package_name,
        data = data + [":idl"],
        libraries = [
            ":cc",
            ":c",
            ":py",
            ":rs",
        ],
    )

    # Install layout:
    # ---------------
    # One shared library per typesupport kind (lib<pkg>__<kind>.so), like
    # colcon installs, plus the install map for everything else.
    bundles = {}
    for kind, lib_deps in _BUNDLE_LIB_DEPS:
        bundle = "{}__{}".format(package_name, kind)
        bundles[kind] = ":" + bundle
        rosidl_bundled_library(
            name = bundle,
            kind = kind,
            package_name = package_name,
            deps = deps,
            lib_deps = [bundles[dep] for dep in lib_deps],
            dynamic_deps = _bundle_dynamic_deps(kind),
            tags = ["manual"],
        )
    native.filegroup(
        name = "rosidl_libraries",
        srcs = [bundles[kind] for kind in _EXPORTED_LIBRARY_KINDS],
        tags = ["manual"],
    )
    for typesupport in _PY_TYPESUPPORTS:
        rosidl_bundled_python_module(
            name = "rosidl_python_{}".format(typesupport),
            package_name = package_name,
            typesupport = typesupport,
            deps = deps,
            lib_deps = [bundles[kind] for kind in _PY_MODULE_LIB_DEPS[typesupport]],
            tags = ["manual"],
        )
    rosidl_install(
        name = "rosidl_install",
        package_name = package_name,
        deps = deps,
        libraries = [bundles[kind] for kind in _LIBRARY_KINDS if kind not in _EXPORTED_LIBRARY_KINDS],
        python_modules = ["rosidl_python_{}".format(typesupport) for typesupport in _PY_TYPESUPPORTS],
        tags = ["manual"],
    )
    rosidl_skip_install(
        name = "rosidl_skip_install",
        package_name = package_name,
        tags = ["manual"],
    )
    native.filegroup(
        name = "rosidl_cmake",
        srcs = [":rosidl_install"],
        output_group = "cmake",
        tags = ["manual"],
    )

_ROSIDL_CMAKE_EXTRAS = [
    "rosidl_cmake-extras.cmake",
    "ament_cmake_export_include_directories-extras.cmake",
    "rosidl_cmake_export_typesupport_targets-extras.cmake",
    "rosidl_cmake_export_typesupport_libraries-extras.cmake",
    "rosidl_cmake_aggregate_target-extras.cmake",
]

def rosidl_ament_package(
        name = "ament_package",
        libraries = [],
        install = [],
        cmake_extras = [],
        interface_library = None,
        interface_library_export = None,
        interface_library_location = None,
        interface_library_link_libraries = [],
        **kwargs):
    """ament_package for an interface package built with core_generators.

    Wires the install targets core_generators declares into ament_package so
    the package's `:tar` matches what colcon installs. Accepts every
    ament_package argument; `libraries`, `install` and `cmake_extras` are
    extended.

    Args:
        name: target name (default "ament_package").
        libraries: additional exported libraries.
        install: additional PackageFilesInfo targets.
        cmake_extras: additional cmake extra filenames included by <pkg>Config.cmake.
        interface_library: name of an additional CMake target the package
            exports alongside its messages (e.g. "sensor_msgs_library" for
            sensor_msgs' hand written headers, or "rmw_dds_common_library");
            None for none.
        interface_library_export: export set name for `interface_library`
            (defaults to "export_<pkg>").
        interface_library_location: relative library path (e.g.
            "lib/librmw_dds_common.so") when `interface_library` is SHARED;
            None for INTERFACE.
        interface_library_link_libraries: INTERFACE_LINK_LIBRARIES of that
            target (CMake target names).
        **kwargs: forwarded to ament_package.
    """
    package_name = kwargs.get("export_name") or native.module_name()
    rosidl_cmake_exports(
        name = name + "_cmake_exports",
        package_name = package_name,
        bundles = [":{}__{}".format(package_name, kind) for kind, _ in _BUNDLE_LIB_DEPS],
        interface_library = interface_library,
        interface_library_export = interface_library_export,
        interface_library_location = interface_library_location,
        interface_library_link_libraries = interface_library_link_libraries,
        tags = ["manual"],
    )
    ament_package(
        name = name,
        libraries = [":rosidl_libraries"] + libraries,
        install = [":rosidl_install"] + install,
        cmake_extras = _ROSIDL_CMAKE_EXTRAS + cmake_extras,
        cmake_exports = ":" + name + "_cmake_exports",
        cmake_export_include_directories = False,
        **kwargs
    )

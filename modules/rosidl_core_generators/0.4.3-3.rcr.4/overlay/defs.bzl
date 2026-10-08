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

load("@rosdistro//ament:defs.bzl", "ament_index")
load(
    "@rosidl_cmake//:defs.bzl",
    _RosInterfaceInfo = "RosInterfaceInfo",
    _ros_interface = "ros_interface",
)
load("@rules_cc//cc:defs.bzl", "cc_library")
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

def core_generators(package_xml, name = None, export_name = None, deps = [], hdrs = [], includes = [], data = [], alwayslink = None):
    """Generate core interface targets

    This macro is responsible for generating all interface targets for the
    package. Some examples include:

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
        export_name = export_name if export_name else native.module_name(),
        data = data + [":idl"],
        libraries = [
            ":cc",
            ":c",
            ":py",
            ":rs",
        ],
    )

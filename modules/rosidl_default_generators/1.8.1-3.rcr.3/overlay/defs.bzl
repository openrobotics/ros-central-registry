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

"""
Starlark rules for declaring ROS interfaces.
"""

load(
    "@rosidl_core_generators//:defs.bzl",
    _RosInterfaceInfo = "RosInterfaceInfo",
    _c_ros_library = "c_ros_library",
    _cc_proto_ros_library = "cc_proto_ros_library",
    _cc_ros_library = "cc_ros_library",
    _core_generators = "core_generators",
    _proto_ros_library = "proto_ros_library",
    _py_ros_library = "py_ros_library",
    _ros_interface = "ros_interface",
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

# Language generators
c_ros_library = _c_ros_library
cc_ros_library = _cc_ros_library
py_ros_library = _py_ros_library
rs_ros_library = _rs_ros_library

# Default generators are just core generators (for now)
default_generators = _core_generators

def ros_idl(name, src, package = None, deps = []):
    return _ros_interface(
        name = name,
        src = src,
        package = package if package else native.module_name(),
        deps = deps,
    )

def ros_message(name, src, package = None, deps = []):
    return _ros_interface(
        name = name,
        src = src,
        package = package if package else native.module_name(),
        deps = deps,
    )

def ros_service(name, src, package = None, deps = []):
    return _ros_interface(
        name = name,
        src = src,
        package = package if package else native.module_name(),
        deps = deps + [
            "@rosidl_default_generators//:msg_ServiceEventInfo",
        ],
    )

def ros_action(name, src, package = None, deps = []):
    return _ros_interface(
        name = name,
        src = src,
        package = package if package else native.module_name(),
        deps = deps + [
            "@rosidl_default_generators//:msg_GoalInfo",
            "@rosidl_default_generators//:msg_GoalStatus",
            "@rosidl_default_generators//:msg_GoalStatusArray",
            "@rosidl_default_generators//:srv_CancelGoal",
        ],
    )

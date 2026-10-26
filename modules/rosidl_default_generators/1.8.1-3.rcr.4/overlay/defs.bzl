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
    _c_ros_shared_library = "c_ros_shared_library",
    _cc_proto_ros_library = "cc_proto_ros_library",
    _cc_ros_library = "cc_ros_library",
    _cc_ros_shared_library = "cc_ros_shared_library",
    _core_generators = "core_generators",
    _proto_ros_library = "proto_ros_library",
    _py_ros_library = "py_ros_library",
    _ros_interface = "ros_interface",
    _ros_library = "ros_library",
    _rosidl_ament_package = "rosidl_ament_package",
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
c_ros_shared_library = _c_ros_shared_library
cc_ros_shared_library = _cc_ros_shared_library
py_ros_library = _py_ros_library
rs_ros_library = _rs_ros_library

# Interface packages every service (service_msgs) and action (action_msgs,
# and through it unique_identifier_msgs and builtin_interfaces) implicitly
# depends on -- see ros_service/ros_action below. They are offered to every
# package as `dependencies`; the rules only link the ones the interfaces
# actually use. The packages that *are* these dependencies (or that they
# depend on) must not get them, that would be a cycle.
_IMPLICIT_DEPENDENCIES = [
    Label("@service_msgs"),
    Label("@action_msgs"),
]

_IMPLICIT_DEPENDENCY_PACKAGES = [
    "builtin_interfaces",
    "unique_identifier_msgs",
    "service_msgs",
    "action_msgs",
]

def default_generators(dependencies = [], **kwargs):
    """core_generators plus the implicit service/action interface dependencies.

    Args:
        dependencies: see core_generators.
        **kwargs: see core_generators.
    """
    if native.module_name() not in _IMPLICIT_DEPENDENCY_PACKAGES:
        dependencies = list(dependencies) + _IMPLICIT_DEPENDENCIES
    _core_generators(dependencies = dependencies, **kwargs)

# ament_package wired up with the install layout default_generators declares.
rosidl_ament_package = _rosidl_ament_package

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

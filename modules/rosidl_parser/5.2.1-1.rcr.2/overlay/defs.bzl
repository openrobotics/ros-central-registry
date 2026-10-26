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

load(
    "@rosidl_adapter//:defs.bzl",
    _ROSIDL_COMMON_ATTRS = "ROSIDL_COMMON_ATTRS",
    _RosIdlInfo = "RosIdlInfo",
    _RosInterfaceInfo = "RosInterfaceInfo",
    _generate_compilation_information = "generate_compilation_information",
    _generate_sources = "generate_sources",
    _idl_tuple_from_path = "idl_tuple_from_path",
    _pkg_name_and_base_from_path = "pkg_name_and_base_from_path",
    _ros_interface = "ros_interface",
    _rosidl_adapter_aspect = "rosidl_adapter_aspect",
    _rosidl_export_dynamic_link_flags = "rosidl_export_dynamic_link_flags",
    _rosidl_is_darwin = "rosidl_is_darwin",
    _rosidl_is_windows = "rosidl_is_windows",
    _rosidl_link_shared_library = "rosidl_link_shared_library",
    _rosidl_runtime_dynamic_libraries = "rosidl_runtime_dynamic_libraries",
    _rosidl_shared_library_name = "rosidl_shared_library_name",
    _rosidl_static_typesupport = "rosidl_static_typesupport",
    _rosidl_whole_archive = "rosidl_whole_archive",
)

RosIdlInfo = _RosIdlInfo
RosInterfaceInfo = _RosInterfaceInfo

rosidl_adapter_aspect = _rosidl_adapter_aspect

ROSIDL_COMMON_ATTRS = _ROSIDL_COMMON_ATTRS
generate_compilation_information = _generate_compilation_information
rosidl_runtime_dynamic_libraries = _rosidl_runtime_dynamic_libraries
rosidl_link_shared_library = _rosidl_link_shared_library
rosidl_shared_library_name = _rosidl_shared_library_name
rosidl_whole_archive = _rosidl_whole_archive
rosidl_is_darwin = _rosidl_is_darwin
rosidl_is_windows = _rosidl_is_windows
rosidl_export_dynamic_link_flags = _rosidl_export_dynamic_link_flags
rosidl_static_typesupport = _rosidl_static_typesupport
generate_sources = _generate_sources
idl_tuple_from_path = _idl_tuple_from_path
pkg_name_and_base_from_path = _pkg_name_and_base_from_path
ros_interface = _ros_interface

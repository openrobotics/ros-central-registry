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
    ":aspects.bzl",
    _rosidl_adapter_aspect = "rosidl_adapter_aspect",
)
load(
    ":rules.bzl",
    _ros_interface = "ros_interface",
)
load(
    ":tools.bzl",
    _generate_compilation_information = "generate_compilation_information",
    _generate_sources = "generate_sources",
    _idl_tuple_from_path = "idl_tuple_from_path",
    _pkg_name_and_base_from_path = "pkg_name_and_base_from_path",
)
load(
    ":types.bzl",
    _RosIdlInfo = "RosIdlInfo",
    _RosInterfaceInfo = "RosInterfaceInfo",
)

RosInterfaceInfo = _RosInterfaceInfo
RosIdlInfo = _RosIdlInfo

rosidl_adapter_aspect = _rosidl_adapter_aspect

ros_interface = _ros_interface
generate_compilation_information = _generate_compilation_information
generate_sources = _generate_sources
idl_tuple_from_path = _idl_tuple_from_path
pkg_name_and_base_from_path = _pkg_name_and_base_from_path

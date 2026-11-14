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

load(
    "@rosidl_generator_type_description//:defs.bzl",
    _RosTypeDescriptionInfo = "RosTypeDescriptionInfo",
    _rosidl_generator_type_description_aspect = "rosidl_generator_type_description_aspect",
)
load(":aspects.bzl", _rosidl_generator_cpp_aspect = "rosidl_generator_cpp_aspect")
load(":types.bzl", _RosCcBindingsInfo = "RosCcBindingsInfo")

RosCcBindingsInfo = _RosCcBindingsInfo
RosTypeDescriptionInfo = _RosTypeDescriptionInfo

rosidl_generator_cpp_aspect = _rosidl_generator_cpp_aspect
rosidl_generator_type_description_aspect = _rosidl_generator_type_description_aspect

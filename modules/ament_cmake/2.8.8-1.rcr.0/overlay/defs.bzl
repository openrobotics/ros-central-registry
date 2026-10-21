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

"""Bazel equivalents of the CMake macros ament_cmake re-exports from its sub-packages.

Packages depend on ament_cmake (not on each ament_cmake_* sub-package), so they load these
macros from here, just as CMake packages get them via find_package(ament_cmake).
"""

load(
    "@ament_cmake_export_include_directories//:defs.bzl",
    _ament_cmake_export_include_directories = "ament_cmake_export_include_directories",
)

ament_cmake_export_include_directories = _ament_cmake_export_include_directories

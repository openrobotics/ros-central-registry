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

load("@cmake_configure_file//:cmake_configure_file.bzl", "cmake_configure_file")

def generate_version_h(name, out):
    """Generates a package's own version.h.

    Mirrors the real ament_cmake_gen_version_h CMake macro
    (ament_generate_version_header()): expands the real upstream
    cmake/version.h.in template with the consuming package's own
    name/version via cmake_configure_file.

    Args:
        name: name of this target.
        out: output path for the generated header, e.g.
            "include/ament_index_cpp/version.h".
    """
    cmake_configure_file(
        name = name,
        src = "@ament_cmake_gen_version_h//cmake:version.h.in",
        out = out,
        defines = generate_ros_version_defines(),
    )

def generate_ros_version_defines():
    package_name = native.module_name()
    package_version = native.module_version()
    package_version_parts = package_version.split(".")
    package_version_major = package_version_parts[0] if len(package_version_parts) > 0 else ""
    package_version_minor = package_version_parts[1] if len(package_version_parts) > 1 else ""
    package_version_patch = package_version_parts[2] if len(package_version_parts) > 2 else ""
    return [
        "PROJECT_NAME_UPPER={}".format(package_name.upper()),
        "VERSION_MAJOR={}".format(package_version_major),
        "VERSION_MINOR={}".format(package_version_minor),
        "VERSION_PATCH={}".format(package_version_patch),
        "VERSION_STR={}".format(package_version),
    ]

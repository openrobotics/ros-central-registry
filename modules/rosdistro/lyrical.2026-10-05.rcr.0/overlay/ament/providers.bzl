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

"""Providers shared by the ament packaging rules."""

AmentPackageInfo = provider(
    doc = """Describes the install-tree contribution of exactly one ROS package.

Paths in `files` are relative to the *package prefix* (i.e. the directory that
would be `install/<pkg>/` in a colcon isolated-layout install). The underlay
rules prepend `<pkg>/` to turn this into an isolated install layout, which is
what `desktop_full`'s tarball uses.
""",
    fields = {
        "name": "The ROS package name.",
        "files": "dict: destination path (relative to the package prefix) -> File. Tree artifacts map a whole subtree.",
        "deps": "list of Target: the direct ament_package dependencies of this package.",
        "cmake_targets": "list of string: imported CMake targets (ns::name) this package exports.",
    },
)

AmentCMakeExportsInfo = provider(
    doc = """Explicit CMake export sets for a package, overriding the single
`<pkg>::<lib>` export set ament_package derives from `libraries`.""",
    fields = {
        "exports": "list of export-set dicts in install_gen's `exports` JSON schema: " +
                   "[{'export': str, 'namespace': str, 'targets': [{'name': str, 'type': 'SHARED'|'INTERFACE', " +
                   "'location': str|None, 'include_dirs': [str], 'link_libraries': [str]}]}]",
        "dependencies": "optional list of package names passed verbatim to ament_export_dependencies() " +
                        "(appended to the auto-derived list); e.g. rosidl's fixed runtime dependency set.",
    },
)

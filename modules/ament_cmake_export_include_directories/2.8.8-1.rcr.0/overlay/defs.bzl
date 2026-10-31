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

"""Bazel equivalent of CMake's ament_export_include_directories()."""

def _ament_cmake_export_include_directories_impl(ctx):
    package_name = ctx.attr.package_name or ctx.label.workspace_name.removesuffix("+")
    dirs = []
    for d in ctx.attr.include_dirs:
        # Mirrors ament_export_include_directories(): relative paths are relative to the
        # install prefix, absolute paths are exported as-is.
        dirs.append(d if d.startswith("/") else "${%s_DIR}/../../../%s" % (package_name, d))
    out = ctx.actions.declare_file(
        "_gen/share/%s/cmake/ament_cmake_export_include_directories-extras.cmake" % package_name,
    )
    ctx.actions.expand_template(
        template = ctx.file._template,
        output = out,
        substitutions = {
            "@_AMENT_CMAKE_EXPORT_INCLUDE_DIRECTORIES@": ";".join(dirs),
            "@PROJECT_NAME@": package_name,
        },
    )
    return [DefaultInfo(files = depset([out]))]

ament_cmake_export_include_directories = rule(
    implementation = _ament_cmake_export_include_directories_impl,
    doc = """Generates share/<pkg>/cmake/ament_cmake_export_include_directories-extras.cmake.

Pass the result to ament_package(cmake = [...]) and set cmake_export_include_directories = False
so the package does not also emit the default version of the same file.
""",
    attrs = {
        "include_dirs": attr.string_list(
            mandatory = True,
            doc = "Include directories as passed to ament_export_include_directories(), relative to the install prefix.",
        ),
        "package_name": attr.string(doc = "ROS package name. Defaults to the module name."),
        "_template": attr.label(
            allow_single_file = True,
            default = Label("//:cmake/ament_cmake_export_include_directories-extras.cmake.in"),
        ),
    },
)

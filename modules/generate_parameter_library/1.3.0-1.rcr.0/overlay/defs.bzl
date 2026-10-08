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

load("@rules_cc//cc:defs.bzl", "cc_library")

def _generate_parameter_library_impl(ctx):
    output_hpp = ctx.actions.declare_file("include/" + ctx.attr.package_name + "/" + ctx.attr.lib_name + ".hpp")
    inputs = [ctx.file.yaml_file]
    args = ctx.actions.args()
    args.add(output_hpp.path)
    args.add(ctx.file.yaml_file.path)

    outputs = [output_hpp]

    if ctx.file.validate_header:
        # Copy validation header to the same directory as the generated header
        copied_validate_header = ctx.actions.declare_file("include/" + ctx.attr.package_name + "/" + ctx.file.validate_header.basename)
        ctx.actions.run_shell(
            outputs = [copied_validate_header],
            inputs = [ctx.file.validate_header],
            command = "cp %s %s" % (ctx.file.validate_header.path, copied_validate_header.path),
        )
        args.add(ctx.file.validate_header.basename)
        outputs.append(copied_validate_header)

    ctx.actions.run(
        inputs = inputs,
        outputs = outputs,
        executable = ctx.executable._generator,
        arguments = [args],
    )

    return [DefaultInfo(files = depset(outputs))]

_generate_parameter_library_rule = rule(
    implementation = _generate_parameter_library_impl,
    attrs = {
        "lib_name": attr.string(mandatory = True),
        "yaml_file": attr.label(allow_single_file = True, mandatory = True),
        "validate_header": attr.label(allow_single_file = True),
        "package_name": attr.string(mandatory = True),
        "_generator": attr.label(
            executable = True,
            cfg = "exec",
            default = Label("@generate_parameter_library_py//:generate_parameter_library_cpp"),
        ),
    },
)

def generate_parameter_library(name, yaml_file, validate_header = None, package_name = None):
    """Generates a C++ parameter library from a YAML file.

    Args:
        name: The name of the generated target.
        yaml_file: The input YAML parameter descriptor file.
        validate_header: Optional user-defined validation header file.
        package_name: Optional package name override. Defaults to module name.
    """
    if not package_name:
        package_name = native.module_name()

    gen_name = name + "_gen"

    _generate_parameter_library_rule(
        name = gen_name,
        lib_name = name,
        yaml_file = yaml_file,
        validate_header = validate_header,
        package_name = package_name,
    )

    cc_library(
        name = name,
        hdrs = [":" + gen_name],
        includes = ["include"],
        deps = [
            "@generate_parameter_library//:generate_parameter_library",
        ],
        visibility = ["//visibility:public"],
    )

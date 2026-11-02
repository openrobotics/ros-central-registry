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
    "@rosidl_parser//:defs.bzl",
    "RosIdlInfo",
    "RosInterfaceInfo",
    "idl_tuple_from_path",
    "pkg_name_and_base_from_path",
)
load("//:types.bzl", "RosTypeDescriptionInfo")

def _rosidl_generator_type_description_aspect_impl(target, ctx):
    package_name = target[RosIdlInfo].package_name
    message_type = target[RosIdlInfo].interface_type
    message_name = target[RosIdlInfo].interface_name
    message_code = target[RosIdlInfo].interface_code

    # File needed as input to generate this type description
    idl_file = target[RosIdlInfo].idl

    # Templates needed for generation
    template_files = ctx.attr._rosidl_templates[DefaultInfo].files.to_list()

    # This is the single file we'll be generating as part of this aspect call.
    json_file = ctx.actions.declare_file(
        "{}/{}/{}".format(
            package_name,
            message_type,
            "{}.json".format(message_name),
        ),
    )

    # Get all dependency and include paths.
    dependency_files = []
    include_paths = []
    for dep in ctx.rule.attr.deps:
        for include_path in dep[RosTypeDescriptionInfo].include_paths.to_list():
            include_paths.append(include_path)
        for dependency_file in dep[RosTypeDescriptionInfo].jsons.to_list():
            dependency_files.append(dependency_file)

    # The first output file is the JSON file used as args to the generator.
    args_file = ctx.actions.declare_file(
        "{}/{}_{}_TypeDescription.json".format(package_name, message_type, message_name),
    )
    ctx.actions.write(
        args_file,
        json.encode(
            struct(
                package_name = package_name,
                idl_tuples = [idl_tuple_from_path(idl_file.path)],
                output_dir = args_file.dirname,
                template_dir = template_files[0].dirname,
                include_paths = include_paths,
            ),
        ),
    )

    # Run the action to generate the files
    ctx.actions.run(
        inputs = template_files + dependency_files + [idl_file, args_file],
        outputs = [json_file],
        executable = ctx.executable._rosidl_generator,
        arguments = ["--generator-arguments-file={}".format(args_file.path)],
        mnemonic = "IdlToTypeDescription",
        progress_message = "Generating Type Description for {}".format(ctx.label.name),
    )

    # We must propagate the include path for this IDL down to children. It takes
    # a special string form <package_name>:<path>, which we construct here.
    msg_package_name, msg_package_base = pkg_name_and_base_from_path(idl_file.path)
    include_path = "{}:{}".format(msg_package_name, msg_package_base)

    # Collect all of the sources from the dependencies.
    return [
        RosTypeDescriptionInfo(
            jsons = depset(
                direct = [json_file],
                transitive = [
                    dep[RosTypeDescriptionInfo].jsons
                    for dep in ctx.rule.attr.deps
                    if RosTypeDescriptionInfo in dep
                ],
            ),
            include_paths = depset(
                direct = [include_path],
                transitive = [
                    dep[RosTypeDescriptionInfo].include_paths
                    for dep in ctx.rule.attr.deps
                    if RosTypeDescriptionInfo in dep
                ],
            ),
        ),
    ]

rosidl_generator_type_description_aspect = aspect(
    implementation = _rosidl_generator_type_description_aspect_impl,
    attr_aspects = ["deps"],
    attrs = {
        "_rosidl_generator": attr.label(
            default = Label("//:rosidl_generator"),
            executable = True,
            cfg = "exec",
        ),
        "_rosidl_templates": attr.label(
            default = Label("//:templates"),
        ),
    },
    required_providers = [RosInterfaceInfo],
    required_aspect_providers = [RosIdlInfo],
    provides = [RosTypeDescriptionInfo],
)

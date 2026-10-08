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

load(":tools.bzl", "snake_case_from_pascal_case")
load(":types.bzl", "RosIdlInfo", "RosInterfaceInfo")

def _rosidl_adapter_aspect_impl(target, ctx):
    src = target[RosInterfaceInfo].src

    # Calculate the metadata to package alongside the IDL.
    package_name = target[RosInterfaceInfo].package  # eg. sensor_msgs
    interface_type = "msg" if src.extension == "idl" else src.extension  # eg. msg
    interface_name = src.basename[:-len(src.extension) - 1]  # eg. CompressedImage
    interface_code = snake_case_from_pascal_case(interface_name)  # eg. compressed_image

    # Declare the output IDL file.
    dst = ctx.actions.declare_file(
        "{}/{}/{}.idl".format(package_name, interface_type, interface_name),
    )

    # The tool we use depends on the file suffix.
    executable_map = {
        "msg": ctx.executable._msg2idl,
        "srv": ctx.executable._srv2idl,
        "action": ctx.executable._action2idl,
    }

    # For the three fundamental message types we use generators.
    if src.extension in ["msg", "srv", "action"]:
        executable = executable_map[src.extension]
        rel_src_path = target.label.package + "/" + src.basename if target.label.package else src.basename
        pkg_root = src.path[:-len(rel_src_path) - 1]
        ctx.actions.run_shell(
            command = "{exec} -p {src_dir} -n {pkg} {src_name} {dst_dir} {out}".format(
                exec = executable.path,
                src_dir = pkg_root if pkg_root else ".",
                pkg = package_name,
                src_name = rel_src_path,
                dst_dir = dst.dirname,
                out = "> /dev/null 2>&1",
            ),
            tools = [executable],
            inputs = [src],
            outputs = [dst],
            mnemonic = "IdlFrom{}".format(src.extension),
            progress_message = "Generating IDL files for {}".format(ctx.label.name),
        )
    elif src.extension == "idl":
        ctx.actions.symlink(output = dst, target_file = src)
    else:
        fail("Unknown file extension: " + src.extension)

    # Return the IDL file and some extra information used by follow-on aspects.
    return [
        RosIdlInfo(
            idl = dst,
            interface_type = interface_type,
            interface_name = interface_name,
            interface_code = interface_code,
            package_name = package_name,
        ),
        DefaultInfo(
            files = depset(
                direct = [target[RosInterfaceInfo].src, dst],
                transitive = [dep[DefaultInfo].files for dep in ctx.rule.attr.deps],
            ),
        ),
    ]

# IDL aspect runs along the deps property to generate IDLs for each RosInterface,
# through one of the three cli tools, producing a ROS IDL for each one.
rosidl_adapter_aspect = aspect(
    implementation = _rosidl_adapter_aspect_impl,
    attr_aspects = ["deps"],
    attrs = {
        "_msg2idl": attr.label(
            default = Label("//:msg2idl"),
            executable = True,
            cfg = "exec",
        ),
        "_srv2idl": attr.label(
            default = Label("//:srv2idl"),
            executable = True,
            cfg = "exec",
        ),
        "_action2idl": attr.label(
            default = Label("//:action2idl"),
            executable = True,
            cfg = "exec",
        ),
    },
    required_providers = [RosInterfaceInfo],
    provides = [RosIdlInfo, DefaultInfo],
)

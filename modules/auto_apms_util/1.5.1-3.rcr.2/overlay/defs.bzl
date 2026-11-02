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

"""Bazel rule for generating AutoAPMS pluginlib XML manifests."""

def _auto_apms_util_register_plugins_impl(ctx):
    out = ctx.outputs.out
    lines = ["<class_libraries>"]
    for entry in ctx.attr.plugins:
        parts = entry.split("|")
        lib, cls, reg_type, base_cls = parts[0], parts[1], parts[2], parts[3]
        lines.append('<library path="{}"><class name="{}" type="{}" base_class_type="{}" /></library>'.format(
            lib,
            cls,
            reg_type,
            base_cls,
        ))
    lines.append("</class_libraries>")
    ctx.actions.write(output = out, content = "\n".join(lines) + "\n")
    return [DefaultInfo(files = depset([out]))]

auto_apms_util_register_plugins = rule(
    implementation = _auto_apms_util_register_plugins_impl,
    attrs = {
        "out": attr.output(mandatory = True),
        "plugins": attr.string_list(mandatory = True),
    },
)

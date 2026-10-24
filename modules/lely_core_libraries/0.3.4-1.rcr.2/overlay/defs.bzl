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

"""Bazel equivalents of cmake/lely_core_libraries-extras.cmake.

generate_dcf(TARGET) / cogen_dcf(TARGET) upstream:
  * (cogen_dcf only) cogen --input-file config/<T>/bus.yml
                           --output-file <build>/config/<T>/preprocessed_bus.yml
  * sed 's|@BUS_CONFIG_PATH@|<prefix>/share/<pkg>/config/<T>|g' -> <build>/config/<T>/bus.yml
  * dcfgen -v -d <build>/config/<T>/ -rS <build>/config/<T>/bus.yml
    (run from config/<T>/ so relative EDS/DCF paths resolve)

The generated files are installed next to the source config directory, i.e.
share/<pkg>/config/<T>/.
"""

load("@bazel_skylib//rules:common_settings.bzl", "BuildSettingInfo")

def _lely_dcf_impl(ctx):
    install_prefix = ctx.attr._install_prefix[BuildSettingInfo].value.rstrip("/")

    # ament_package installs each package into an isolated prefix
    # (<install_prefix>/<pkg>), which is CMAKE_INSTALL_PREFIX for upstream's
    # ${CMAKE_INSTALL_PREFIX}/share/${PROJECT_NAME}/config/${TARGET}.
    bus_config_path = "%s/%s/share/%s/config/%s" % (
        install_prefix,
        ctx.attr.package,
        ctx.attr.package,
        ctx.attr.target,
    )

    out_dir = "_gen/share/%s/config/%s" % (ctx.attr.package, ctx.attr.target)
    names = ["bus.yml", "master.dcf"] + ctx.attr.extra_outs
    if ctx.attr.cogen:
        names.append("preprocessed_bus.yml")
    outs = [ctx.actions.declare_file(out_dir + "/" + n) for n in names]
    out_path = outs[0].dirname

    cmds = ["set -e", "OUT=$PWD/" + out_path, "mkdir -p $OUT"]
    if ctx.attr.cogen:
        cmds.append("{cogen} --input-file {bus} --output-file $OUT/preprocessed_bus.yml".format(
            cogen = ctx.executable._cogen.path,
            bus = ctx.file.bus.path,
        ))
        sed_in = "$OUT/preprocessed_bus.yml"
    else:
        sed_in = ctx.file.bus.path
    cmds.append("sed 's|@BUS_CONFIG_PATH@|{p}|g' {i} > $OUT/bus.yml".format(p = bus_config_path, i = sed_in))
    cmds.append("DCFGEN=$PWD/" + ctx.executable._dcfgen.path)
    cmds.append("cd {d} && $DCFGEN -v -d $OUT/ -rS $OUT/bus.yml > /dev/null".format(d = ctx.file.bus.dirname))

    ctx.actions.run_shell(
        inputs = [ctx.file.bus] + ctx.files.srcs,
        outputs = outs,
        tools = [ctx.executable._dcfgen, ctx.executable._cogen],
        command = "\n".join(cmds),
        mnemonic = "LelyDcfgen",
        progress_message = "Generating CANopen DCF for %s" % ctx.attr.target,
    )
    return [DefaultInfo(files = depset(outs))]

_lely_dcf = rule(
    implementation = _lely_dcf_impl,
    attrs = {
        "bus": attr.label(allow_single_file = [".yml"], mandatory = True),
        "cogen": attr.bool(default = False),
        "extra_outs": attr.string_list(
            doc = "Additional files dcfgen writes (e.g. concise DCF <slave>.bin).",
        ),
        "package": attr.string(mandatory = True),
        "srcs": attr.label_list(allow_files = True, doc = "EDS/DCF files referenced by bus.yml."),
        "target": attr.string(mandatory = True),
        "_cogen": attr.label(default = "//:cogen_tool", executable = True, cfg = "exec"),
        "_dcfgen": attr.label(default = "@rosdistro//python:dcfgen", executable = True, cfg = "exec"),
        "_install_prefix": attr.label(default = "@rosdistro//:install_prefix"),
    },
)

def generate_dcf(name, target, srcs = [], extra_outs = [], **kwargs):
    """generate_dcf(<target>) from lely_core_libraries-extras.cmake."""
    _lely_dcf(
        name = name,
        bus = "config/%s/bus.yml" % target,
        package = native.module_name(),
        srcs = srcs,
        target = target,
        extra_outs = extra_outs,
        **kwargs
    )

def cogen_dcf(name, target, srcs = [], extra_outs = [], **kwargs):
    """cogen_dcf(<target>) from lely_core_libraries-extras.cmake."""
    _lely_dcf(
        name = name,
        bus = "config/%s/bus.yml" % target,
        cogen = True,
        package = native.module_name(),
        srcs = srcs,
        target = target,
        extra_outs = extra_outs,
        **kwargs
    )

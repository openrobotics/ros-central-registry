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

"""Bazel port of mavlink's generateMavlink_v10 / generateMavlink_v20 macros.

Upstream CMakeLists.txt runs, for every dialect in message_definitions/v1.0
(minus minimal/test/python_array_test, list(SORT)ed):
  mavgen.py --lang=C     --wire-protocol=1.0 --output=include/v1.0 <dialect>.xml
  mavgen.py --lang=C++11 --wire-protocol=2.0 --output=include/v2.0 <dialect>.xml
Dialects share output directories (each run also writes the dialects it
includes), so the run order decides which copy of a shared file survives.
CMake only constrains common.xml-v2.0 to run after every other dialect; this
rule uses that order deterministically (ASCII-sorted, common last) for both
protocols.
"""

def _mavlink_generate_impl(ctx):
    out = ctx.actions.declare_directory(ctx.attr.out_dir)
    defs = {f.basename[:-len(".xml")]: f for f in ctx.files.definitions}
    order = [d for d in ctx.attr.dialects if d != "common"]
    if "common" in ctx.attr.dialects:
        order.append("common")
    cmds = ["set -e", "OUT=$PWD/" + out.path, "mkdir -p $OUT"]
    for d in order:
        if d not in defs:
            fail("dialect %s has no message definition" % d)
        cmds.append("{mavgen} --lang={lang} --wire-protocol={wp} --output=$OUT {xml} > /dev/null".format(
            mavgen = ctx.executable._mavgen.path,
            lang = ctx.attr.lang,
            wp = ctx.attr.wire_protocol,
            xml = defs[d].path,
        ))
    ctx.actions.run_shell(
        inputs = ctx.files.definitions,
        outputs = [out],
        tools = [ctx.executable._mavgen],
        command = "\n".join(cmds),
        # version.h embeds MAVLINK_BUILD_DATE; pin it (see the mavparse.py
        # patch) so the generated headers are reproducible.
        env = {"SOURCE_DATE_EPOCH": ctx.attr.source_date_epoch},
        mnemonic = "Mavgen",
        progress_message = "Generating MAVLink %s headers (%s)" % (ctx.attr.wire_protocol, ctx.attr.lang),
    )
    return [DefaultInfo(files = depset([out]))]

mavlink_generate = rule(
    implementation = _mavlink_generate_impl,
    attrs = {
        "definitions": attr.label_list(allow_files = [".xml"], mandatory = True),
        "dialects": attr.string_list(mandatory = True),
        "lang": attr.string(mandatory = True),
        "out_dir": attr.string(mandatory = True),
        # 2026-09-09T00:00:00Z, the date in this package's version.
        "source_date_epoch": attr.string(default = "1788912000"),
        "wire_protocol": attr.string(mandatory = True),
        "_mavgen": attr.label(default = "//:mavgen", executable = True, cfg = "exec"),
    },
)

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

load("@crates_zenoh_c//:data.bzl", "DEP_DATA")
load("@rules_rust//rust:defs.bzl", "rust_common")

_EXTRA_ZENOH_C_FEATURES = [
    "shared-memory",
    "transport_serial",
    "transport_vsock",
    "unstable",
]

def _dedupe(items):
    result = []
    seen = {}
    for item in items:
        if item not in seen:
            result.append(item)
            seen[item] = True
    return result

def zenoh_c_crate_features(extra = []):
    return _dedupe(DEP_DATA[""]["crate_features"] + _EXTRA_ZENOH_C_FEATURES + extra)

def opaque_type_crate_features():
    return zenoh_c_crate_features(extra = ["panic"])

def _rust_build_script_archive_impl(ctx):
    dep_info = ctx.attr.crate[rust_common.dep_info]
    out_dirs = [
        bi.out_dir
        for bi in dep_info.transitive_build_infos.to_list()
        if bi.out_dir and ctx.attr.crate_filter in bi.out_dir.short_path
    ]
    if not out_dirs:
        fail("No cargo_build_script out_dir matching '{}' in {}".format(
            ctx.attr.crate_filter,
            ctx.attr.crate.label,
        ))
    out = ctx.actions.declare_file("lib{}.a".format(ctx.label.name))
    ctx.actions.run_shell(
        inputs = out_dirs,
        outputs = [out],
        command = "cp {}/{} {}".format(
            out_dirs[0].path,
            ctx.attr.archive_glob,
            out.path,
        ),
        mnemonic = "ExtractCargoBuildScriptArchive",
    )
    return [DefaultInfo(files = depset([out]))]

rust_build_script_archive = rule(
    implementation = _rust_build_script_archive_impl,
    attrs = {
        "archive_glob": attr.string(mandatory = True),
        "crate": attr.label(mandatory = True, providers = [rust_common.dep_info]),
        "crate_filter": attr.string(mandatory = True),
    },
)

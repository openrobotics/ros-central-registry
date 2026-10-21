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

load("@rules_cc//cc/common:cc_common.bzl", "cc_common")
load("@rules_cc//cc/common:cc_info.bzl", "CcInfo")
load("@rules_cc//cc/common:cc_shared_library_info.bzl", "CcSharedLibraryInfo")
load(":aspects.bzl", "collect_transitive_dynamic_deps_aspect")
load(":types.bzl", "CollectedCcSharedLibraryInfo")

def _collect_transitive_dynamic_deps_impl(ctx):
    transitive_cc_shared_library_infos = []
    for dep in ctx.attr.dynamic_deps:
        if CollectedCcSharedLibraryInfo in dep:
            transitive_cc_shared_library_infos.append(dep[CollectedCcSharedLibraryInfo].cc_shared_library_info)
        elif CcSharedLibraryInfo in dep:
            transitive_cc_shared_library_infos.append(dep[CcSharedLibraryInfo])

    # 1. Flatten the list of depsets into a single depset and convert to list for iteration
    all_infos = depset(transitive = transitive_cc_shared_library_infos, order = "topological").to_list()

    # 2. Collect the 'libraries' depset from each CcSharedLibraryInfo's linker_input
    transitive_libs = []
    files_to_propagate = []
    for info in all_infos:
        # Check if it has linker_input and it's not None
        if hasattr(info, "linker_input") and info.linker_input:
            transitive_libs += info.linker_input.libraries
            for lib in info.linker_input.libraries:
                if lib.dynamic_library:
                    files_to_propagate.append(lib.dynamic_library)

    linker_input = cc_common.create_linker_input(
        owner = ctx.label,
        libraries = depset(direct = transitive_libs, order = "topological"),
    )

    return [
        CcSharedLibraryInfo(
            # Same entry shape rules_cc's cc_shared_library builds for its own
            # dynamic_deps (see _merge_cc_shared_library_infos), so a shared
            # library reached both through this target and directly (e.g.
            # @qtbase//:widgets_shared) compares equal and is deduplicated,
            # instead of tripping the link-once check as two distinct entries.
            dynamic_deps = depset(
                direct = [
                    struct(
                        exports = info.exports,
                        linker_input = info.linker_input,
                        link_once_static_libs = info.link_once_static_libs,
                    )
                    for info in all_infos
                ],
                order = "topological",
            ),
            exports = [],
            linker_input = linker_input,
            link_once_static_libs = [],
        ),
        DefaultInfo(
            files = depset(direct = files_to_propagate),
            runfiles = ctx.runfiles(files = files_to_propagate),
        ),
    ]

collect_transitive_dynamic_deps = rule(
    implementation = _collect_transitive_dynamic_deps_impl,
    attrs = {
        "dynamic_deps": attr.label_list(
            aspects = [
                collect_transitive_dynamic_deps_aspect,
            ],
            providers = [CcSharedLibraryInfo],
            allow_files = False,
        ),
    },
    provides = [CcSharedLibraryInfo],
)

def _cc_public_headers_impl(ctx):
    headers = []
    for dep in ctx.attr.deps:
        headers.extend(dep[CcInfo].compilation_context.direct_public_headers)
        headers.extend(dep[CcInfo].compilation_context.direct_textual_headers)
    if ctx.attr.prefix:
        # short_path of a file in an external repo is ../<repo>/<path>.
        headers = [h for h in headers if h.short_path.removeprefix("../").split("/", 1)[-1].startswith(ctx.attr.prefix)]
    if ctx.attr.extensions:
        headers = [h for h in headers if any([h.basename.endswith(e) for e in ctx.attr.extensions])]
    return [DefaultInfo(files = depset(headers))]

cc_public_headers = rule(
    implementation = _cc_public_headers_impl,
    doc = "The direct public headers of cc_library targets, as files (e.g. to install a third-party library's headers).",
    attrs = {
        "deps": attr.label_list(providers = [CcInfo], mandatory = True),
        "prefix": attr.string(doc = "Only keep headers whose repository-relative path starts with this prefix."),
        "extensions": attr.string_list(doc = "Only keep headers with one of these file extensions (e.g. ['.hpp'])."),
    },
)

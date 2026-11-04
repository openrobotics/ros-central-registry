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

"""Expose the runtime shared-library closure of cc_shared_library targets.

`cc_shared_library` puts its own `.so` plus the runfiles of every
`dynamic_deps` entry (recursively) into its default runfiles, but a `genrule`
only sees a target's default *outputs*. This rule re-exports those runfiles
as plain files so a genrule can `dlopen` the library with every transitive
shared dependency on `LD_LIBRARY_PATH`, in both dynamic and static
(`--dynamic_mode=off`) builds.
"""

def _shared_library_runfiles_impl(ctx):
    return [DefaultInfo(files = depset(transitive = [
        dep[DefaultInfo].default_runfiles.files
        for dep in ctx.attr.deps
    ] + [
        dep[DefaultInfo].files
        for dep in ctx.attr.deps
    ]))]

shared_library_runfiles = rule(
    implementation = _shared_library_runfiles_impl,
    attrs = {
        "deps": attr.label_list(
            doc = "cc_shared_library targets whose runtime closure to expose.",
            allow_files = False,
        ),
    },
)

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

"""Bazel port of ViSP's generated meta headers.

Mirrors, for a given set of built/disabled modules:
  * cmake/VISPModule.cmake      vp_create_global_module_header() -> visp3/visp_<m>.h
  * cmake/VISPModule.cmake      vp_create_compat_headers()       -> visp/<h>.h
  * cmake/VISPGenerateHeaders.cmake                                -> visp3/visp_modules.h, visp3/visp.h
All files are rendered from the upstream templates in cmake/templates/.
"""

load("@bazel_skylib//rules:expand_template.bzl", "expand_template")

_HEADER_TEMPLATE = "cmake/templates/vpHeader.h.in"

def _module_public_headers(hdrs, module):
    """VISP_MODULE_<m>_HEADERS: include/visp3/<m>/*.h (non-recursive)."""
    out = []
    marker = "/include/visp3/%s/" % module
    for h in hdrs:
        if marker in h and "/" not in h.split(marker)[1]:
            out.append("visp3/%s/%s" % (module, h.split(marker)[1]))
    return sorted(out)

def visp_generated_headers(name, hdrs, modules, module_deps, disabled_modules, out_dir = "_gen/include/visp"):
    """Declare all generated ViSP meta headers.

    Args:
      name: filegroup collecting every generated header.
      hdrs: all source headers (labels/paths) of the package.
      modules: built (public) modules, short names (e.g. "core").
      module_deps: dict module -> required visp module deps (vp_add_module).
      disabled_modules: modules known to the build but not built.
      out_dir: include root for the generated headers.
    """
    targets = []

    # visp3/visp_<m>.h
    for m in modules:
        content = "#ifndef __visp_%s_h_\n#define __visp_%s_h_\n" % (m, m)
        if m == "core":
            content += "\n#include <visp3/core/vpConfig.h>"
        for dep in module_deps.get(m, []):
            content += "\n#include <visp3/visp_%s.h>" % dep
        for h in _module_public_headers(hdrs, m):
            content += "\n#include <%s>" % h
        if m == "core":
            # VISPModule.cmake appends the generated headers to core's list;
            # vp_create_global_module_header() then rewrites "^.*/include/visp3"
            # to "visp3". (With an include/visp install layout that regex
            # misses and upstream leaks absolute build paths; emit the
            # intended relative form instead.)
            content += "\n#include <visp3/core/vpConfig.h>"
            content += "\n#include <visp3/visp_modules.h>"
        content += "\n\n#endif\n"
        expand_template(
            name = "%s_visp_%s_h" % (name, m),
            out = "%s/visp3/visp_%s.h" % (out_dir, m),
            substitutions = {"@VISP_HEADER_CONTENT_CONFIGMAKE@": content},
            template = _HEADER_TEMPLATE,
        )
        targets.append(":%s_visp_%s_h" % (name, m))

    # visp3/visp_modules.h
    content = "#ifndef _visp_modules_h_\n#define _visp_modules_h_\n\n"
    for m in sorted(modules):
        content += "#define VISP_HAVE_MODULE_%s\n" % m.upper()
    content += "\n#endif\n"
    expand_template(
        name = name + "_visp_modules_h",
        out = out_dir + "/visp3/visp_modules.h",
        substitutions = {"@VISP_MODULE_DEFINITIONS_CONFIGMAKE@": content},
        template = "cmake/templates/visp_modules.h.in",
    )
    targets.append(":%s_visp_modules_h" % name)

    # visp3/visp.h
    content = "#ifndef _visp_h_\n#define _visp_h_\n\n"
    content += "// File that defines which modules where included during ViSP build\n"
    content += "// It contains the defines of the correct VISP_HAVE_MODULE_<modulename> values\n"
    content += "#include <visp3/visp_modules.h>\n\n"
    content += "// Then the list of defines is checked to include the correct headers\n"
    for m in sorted(modules + disabled_modules):
        if m == "core":
            content += "// Core library is always included; without no ViSP functionality available\n"
            content += "#include <visp3/visp_%s.h>\n\n" % m
        else:
            content += "#ifdef VISP_HAVE_MODULE_%s\n#  include <visp3/visp_%s.h>\n#endif\n\n" % (m.upper(), m)
    content += "#endif\n"
    expand_template(
        name = name + "_visp_h",
        out = out_dir + "/visp3/visp.h",
        substitutions = {"@VISP_ALL_HEADERS_CONFIGMAKE@": content},
        template = "cmake/templates/visp.h.in",
    )
    targets.append(":%s_visp_h" % name)

    # visp/<h>.h compat headers (vp_create_compat_headers)
    for compat, include in [("visp_modules", "visp3/visp_modules.h"), ("vpConfig", "visp3/core/vpConfig.h")]:
        expand_template(
            name = "%s_compat_%s_h" % (name, compat),
            out = "%s/visp/%s.h" % (out_dir, compat),
            substitutions = {
                "@VISP_HEADER_CONTENT_CONFIGMAKE@": "#ifndef __%s_gen_h_\n#define __%s_gen_h_\n\n#include <%s>\n\n#endif\n" % (compat, compat, include),
            },
            template = _HEADER_TEMPLATE,
        )
        targets.append(":%s_compat_%s_h" % (name, compat))

    native.filegroup(
        name = name,
        srcs = targets,
    )

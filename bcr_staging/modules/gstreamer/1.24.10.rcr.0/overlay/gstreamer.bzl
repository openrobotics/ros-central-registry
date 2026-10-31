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

"""Helper macros for building GStreamer enum types."""

load("@glib//gobject:gobject.bzl", "mkenums")

def gst_mkenums_simple(
        name,
        srcs,
        out_h,
        out_c,
        header_prefix = "",
        body_prefix = "",
        decorator = "",
        include_prefix = ""):
    """Generates GObject enum type header and source matching Meson's gnome.mkenums_simple."""
    h_basename = out_h.split("/")[-1]
    h_fhead = "#pragma once\n\n#include <glib-object.h>\n"
    if header_prefix:
        h_fhead += header_prefix + "\n"
    h_fhead += "\nG_BEGIN_DECLS\n"

    h_vhead = ""
    if decorator:
        h_vhead += decorator + "\n"
    h_vhead += "GType @enum_name@_get_type (void);\n#define @ENUMPREFIX@_TYPE_@ENUMSHORT@ (@enum_name@_get_type())\n"

    mkenums(
        name = name + "_h",
        srcs = srcs,
        out = out_h,
        options = [
            "--fhead",
            h_fhead,
            "--fprod",
            "\n/* enumerations from \"@basename@\" */\n",
            "--vhead",
            h_vhead,
            "--ftail",
            "G_END_DECLS\n",
        ],
    )

    c_fhead = ""
    if body_prefix:
        c_fhead += body_prefix + "\n"
    if include_prefix:
        c_fhead += "#include <" + include_prefix + "/" + h_basename + ">\n"
    else:
        c_fhead += "#include \"" + h_basename + "\"\n"
    for src in srcs:
        s_base = src.split("/")[-1]
        if include_prefix:
            c_fhead += "#include <" + include_prefix + "/" + s_base + ">\n"
        else:
            c_fhead += "#include \"" + s_base + "\"\n"

    c_vhead = "\nGType\n@enum_name@_get_type (void)\n{\n  static gsize g_define_type_id__volatile = 0;\n  if (g_once_init_enter (&g_define_type_id__volatile)) {\n    static const G@Type@Value values[] = {\n"
    c_vprod = "      { @VALUENAME@, \"@VALUENAME@\", \"@valuenick@\" },\n"
    c_vtail = "      { 0, NULL, NULL }\n    };\n    GType g_define_type_id =\n       g_@type@_register_static (g_intern_static_string (\"@EnumName@\"), values);\n    g_once_init_leave (&g_define_type_id__volatile, g_define_type_id);\n  }\n  return g_define_type_id__volatile;\n}\n"

    mkenums(
        name = name + "_c",
        srcs = srcs,
        out = out_c,
        options = [
            "--fhead",
            c_fhead,
            "--fprod",
            "\n/* enumerations from \"@basename@\" */",
            "--vhead",
            c_vhead,
            "--vprod",
            c_vprod,
            "--vtail",
            c_vtail,
        ],
    )

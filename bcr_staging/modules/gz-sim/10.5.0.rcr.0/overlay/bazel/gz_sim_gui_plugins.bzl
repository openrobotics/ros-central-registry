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

load("@gz-gui//:gui_plugins.bzl", "GZ_GUI_QT_SHARED_DEPS")
load("@rules_cc//cc:defs.bzl", "cc_binary")

def gz_sim_gui_plugin(name, srcs = [], hdrs = [], qrc = None, qml = [], moc_headers = [], deps = [], dynamic_deps = []):
    """Helper macro to build a GUI plugin shared library for gz-sim.

    Args:
      name: Name of the plugin (produces lib<name>.so).
      srcs: Source files.
      hdrs: Non-MOC header files.
      qrc: RCC resource file.
      qml: QML and image resource files referenced by qrc.
      moc_headers: Headers that need MOC compilation.
      deps: Additional cc_library dependencies.
      dynamic_deps: Additional cc_shared_library dependencies.
    """
    moc_files = []
    for hdr in moc_headers:
        moc_name = "moc_" + name + "_" + hdr.split("/")[-1].replace(".hh", "").replace(".h", "")
        native.genrule(
            name = moc_name,
            srcs = [hdr],
            outs = [hdr.replace(".hh", "_moc.cpp").replace(".h", "_moc.cpp")],
            cmd = "$(execpath @qtbase//:moc) $< -o $@",
            tools = ["@qtbase//:moc"],
        )
        moc_files.append(":" + moc_name)

    rcc_files = []
    if qrc:
        rcc_name = "qrc_" + name
        native.genrule(
            name = rcc_name,
            srcs = [qrc] + qml,
            outs = [qrc.replace(".qrc", "_rcc.cpp")],
            cmd = "ROOT=$$PWD && cd $$(dirname $(execpath %s)) && $$ROOT/$(execpath @qtbase//:rcc) --name %s --output $$ROOT/$@ $$(basename $(execpath %s))" % (qrc, name, qrc),
            tools = ["@qtbase//:rcc"],
        )
        rcc_files.append(":" + rcc_name)

    dir_name = srcs[0].rsplit("/", 1)[0] if srcs else ""

    cc_binary(
        name = "lib" + name + ".so",
        srcs = srcs + hdrs + moc_headers + moc_files + rcc_files,
        copts = ([
            "-fPIC",
            "-Wno-private-header",
            "-I" + dir_name,
            "-I$(GENDIR)/" + dir_name,
            "-Iexternal/gz-sim+/" + dir_name,
            "-I$(GENDIR)/external/gz-sim+/" + dir_name,
            "-Isrc/gui",
            "-Iexternal/gz-sim+/src/gui",
            "-Iexternal/gz-sim+",
            "-I$(GENDIR)/external/gz-sim+",
        ] if dir_name else ["-fPIC", "-Wno-private-header"]),
        dynamic_deps = GZ_GUI_QT_SHARED_DEPS + [
            "@gz-gui//:libgz-gui-shared.so",
            "//:libgz-sim-gui-shared.so",
        ] + dynamic_deps,
        features = ["-layering_check"],
        linkshared = True,
        linkstatic = False,
        visibility = ["//visibility:public"],
        deps = [
            "//:gz-sim",
            "//:gz-sim-gui",
            "@com_google_protobuf//:protobuf",
            "@gz-common",
            "@gz-common//events",
            "@gz-common//geospatial",
            "@gz-common//graphics",
            "@gz-common//io",
            "@gz-common//profiler",
            "@gz-gui",
            "@gz-math",
            "@gz-msgs",
            "@gz-msgs//:gzmsgs_cc_proto",
            "@gz-plugin//:core",
            "@gz-plugin//:loader",
            "@gz-plugin//:register",
            "@gz-rendering",
            "@gz-transport",
            "@gz-utils",
            "@qtbase//:core",
            "@qtbase//:gui",
            "@qtbase//:widgets",
            "@qtdeclarative//:qml",
            "@qtdeclarative//:quick",
            "@qtdeclarative//:quickcontrols2",
            "@sdformat",
            "@tinyxml2",
        ] + deps,
    )

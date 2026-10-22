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

load("@rules_cc//cc:defs.bzl", "cc_binary")

# Qt is built from source as static cc_library targets plus matching
# cc_shared_library (`*_shared`) targets. Every shared object here must link
# the shared variants so a process only ever contains one copy of Qt (one
# QGuiApplication / QML engine type registry).
GZ_GUI_QT_SHARED_DEPS = [
    "@qtbase//:core_shared",
    "@qtbase//:gui_shared",
    "@qtbase//:opengl_shared",
    "@qtbase//:openglwidgets_shared",
    "@qtbase//:widgets_shared",
    "@qtdeclarative//:qml_shared",
    "@qtdeclarative//:qmlmeta_shared",
    "@qtdeclarative//:qmlworkerscript_shared",
    "@qtdeclarative//:quick_shared",
    "@qtdeclarative//:quickcontrols2_shared",
    "@qtdeclarative//:quickcontrols2impl_shared",
    "@qtdeclarative//:quicktemplates2_shared",
]

def gz_gui_plugin(name, srcs = [], hdrs = [], qrc = None, qml = [], moc_headers = [], deps = []):
    """Helper macro to build a simple plugin shared library for gz-gui.

    Args:
      name: Name of the plugin.
      srcs: Source files.
      hdrs: Header files.
      qrc: RCC resource file.
      qml: QML source files.
      moc_headers: Headers that need MOC compilation.
      deps: Dependencies.
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
            cmd = "ROOT=$$PWD && cd $$(dirname $(location %s)) && $$ROOT/$(execpath @qtbase//:rcc) --name %s --output $$ROOT/$@ $$(basename $(location %s))" % (qrc, name, qrc),
            tools = ["@qtbase//:rcc"],
        )
        rcc_files.append(":" + rcc_name)

    dir_name = srcs[0].rsplit("/", 1)[0] if srcs else ""

    cc_binary(
        name = "lib" + name + ".so",
        srcs = srcs + hdrs + moc_headers + moc_files + rcc_files,
        copts = [
            "-fPIC",
            "-I" + dir_name,
            "-I$(GENDIR)/" + dir_name,
            "-Iexternal/gz-gui+/" + dir_name,
            "-I$(GENDIR)/external/gz-gui+/" + dir_name,
            "-Iexternal/gz-gui+",
            "-I$(GENDIR)/external/gz-gui+",
        ] if dir_name else ["-fPIC"],
        dynamic_deps = GZ_GUI_QT_SHARED_DEPS + [
            "//:libgz-gui-shared.so",
        ],
        linkshared = True,
        linkstatic = False,
        visibility = ["//visibility:public"],
        deps = [
            "//:gz-gui",
            "@gz-plugin//:register",
            "@qtbase//:core",
            "@qtbase//:gui",
            "@qtdeclarative//:qml",
            "@qtdeclarative//:quick",
            "@qtbase//:widgets",
        ] + deps,
    )

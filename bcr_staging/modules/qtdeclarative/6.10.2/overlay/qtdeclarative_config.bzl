"""Generated configuration headers and RegExpJitTables.h helper for @qtdeclarative 6.10.2."""

load("@qt//:qt_tools.bzl", "qt_write_file")
load("@rules_cc//cc:cc_library.bzl", "cc_library")

_QTQML_CONFIG_H = """#ifndef QT_QML_CONFIG_H
#define QT_QML_CONFIG_H

#define QT_FEATURE_qml_network 1
#define QT_FEATURE_qml_ssl 1
#define QT_FEATURE_qml_debug 1

#endif // QT_QML_CONFIG_H
"""

_QTQML_CONFIG_P_H = """#ifndef QT_QML_CONFIG_P_H
#define QT_QML_CONFIG_P_H

#include "qtqml-config.h"

#if defined(__x86_64__) || defined(_M_X64) || ((defined(__aarch64__) || defined(_M_ARM64)) && !defined(_WIN32))
#  define QT_FEATURE_qml_jit 1
#else
#  define QT_FEATURE_qml_jit -1
#endif

#define QT_FEATURE_qml_profiler 1
#define QT_FEATURE_qml_preview 1
#define QT_FEATURE_qml_xml_http_request 1
#define QT_FEATURE_qml_locale 1
#define QT_FEATURE_qml_animation 1
#define QT_FEATURE_qml_worker_script 1
#define QT_FEATURE_qml_itemmodel 1
#define QT_FEATURE_qml_xmllistmodel 1
#define QT_FEATURE_qml_type_loader_thread 1
#define QT_FEATURE_qml_python 1

#define QT_QML_JIT_SUPPORTED_IMPL 0
#undef QT_QML_JIT_SUPPORTED_IMPL
#if QT_CONFIG(qml_jit) && !(defined(Q_OS_MACOS) && defined(Q_PROCESSOR_ARM))
#define QT_QML_JIT_SUPPORTED_IMPL 1
#else
#define QT_QML_JIT_SUPPORTED_IMPL 0
#endif
#undef QT_FEATURE_qml_jit
#if QT_QML_JIT_SUPPORTED_IMPL
#define QT_FEATURE_qml_jit 1
#else
#define QT_FEATURE_qml_jit -1
#endif

#endif // QT_QML_CONFIG_P_H
"""

_QTQMLMODELS_CONFIG_H = """#ifndef QT_QMLMODELS_CONFIG_H
#define QT_QMLMODELS_CONFIG_H

#endif // QT_QMLMODELS_CONFIG_H
"""

_QTQMLMODELS_CONFIG_P_H = """#ifndef QT_QMLMODELS_CONFIG_P_H
#define QT_QMLMODELS_CONFIG_P_H

#include "qtqmlmodels-config.h"

#define QT_FEATURE_qml_object_model 1
#define QT_FEATURE_qml_list_model 1
#define QT_FEATURE_qml_delegate_model 1
#define QT_FEATURE_qml_table_model 1
#define QT_FEATURE_qml_tree_model 1
#define QT_FEATURE_qml_sfpm_model 1

#endif // QT_QMLMODELS_CONFIG_P_H
"""

_QTQUICK_CONFIG_H = """#ifndef QT_QUICK_CONFIG_H
#define QT_QUICK_CONFIG_H

#define QT_FEATURE_quick_shadereffect 1
#define QT_FEATURE_quick_draganddrop 1
#define QT_FEATURE_quick_pixmap_cache_threaded_download 1

#endif // QT_QUICK_CONFIG_H
"""

_QTQUICK_CONFIG_P_H = """#ifndef QT_QUICK_CONFIG_P_H
#define QT_QUICK_CONFIG_P_H

#include "qtquick-config.h"

#define QT_FEATURE_quick_animatedimage 1
#define QT_FEATURE_quick_canvas 1
#define QT_FEATURE_quick_designer 1
#define QT_FEATURE_quick_flipable 1
#define QT_FEATURE_quick_gridview 1
#define QT_FEATURE_quick_itemview 1
#define QT_FEATURE_quick_viewtransitions 1
#define QT_FEATURE_quick_listview 1
#define QT_FEATURE_quick_tableview 1
#define QT_FEATURE_quick_treeview 1
#define QT_FEATURE_quick_particles 1
#define QT_FEATURE_quick_path 1
#define QT_FEATURE_quick_pathview 1
#define QT_FEATURE_quick_positioners 1
#define QT_FEATURE_quick_repeater 1
#define QT_FEATURE_quick_sprite 1

#endif // QT_QUICK_CONFIG_P_H
"""

_QTQUICKTEMPLATES2_CONFIG_H = """#ifndef QT_QUICKTEMPLATES2_CONFIG_H
#define QT_QUICKTEMPLATES2_CONFIG_H

#endif // QT_QUICKTEMPLATES2_CONFIG_H
"""

_QTQUICKTEMPLATES2_CONFIG_P_H = """#ifndef QT_QUICKTEMPLATES2_CONFIG_P_H
#define QT_QUICKTEMPLATES2_CONFIG_P_H

#include "qtquicktemplates2-config.h"

#define QT_FEATURE_quicktemplates2_hover 1
#define QT_FEATURE_quicktemplates2_multitouch 1
#define QT_FEATURE_quicktemplates2_calendar 1
#define QT_FEATURE_quicktemplates2_container 1

#endif // QT_QUICKTEMPLATES2_CONFIG_P_H
"""

_QTQUICKCONTROLS2_CONFIG_H = """#ifndef QT_QUICKCONTROLS2_CONFIG_H
#define QT_QUICKCONTROLS2_CONFIG_H

#endif // QT_QUICKCONTROLS2_CONFIG_H
"""

_QTQUICKCONTROLS2_CONFIG_P_H = """#ifndef QT_QUICKCONTROLS2_CONFIG_P_H
#define QT_QUICKCONTROLS2_CONFIG_P_H

#include "qtquickcontrols2-config.h"

#define QT_FEATURE_quickcontrols2_basic 1
#define QT_FEATURE_quickcontrols2_fusion 1
#define QT_FEATURE_quickcontrols2_imagine 1
#define QT_FEATURE_quickcontrols2_material 1
#define QT_FEATURE_quickcontrols2_universal 1
#define QT_FEATURE_quickcontrols2_fluentwinui3 1
#if defined(__APPLE__)
#  define QT_FEATURE_quickcontrols2_macos 1
#  define QT_FEATURE_quickcontrols2_ios 1
#else
#  define QT_FEATURE_quickcontrols2_macos -1
#  define QT_FEATURE_quickcontrols2_ios -1
#endif
#if defined(_WIN32)
#  define QT_FEATURE_quickcontrols2_windows 1
#else
#  define QT_FEATURE_quickcontrols2_windows -1
#endif

#endif // QT_QUICKCONTROLS2_CONFIG_P_H
"""

_QTQUICKSHAPES_CONFIG_H = """#ifndef QT_QUICKSHAPES_CONFIG_H
#define QT_QUICKSHAPES_CONFIG_H

#endif // QT_QUICKSHAPES_CONFIG_H
"""

_QTQUICKSHAPES_CONFIG_P_H = """#ifndef QT_QUICKSHAPES_CONFIG_P_H
#define QT_QUICKSHAPES_CONFIG_P_H

#include "qtquickshapes-config.h"

#define QT_FEATURE_quickshapes_designhelpers 1

#endif // QT_QUICKSHAPES_CONFIG_P_H
"""

_TRACEPOINTS_P_H = """#ifndef QT_DECLARATIVE_TRACEPOINTS_P_H
#define QT_DECLARATIVE_TRACEPOINTS_P_H

#include <QtCore/private/qtrace_p.h>

#endif // QT_DECLARATIVE_TRACEPOINTS_P_H
"""

def declare_qtdeclarative_config_targets():
    """Declares generated config headers and tracepoints headers."""
    qt_write_file(
        name = "gen_qtqml_config_h",
        content = _QTQML_CONFIG_H,
        out = "generated_cfg/QtQml/qtqml-config.h",
    )
    qt_write_file(
        name = "gen_qtqml_config_p_h",
        content = _QTQML_CONFIG_P_H,
        out = "generated_cfg/QtQml/private/qtqml-config_p.h",
    )
    qt_write_file(
        name = "gen_qtqml_tracepoints_p_h",
        content = _TRACEPOINTS_P_H,
        out = "generated_cfg/QtQml/private/qtqml_tracepoints_p.h",
    )
    cc_library(
        name = "qml_internal_cfg",
        hdrs = [
            ":gen_qtqml_config_h",
            ":gen_qtqml_config_p_h",
            ":gen_qtqml_tracepoints_p_h",
            # Pre-generated output of src/3rdparty/masm/yarr/create_regex_tables
            # (deterministic); avoids needing a host python at build time.
            "bazel_prebuilt/yarr/RegExpJitTables.h",
        ],
        includes = [
            "bazel_prebuilt/yarr",
            "generated_cfg",
            "generated_cfg/QtQml",
            "generated_cfg/QtQml/private",
        ],
    )

    qt_write_file(
        name = "gen_qtqmlmodels_config_h",
        content = _QTQMLMODELS_CONFIG_H,
        out = "generated_cfg/QtQmlModels/qtqmlmodels-config.h",
    )
    qt_write_file(
        name = "gen_qtqmlmodels_config_p_h",
        content = _QTQMLMODELS_CONFIG_P_H,
        out = "generated_cfg/QtQmlModels/private/qtqmlmodels-config_p.h",
    )
    cc_library(
        name = "qmlmodels_internal_cfg",
        hdrs = [
            ":gen_qtqmlmodels_config_h",
            ":gen_qtqmlmodels_config_p_h",
        ],
        includes = [
            "generated_cfg",
            "generated_cfg/QtQmlModels",
            "generated_cfg/QtQmlModels/private",
        ],
    )

    qt_write_file(
        name = "gen_qtquick_config_h",
        content = _QTQUICK_CONFIG_H,
        out = "generated_cfg/QtQuick/qtquick-config.h",
    )
    qt_write_file(
        name = "gen_qtquick_config_p_h",
        content = _QTQUICK_CONFIG_P_H,
        out = "generated_cfg/QtQuick/private/qtquick-config_p.h",
    )
    qt_write_file(
        name = "gen_qtquick_tracepoints_p_h",
        content = _TRACEPOINTS_P_H,
        out = "generated_cfg/QtQuick/private/qtquick_tracepoints_p.h",
    )
    cc_library(
        name = "quick_internal_cfg",
        hdrs = [
            ":gen_qtquick_config_h",
            ":gen_qtquick_config_p_h",
            ":gen_qtquick_tracepoints_p_h",
        ],
        includes = [
            "generated_cfg",
            "generated_cfg/QtQuick",
            "generated_cfg/QtQuick/private",
        ],
    )

    qt_write_file(
        name = "gen_qtquicktemplates2_config_h",
        content = _QTQUICKTEMPLATES2_CONFIG_H,
        out = "generated_cfg/QtQuickTemplates2/qtquicktemplates2-config.h",
    )
    qt_write_file(
        name = "gen_qtquicktemplates2_config_p_h",
        content = _QTQUICKTEMPLATES2_CONFIG_P_H,
        out = "generated_cfg/QtQuickTemplates2/private/qtquicktemplates2-config_p.h",
    )
    cc_library(
        name = "quicktemplates2_internal_cfg",
        hdrs = [
            ":gen_qtquicktemplates2_config_h",
            ":gen_qtquicktemplates2_config_p_h",
        ],
        includes = [
            "generated_cfg",
            "generated_cfg/QtQuickTemplates2",
            "generated_cfg/QtQuickTemplates2/private",
        ],
    )

    qt_write_file(
        name = "gen_qtquickcontrols2_config_h",
        content = _QTQUICKCONTROLS2_CONFIG_H,
        out = "generated_cfg/QtQuickControls2/qtquickcontrols2-config.h",
    )
    qt_write_file(
        name = "gen_qtquickcontrols2_config_p_h",
        content = _QTQUICKCONTROLS2_CONFIG_P_H,
        out = "generated_cfg/QtQuickControls2/private/qtquickcontrols2-config_p.h",
    )
    cc_library(
        name = "quickcontrols2_internal_cfg",
        hdrs = [
            ":gen_qtquickcontrols2_config_h",
            ":gen_qtquickcontrols2_config_p_h",
        ],
        includes = [
            "generated_cfg",
            "generated_cfg/QtQuickControls2",
            "generated_cfg/QtQuickControls2/private",
        ],
    )

    qt_write_file(
        name = "gen_qtquickshapes_config_h",
        content = _QTQUICKSHAPES_CONFIG_H,
        out = "generated_cfg/QtQuickShapes/qtquickshapes-config.h",
    )
    qt_write_file(
        name = "gen_qtquickshapes_config_p_h",
        content = _QTQUICKSHAPES_CONFIG_P_H,
        out = "generated_cfg/QtQuickShapes/private/qtquickshapes-config_p.h",
    )
    cc_library(
        name = "quickshapes_internal_cfg",
        hdrs = [
            ":gen_qtquickshapes_config_h",
            ":gen_qtquickshapes_config_p_h",
        ],
        includes = [
            "generated_cfg",
            "generated_cfg/QtQuickShapes",
            "generated_cfg/QtQuickShapes/private",
        ],
    )

    qt_write_file(
        name = "gen_qtqmltest_config_h",
        content = "#ifndef QT_QMLTEST_CONFIG_H\n#define QT_QMLTEST_CONFIG_H\n#endif\n",
        out = "generated_cfg/QtQuickTest/qtqmltest-config.h",
    )
    qt_write_file(
        name = "gen_qtqmltest_config_p_h",
        content = "#ifndef QT_QMLTEST_CONFIG_P_H\n#define QT_QMLTEST_CONFIG_P_H\n#include \"qtqmltest-config.h\"\n#endif\n",
        out = "generated_cfg/QtQuickTest/private/qtqmltest-config_p.h",
    )
    cc_library(
        name = "quicktest_internal_cfg",
        hdrs = [
            ":gen_qtqmltest_config_h",
            ":gen_qtqmltest_config_p_h",
        ],
        includes = [
            "generated_cfg",
            "generated_cfg/QtQuickTest",
            "generated_cfg/QtQuickTest/private",
        ],
    )

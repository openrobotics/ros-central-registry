"""Generated configuration and tracepoint headers for @qtquick3d."""

load("@qt//:qt_tools.bzl", "qt_write_file")

_QTQUICK3D_TRACEPOINTS_P_H = """#ifndef QT_QUICK3D_TRACEPOINTS_P_H
#define QT_QUICK3D_TRACEPOINTS_P_H

#include <QtCore/private/qtrace_p.h>

#endif // QT_QUICK3D_TRACEPOINTS_P_H
"""

def declare_qtquick3d_config_targets():
    """Declares generated tracepoint headers and QML registration stubs for @qtquick3d."""
    qt_write_file(
        name = "gen_qtquick3d_tracepoints_p_h",
        out = "generated_config/qtquick3d_tracepoints_p.h",
        content = _QTQUICK3D_TRACEPOINTS_P_H,
    )
    qt_write_file(
        name = "gen_quick3d_qmltypereg_cpp",
        out = "generated_config/quick3d_qmltyperegistrations.cpp",
        content = """\
#include <QtQuick3D/private/qtquick3dglobal_p.h>
QT_BEGIN_NAMESPACE
void Q_QUICK3D_EXPORT qml_register_types_QtQuick3D() {}
QT_END_NAMESPACE
""",
    )
    qt_write_file(
        name = "gen_qtquick3dxr_config_h",
        out = "generated_config/qtquick3dxr-config.h",
        content = """#ifndef QTQUICK3DXR_CONFIG_H
#define QTQUICK3DXR_CONFIG_H

#endif // QTQUICK3DXR_CONFIG_H
""",
    )
    qt_write_file(
        name = "gen_qtquick3dxr_config_p_h",
        out = "generated_config/qtquick3dxr-config_p.h",
        content = """#ifndef QTQUICK3DXR_CONFIG_P_H
#define QTQUICK3DXR_CONFIG_P_H

#include <QtQuick3DXr/qtquick3dxr-config.h>

#define QT_FEATURE_quick3dxr_openxr 1
#define QT_FEATURE_system_openxr -1

#endif // QTQUICK3DXR_CONFIG_P_H
""",
    )

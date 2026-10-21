"""Generated configuration and QML registration stubs for @qt3d."""

load("@qt//:qt_tools.bzl", "qt_write_file")

_QT3DCORE_CONFIG_H = """#ifndef QT_3DCORE_CONFIG_H
#define QT_3DCORE_CONFIG_H

#define QT_FEATURE_qt3d_assimp 1
#define QT_FEATURE_qt3d_render 1
#define QT_FEATURE_qt3d_input 1
#define QT_FEATURE_qt3d_logic 1
#define QT_FEATURE_qt3d_extras 1
#define QT_FEATURE_qt3d_animation 1

#endif // QT_3DCORE_CONFIG_H
"""

_QT3DCORE_CONFIG_P_H = """#ifndef QT_3DCORE_CONFIG_P_H
#define QT_3DCORE_CONFIG_P_H

#include "qt3dcore-config.h"

#define QT_FEATURE_qt3d_system_assimp 1
#ifdef __SSE2__
#define QT_FEATURE_qt3d_simd_sse2 1
#else
#define QT_FEATURE_qt3d_simd_sse2 -1
#endif
#define QT_FEATURE_qt3d_simd_avx2 -1

#endif // QT_3DCORE_CONFIG_P_H
"""

_QT3DRENDER_CONFIG_H = """#ifndef QT_3DRENDER_CONFIG_H
#define QT_3DRENDER_CONFIG_H

#define QT_FEATURE_qt3d_opengl_renderer 1
#define QT_FEATURE_qt3d_rhi_renderer 1
#define QT_FEATURE_qt3d_vulkan -1

#endif // QT_3DRENDER_CONFIG_H
"""

_QT3DRENDER_CONFIG_P_H = """#ifndef QT_3DRENDER_CONFIG_P_H
#define QT_3DRENDER_CONFIG_P_H

#include "qt3drender-config.h"

#endif // QT_3DRENDER_CONFIG_P_H
"""

def declare_qt3d_config_targets():
    """Declares generated config headers and QML registration stubs for @qt3d."""
    qt_write_file(
        name = "gen_qt3dcore_config_h",
        out = "generated_config/qt3dcore-config.h",
        content = _QT3DCORE_CONFIG_H,
    )
    qt_write_file(
        name = "gen_qt3dcore_config_p_h",
        out = "generated_config/qt3dcore-config_p.h",
        content = _QT3DCORE_CONFIG_P_H,
    )
    qt_write_file(
        name = "gen_qt3drender_config_h",
        out = "generated_config/qt3drender-config.h",
        content = _QT3DRENDER_CONFIG_H,
    )
    qt_write_file(
        name = "gen_qt3drender_config_p_h",
        out = "generated_config/qt3drender-config_p.h",
        content = _QT3DRENDER_CONFIG_P_H,
    )

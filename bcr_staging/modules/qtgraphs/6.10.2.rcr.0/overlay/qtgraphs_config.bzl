"""Generated configuration and tracepoint headers for @qtgraphs."""

load("@qt//:qt_tools.bzl", "qt_write_file")

_QTGRAPHS_CONFIG_H = """#define QT_FEATURE_graphs_2d 1
#define QT_FEATURE_graphs_2d_area 1
#define QT_FEATURE_graphs_2d_bar 1
#define QT_FEATURE_graphs_2d_donut_pie 1
#define QT_FEATURE_graphs_2d_line 1
#define QT_FEATURE_graphs_2d_scatter 1
#define QT_FEATURE_graphs_2d_spline 1
#define QT_FEATURE_graphs_3d 1
#define QT_FEATURE_graphs_3d_bars3d 1
#define QT_FEATURE_graphs_3d_scatter3d 1
#define QT_FEATURE_graphs_3d_surface3d 1
"""

_QTGRAPHS_CONFIG_P_H = """#include <QtGraphs/qtgraphs-config.h>
"""

_QTGRAPHS_TRACEPOINTS_P_H = """#ifndef QT_GRAPHS_TRACEPOINTS_P_H
#define QT_GRAPHS_TRACEPOINTS_P_H

#include <QtCore/private/qtrace_p.h>

#endif // QT_GRAPHS_TRACEPOINTS_P_H
"""

def declare_qtgraphs_config_targets():
    """Declares generated config and tracepoint headers for @qtgraphs."""
    qt_write_file(
        name = "gen_qtgraphs_config_h",
        out = "generated_config/qtgraphs-config.h",
        content = _QTGRAPHS_CONFIG_H,
    )
    qt_write_file(
        name = "gen_qtgraphs_config_p_h",
        out = "generated_config/qtgraphs-config_p.h",
        content = _QTGRAPHS_CONFIG_P_H,
    )
    qt_write_file(
        name = "gen_qtgraphs_tracepoints_p_h",
        out = "generated_config/qtgraphs_tracepoints_p.h",
        content = _QTGRAPHS_TRACEPOINTS_P_H,
    )

"""Generated config headers for @qtwebview."""

load("@qt//:qt_tools.bzl", "qt_write_file")

_QTWEBVIEW_CONFIG_H = """\
#ifndef QTWEBVIEW_CONFIG_H
#define QTWEBVIEW_CONFIG_H

#define QT_FEATURE_webview_webview2_plugin -1
#define QT_FEATURE_webview_webengine_plugin -1
#define QT_FEATURE_webview_android_plugin -1
#if defined(__APPLE__)
#define QT_FEATURE_webview_darwin_plugin 1
#else
#define QT_FEATURE_webview_darwin_plugin -1
#endif
#define QT_FEATURE_webview_winrt_plugin -1
#define QT_FEATURE_webview_wasm_plugin -1

#endif // QTWEBVIEW_CONFIG_H
"""

_QTWEBVIEW_CONFIG_P_H = """\
#ifndef QTWEBVIEW_CONFIG_P_H
#define QTWEBVIEW_CONFIG_P_H

#include <QtWebView/qtwebview-config.h>

#endif // QTWEBVIEW_CONFIG_P_H
"""

def declare_qtwebview_config_targets(name = "qtwebview_config"):
    qt_write_file(
        name = "gen_qtwebview_config_h",
        out = "generated_config/qtwebview-config.h",
        content = _QTWEBVIEW_CONFIG_H,
    )
    qt_write_file(
        name = "gen_qtwebview_config_p_h",
        out = "generated_config/qtwebview-config_p.h",
        content = _QTWEBVIEW_CONFIG_P_H,
    )

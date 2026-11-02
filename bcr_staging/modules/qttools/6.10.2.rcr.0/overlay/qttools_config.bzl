"""Configuration headers for @qttools (QtTools)."""

load("@qt//:qt_tools.bzl", "qt_write_file")

def declare_qttools_config_targets():
    """Declares build-time generated config headers for QtTools."""
    qt_write_file(
        name = "gen_qttools_config_h",
        out = "generated_cfg/QtTools/qttools-config.h",
        content = """#ifndef QTTOOLS_CONFIG_H
#define QTTOOLS_CONFIG_H

#define QT_FEATURE_fullqthelp 1

#endif // QTTOOLS_CONFIG_H
""",
    )

    qt_write_file(
        name = "gen_qttools_config_p_h",
        out = "generated_cfg/QtTools/private/qttools-config_p.h",
        content = """#ifndef QTTOOLS_CONFIG_P_H
#define QTTOOLS_CONFIG_P_H

#include <QtTools/qttools-config.h>

#define QT_FEATURE_assistant 1
#define QT_FEATURE_clang 1
#define QT_FEATURE_clang_rtti 1
#define QT_FEATURE_qdoc 1
#define QT_FEATURE_designer 1
#define QT_FEATURE_distancefieldgenerator 1
#define QT_FEATURE_kmap2qmap 1
#define QT_FEATURE_linguist 1
#define QT_FEATURE_pixeltool 1
#define QT_FEATURE_qdbus 1
#define QT_FEATURE_qev 1
#define QT_FEATURE_qtattributionsscanner 1
#define QT_FEATURE_qtdiag 1
#define QT_FEATURE_qtplugininfo 1

#endif // QTTOOLS_CONFIG_P_H
""",
    )

    qt_write_file(
        name = "gen_qhelpgenerator_plugin_imports_cpp",
        out = "generated_cfg/qhelpgenerator_plugin_imports_custom.cpp",
        content = """// Auto-generated static plugin imports for qhelpgenerator.
#include <QtCore/QtPlugin>

Q_IMPORT_PLUGIN(QMinimalIntegrationPlugin)
Q_IMPORT_PLUGIN(QSQLiteDriverPlugin)
""",
    )

    qt_write_file(
        name = "linguist_no_printsupport_h",
        out = "linguist_no_printsupport/linguist_no_printsupport.h",
        content = """#include <QtCore/private/qconfig_p.h>
#undef QT_FEATURE_printsupport
#define QT_FEATURE_printsupport -1
""",
    )

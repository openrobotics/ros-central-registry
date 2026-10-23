"""Generated config headers for @qtgrpc (QtProtobuf and QtGrpc)."""

load("@qt//:qt_tools.bzl", "qt_write_file")

_QTPROTOBUF_CONFIG_H = """\
#ifndef QTPROTOBUF_CONFIG_H
#define QTPROTOBUF_CONFIG_H

#define QT_FEATURE_protobuf_qtcoretypes 1
#define QT_FEATURE_protobuf_qtguitypes 1
#define QT_FEATURE_protobuf_wellknowntypes 1
#define QT_FEATURE_protobufquick 1

#endif // QTPROTOBUF_CONFIG_H
"""

_QTPROTOBUF_CONFIG_P_H = """\
#ifndef QTPROTOBUF_CONFIG_P_H
#define QTPROTOBUF_CONFIG_P_H

#include <QtProtobuf/qtprotobuf-config.h>

#define QT_FEATURE_qtprotobufgen 1
#define QT_FEATURE_protobuf_unsafe_registry -1

#endif // QTPROTOBUF_CONFIG_P_H
"""

_QTGRPC_CONFIG_H = """\
#ifndef QTGRPC_CONFIG_H
#define QTGRPC_CONFIG_H

#define QT_FEATURE_grpc 1
#define QT_FEATURE_grpcquick 1

#endif // QTGRPC_CONFIG_H
"""

_QTGRPC_CONFIG_P_H = """\
#ifndef QTGRPC_CONFIG_P_H
#define QTGRPC_CONFIG_P_H

#include <QtGrpc/qtgrpc-config.h>

#define QT_FEATURE_qtgrpcgen 1

#endif // QTGRPC_CONFIG_P_H
"""

def declare_qtgrpc_config_targets(name = "qtgrpc_config"):
    qt_write_file(
        name = "gen_qtprotobuf_config_h",
        out = "generated_config/QtProtobuf/qtprotobuf-config.h",
        content = _QTPROTOBUF_CONFIG_H,
    )
    qt_write_file(
        name = "gen_qtprotobuf_config_p_h",
        out = "generated_config/QtProtobuf/private/qtprotobuf-config_p.h",
        content = _QTPROTOBUF_CONFIG_P_H,
    )
    qt_write_file(
        name = "gen_qtgrpc_config_h",
        out = "generated_config/QtGrpc/qtgrpc-config.h",
        content = _QTGRPC_CONFIG_H,
    )
    qt_write_file(
        name = "gen_qtgrpc_config_p_h",
        out = "generated_config/QtGrpc/private/qtgrpc-config_p.h",
        content = _QTGRPC_CONFIG_P_H,
    )

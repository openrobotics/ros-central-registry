"""Generated configuration headers for @qtspeech."""

load("@qt//:qt_tools.bzl", "qt_write_file")

_QTTEXTTOSPEECH_CONFIG_H = """#if defined(__linux__)
#define QT_FEATURE_speechd 1
#else
#define QT_FEATURE_speechd -1
#endif
"""

_QTTEXTTOSPEECH_CONFIG_P_H = """#include <QtTextToSpeech/qttexttospeech-config.h>
#define QT_FEATURE_flite -1
"""

def declare_qtspeech_config_targets():
    """Declares generated config headers for @qtspeech."""
    qt_write_file(
        name = "gen_qttexttospeech_config_h",
        out = "generated_config/qttexttospeech-config.h",
        content = _QTTEXTTOSPEECH_CONFIG_H,
    )
    qt_write_file(
        name = "gen_qttexttospeech_config_p_h",
        out = "generated_config/qttexttospeech-config_p.h",
        content = _QTTEXTTOSPEECH_CONFIG_P_H,
    )

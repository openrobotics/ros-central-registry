"""Generated configuration headers for @qtmultimedia."""

load("@qt//:qt_tools.bzl", "qt_write_file")

_QTMULTIMEDIA_CONFIG_H = """#define QT_FEATURE_alsa -1
#if defined(__APPLE__)
#define QT_FEATURE_avfoundation 1
#define QT_FEATURE_coreaudio 1
#define QT_FEATURE_videotoolbox 1
#else
#define QT_FEATURE_avfoundation -1
#define QT_FEATURE_coreaudio -1
#define QT_FEATURE_videotoolbox -1
#endif
#define QT_FEATURE_mmrenderer -1
#define QT_FEATURE_native_android_backend -1
#if defined(_WIN32)
#define QT_FEATURE_native_windows_backend 1
#else
#define QT_FEATURE_native_windows_backend -1
#endif
#if defined(__linux__)
#define QT_FEATURE_pulseaudio 1
#else
#define QT_FEATURE_pulseaudio -1
#endif
"""

_QTMULTIMEDIA_CONFIG_P_H = """#include <QtMultimedia/qtmultimedia-config.h>
#define QT_FEATURE_pipewire -1
#define QT_FEATURE_pipewire_screencapture -1
#define QT_FEATURE_gstreamer -1
#define QT_FEATURE_gstreamer_photography -1
#define QT_FEATURE_gstreamer_gl -1
#define QT_FEATURE_gstreamer_gl_wayland -1
#define QT_FEATURE_gstreamer_gl_egl -1
#define QT_FEATURE_gstreamer_gl_x11 -1
#define QT_FEATURE_gpu_vivante -1
#if defined(__linux__)
#define QT_FEATURE_linux_v4l 1
#else
#define QT_FEATURE_linux_v4l -1
#endif
#define QT_FEATURE_linux_dmabuf -1
#define QT_FEATURE_vaapi -1
#define QT_FEATURE_aaudio -1
#define QT_FEATURE_wasm -1
#if defined(_WIN32)
#define QT_FEATURE_wasapi 1
#else
#define QT_FEATURE_wasapi -1
#endif
#define QT_FEATURE_spatialaudio 1
#define QT_FEATURE_spatialaudio_quick3d 1
#define QT_FEATURE_ffmpeg 1
#define QT_FEATURE_ffmpeg_stubs -1
"""

def declare_qtmultimedia_config_targets():
    """Declares generated config headers for @qtmultimedia."""
    qt_write_file(
        name = "gen_qtmultimedia_config_h",
        out = "generated_config/qtmultimedia-config.h",
        content = _QTMULTIMEDIA_CONFIG_H,
    )
    qt_write_file(
        name = "gen_qtmultimedia_config_p_h",
        out = "generated_config/qtmultimedia-config_p.h",
        content = _QTMULTIMEDIA_CONFIG_P_H,
    )

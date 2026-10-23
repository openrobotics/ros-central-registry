"""Generates Qt 6.10.2 configuration headers and mimetype database at build time."""

load("@qt//:qt_tools.bzl", "qt_write_file")
load("@rules_cc//cc:cc_library.bzl", "cc_library")

_QCONFIG_H = """#ifndef QT_QCONFIG_H
#define QT_QCONFIG_H

#define QT_FEATURE_version_tagging -1
#define QT_FEATURE_shared 1
#define QT_FEATURE_static -1
#define QT_FEATURE_cross_compile -1
#if defined(_WIN32) || defined(__APPLE__)
#define QT_FEATURE_pkg_config -1
#define QT_FEATURE_reduce_relocations -1
#else
#define QT_FEATURE_pkg_config 1
#define QT_FEATURE_reduce_relocations 1
#define QT_REDUCE_RELOCATIONS
#endif
#define QT_FEATURE_debug_and_release -1
#define QT_FEATURE_separate_debug_info -1
#define QT_FEATURE_appstore_compliant -1
#define QT_FEATURE_simulator_and_device -1
#ifdef _WIN32
#define QT_FEATURE_rpath -1
#else
#define QT_FEATURE_rpath 1
#define QT_VISIBILITY_AVAILABLE
#endif
#define QT_FEATURE_force_asserts -1
#define QT_FEATURE_framework -1
#define QT_FEATURE_cxx20 -1
#define QT_FEATURE_cxx2a -1
#define QT_FEATURE_cxx2b -1
#define QT_FEATURE_cxx2c -1
#define QT_FEATURE_signaling_nan 1
#define QT_FEATURE_wasm_simd128 -1
#define QT_FEATURE_wasm_exceptions -1
#define QT_FEATURE_wasm_jspi -1
#define QT_FEATURE_zstd -1
#define QT_FEATURE_thread 1
#define QT_FEATURE_future 1
#define QT_FEATURE_concurrent 1
#define QT_FEATURE_dbus 1
#define QT_FEATURE_openssl_linked -1
#define QT_FEATURE_openssl_runtime -1
#define QT_FEATURE_opensslv11 -1
#define QT_FEATURE_opensslv30 1
#define QT_FEATURE_test_gui 1
#define QT_FEATURE_android_16kb_pages -1

#define QT_VERSION_STR "6.10.2"
#define QT_VERSION_MAJOR 6
#define QT_VERSION_MINOR 10
#define QT_VERSION_PATCH 2

#define QT_COPYRIGHT "Copyright (C) The Qt Company Ltd. and other contributors."
#define QT_LARGEFILE_SUPPORT 64

#if defined(__x86_64__) || defined(_M_X64)
#define QT_COMPILER_SUPPORTS_SSE2 1
#define QT_COMPILER_SUPPORTS_SSE3 1
#define QT_COMPILER_SUPPORTS_SSSE3 1
#define QT_COMPILER_SUPPORTS_SSE4_1 1
#define QT_COMPILER_SUPPORTS_SSE4_2 1
#define QT_COMPILER_SUPPORTS_AVX 1
#define QT_COMPILER_SUPPORTS_F16C 1
#define QT_COMPILER_SUPPORTS_AVX2 1
#define QT_COMPILER_SUPPORTS_AVX512F 1
#define QT_COMPILER_SUPPORTS_AVX512ER 1
#define QT_COMPILER_SUPPORTS_AVX512CD 1
#define QT_COMPILER_SUPPORTS_AVX512PF 1
#define QT_COMPILER_SUPPORTS_AVX512DQ 1
#define QT_COMPILER_SUPPORTS_AVX512BW 1
#define QT_COMPILER_SUPPORTS_AVX512VL 1
#define QT_COMPILER_SUPPORTS_AVX512IFMA 1
#define QT_COMPILER_SUPPORTS_AVX512VBMI 1
#define QT_COMPILER_SUPPORTS_AVX512VBMI2 1
#define QT_COMPILER_SUPPORTS_AES 1
#define QT_COMPILER_SUPPORTS_VAES 1
#define QT_COMPILER_SUPPORTS_RDRND 1
#define QT_COMPILER_SUPPORTS_RDSEED 1
#define QT_COMPILER_SUPPORTS_SHA 1
#endif

#if defined(__aarch64__) || defined(_M_ARM64)
#define QT_COMPILER_SUPPORTS_NEON 1
#define QT_COMPILER_SUPPORTS_CRC32 1
#define QT_COMPILER_SUPPORTS_AES 1
#endif

#define QT_GUI_TEST 1

#endif // QT_QCONFIG_H
"""

_QCONFIG_P_H = """#ifndef QT_QCONFIG_P_H
#define QT_QCONFIG_P_H

#define QT_FEATURE_use_bfd_linker -1
#define QT_FEATURE_use_gold_linker -1
#define QT_FEATURE_use_lld_linker -1
#define QT_FEATURE_use_mold_linker -1
#define QT_FEATURE_android_style_assets -1
#define QT_FEATURE_gc_binaries -1
#define QT_FEATURE_developer_build -1
#define QT_FEATURE_private_tests -1
#define QT_FEATURE_doc_snippets -1
#define QT_FEATURE_debug -1
#define QT_FEATURE_elf_private_full_version -1
#define QT_FEATURE_reduce_exports 1
#define QT_FEATURE_no_direct_extern_access -1

#if defined(__x86_64__) || defined(_M_X64)
#define QT_FEATURE_x86intrin 1
#define QT_FEATURE_sse2 1
#define QT_FEATURE_sse3 1
#define QT_FEATURE_ssse3 1
#define QT_FEATURE_sse4_1 1
#define QT_FEATURE_sse4_2 1
#define QT_FEATURE_avx 1
#define QT_FEATURE_f16c 1
#define QT_FEATURE_avx2 1
#define QT_FEATURE_avx512f 1
#define QT_FEATURE_avx512er 1
#define QT_FEATURE_avx512cd 1
#define QT_FEATURE_avx512pf 1
#define QT_FEATURE_avx512dq 1
#define QT_FEATURE_avx512bw 1
#define QT_FEATURE_avx512vl 1
#define QT_FEATURE_avx512ifma 1
#define QT_FEATURE_avx512vbmi 1
#define QT_FEATURE_avx512vbmi2 1
#define QT_FEATURE_aesni 1
#define QT_FEATURE_vaes 1
#define QT_FEATURE_rdrnd 1
#define QT_FEATURE_rdseed 1
#define QT_FEATURE_shani 1
#define QT_FEATURE_neon -1
#define QT_FEATURE_arm_crc32 -1
#define QT_FEATURE_arm_crypto -1
#elif defined(__aarch64__) || defined(_M_ARM64)
#define QT_FEATURE_x86intrin -1
#define QT_FEATURE_sse2 -1
#define QT_FEATURE_sse3 -1
#define QT_FEATURE_ssse3 -1
#define QT_FEATURE_sse4_1 -1
#define QT_FEATURE_sse4_2 -1
#define QT_FEATURE_avx -1
#define QT_FEATURE_f16c -1
#define QT_FEATURE_avx2 -1
#define QT_FEATURE_avx512f -1
#define QT_FEATURE_avx512er -1
#define QT_FEATURE_avx512cd -1
#define QT_FEATURE_avx512pf -1
#define QT_FEATURE_avx512dq -1
#define QT_FEATURE_avx512bw -1
#define QT_FEATURE_avx512vl -1
#define QT_FEATURE_avx512ifma -1
#define QT_FEATURE_avx512vbmi -1
#define QT_FEATURE_avx512vbmi2 -1
#define QT_FEATURE_aesni -1
#define QT_FEATURE_vaes -1
#define QT_FEATURE_rdrnd -1
#define QT_FEATURE_rdseed -1
#define QT_FEATURE_shani -1
#define QT_FEATURE_neon 1
#define QT_FEATURE_arm_crc32 1
#define QT_FEATURE_arm_crypto 1
#endif

#define QT_FEATURE_arm_sve -1
#define QT_FEATURE_lsx -1
#define QT_FEATURE_lasx -1
#define QT_FEATURE_mips_dsp -1
#define QT_FEATURE_mips_dspr2 -1

#ifdef _WIN32
#define QT_FEATURE_localtime_r -1
#define QT_FEATURE_localtime_s 1
#define QT_FEATURE_posix_fallocate -1
#define QT_FEATURE_dbus_linked -1
#define QT_FEATURE_dlopen -1
#define QT_FEATURE_glibc_fortify_source -1
#define QT_FEATURE_stack_protector -1
#define QT_FEATURE_stack_clash_protection -1
#define QT_FEATURE_libstdcpp_assertions -1
#define QT_FEATURE_relro_now_linker -1
#elif defined(__APPLE__)
#define QT_FEATURE_localtime_r 1
#define QT_FEATURE_localtime_s -1
#define QT_FEATURE_posix_fallocate -1
#define QT_FEATURE_dbus_linked -1
#define QT_FEATURE_dlopen 1
#define QT_FEATURE_glibc_fortify_source -1
#define QT_FEATURE_stack_protector 1
#define QT_FEATURE_stack_clash_protection -1
#define QT_FEATURE_libstdcpp_assertions -1
#define QT_FEATURE_relro_now_linker -1
#else
#define QT_FEATURE_localtime_r 1
#define QT_FEATURE_localtime_s -1
#define QT_FEATURE_posix_fallocate 1
#define QT_FEATURE_dbus_linked 1
#define QT_FEATURE_dlopen 1
#define QT_FEATURE_glibc_fortify_source 1
#define QT_FEATURE_stack_protector 1
#define QT_FEATURE_stack_clash_protection 1
#define QT_FEATURE_libstdcpp_assertions -1
#define QT_FEATURE_relro_now_linker 1
#endif

#define QT_FEATURE_force_system_libs -1
#define QT_FEATURE_force_bundled_libs -1
#define QT_FEATURE_system_zlib 1
#define QT_FEATURE_stdlib_libcpp 1
#define QT_FEATURE_dbus 1
#define QT_FEATURE_gui 1
#define QT_FEATURE_network 1
#define QT_FEATURE_printsupport 1
#define QT_FEATURE_sql 1
#define QT_FEATURE_testlib 1
#define QT_FEATURE_widgets 1
#define QT_FEATURE_xml 1
#define QT_FEATURE_libudev -1
#define QT_FEATURE_openssl 1
#define QT_FEATURE_relocatable 1
#define QT_FEATURE_intelcet -1
#define QT_FEATURE_trivial_auto_var_init_pattern -1
#define QT_FEATURE_libcpp_hardening -1

#endif // QT_QCONFIG_P_H
"""

_QCONFIG_CPP = """#include "private/qoffsetstringarray_p.h"

/* Installation Info */
static const char qt_configure_prefix_path_str  [12+256] = "qt_prfxpath=";

static constexpr auto qt_configure_strs = QT_PREPEND_NAMESPACE(qOffsetStringArray)(
    R"qconfig(doc)qconfig",
    R"qconfig(include)qconfig",
    R"qconfig(lib)qconfig",
    R"qconfig(libexec)qconfig",
    R"qconfig(bin)qconfig",
    R"qconfig(plugins)qconfig",
    R"qconfig(qml)qconfig",
    R"qconfig(.)qconfig",
    R"qconfig(.)qconfig",
    R"qconfig(translations)qconfig",
    R"qconfig(examples)qconfig",
    R"qconfig(tests)qconfig"
);

#define QT_CONFIGURE_SETTINGS_PATH "etc/xdg"
#define QT_CONFIGURE_LIBLOCATION_TO_PREFIX_PATH "../"_L1
#define QT_CONFIGURE_PREFIX_PATH qt_configure_prefix_path_str + 12
"""

_QTDEPRECATIONDEFINITIONS_H = """#ifndef QTDEPRECATIONDEFINITIONS_H
#define QTDEPRECATIONDEFINITIONS_H

#include <QtCore/qcompilerdetection.h>

#ifndef QT_DISABLE_DEPRECATED_UP_TO
#  ifdef QT_DISABLE_DEPRECATED_BEFORE
#    define QT_DISABLE_DEPRECATED_UP_TO QT_DISABLE_DEPRECATED_BEFORE
#  else
#    define QT_DISABLE_DEPRECATED_UP_TO 0x050000
#  endif
#endif

#if QT_DISABLE_DEPRECATED_UP_TO < 0x050000 && defined(Q_CC_GNU)
#  warning QT_DISABLE_DEPRECATED_UP_TO is set to the version that is lower than the version that \\
           Qt was built with. This may lead to linking issues.
#endif

#ifndef QT_WARN_DEPRECATED_UP_TO
#  ifdef QT_DEPRECATED_WARNINGS_SINCE
#    define QT_WARN_DEPRECATED_UP_TO QT_DEPRECATED_WARNINGS_SINCE
#  else
#    define QT_WARN_DEPRECATED_UP_TO 0x070000
#  endif
#endif

#endif // QTDEPRECATIONDEFINITIONS_H
"""

_QTCORE_CONFIG_H = """#ifndef QTCORE_CONFIG_H
#define QTCORE_CONFIG_H

#define QT_FEATURE_clock_monotonic 1
#define QT_FEATURE_cxx11_future 1
#define QT_FEATURE_cxx17_filesystem 1

#if defined(__APPLE__) || defined(_WIN32)
#define QT_FEATURE_glib -1
#define QT_NO_GLIB 1
#define QT_FEATURE_inotify -1
#else
#define QT_FEATURE_glib 1
#define QT_FEATURE_inotify 1
#endif

#define QT_FEATURE_std_atomic64 1
#define QT_FEATURE_mimetype 1
#define QT_FEATURE_regularexpression 1
#define QT_FEATURE_sharedmemory 1
#define QT_FEATURE_shortcut 1
#define QT_FEATURE_systemsemaphore 1
#define QT_FEATURE_xmlstream 1
#define QT_FEATURE_cpp_winrt -1
#define QT_FEATURE_xmlstreamreader 1
#define QT_FEATURE_xmlstreamwriter 1
#define QT_FEATURE_textdate 1
#define QT_FEATURE_datestring 1
#define QT_FEATURE_process 1
#define QT_FEATURE_processenvironment 1
#define QT_FEATURE_temporaryfile 1
#define QT_FEATURE_library 1
#define QT_FEATURE_settings 1
#define QT_FEATURE_filesystemwatcher 1
#define QT_FEATURE_filesystemiterator 1
#define QT_FEATURE_itemmodel 1
#define QT_FEATURE_proxymodel 1
#define QT_FEATURE_sortfilterproxymodel 1
#define QT_FEATURE_identityproxymodel 1
#define QT_FEATURE_transposeproxymodel 1
#define QT_FEATURE_concatenatetablesproxymodel 1
#define QT_FEATURE_stringlistmodel 1
#define QT_FEATURE_translation 1
#define QT_FEATURE_easingcurve 1
#define QT_FEATURE_animation 1
#define QT_FEATURE_gestures 1
#define QT_FEATURE_jalalicalendar 1
#define QT_FEATURE_islamiccivilcalendar 1
#define QT_FEATURE_timezone 1
#define QT_FEATURE_timezone_tzdb -1
#define QT_FEATURE_commandlineparser 1
#define QT_FEATURE_cborstreamreader 1
#define QT_FEATURE_cborstreamwriter 1
#define QT_FEATURE_permissions 1
#define QT_FEATURE_jemalloc -1
#if !defined(__APPLE__) && !defined(_WIN32)
#define QT_THREADSAFE_CLOEXEC 1
#endif

#endif // QTCORE_CONFIG_H
"""

_QTCORE_CONFIG_P_H = """#ifndef QTCORE_CONFIG_P_H
#define QTCORE_CONFIG_P_H

#define QT_FEATURE_doubleconversion 1
#define QT_FEATURE_system_doubleconversion -1

#ifdef _WIN32
#define QT_FEATURE_clock_gettime -1
#define QT_FEATURE_broken_threadlocal_dtors 1
#define QT_FEATURE_dladdr -1
#define QT_FEATURE_futimens -1
#define QT_FEATURE_getauxval -1
#define QT_FEATURE_getentropy -1
#define QT_FEATURE_glib -1
#define QT_FEATURE_icu -1
#define QT_FEATURE_inotify -1
#define QT_FEATURE_linkat -1
#define QT_FEATURE_memmem -1
#define QT_FEATURE_memrchr -1
#define QT_FEATURE_poll_ppoll -1
#define QT_FEATURE_poll_pollts -1
#define QT_FEATURE_poll_poll -1
#define QT_FEATURE_poll_select -1
#define QT_FEATURE_pthread_condattr_setclock -1
#define QT_FEATURE_pthread_timedjoin -1
#define QT_FEATURE_renameat2 -1
#define QT_FEATURE_forkfd_pidfd -1
#define QT_FEATURE_copy_file_range -1
#define QT_FEATURE_dup3 -1
#define QT_FEATURE_accept4 -1
#define QT_FEATURE_posix_sem -1
#define QT_FEATURE_posix_shm -1
#define QT_FEATURE_sysv_sem -1
#define QT_FEATURE_sysv_shm -1
#define QT_FEATURE_backtrace -1
#define QT_FEATURE_timezone_locale 1
#elif defined(__APPLE__)
#define QT_FEATURE_clock_gettime 1
#define QT_FEATURE_broken_threadlocal_dtors -1
#define QT_FEATURE_dladdr 1
#define QT_FEATURE_futimens 1
#define QT_FEATURE_getauxval -1
#define QT_FEATURE_getentropy 1
#define QT_FEATURE_glib -1
#define QT_FEATURE_icu -1
#define QT_FEATURE_inotify -1
#define QT_FEATURE_linkat 1
#define QT_FEATURE_memmem 1
#define QT_FEATURE_memrchr -1
#define QT_FEATURE_poll_ppoll -1
#define QT_FEATURE_poll_pollts -1
#define QT_FEATURE_poll_poll 1
#define QT_FEATURE_poll_select -1
#define QT_FEATURE_pthread_condattr_setclock -1
#define QT_FEATURE_pthread_timedjoin -1
#define QT_FEATURE_renameat2 -1
#define QT_FEATURE_forkfd_pidfd -1
#define QT_FEATURE_copy_file_range -1
#define QT_FEATURE_dup3 -1
#define QT_FEATURE_accept4 -1
#define QT_FEATURE_posix_sem 1
#define QT_FEATURE_posix_shm 1
#define QT_FEATURE_sysv_sem 1
#define QT_FEATURE_sysv_shm 1
#define QT_FEATURE_backtrace 1
#define QT_FEATURE_timezone_locale -1
#else
#define QT_FEATURE_clock_gettime 1
#define QT_FEATURE_broken_threadlocal_dtors -1
#define QT_FEATURE_dladdr 1
#define QT_FEATURE_futimens 1
#define QT_FEATURE_getauxval 1
#define QT_FEATURE_getentropy 1
#define QT_FEATURE_glib 1
#define QT_FEATURE_icu 1
#define QT_FEATURE_inotify 1
#define QT_FEATURE_linkat 1
#define QT_FEATURE_memmem 1
#define QT_FEATURE_memrchr 1
#define QT_FEATURE_poll_ppoll 1
#define QT_FEATURE_poll_pollts -1
#define QT_FEATURE_poll_poll -1
#define QT_FEATURE_poll_select -1
#define QT_FEATURE_pthread_condattr_setclock 1
#define QT_FEATURE_pthread_timedjoin 1
#define QT_FEATURE_renameat2 1
#define QT_FEATURE_forkfd_pidfd 1
#define QT_FEATURE_copy_file_range 1
#define QT_FEATURE_dup3 1
#define QT_FEATURE_accept4 1
#define QT_FEATURE_posix_sem 1
#define QT_FEATURE_posix_shm 1
#define QT_FEATURE_sysv_sem 1
#define QT_FEATURE_sysv_shm 1
#define QT_FEATURE_backtrace 1
#define QT_FEATURE_timezone_locale 1
#endif

#define QT_FEATURE_journald -1
#define QT_FEATURE_system_libb2 -1
#define QT_FEATURE_mimetype_database 1
#define QT_FEATURE_system_pcre2 1
#define QT_FEATURE_pthread_clockjoin -1
#define QT_FEATURE_qqnx_pps -1
#define QT_FEATURE_slog2 -1
#define QT_FEATURE_syslog -1
#define QT_FEATURE_cxx20_format -1
#define QT_FEATURE_cxx23_stacktrace -1
#define QT_FEATURE_cpp_winrt -1
#define QT_FEATURE_sha3_fast 1
#define QT_FEATURE_hijricalendar 1
#define QT_FEATURE_datetimeparser 1
#define QT_FEATURE_lttng -1
#define QT_FEATURE_etw -1
#define QT_FEATURE_ctf -1
#define QT_FEATURE_poll_exit_on_error -1
#define QT_FEATURE_openssl_hash -1
#define QT_FEATURE_winsdkicu -1
#define QT_FEATURE_jemalloc -1
#define QT_FEATURE_vxpipedrv -1

#endif // QTCORE_CONFIG_P_H
"""

_QTGUI_CONFIG_H = """#ifndef QTGUI_CONFIG_H
#define QTGUI_CONFIG_H

#if defined(_WIN32) || defined(__APPLE__)
#define QT_FEATURE_accessibility_atspi_bridge -1
#define QT_NO_ACCESSIBILITY_ATSPI_BRIDGE 1
#else
#define QT_FEATURE_accessibility_atspi_bridge 1
#endif
#define QT_FEATURE_freetype 1

#ifdef _WIN32
#define QT_FEATURE_fontconfig -1
#define QT_FEATURE_xcb -1
#define QT_FEATURE_xcb_glx_plugin -1
#define QT_FEATURE_metal -1
#define QT_FEATURE_egl -1
#define QT_FEATURE_wayland -1
#define QT_FEATURE_waylandscanner -1
#elif defined(__APPLE__)
#define QT_FEATURE_fontconfig -1
#define QT_FEATURE_xcb -1
#define QT_FEATURE_xcb_glx_plugin -1
#define QT_FEATURE_metal 1
#define QT_FEATURE_egl -1
#define QT_FEATURE_wayland -1
#define QT_FEATURE_waylandscanner -1
#else
#define QT_FEATURE_fontconfig 1
#define QT_FEATURE_xcb 1
#define QT_FEATURE_xcb_glx_plugin 1
#define QT_FEATURE_metal -1
#define QT_FEATURE_egl 1
#define QT_FEATURE_wayland 1
#define QT_FEATURE_waylandscanner 1
#endif

#define QT_FEATURE_harfbuzz 1
#define QT_FEATURE_opengles2 -1
#define QT_FEATURE_opengles3 -1
#define QT_FEATURE_opengles31 -1
#define QT_FEATURE_opengles32 -1
#define QT_FEATURE_dynamicgl -1
#define QT_FEATURE_opengl 1
#define QT_FEATURE_vulkan 1
#define QT_FEATURE_openvg -1
#define QT_FEATURE_ico 1
#define QT_FEATURE_sessionmanager 1
#define QT_FEATURE_texthtmlparser 1
#define QT_FEATURE_textmarkdownreader 1
#define QT_FEATURE_system_textmarkdownreader -1
#define QT_FEATURE_textmarkdownwriter 1
#define QT_FEATURE_textodfwriter 1
#define QT_FEATURE_cssparser 1
#define QT_FEATURE_draganddrop 1
#define QT_FEATURE_action 1
#define QT_FEATURE_cursor 1
#define QT_FEATURE_clipboard 1
#define QT_FEATURE_wheelevent 1
#define QT_FEATURE_tabletevent 1
#define QT_FEATURE_im 1
#define QT_FEATURE_highdpiscaling 1
#define QT_FEATURE_validator 1
#define QT_FEATURE_standarditemmodel 1
#define QT_FEATURE_filesystemmodel 1
#define QT_FEATURE_imageformatplugin 1
#define QT_FEATURE_movie 1
#define QT_FEATURE_imageformat_bmp 1
#define QT_FEATURE_imageformat_ppm 1
#define QT_FEATURE_imageformat_xbm 1
#define QT_FEATURE_imageformat_xpm 1
#define QT_FEATURE_imageformat_png 1
#define QT_FEATURE_imageformat_jpeg 1
#define QT_FEATURE_image_heuristic_mask 1
#define QT_FEATURE_image_text 1
#define QT_FEATURE_picture 1
#define QT_FEATURE_colornames 1
#define QT_FEATURE_pdf 1
#define QT_FEATURE_desktopservices 1
#define QT_FEATURE_systemtrayicon 1
#define QT_FEATURE_accessibility 1
#define QT_FEATURE_whatsthis 1
#define QT_FEATURE_undocommand 1
#define QT_FEATURE_undostack 1
#define QT_FEATURE_undogroup 1
#define QT_FEATURE_emojisegmenter 1

#endif // QTGUI_CONFIG_H
"""

_QTGUI_CONFIG_P_H = """#ifndef QTGUI_CONFIG_P_H
#define QTGUI_CONFIG_P_H

#if defined(_WIN32) || defined(__APPLE__)
#define QT_FEATURE_accessibility_atspi_bridge -1
#else
#define QT_FEATURE_accessibility_atspi_bridge 1
#endif
#define QT_FEATURE_directfb -1
#define QT_FEATURE_freetype 1
#define QT_FEATURE_system_freetype 1

#ifdef _WIN32
#define QT_FEATURE_directwrite 1
#define QT_FEATURE_directwrite3 1
#define QT_FEATURE_directwritecolrv1 -1
#define QT_FEATURE_direct2d 1
#define QT_FEATURE_direct2d1_1 1
#define QT_FEATURE_evdev -1
#define QT_FEATURE_fontconfig -1
#define QT_FEATURE_linuxfb -1
#define QT_FEATURE_xcb_glx -1
#define QT_FEATURE_xcb_egl_plugin -1
#define QT_FEATURE_xcb_xlib -1
#define QT_FEATURE_xcb_sm -1
#define QT_FEATURE_xkbcommon -1
#define QT_FEATURE_xkbcommon_x11 -1
#define QT_FEATURE_xlib -1
#define QT_FEATURE_egl_x11 -1
#define QT_FEATURE_wayland_client -1
#define QT_FEATURE_wayland_server -1
#define QT_FEATURE_wayland_egl -1
#define QT_FEATURE_wayland_brcm -1
#define QT_FEATURE_wayland_drm_egl_server_buffer -1
#define QT_FEATURE_wayland_libhybris_egl_server_buffer -1
#define QT_FEATURE_wayland_dmabuf_server_buffer -1
#define QT_FEATURE_wayland_shm_emulation_server_buffer -1
#define QT_FEATURE_wayland_vulkan_server_buffer -1
#define QT_FEATURE_wayland_datadevice -1
#define QT_FEATURE_wayland_client_primary_selection -1
#define QT_FEATURE_wayland_client_fullscreen_shell_v1 -1
#define QT_FEATURE_wayland_client_wl_shell -1
#define QT_FEATURE_wayland_client_xdg_shell -1
#define QT_FEATURE_egl_extension_platform_wayland -1
#define QT_FEATURE_vnc -1
#define QT_FEATURE_multiprocess -1
#elif defined(__APPLE__)
#define QT_FEATURE_directwrite -1
#define QT_FEATURE_directwrite3 -1
#define QT_FEATURE_directwritecolrv1 -1
#define QT_FEATURE_direct2d -1
#define QT_FEATURE_direct2d1_1 -1
#define QT_FEATURE_evdev -1
#define QT_FEATURE_fontconfig -1
#define QT_FEATURE_linuxfb -1
#define QT_FEATURE_xcb_glx -1
#define QT_FEATURE_xcb_egl_plugin -1
#define QT_FEATURE_xcb_xlib -1
#define QT_FEATURE_xcb_sm -1
#define QT_FEATURE_xkbcommon -1
#define QT_FEATURE_xkbcommon_x11 -1
#define QT_FEATURE_xlib -1
#define QT_FEATURE_egl_x11 -1
#define QT_FEATURE_wayland_client -1
#define QT_FEATURE_wayland_server -1
#define QT_FEATURE_wayland_egl -1
#define QT_FEATURE_wayland_brcm -1
#define QT_FEATURE_wayland_drm_egl_server_buffer -1
#define QT_FEATURE_wayland_libhybris_egl_server_buffer -1
#define QT_FEATURE_wayland_dmabuf_server_buffer -1
#define QT_FEATURE_wayland_shm_emulation_server_buffer -1
#define QT_FEATURE_wayland_vulkan_server_buffer -1
#define QT_FEATURE_wayland_datadevice -1
#define QT_FEATURE_wayland_client_primary_selection -1
#define QT_FEATURE_wayland_client_fullscreen_shell_v1 -1
#define QT_FEATURE_wayland_client_wl_shell -1
#define QT_FEATURE_wayland_client_xdg_shell -1
#define QT_FEATURE_egl_extension_platform_wayland -1
#define QT_FEATURE_vnc -1
#define QT_FEATURE_multiprocess -1
#else
#define QT_FEATURE_directwrite -1
#define QT_FEATURE_directwrite3 -1
#define QT_FEATURE_directwritecolrv1 -1
#define QT_FEATURE_direct2d -1
#define QT_FEATURE_direct2d1_1 -1
#define QT_FEATURE_evdev 1
#define QT_FEATURE_fontconfig 1
#define QT_FEATURE_linuxfb 1
#define QT_FEATURE_xcb_glx 1
#define QT_FEATURE_xcb_egl_plugin 1
#define QT_FEATURE_xcb_xlib 1
#define QT_FEATURE_xcb_sm 1
#define QT_FEATURE_xkbcommon 1
#define QT_FEATURE_xkbcommon_x11 1
#define QT_FEATURE_xlib 1
#define QT_FEATURE_egl_x11 1
#define QT_FEATURE_wayland_client 1
#define QT_FEATURE_wayland_server 1
#define QT_FEATURE_wayland_egl 1
#define QT_FEATURE_wayland_brcm -1
#define QT_FEATURE_wayland_drm_egl_server_buffer 1
#define QT_FEATURE_wayland_libhybris_egl_server_buffer -1
#define QT_FEATURE_wayland_dmabuf_server_buffer -1
#define QT_FEATURE_wayland_shm_emulation_server_buffer 1
#define QT_FEATURE_wayland_vulkan_server_buffer -1
#define QT_FEATURE_wayland_datadevice 1
#define QT_FEATURE_wayland_client_primary_selection 1
#define QT_FEATURE_wayland_client_fullscreen_shell_v1 1
#define QT_FEATURE_wayland_client_wl_shell 1
#define QT_FEATURE_wayland_client_xdg_shell 1
#define QT_FEATURE_egl_extension_platform_wayland -1
#define QT_FEATURE_vnc 1
#define QT_FEATURE_multiprocess 1
#endif

#define QT_FEATURE_harfbuzz 1
#define QT_FEATURE_system_harfbuzz -1
#define QT_FEATURE_qqnx_imf -1
#define QT_FEATURE_integrityfb -1
#define QT_FEATURE_kms -1
#define QT_FEATURE_drm_atomic -1
#define QT_FEATURE_libinput -1
#define QT_FEATURE_integrityhid -1
#define QT_FEATURE_libinput_axis_api -1
#define QT_FEATURE_libinput_hires_wheel_support -1
#define QT_FEATURE_vsp2 -1
#define QT_FEATURE_mtdev -1
#define QT_FEATURE_vkgen 1
#define QT_FEATURE_vkkhrdisplay -1
#define QT_FEATURE_eglfs -1
#define QT_FEATURE_eglfs_brcm -1
#define QT_FEATURE_eglfs_egldevice -1
#define QT_FEATURE_eglfs_gbm -1
#define QT_FEATURE_eglfs_vsp2 -1
#define QT_FEATURE_eglfs_mali -1
#define QT_FEATURE_eglfs_viv -1
#define QT_FEATURE_eglfs_rcar -1
#define QT_FEATURE_eglfs_viv_wl -1
#define QT_FEATURE_eglfs_openwfd -1
#define QT_FEATURE_eglfs_x11 -1
#define QT_FEATURE_gif 1
#define QT_FEATURE_ico 1
#define QT_FEATURE_jpeg 1
#define QT_FEATURE_system_jpeg 1
#define QT_FEATURE_png 1
#define QT_FEATURE_system_png 1
#define QT_FEATURE_imageio_text_loading 1
#define QT_FEATURE_tslib -1
#define QT_FEATURE_tuiotouch 1
#define QT_FEATURE_xcb_native_painting -1
#define QT_FEATURE_xrender -1
#define QT_FEATURE_system_xcb_xinput -1
#define QT_FEATURE_raster_64bit 1
#define QT_FEATURE_raster_fp 1
#define QT_FEATURE_graphicsframecapture -1
#define QT_FEATURE_vxworksevdev -1
#define QT_FEATURE_qtgui_threadpool 1
#define QT_FEATURE_emojisegmenter 1

#endif // QTGUI_CONFIG_P_H
"""

_QTWIDGETS_CONFIG_H = """#ifndef QTWIDGETS_CONFIG_H
#define QTWIDGETS_CONFIG_H

#define QT_FEATURE_style_stylesheet 1
#define QT_FEATURE_itemviews 1
#define QT_FEATURE_treewidget 1
#define QT_FEATURE_listwidget 1
#define QT_FEATURE_tablewidget 1
#define QT_FEATURE_abstractbutton 1
#define QT_FEATURE_commandlinkbutton 1
#define QT_FEATURE_datetimeedit 1
#define QT_FEATURE_stackedwidget 1
#define QT_FEATURE_textbrowser 1
#define QT_FEATURE_splashscreen 1
#define QT_FEATURE_splitter 1
#define QT_FEATURE_label 1
#define QT_FEATURE_formlayout 1
#define QT_FEATURE_lcdnumber 1
#define QT_FEATURE_menu 1
#define QT_FEATURE_lineedit 1
#define QT_FEATURE_radiobutton 1
#define QT_FEATURE_spinbox 1
#define QT_FEATURE_tabbar 1
#define QT_FEATURE_tabwidget 1
#define QT_FEATURE_combobox 1
#define QT_FEATURE_fontcombobox 1
#define QT_FEATURE_checkbox 1
#define QT_FEATURE_pushbutton 1
#define QT_FEATURE_toolbutton 1
#define QT_FEATURE_toolbar 1
#define QT_FEATURE_toolbox 1
#define QT_FEATURE_groupbox 1
#define QT_FEATURE_buttongroup 1
#define QT_FEATURE_mainwindow 1
#define QT_FEATURE_dockwidget 1
#define QT_FEATURE_mdiarea 1
#define QT_FEATURE_resizehandler 1
#define QT_FEATURE_statusbar 1
#define QT_FEATURE_menubar 1
#define QT_FEATURE_contextmenu 1
#define QT_FEATURE_progressbar 1
#define QT_FEATURE_abstractslider 1
#define QT_FEATURE_slider 1
#define QT_FEATURE_scrollbar 1
#define QT_FEATURE_dial 1
#define QT_FEATURE_scrollarea 1
#define QT_FEATURE_scroller 1
#define QT_FEATURE_graphicsview 1
#define QT_FEATURE_graphicseffect 1
#define QT_FEATURE_textedit 1
#define QT_FEATURE_syntaxhighlighter 1
#define QT_FEATURE_rubberband 1
#define QT_FEATURE_tooltip 1
#define QT_FEATURE_statustip 1
#define QT_FEATURE_sizegrip 1
#define QT_FEATURE_calendarwidget 1
#define QT_FEATURE_keysequenceedit 1
#define QT_FEATURE_dialog 1
#define QT_FEATURE_dialogbuttonbox 1
#define QT_FEATURE_messagebox 1
#define QT_FEATURE_colordialog 1
#define QT_FEATURE_filedialog 1
#define QT_FEATURE_fontdialog 1
#define QT_FEATURE_progressdialog 1
#define QT_FEATURE_inputdialog 1
#define QT_FEATURE_errormessage 1
#define QT_FEATURE_wizard 1
#define QT_FEATURE_listview 1
#define QT_FEATURE_tableview 1
#define QT_FEATURE_treeview 1
#define QT_FEATURE_datawidgetmapper 1
#define QT_FEATURE_columnview 1
#define QT_FEATURE_completer 1
#define QT_FEATURE_fscompleter 1
#define QT_FEATURE_undoview 1

#endif // QTWIDGETS_CONFIG_H
"""

_QTWIDGETS_CONFIG_P_H = """#ifndef QTWIDGETS_CONFIG_P_H
#define QTWIDGETS_CONFIG_P_H

#define QT_FEATURE_gtk3 -1
#define QT_FEATURE_style_fusion 1
#if defined(__APPLE__)
#define QT_FEATURE_style_mac 1
#else
#define QT_FEATURE_style_mac -1
#endif
#define QT_FEATURE_style_windows 1
#if defined(_WIN32)
#define QT_FEATURE_style_windowsvista 1
#define QT_FEATURE_style_windows11 1
#else
#define QT_FEATURE_style_windowsvista -1
#define QT_FEATURE_style_windows11 -1
#endif
#define QT_FEATURE_style_android -1
#define QT_FEATURE_effects 1
#define QT_FEATURE_widgettextcontrol 1

#endif // QTWIDGETS_CONFIG_P_H
"""

_QTTESTLIB_CONFIG_H = """#ifndef QTTESTLIB_CONFIG_H
#define QTTESTLIB_CONFIG_H

#define QT_FEATURE_testlib_selfcover -1
#define QT_FEATURE_itemmodeltester 1
#define QT_FEATURE_valgrind 1
#define QT_FEATURE_batch_test_support -1

#endif // QTTESTLIB_CONFIG_H
"""

_QTTESTLIB_CONFIG_P_H = """#ifndef QTTESTLIB_CONFIG_P_H
#define QTTESTLIB_CONFIG_P_H

#endif // QTTESTLIB_CONFIG_P_H
"""

_TRACEPOINTS_P_H = """#include <private/qtrace_p.h>
"""

_QTXML_CONFIG_H = """#ifndef QTXML_CONFIG_H
#define QTXML_CONFIG_H

#define QT_FEATURE_dom 1

#endif // QTXML_CONFIG_H
"""

_QTSQL_CONFIG_H = """#ifndef QTSQL_CONFIG_H
#define QTSQL_CONFIG_H

#define QT_FEATURE_sqlmodel 1

#endif // QTSQL_CONFIG_H
"""

_QTSQL_CONFIG_P_H = """#ifndef QTSQL_CONFIG_P_H
#define QTSQL_CONFIG_P_H

#endif // QTSQL_CONFIG_P_H
"""

# src/plugins/sqldrivers/configure.cmake (SQLite on all platforms + ODBC on Windows).
_QTSQLDRIVERS_CONFIG_P_H = """#ifndef QTSQLDRIVERS_CONFIG_P_H
#define QTSQLDRIVERS_CONFIG_P_H

#define QT_FEATURE_sql_db2 -1
#define QT_FEATURE_sql_ibase -1
#define QT_FEATURE_sql_mysql -1
#define QT_FEATURE_sql_oci -1
#ifdef _WIN32
#define QT_FEATURE_sql_odbc 1
#else
#define QT_FEATURE_sql_odbc -1
#endif
#define QT_FEATURE_sql_psql -1
#define QT_FEATURE_sql_sqlite 1
#define QT_FEATURE_system_sqlite -1
#define QT_FEATURE_sql_mimer -1

#endif // QTSQLDRIVERS_CONFIG_P_H
"""

# src/network/configure.cmake, with OpenSSL + native TLS backends.
_QTNETWORK_CONFIG_H = """#ifndef QTNETWORK_CONFIG_H
#define QTNETWORK_CONFIG_H

#ifdef __APPLE__
#define QT_FEATURE_getifaddrs 1
#define QT_FEATURE_ipv6ifname 1
#define QT_FEATURE_securetransport 1
#else
#define QT_FEATURE_getifaddrs -1
#define QT_NO_GETIFADDRS 1
#define QT_FEATURE_ipv6ifname -1
#define QT_NO_IPV6IFNAME 1
#define QT_FEATURE_securetransport -1
#endif
#ifdef _WIN32
#define QT_FEATURE_schannel 1
#else
#define QT_FEATURE_schannel -1
#endif
#define QT_FEATURE_ssl 1
#define QT_FEATURE_dtls 1
#define QT_FEATURE_ocsp 1
#define QT_FEATURE_sctp -1
#define QT_NO_SCTP 1
#define QT_FEATURE_http 1
#define QT_FEATURE_udpsocket 1
#define QT_FEATURE_networkproxy 1
#define QT_FEATURE_socks5 1
#define QT_FEATURE_networkinterface 1
#define QT_FEATURE_networkdiskcache 1
#define QT_FEATURE_brotli -1
#define QT_NO_BROTLI 1
#define QT_FEATURE_localserver 1
#define QT_FEATURE_dnslookup 1
#define QT_FEATURE_gssapi -1
#define QT_NO_GSSAPI 1
#define QT_FEATURE_sspi -1
#define QT_NO_SSPI 1
#define QT_FEATURE_topleveldomain 1

#endif // QTNETWORK_CONFIG_H
"""

_QTNETWORK_CONFIG_P_H = """#ifndef QTNETWORK_CONFIG_P_H
#define QTNETWORK_CONFIG_P_H

#ifdef _WIN32
#define QT_FEATURE_libresolv -1
#define QT_FEATURE_linux_netlink -1
#define QT_FEATURE_networklistmanager 1
#elif defined(__APPLE__)
#define QT_FEATURE_libresolv 1
#define QT_FEATURE_linux_netlink -1
#define QT_FEATURE_networklistmanager -1
#else
#define QT_FEATURE_libresolv 1
#define QT_FEATURE_linux_netlink 1
#define QT_FEATURE_networklistmanager -1
#endif
#define QT_FEATURE_libproxy -1
#define QT_FEATURE_res_setservers -1
#define QT_FEATURE_system_proxies 1
#define QT_FEATURE_publicsuffix_qt 1
#define QT_FEATURE_publicsuffix_system -1

#endif // QTNETWORK_CONFIG_P_H
"""

_QTPRINTSUPPORT_CONFIG_H = """#ifndef QTPRINTSUPPORT_CONFIG_H
#define QTPRINTSUPPORT_CONFIG_H

#define QT_FEATURE_printer 1
#define QT_FEATURE_printpreviewwidget 1
#define QT_FEATURE_printdialog 1
#define QT_FEATURE_printpreviewdialog 1
#define QT_FEATURE_cups -1
#define QT_NO_CUPS 1
#define QT_FEATURE_cupsjobwidget -1
#define QT_NO_CUPSJOBWIDGET 1

#endif // QTPRINTSUPPORT_CONFIG_H
"""

_QTPRINTSUPPORT_CONFIG_P_H = """#ifndef QTPRINTSUPPORT_CONFIG_P_H
#define QTPRINTSUPPORT_CONFIG_P_H

#include <QtPrintSupport/qtprintsupport-config.h>
#define QT_FEATURE_cups -1
#define QT_FEATURE_cupsjobwidget -1
#define QT_FEATURE_cupspassworddialog 1

#endif // QTPRINTSUPPORT_CONFIG_P_H
"""

_QTWAYLANDGLOBAL_CONFIG_H = """#ifndef QTWAYLANDGLOBAL_CONFIG_H
#define QTWAYLANDGLOBAL_CONFIG_H

#endif // QTWAYLANDGLOBAL_CONFIG_H
"""

_QTWAYLANDGLOBAL_CONFIG_P_H = """#ifndef QTWAYLANDGLOBAL_CONFIG_P_H
#define QTWAYLANDGLOBAL_CONFIG_P_H

#include <QtGui/private/qtgui-config_p.h>

#endif // QTWAYLANDGLOBAL_CONFIG_P_H
"""

_QTWAYLANDCLIENT_CONFIG_H = """#ifndef QTWAYLANDCLIENT_CONFIG_H
#define QTWAYLANDCLIENT_CONFIG_H

#include <QtWaylandGlobal/qtwaylandglobal-config.h>

#endif // QTWAYLANDCLIENT_CONFIG_H
"""

_QTWAYLANDCLIENT_CONFIG_P_H = """#ifndef QTWAYLANDCLIENT_CONFIG_P_H
#define QTWAYLANDCLIENT_CONFIG_P_H

#include <QtWaylandGlobal/private/qtwaylandglobal-config_p.h>

#endif // QTWAYLANDCLIENT_CONFIG_P_H
"""

_QTWAYLANDCLIENTVERSION_H = """#ifndef QT_QTWAYLANDCLIENT_VERSION_H
#define QT_QTWAYLANDCLIENT_VERSION_H

#define QTWAYLANDCLIENT_VERSION_STR "6.10.2"
#define QTWAYLANDCLIENT_VERSION 0x061002

#endif // QT_QTWAYLANDCLIENT_VERSION_H
"""

_CONFIG_CONTENTS = {
    "qconfig.h": _QCONFIG_H,
    "qconfig_p.h": _QCONFIG_P_H,
    "qconfig.cpp": _QCONFIG_CPP,
    "qtdeprecationdefinitions.h": _QTDEPRECATIONDEFINITIONS_H,
    "qtcore-config.h": _QTCORE_CONFIG_H,
    "qtcore-config_p.h": _QTCORE_CONFIG_P_H,
    "qtgui-config.h": _QTGUI_CONFIG_H,
    "qtgui-config_p.h": _QTGUI_CONFIG_P_H,
    "qtwidgets-config.h": _QTWIDGETS_CONFIG_H,
    "qtwidgets-config_p.h": _QTWIDGETS_CONFIG_P_H,
    "qttestlib-config.h": _QTTESTLIB_CONFIG_H,
    "qttestlib-config_p.h": _QTTESTLIB_CONFIG_P_H,
    "qtxml-config.h": _QTXML_CONFIG_H,
    "qtsql-config.h": _QTSQL_CONFIG_H,
    "qtsql-config_p.h": _QTSQL_CONFIG_P_H,
    "qtsqldrivers-config_p.h": _QTSQLDRIVERS_CONFIG_P_H,
    "qtnetwork-config.h": _QTNETWORK_CONFIG_H,
    "qtnetwork-config_p.h": _QTNETWORK_CONFIG_P_H,
    "qtprintsupport-config.h": _QTPRINTSUPPORT_CONFIG_H,
    "qtprintsupport-config_p.h": _QTPRINTSUPPORT_CONFIG_P_H,
    "qtnetwork_tracepoints_p.h": _TRACEPOINTS_P_H,
    "qtcore_tracepoints_p.h": _TRACEPOINTS_P_H,
    "qtgui_tracepoints_p.h": _TRACEPOINTS_P_H,
    "qtwidgets_tracepoints_p.h": _TRACEPOINTS_P_H,
    "qtopengl_tracepoints_p.h": _TRACEPOINTS_P_H,
    "qtwaylandglobal-config.h": _QTWAYLANDGLOBAL_CONFIG_H,
    "qtwaylandglobal-config_p.h": _QTWAYLANDGLOBAL_CONFIG_P_H,
    "qtwaylandclient-config.h": _QTWAYLANDCLIENT_CONFIG_H,
    "qtwaylandclient-config_p.h": _QTWAYLANDCLIENT_CONFIG_P_H,
    "qtwaylandclientversion.h": _QTWAYLANDCLIENTVERSION_H,
}

def _qt_write_config_file_impl(ctx):
    out = ctx.actions.declare_file(ctx.attr.out)
    content = _CONFIG_CONTENTS[ctx.attr.template_key]
    ctx.actions.write(out, content)
    return [DefaultInfo(files = depset([out]))]

qt_write_config_file = rule(
    implementation = _qt_write_config_file_impl,
    attrs = {
        "out": attr.string(mandatory = True),
        "template_key": attr.string(mandatory = True),
    },
)

def _qt_mime_database_impl(ctx):
    out = ctx.actions.declare_file(ctx.attr.out)
    ctx.actions.run(
        executable = ctx.executable._tool,
        arguments = [ctx.file.src.path, out.path],
        inputs = [ctx.file.src],
        outputs = [out],
        mnemonic = "QtMimeDatabase",
        progress_message = "Generating qmimeprovider_database.cpp",
    )
    return [DefaultInfo(files = depset([out]))]

# Compresses the shared-mime-info XML into the C array that
# src/corelib/mimetypes/qmimeprovider.cpp embeds. The compressor is a small
# cc_binary built for the execution platform (see qt_mime_database_gen.cc), so
# this works on every host without relying on a system python3/gzip.
qt_mime_database = rule(
    implementation = _qt_mime_database_impl,
    attrs = {
        "src": attr.label(allow_single_file = True, mandatory = True),
        "out": attr.string(mandatory = True),
        "_tool": attr.label(
            default = Label("//:qt_mime_database_gen"),
            executable = True,
            cfg = "exec",
        ),
    },
)

def _qt_vkgen_impl(ctx):
    out_h = ctx.actions.declare_file("vulkan/qvulkanfunctions.h")
    out_p_h = ctx.actions.declare_file("vulkan/qvulkanfunctions_p.h")
    out_p_cpp = ctx.actions.declare_file("vulkan/qvulkanfunctions_p.cpp")
    prefix = out_h.path[:-2]
    ctx.actions.run(
        executable = ctx.executable._qvkgen,
        arguments = [
            ctx.file.vk_xml.path,
            ctx.file.license_header.path,
            prefix,
        ],
        inputs = [ctx.file.vk_xml, ctx.file.license_header],
        outputs = [out_h, out_p_h, out_p_cpp],
        mnemonic = "QtVkGen",
        progress_message = "Generating Qt Vulkan function wrappers",
    )
    return [
        DefaultInfo(files = depset([out_h, out_p_h, out_p_cpp])),
        OutputGroupInfo(
            h = depset([out_h]),
            p_h = depset([out_p_h]),
            p_cpp = depset([out_p_cpp]),
        ),
    ]

qt_vkgen = rule(
    implementation = _qt_vkgen_impl,
    attrs = {
        "vk_xml": attr.label(allow_single_file = True, mandatory = True),
        "license_header": attr.label(allow_single_file = True, mandatory = True),
        "_qvkgen": attr.label(
            default = Label("//:qvkgen"),
            executable = True,
            cfg = "exec",
        ),
    },
)

def declare_qtbase_config_targets():
    """Declares all generated config header and source targets for @qtbase."""
    qt_write_config_file(
        name = "gen_qconfig_h",
        out = "generated_cfg/QtCore/qconfig.h",
        template_key = "qconfig.h",
    )
    qt_write_config_file(
        name = "gen_qconfig_p_h",
        out = "generated_cfg/QtCore/private/qconfig_p.h",
        template_key = "qconfig_p.h",
    )
    qt_write_config_file(
        name = "gen_qconfig_cpp",
        out = "generated_cfg/QtCore/qconfig.cpp",
        template_key = "qconfig.cpp",
    )
    qt_write_config_file(
        name = "gen_qtdeprecationdefinitions_h",
        out = "generated_cfg/QtCore/qtdeprecationdefinitions.h",
        template_key = "qtdeprecationdefinitions.h",
    )
    qt_write_config_file(
        name = "gen_qtcore_config_h",
        out = "generated_cfg/QtCore/qtcore-config.h",
        template_key = "qtcore-config.h",
    )
    qt_write_config_file(
        name = "gen_qtcore_config_p_h",
        out = "generated_cfg/QtCore/private/qtcore-config_p.h",
        template_key = "qtcore-config_p.h",
    )
    qt_write_config_file(
        name = "gen_qtcore_tracepoints_p_h",
        out = "generated_cfg/QtCore/qtcore_tracepoints_p.h",
        template_key = "qtcore_tracepoints_p.h",
    )
    qt_write_config_file(
        name = "gen_qtgui_config_h",
        out = "generated_cfg/QtGui/qtgui-config.h",
        template_key = "qtgui-config.h",
    )
    qt_write_config_file(
        name = "gen_qtgui_config_p_h",
        out = "generated_cfg/QtGui/private/qtgui-config_p.h",
        template_key = "qtgui-config_p.h",
    )
    qt_write_config_file(
        name = "gen_qtgui_tracepoints_p_h",
        out = "generated_cfg/QtGui/qtgui_tracepoints_p.h",
        template_key = "qtgui_tracepoints_p.h",
    )
    qt_write_config_file(
        name = "gen_qtwidgets_config_h",
        out = "generated_cfg/QtWidgets/qtwidgets-config.h",
        template_key = "qtwidgets-config.h",
    )
    qt_write_config_file(
        name = "gen_qtwidgets_config_p_h",
        out = "generated_cfg/QtWidgets/private/qtwidgets-config_p.h",
        template_key = "qtwidgets-config_p.h",
    )
    qt_write_config_file(
        name = "gen_qtwidgets_tracepoints_p_h",
        out = "generated_cfg/QtWidgets/qtwidgets_tracepoints_p.h",
        template_key = "qtwidgets_tracepoints_p.h",
    )
    qt_write_config_file(
        name = "gen_qttestlib_config_h",
        out = "generated_cfg/QtTest/qttestlib-config.h",
        template_key = "qttestlib-config.h",
    )
    qt_write_config_file(
        name = "gen_qttestlib_config_p_h",
        out = "generated_cfg/QtTest/private/qttestlib-config_p.h",
        template_key = "qttestlib-config_p.h",
    )
    qt_mime_database(
        name = "gen_qmimeprovider_database_cpp",
        src = "src/corelib/mimetypes/3rdparty/tika-mimetypes.xml",
        out = "generated_cfg/QtCore/.rcc/qmimeprovider_database.cpp",
    )
    cc_library(
        name = "core_internal_cfg",
        textual_hdrs = [
            ":gen_qconfig_cpp",
            ":gen_qconfig_h",
            ":gen_qconfig_p_h",
            ":gen_qtdeprecationdefinitions_h",
            ":gen_qtcore_config_h",
            ":gen_qtcore_config_p_h",
            ":gen_qtcore_tracepoints_p_h",
            ":gen_qmimeprovider_database_cpp",
        ],
        includes = [
            "generated_cfg/QtCore",
            "generated_cfg/QtCore/private",
            "generated_cfg/QtCore/.rcc",
        ],
    )
    cc_library(
        name = "gui_internal_cfg",
        textual_hdrs = [
            ":gen_qtgui_config_h",
            ":gen_qtgui_config_p_h",
            ":gen_qtgui_tracepoints_p_h",
        ],
        includes = [
            "generated_cfg/QtGui",
            "generated_cfg/QtGui/private",
        ],
    )
    cc_library(
        name = "widgets_internal_cfg",
        textual_hdrs = [
            ":gen_qtwidgets_config_h",
            ":gen_qtwidgets_config_p_h",
            ":gen_qtwidgets_tracepoints_p_h",
        ],
        includes = [
            "generated_cfg/QtWidgets",
            "generated_cfg/QtWidgets/private",
        ],
    )
    for key, out in [
        ("qtxml-config.h", "generated_cfg/QtXml/qtxml-config.h"),
        ("qtsql-config.h", "generated_cfg/QtSql/qtsql-config.h"),
        ("qtsql-config_p.h", "generated_cfg/QtSql/private/qtsql-config_p.h"),
        ("qtsqldrivers-config_p.h", "generated_cfg/QtSql/private/qtsqldrivers-config_p.h"),
        ("qtnetwork-config.h", "generated_cfg/QtNetwork/qtnetwork-config.h"),
        ("qtnetwork-config_p.h", "generated_cfg/QtNetwork/private/qtnetwork-config_p.h"),
        ("qtnetwork_tracepoints_p.h", "generated_cfg/QtNetwork/qtnetwork_tracepoints_p.h"),
        ("qtprintsupport-config.h", "generated_cfg/QtPrintSupport/qtprintsupport-config.h"),
        ("qtprintsupport-config_p.h", "generated_cfg/QtPrintSupport/private/qtprintsupport-config_p.h"),
        ("qtopengl_tracepoints_p.h", "generated_cfg/QtOpenGL/qtopengl_tracepoints_p.h"),
        ("qtwaylandglobal-config.h", "generated_cfg/QtWaylandGlobal/qtwaylandglobal-config.h"),
        ("qtwaylandglobal-config_p.h", "generated_cfg/QtWaylandGlobal/private/qtwaylandglobal-config_p.h"),
        ("qtwaylandclient-config.h", "generated_cfg/QtWaylandClient/qtwaylandclient-config.h"),
        ("qtwaylandclient-config_p.h", "generated_cfg/QtWaylandClient/private/qtwaylandclient-config_p.h"),
        ("qtwaylandclientversion.h", "generated_cfg/QtWaylandClient/qtwaylandclientversion.h"),
    ]:
        qt_write_config_file(
            name = "gen_" + key.replace("-", "_").replace(".", "_"),
            out = out,
            template_key = key,
        )
    cc_library(
        name = "printsupport_internal_cfg",
        textual_hdrs = [
            ":gen_qtprintsupport_config_h",
            ":gen_qtprintsupport_config_p_h",
        ],
        includes = [
            "generated_cfg/QtPrintSupport",
            "generated_cfg/QtPrintSupport/private",
        ],
    )
    cc_library(
        name = "opengl_internal_cfg",
        textual_hdrs = [":gen_qtopengl_tracepoints_p_h"],
        includes = ["generated_cfg/QtOpenGL"],
    )
    cc_library(
        name = "xml_internal_cfg",
        textual_hdrs = [":gen_qtxml_config_h"],
        includes = ["generated_cfg/QtXml"],
    )
    cc_library(
        name = "sql_internal_cfg",
        textual_hdrs = [
            ":gen_qtsql_config_h",
            ":gen_qtsql_config_p_h",
            ":gen_qtsqldrivers_config_p_h",
        ],
        includes = [
            "generated_cfg/QtSql",
            "generated_cfg/QtSql/private",
        ],
    )
    cc_library(
        name = "network_internal_cfg",
        textual_hdrs = [
            ":gen_qtnetwork_config_h",
            ":gen_qtnetwork_config_p_h",
            ":gen_qtnetwork_tracepoints_p_h",
        ],
        includes = [
            "generated_cfg/QtNetwork",
            "generated_cfg/QtNetwork/private",
        ],
    )
    cc_library(
        name = "testlib_internal_cfg",
        textual_hdrs = [
            ":gen_qttestlib_config_h",
            ":gen_qttestlib_config_p_h",
        ],
        includes = [
            "generated_cfg/QtTest",
            "generated_cfg/QtTest/private",
        ],
    )
    cc_library(
        name = "atspi_headers",
        hdrs = [
            "atspi/atspi-constants.h",
            "atspi/atspi.h",
        ],
        applicable_licenses = [":license_atspi"],
        includes = ["."],
        target_compatible_with = ["@platforms//os:linux"],
    )
    cc_library(
        name = "mvk_vulkan_h",
        hdrs = ["moltenvk/mvk_vulkan.h"],
        include_prefix = "MoltenVK",
        strip_include_prefix = "moltenvk",
        target_compatible_with = ["@platforms//os:macos"],
        deps = ["@vulkan_headers//:vulkan_headers_no_prototypes"],
    )
    native.alias(
        name = "glvnd_stubs",
        actual = "@libglvnd//:glvnd_stubs",
        target_compatible_with = ["@platforms//os:linux"],
    )
    qt_vkgen(
        name = "gen_qvulkanfunctions",
        license_header = "src/gui/vulkan/licenseheader.h.in",
        vk_xml = "src/gui/vulkan/vk.xml",
    )
    native.filegroup(
        name = "qvulkanfunctions_h",
        srcs = [":gen_qvulkanfunctions"],
        output_group = "h",
    )
    native.filegroup(
        name = "qvulkanfunctions_p_h",
        srcs = [":gen_qvulkanfunctions"],
        output_group = "p_h",
    )
    native.filegroup(
        name = "qvulkanfunctions_p_cpp",
        srcs = [":gen_qvulkanfunctions"],
        output_group = "p_cpp",
    )
    qt_write_file(
        name = "gen_qfilesystemengine_unix_mac_mm",
        out = "generated_cfg/QtCore/qfilesystemengine_unix_mac.mm",
        content = '#include "src/corelib/io/qfilesystemengine_unix.cpp"\n',
    )

#ifndef __GST_OVERALL_CONFIG_H__
#define __GST_OVERALL_CONFIG_H__

#define GST_API_VERSION "1.0"
#define GST_DATADIR "/nonexistent/share"
#define LOCALEDIR "/nonexistent/share/locale"
#define LIBDIR "/nonexistent/lib"
#define PLUGINDIR "/nonexistent/lib/gstreamer-1.0"
#define GETTEXT_PACKAGE "gstreamer-1.0"
#define GST_LICENSE "LGPL"
#define GST_PACKAGE_NAME "GStreamer source release"
#define GST_PACKAGE_ORIGIN "Unknown package origin"
#define GST_PACKAGE_RELEASE_DATETIME "2024-12-03"
#define PACKAGE "gstreamer"
#define PACKAGE_NAME "GStreamer"
#define PACKAGE_STRING "GStreamer 1.24.10"
#define PACKAGE_TARNAME "gstreamer"
#define PACKAGE_BUGREPORT "https://gitlab.freedesktop.org/gstreamer/gstreamer/issues/new"
#define PACKAGE_URL ""
#define PACKAGE_VERSION "1.24.10"
#define VERSION "1.24.10"

#define GST_PLUGIN_SCANNER_INSTALLED "/nonexistent/libexec/gstreamer-1.0/gst-plugin-scanner"
#define GST_PTP_HELPER_INSTALLED "/nonexistent/libexec/gstreamer-1.0/gst-ptp-helper"
#define GST_PLUGIN_SUBDIR "lib"
#define GST_PLUGIN_SCANNER_SUBDIR "libexec"
#define GST_PTP_HELPER_SUBDIR "libexec"
#define GST_INSTALL_PLUGINS_HELPER "/nonexistent/libexec/gst-install-plugins-helper"
#define GIO_MODULE_DIR "/nonexistent/lib/gio/modules"
#define GIO_LIBDIR "/nonexistent/lib"
#define GIO_PREFIX "/nonexistent"

#define DEFAULT_VIDEOSINK "autovideosink"
#define DEFAULT_AUDIOSINK "autoaudiosink"
#define COLORSPACE "videoconvert"
#define LICENSE_TRANSLATIONS_PATH "/nonexistent/share/gst-plugins-base/1.0/license-translations.dict"
#define AUDIORESAMPLE_FORMAT_AUTO 1
#define MEMORY_ALIGNMENT_MALLOC 1
#define GST_LEVEL_DEFAULT GST_LEVEL_NONE
#define GST_ENABLE_EXTRA_CHECKS 1
#define DISABLE_ORC 1
#define HAVE_ZLIB 1
#define HAVE_GIO 1

#if defined(__x86_64__) || defined(_M_X64)
#define HAVE_CPU_X86_64 1
#define HOST_CPU "x86_64"
#define TARGET_CPU "x86_64"
#elif defined(__aarch64__) || defined(_M_ARM64)
#define HAVE_CPU_AARCH64 1
#define HOST_CPU "aarch64"
#define TARGET_CPU "aarch64"
#else
#define HOST_CPU "unknown"
#define TARGET_CPU "unknown"
#endif

#define SIZEOF_CHAR 1
#define SIZEOF_SHORT 2
#define SIZEOF_INT 4
#define SIZEOF_LONG __SIZEOF_LONG__
#define SIZEOF_VOIDP __SIZEOF_POINTER__
#define SIZEOF_OFF_T 8

#define HAVE_LONG_LONG 1
#define HAVE_UINT128_T 1
#define HAVE_DLFCN_H 1
#define HAVE_INTTYPES_H 1
#define HAVE_MEMORY_H 1
#define HAVE_NETINET_IN_H 1
#define HAVE_NETINET_TCP_H 1
#define HAVE_POLL_H 1
#define HAVE_STDINT_H 1
#define HAVE_STRINGS_H 1
#define HAVE_STRING_H 1
#define HAVE_SYS_PARAM_H 1
#define HAVE_SYS_POLL_H 1
#define HAVE_SYS_RESOURCE_H 1
#define HAVE_SYS_SOCKET_H 1
#define HAVE_SYS_STAT_H 1
#define HAVE_SYS_TIMES_H 1
#define HAVE_SYS_TIME_H 1
#define HAVE_SYS_TYPES_H 1
#define HAVE_SYS_UIO_H 1
#define HAVE_SYS_UTSNAME_H 1
#define HAVE_SYS_WAIT_H 1
#define HAVE_UCONTEXT_H 1
#define HAVE_UNISTD_H 1

#define HAVE_ALARM 1
#define HAVE_ASINH 1
#define HAVE_CLOCK_GETTIME 1
#define HAVE_COSH 1
#define HAVE_DECL_LOCALTIME_R 1
#define HAVE_DECL_STRDUP 1
#define HAVE_DECL_STRSIGNAL 1
#define HAVE_DLADDR 1
#define HAVE_FORK 1
#define HAVE_FSEEKO 1
#define HAVE_FTELLO 1
#define HAVE_GETLINE 1
#define HAVE_GETPAGESIZE 1
#define HAVE_GETPID 1
#define HAVE_GETRUSAGE 1
#define HAVE_GETTIMEOFDAY 1
#define HAVE_GIO_UNIX_2_0 1
#define HAVE_GMTIME_R 1
#define HAVE_ISINF 1
#define HAVE_LOCALTIME_R 1
#define HAVE_LOG2 1
#define HAVE_LRINTF 1
#define HAVE_MEMMEM 1
#define HAVE_MKSTEMP 1
#define HAVE_MMAP 1
#define HAVE_MONOTONIC_CLOCK 1
#define HAVE_PIPE 1
#define HAVE_POLL 1
#define HAVE_POSIX_TIMERS 1
#define HAVE_PSELECT 1
#define HAVE_RTLD_NOLOAD 1
#define HAVE_SIGACTION 1
#define HAVE_SINH 1
#define HAVE_STRNLEN 1
#define HAVE_TM_GMTOFF 1

#ifdef __linux__
#define HAVE_CLOCK_NANOSLEEP 1
#define HAVE_FGETPOS 1
#define HAVE_FSETPOS 1
#define HAVE_FUTEX 1
#define HAVE_LINUX_DMA_BUF_H 1
#define HAVE_MMAP64 1
#define HAVE_PPOLL 1
#define HAVE_PTHREAD_CONDATTR_SETCLOCK 1
#define HAVE_STDIO_EXT_H 1
#define HAVE_SYS_PRCTL_H 1
#endif

#ifdef __APPLE__
#define GST_EXTRA_MODULE_SUFFIX ".dylib"
#define HAVE_PTHREAD_SETNAME_NP_WITHOUT_TID 1
#define HAVE_PTHREAD_COND_TIMEDWAIT_RELATIVE_NP 1
#endif

#endif /* __GST_OVERALL_CONFIG_H__ */

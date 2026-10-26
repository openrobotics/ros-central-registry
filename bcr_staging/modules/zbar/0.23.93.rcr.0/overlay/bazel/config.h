/*
 * config.h for zbar 0.23.93 on Linux (glibc), as produced by upstream's
 * `./configure --without-x --without-gtk --without-qt --without-python
 * --without-imagemagick --without-graphicsmagick --without-java
 * --without-dbus --disable-doc` with libjpeg available (JPEG conversions
 * enabled via libjpeg-turbo). Nothing below is CPU-architecture specific.
 */

/* Symbologies: upstream default --enable-codes set (PDF417 disabled). */
#define ENABLE_CODABAR 1
#define ENABLE_CODE128 1
#define ENABLE_CODE39 1
#define ENABLE_CODE93 1
#define ENABLE_DATABAR 1
#define ENABLE_EAN 1
#define ENABLE_I25 1
#define ENABLE_PDF417 0
#define ENABLE_QRCODE 1
#define ENABLE_SQCODE 1

#define HAVE_ALARM 1
#define HAVE_CLOCK_GETTIME 1
#define HAVE_DLFCN_H 1
#define HAVE_ERRNO_H 1
#define HAVE_FCNTL_H 1
#ifndef __APPLE__
#define HAVE_FEATURES_H 1
#endif
#define HAVE_FLOAT_H 1
#define HAVE_GETCWD 1
#define HAVE_GETPAGESIZE 1
#define HAVE_GETTIMEOFDAY 1
#define HAVE_ICONV 1
#define HAVE_INTTYPES_H 1
#define HAVE_JERROR_H 1
#define HAVE_JPEGLIB_H 1
#define HAVE_LIBJPEG 1
#define HAVE_LIBPTHREAD 1
#define HAVE_LIMITS_H 1
#ifndef __APPLE__
#define HAVE_LINUX_VIDEODEV2_H 1
#endif
#define HAVE_LOCALECONV 1
#define HAVE_LOCALE_H 1
#define HAVE_MALLOC 1
#define HAVE_MEMCHR 1
#define HAVE_MEMMOVE 1
#define HAVE_MEMSET 1
#define HAVE_MMAP 1
#define HAVE_MODF 1
#define HAVE_MUNMAP 1
#define HAVE_POLL_H 1
#define HAVE_PTHREAD_H 1
#define HAVE_REALLOC 1
#define HAVE_SELECT 1
#define HAVE_SETENV 1
#define HAVE_STDDEF_H 1
#define HAVE_STDINT_H 1
#define HAVE_STDIO_H 1
#define HAVE_STDLIB_H 1
#define HAVE_STRCASECMP 1
#define HAVE_STRCHR 1
#define HAVE_STRDUP 1
#define HAVE_STRERROR 1
#define HAVE_STRINGS_H 1
#define HAVE_STRING_H 1
#define HAVE_STRRCHR 1
#define HAVE_STRSTR 1
#define HAVE_STRTOL 1
#define HAVE_STRTOUL 1
#define HAVE_STRUCT_STAT_ST_RDEV 1
#define HAVE_SYS_IOCTL_H 1
#define HAVE_SYS_IPC_H 1
#define HAVE_SYS_MMAN_H 1
#define HAVE_SYS_PARAM_H 1
#define HAVE_SYS_SHM_H 1
#define HAVE_SYS_STAT_H 1
#define HAVE_SYS_TIMES_H 1
#define HAVE_SYS_TIME_H 1
#define HAVE_SYS_TYPES_H 1
#define HAVE_UINTPTR_T 1
#define HAVE_UNISTD_H 1
#define HAVE__BOOL 1

#define ICONV_CONST

/* LIB_VERSION 3:0:3 */
#define LIB_VERSION_MAJOR 0
#define LIB_VERSION_MINOR 3
#define LIB_VERSION_REVISION 0

#define LT_OBJDIR ".libs/"
#define MAJOR_IN_SYSMACROS 1

#define PACKAGE "zbar"
#define PACKAGE_BUGREPORT "mchehab+huawei@kernel.org"
#define PACKAGE_NAME "zbar"
#define PACKAGE_STRING "zbar 0.23.93"
#define PACKAGE_TARNAME "zbar"
#define PACKAGE_URL ""
#define PACKAGE_VERSION "0.23.93"
#define STDC_HEADERS 1
#define VERSION "0.23.93"

/* No X11 window/processor support (window/null.c, processor/null.c). */
#define X_DISPLAY_MISSING 1

#define ZBAR_VERSION_MAJOR 0
#define ZBAR_VERSION_MINOR 23
#define ZBAR_VERSION_PATCH 93

/* used only for pthread debug attributes */
#define __USE_UNIX98 1

#ifndef X_DISPLAY_MISSING
# define HAVE_X
#endif

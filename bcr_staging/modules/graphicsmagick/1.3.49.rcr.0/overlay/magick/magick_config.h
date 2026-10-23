/*
  Static replacement for the autoconf-generated magick/magick_config.h (and
  the installed magick_config_api.h) used by the Bazel build.

  Upstream's configure script produces two headers from
  magick/magick_config.h.in and magick/magick_config_api.h.in:

    * magick/magick_config.h      -- the full build configuration, used while
                                     compiling the library itself.
    * magick/magick_config_api.h  -- a tiny subset (QuantumDepth, HasX11,
                                     WORDS_BIGENDIAN), installed under the
                                     name magick/magick_config.h for API
                                     consumers.

  Bazel consumes the library in-tree, so both roles are served by this single
  file: every library translation unit defines MAGICK_IMPLEMENTATION before
  including it (magick/studio.h does so for the C library; each Magick++
  library source does so explicitly), and only those translation units see the
  full configuration. Downstream consumers only see the public subset, which
  is identical to what an installed GraphicsMagick exposes.

  The values below mirror a reference run of upstream's configure on
  x86_64 Linux (glibc) with:

    --disable-shared --enable-static --without-modules --without-x
    --disable-openmp --with-quantum-depth=16 --without-bzlib --without-lzma
    --without-zstd --without-lcms2 --without-wmf --without-gslib --without-ttf
    --without-xml --without-jbig --without-jp2 --without-jxl --without-heif
    --without-webp --without-fpx --without-trio --without-umem
    --without-mtmalloc --without-tcmalloc

  with JPEG/PNG/TIFF/zlib supplied by their Bazel Central Registry modules.
  The few function/header checks whose results differ between glibc and
  macOS are switched on __linux__/__APPLE__ below rather than via select()
  so the header stays correct for any consumer, including cross builds.

  Deliberate deviations from that reference run:
    * QuantumDepth is 16 (configure defaults to 8) to match the Q16 builds
      shipped by Debian/Ubuntu, which ROS packages are developed against.
    * HAVE_STRLCPY/HAVE_STRLCAT are left undefined so GraphicsMagick always
      uses its own MagickStrlCpy/MagickStrlCat (glibc only gained strlcpy in
      2.38, and only declares it with _DEFAULT_SOURCE/_GNU_SOURCE).
    * HAVE_FTIME/HAVE_READDIR_R/HAVE_QSORT_R/HAVE_STRERROR_R are not defined:
      they are deprecated or have platform-specific signatures, and are
      either unused by the sources or have portable fallbacks.
    * UseInstalledMagick is not defined, so the library is relocatable and
      looks for optional *.mgk configuration files under $MAGICK_HOME or
      next to the executable instead of a hard-coded install prefix. None of
      those files are required: colors, logging defaults and module aliases
      are compiled in.
    * The libjpeg 12/16-bit and lossless entry points are not advertised,
      since the BCR libjpeg_turbo build does not guarantee them.
*/
#ifndef _MAGICK_MAGICK_CONFIG_H
#define _MAGICK_MAGICK_CONFIG_H

/* ------------------------------------------------------------------------
   Public configuration (magick_config_api.h equivalent).
   ------------------------------------------------------------------------ */

/* Number of bits in a pixel Quantum (8/16/32) */
#define QuantumDepth 16

/* Define if you have X11 library */
/* #undef HasX11 */

/* Define to 1 if your processor stores words with the most significant byte
   first (like Motorola and SPARC, unlike Intel and VAX). */
#if defined(__BYTE_ORDER__) && defined(__ORDER_BIG_ENDIAN__) && \
    (__BYTE_ORDER__ == __ORDER_BIG_ENDIAN__)
#  define WORDS_BIGENDIAN 1
#endif

/* ------------------------------------------------------------------------
   Private build configuration (magick_config.h equivalent).
   ------------------------------------------------------------------------ */
#if defined(MAGICK_IMPLEMENTATION)

/* Coders and filters are linked statically (no BuildMagickModules). */
/* #undef BuildMagickModules */

/* Disable OpenMP for algorithms which sometimes run slower */
#define DisableSlowOpenMP 1

/* Host identification triplet */
#if defined(__APPLE__)
#  define GM_BUILD_HOST "apple-darwin"
#elif defined(__linux__)
#  define GM_BUILD_HOST "linux-gnu"
#endif

/* Arguments passed to configure */
#define GM_BUILD_CONFIGURE_ARGS "bazel (static magick_config.h)"

/* Define if C++ compiler supports __func__ */
#define HAS_CPP__func__ 1

/* Define if C compiler supports __func__ */
#define HAS_C__func__ 1

#define HAVE_ATOLL 1
#define HAVE_BOOL /**/
#define HAVE_CLOCK_GETRES 1
#define HAVE_CLOCK_GETTIME 1
#define HAVE_CONST_CAST /**/
#define HAVE_COSF 1
#define HAVE_CTIME_R 1
#define HAVE_DECL_PREAD 1
#define HAVE_DECL_PWRITE 1
#define HAVE_DEFAULT_TEMPLATE_PARAMETERS /**/
#define HAVE_DEV_URANDOM 1
#define HAVE_DIRENT_H 1
#define HAVE_DLFCN_H 1
#define HAVE_EXCEPTIONS /**/
#define HAVE_EXPLICIT /**/
#define HAVE_FABSF 1
#define HAVE_FCNTL 1
#define HAVE_FSEEKO 1
#define HAVE_FSTATVFS 1
#define HAVE_GETC_UNLOCKED 1
#define HAVE_GETPAGESIZE 1
#define HAVE_GETPID 1
#define HAVE_GETPWNAM_R 1
#define HAVE_GETRLIMIT 1
#define HAVE_INTTYPES_H 1
#define HAVE_LOCALTIME_R 1
#define HAVE_LOGF 1
#define HAVE_MADVISE 1
#define HAVE_MMAP_FILEIO 1
#define HAVE_MUTABLE /**/
#define HAVE_NAMESPACES /**/
#define HAVE_NEW_FOR_SCOPING /**/
#define HAVE_PCLOSE 1
#define HAVE_POLL 1
#define HAVE_POPEN 1
#define HAVE_POSIX_MADVISE 1
#define HAVE_POSIX_MEMALIGN 1
#define HAVE_POSIX_SPAWNP 1
#define HAVE_PREAD 1
#define HAVE_PTHREAD 1
#define HAVE_PUTC_UNLOCKED 1
#define HAVE_PWRITE 1
#define HAVE_RAISE 1
#define HAVE_RAND_R 1
#define HAVE_READLINK 1
#define HAVE_REALPATH 1
#define HAVE_SEEKDIR 1
#define HAVE_SELECT 1
#define HAVE_SETRLIMIT 1
#define HAVE_SIGACTION 1
#define HAVE_SIGEMPTYSET 1
#define HAVE_SINF 1
#define HAVE_SQRTF 1
#define HAVE_STATIC_CAST /**/
#define HAVE_STD /**/
#define HAVE_STDINT_H 1
#define HAVE_STDIO_H 1
#define HAVE_STDLIB_H 1
#define HAVE_STL /**/
#define HAVE_STRERROR 1
#define HAVE_STRINGS_H 1
#define HAVE_STRING_H 1
#define HAVE_STRTOLL 1
#define HAVE_SYSCONF 1
#define HAVE_SYS_MMAN_H 1
#define HAVE_SYS_RESOURCE_H 1
#define HAVE_SYS_STAT_H 1
#define HAVE_SYS_TIMES_H 1
#define HAVE_SYS_TYPES_H 1
#define HAVE_TELLDIR 1
#define HAVE_TEMPLATES /**/
#define HAVE_TIMES 1
#define HAVE_UNISTD_H 1
#define HAVE_VSNPRINTF 1
#define HAVE_VSPRINTF 1
#define HAVE_WCHAR_H 1
#define HAVE__EXIT 1

#if defined(__linux__)
/* glibc-only facilities. */
#  define HAVE_MALLOC_H 1
#  define HAVE_MALLOPT 1
#  define HAVE_POSIX_FADVISE 1
#  define HAVE_POSIX_FALLOCATE 1
#endif /* defined(__linux__) */

#if defined(__APPLE__)
/* Used to locate the running executable. */
#  define HAVE_MACH_O_DYLD_H 1
#  define HAVE__NSGETEXECUTABLEPATH 1
#endif /* defined(__APPLE__) */

/* Define to 1 if the type 'long double' is wider than 'double' (true for
   x86 80-bit and AArch64 Linux 128-bit long double; false on Apple arm64). */
#if defined(__SIZEOF_LONG_DOUBLE__) && defined(__SIZEOF_DOUBLE__) && \
    (__SIZEOF_LONG_DOUBLE__ > __SIZEOF_DOUBLE__)
#  define HAVE_LONG_DOUBLE_WIDER 1
#endif

/* The size of 'signed long', as computed by sizeof. */
#define SIZEOF_SIGNED_LONG __SIZEOF_LONG__

/* Setjmp/longjmp are thread safe */
#define SETJMP_IS_THREAD_SAFE 1

/* Define to 1 if all of the C89 standard headers exist. */
#define STDC_HEADERS 1

/* Delegate libraries supplied by Bazel Central Registry modules. */
#define HasJPEG 1
#define HasPNG 1
#define HasTIFF 1
#define HasZLIB 1

/* libtiff >= 4.5 features (BCR libtiff). */
#define HAVE_TIFFCONF_H 1
#define HAVE_TIFFERROREXTR 1
#define HAVE_TIFFISCODECCONFIGURED 1
#define HAVE_TIFFMERGEFIELDINFO 1
#define HAVE_TIFFOPENOPTIONSSETMAXCUMULATEDMEMALLOC 1
#define HAVE_TIFFSETERRORHANDLEREXT 1
#define HAVE_TIFFSETTAGEXTENDER 1
#define HAVE_TIFFSETWARNINGHANDLEREXT 1
#define HAVE_TIFFSWABARRAYOFTRIPLES 1
#define HAVE_TIFFWARNINGEXTR 1

/* Informational target triplet (only used in version banners). */
#if defined(__x86_64__)
#  define MAGICK_TARGET_CPU x86_64
#elif defined(__aarch64__) || defined(__arm64__)
#  define MAGICK_TARGET_CPU aarch64
#endif
#if defined(__APPLE__)
#  define MAGICK_TARGET_OS darwin
#  define MAGICK_TARGET_VENDOR apple
#elif defined(__linux__)
#  define MAGICK_TARGET_OS linux-gnu
#  define MAGICK_TARGET_VENDOR pc
#endif

/* Relative configuration/module sub-directories. Only consulted when
   searching $MAGICK_HOME or the executable's prefix for optional *.mgk
   files (UseInstalledMagick is intentionally not defined). */
#define MagickCoderModulesSubdir "GraphicsMagick-1.3.49/modules-Q16/coders"
#define MagickFilterModulesSubdir "GraphicsMagick-1.3.49/modules-Q16/filters"
#define MagickLibConfigSubDir "GraphicsMagick-1.3.49/config"
#define MagickLibSubdir "GraphicsMagick-1.3.49"
#define MagickShareConfigSubDir "GraphicsMagick-1.3.49/config"

/* Package identification (configure leaves these empty). */
#define PACKAGE_BUGREPORT ""
#define PACKAGE_NAME ""
#define PACKAGE_STRING ""
#define PACKAGE_TARNAME ""
#define PACKAGE_URL ""
#define PACKAGE_VERSION ""

/* Define to 1 if the X Window System is missing or not being used. */
#define X_DISPLAY_MISSING 1

/* Enable extensions on systems that have them (AC_USE_SYSTEM_EXTENSIONS). */
#ifndef _ALL_SOURCE
#  define _ALL_SOURCE 1
#endif
#ifndef _DARWIN_C_SOURCE
#  define _DARWIN_C_SOURCE 1
#endif
#ifndef __EXTENSIONS__
#  define __EXTENSIONS__ 1
#endif
#ifndef _GNU_SOURCE
#  define _GNU_SOURCE 1
#endif
#ifndef _POSIX_PTHREAD_SEMANTICS
#  define _POSIX_PTHREAD_SEMANTICS 1
#endif

/* Define to the equivalent of the C99 'restrict' keyword (needed because
   this header is also seen by the C++ Magick++ sources). */
#define restrict __restrict__

#endif /* defined(MAGICK_IMPLEMENTATION) */

#endif /* _MAGICK_MAGICK_CONFIG_H */

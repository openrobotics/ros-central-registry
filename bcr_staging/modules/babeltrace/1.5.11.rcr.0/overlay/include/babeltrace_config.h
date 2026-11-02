#ifndef BABELTRACE_CONFIG_H
#define BABELTRACE_CONFIG_H

#ifndef _GNU_SOURCE
#define _GNU_SOURCE 1
#endif

#define BABELTRACE_HAVE_FACCESSAT 1
#define BABELTRACE_HAVE_FMEMOPEN 1
#define BABELTRACE_HAVE_LIBUUID 1
#define BABELTRACE_HAVE_OPEN_MEMSTREAM 1
#define BABELTRACE_HAVE_POSIX_FALLOCATE 1

#define HAVE_ALARM 1
#define HAVE_ALLOCA 1
#define HAVE_ALLOCA_H 1
#define HAVE_ATEXIT 1
#define HAVE_DIRFD 1
#define HAVE_DLFCN_H 1
#define HAVE_DUP2 1
#define HAVE_FCNTL_H 1
#define HAVE_FLOAT_H 1
#define HAVE_FORK 1
#define HAVE_FTRUNCATE 1
#define HAVE_GETHOSTBYNAME 1
#define HAVE_GETHOSTNAME 1
#define HAVE_GETPAGESIZE 1
#define HAVE_GETTIMEOFDAY 1
#define HAVE_INTTYPES_H 1
#define HAVE_LIBINTL_H 1
#define HAVE_LIBPOPT 1
#define HAVE_LIMITS_H 1
#define HAVE_LOCALTIME_R 1
#define HAVE_MALLOC 1
#define HAVE_MALLOC_H 1
#define HAVE_MEMCHR 1
#define HAVE_MEMORY_H 1
#define HAVE_MEMSET 1
#define HAVE_MKDIR 1
#define HAVE_MKDTEMP 1
#define HAVE_MMAP 1
#define HAVE_MUNMAP 1
#define HAVE_NETDB_H 1
#define HAVE_NETINET_IN_H 1
#define HAVE_PTHREAD 1
#define HAVE_PTHREAD_PRIO_INHERIT 1
#define HAVE_REALLOC 1
#define HAVE_RMDIR 1
#define HAVE_SETENV 1
#define HAVE_SOCKET 1
#define HAVE_STDBOOL_H 1
#define HAVE_STDDEF_H 1
#define HAVE_STDINT_H 1
#define HAVE_STDLIB_H 1
#define HAVE_STRCHR 1
#define HAVE_STRDUP 1
#define HAVE_STRERROR 1
#define HAVE_STRINGS_H 1
#define HAVE_STRING_H 1
#define HAVE_STRNDUP 1
#define HAVE_STRNLEN 1
#define HAVE_STRRCHR 1
#define HAVE_STRTOUL 1
#define HAVE_STRTOULL 1
#define HAVE_SYS_PARAM_H 1
#define HAVE_SYS_SOCKET_H 1
#define HAVE_SYS_STAT_H 1
#define HAVE_SYS_TIME_H 1
#define HAVE_SYS_TYPES_H 1
#define HAVE_TZSET 1
#define HAVE_UNAME 1
#define HAVE_UNISTD_H 1
#define HAVE_UUID_GENERATE 1
#define HAVE_VFORK 1
#define HAVE_WORKING_FORK 1
#define HAVE_WORKING_VFORK 1
#define HAVE__BOOL 1
#define HAVE___ATTRIBUTE__ 1

#define PACKAGE "babeltrace"
#define PACKAGE_BUGREPORT "jeremie.galarneau@efficios.com"
#define PACKAGE_NAME "babeltrace"
#define PACKAGE_STRING "babeltrace 1.5.11"
#define PACKAGE_TARNAME "babeltrace"
#define PACKAGE_URL ""
#define PACKAGE_VERSION "1.5.11"
#define STDC_HEADERS 1
#define TIME_WITH_SYS_TIME 1
#define VERSION "1.5.11"

/*
 * When GLib is linked statically into _babeltrace.so, its unnumbered
 * __attribute__((constructor)) (glib_init_ctor) is placed after babeltrace's
 * own constructors in .init_array, causing g_quark_from_static_string() calls
 * in babeltrace constructors to fail before glib_init() runs. Running
 * glib_init() at priority 101 ensures GLib's quark table is initialized first.
 */
extern void glib_init(void);
static __attribute__((constructor(101), unused)) void bt_early_glib_init(void) {
    glib_init();
}

#endif /* BABELTRACE_CONFIG_H */

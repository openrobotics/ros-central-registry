#ifndef AVAHI_CONFIG_H
#define AVAHI_CONFIG_H
#define _GNU_SOURCE 1
#define PACKAGE "avahi"
#define PACKAGE_VERSION "0.8"
#define HAVE_DBUS 1
#define HAVE_DLOPEN 1
#define HAVE_PTHREAD 1
#ifndef __APPLE__
#define HAVE_STRCHRNUL 1
#define HAVE_SYS_PRCTL_H 1
#else
#undef _FORTIFY_SOURCE
#define _FORTIFY_SOURCE 0
#define HAVE_STRLCPY 1
#endif
#define HAVE_UNISTD_H 1
#define HAVE_STDINT_H 1
#define HAVE_STDLIB_H 1
#define HAVE_STRING_H 1
#define GETTEXT_PACKAGE "avahi"
#define HAVE_DBUS_CONNECTION_CLOSE 1
#define AVAHI_LOCALEDIR "/usr/share/locale"
#define DBUS_SYSTEM_BUS_DEFAULT_ADDRESS "unix:path=/var/run/dbus/system_bus_socket"
#endif

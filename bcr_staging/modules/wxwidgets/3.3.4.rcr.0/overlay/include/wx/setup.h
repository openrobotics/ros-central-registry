/* wx/setup.h for the wxQt port on Linux (glibc, LP64), rendered from
   upstream's build/cmake/setup.h.in with the option values that
   build/cmake/{options,init,setup}.cmake select for wxBUILD_TOOLKIT=qt
   and the dependencies available in this registry. */
/* This define (__WX_SETUP_H__) is used both to ensure setup.h is included
 * only once and to indicate that we are building using configure. */
#ifndef __WX_SETUP_H__
#define __WX_SETUP_H__

/* Deal with wxUSE_GUI first, before any toolkit definitions below. */
#ifndef wxUSE_GUI
    #ifdef __WXQT__
        #define wxUSE_GUI 1
    #else
        #define wxUSE_GUI 0
    #endif
#endif


/* never undefine inline or const keywords for C++ compilation */
#ifndef __cplusplus

/* Define to empty if the keyword does not work.  */
/* #undef const */

/* Define as __inline if that's what the C compiler calls it.  */
/* #undef inline */

#endif /* __cplusplus */

/* the installation location prefix from configure */
/* #undef wxINSTALL_PREFIX */

/* Define if ssize_t type is available.  */
#define HAVE_SSIZE_T 1

/* Define if you have the ANSI C header files.  */
#define STDC_HEADERS 1

/* Define this to get extra features from GNU libc. */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE 1
#endif

/* Define if your processor stores words with the most significant
   byte first (like Motorola and SPARC, unlike Intel and VAX).  */
#if defined(__BYTE_ORDER__) && __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__
#define WORDS_BIGENDIAN 1
#endif

/* Define this if your version of GTK+ is greater than 2.0 */
/* #undef __WXGTK20__ */

/* Define this if your version of GTK+ is greater than 2.10 */
/* #undef __WXGTK210__ */

/* Define this if your version of GTK+ is greater than 2.18 */
/* #undef __WXGTK218__ */

/* Define this if your version of GTK+ is greater than 2.20 */
/* #undef __WXGTK220__ */

/* Define this if your version of GTK+ is >= 3.0 */
/* #undef __WXGTK3__ */

/* Define this if your version of GTK+ is >= 3.90.0 */
/* #undef __WXGTK4__ */

/*
 * Define to 1 for Unix[-like] system
 */
#define wxUSE_UNIX 1

#define __UNIX__ 1

/* #undef __AIX__ */
/* #undef __BSD__ */
/* #undef __DARWIN__ */
/* #undef __EMX__ */
/* #undef __FREEBSD__ */
/* #undef __HPUX__ */
#define __LINUX__ 1
/* #undef __NETBSD__ */
/* #undef __OPENBSD__ */
/* #undef __OSF__ */
/* #undef __QNX__ */
/* #undef __SGI__ */
/* #undef __SOLARIS__ */
/* #undef __SUN__ */
/* #undef __SUNOS__ */
/* #undef __SVR4__ */
/* #undef __SYSV__ */
/* #undef __ULTRIX__ */
/* #undef __UNIXWARE__ */
/* #undef __VMS__ */

/* #undef __IA64__ */

/* NanoX (with wxX11) */
#define wxUSE_NANOX 0

/* Stupid hack; __WINDOWS__ clashes with wx/defs.h */
#ifndef __WINDOWS__
/* #undef __WINDOWS__ */
#endif

#ifndef __WIN32__
/* #undef __WIN32__ */
#endif
#ifndef __GNUWIN32__
/* #undef __GNUWIN32__ */
#endif
#ifndef STRICT
/* #undef STRICT */
#endif
#ifndef WINVER
/* #undef WINVER */
#endif

/* --- start common options --- */

#ifndef wxUSE_GUI
    #define wxUSE_GUI 1
#endif


#define WXWIN_COMPATIBILITY_3_0 0

#define WXWIN_COMPATIBILITY_3_2 1

#define wxDIALOG_UNIT_COMPATIBILITY 0

#define wxUSE_REPRODUCIBLE_BUILD 0


#define wxUSE_UNICODE_UTF8 0

#define wxUSE_UTF8_LOCALE_ONLY 0



#define wxUSE_ON_FATAL_EXCEPTION 1

#define wxUSE_STACKWALKER 1

#define wxUSE_DEBUGREPORT 1



#define wxUSE_EXCEPTIONS 1

#define wxUSE_EXTENDED_RTTI 0

#define wxUSE_LOG 1

#define wxUSE_LOGWINDOW 1

#define wxUSE_LOGGUI 1

#define wxUSE_LOG_DIALOG 1

#define wxUSE_CMDLINE_PARSER 1

#define wxUSE_THREADS 1

#define wxUSE_STREAMS 1

#define wxUSE_PRINTF_POS_PARAMS 1


#define wxUSE_STD_CONTAINERS 1

#define wxUSE_STD_IOSTREAM 1


#define wxUSE_UNSAFE_WXSTRING_CONV 1

#define wxUSE_STD_STRING_CONV_IN_WXSTRING 0


#define wxUSE_BASE64 1

#define wxUSE_CONSOLE_EVENTLOOP 1

#define wxUSE_FILE 1
#define wxUSE_FFILE 1

#define wxUSE_FSVOLUME 1

#define wxUSE_SECRETSTORE 0

#define wxUSE_SPELLCHECK 1

#define wxUSE_STDPATHS 1

#define wxUSE_TEXTBUFFER 1

#define wxUSE_TEXTFILE 1

#define wxUSE_INTL 1

#define wxUSE_XLOCALE 1

#define wxUSE_DATETIME 1

#define wxUSE_TIMER 1

#define wxUSE_STOPWATCH 1

#define wxUSE_FSWATCHER 1

#define wxUSE_CONFIG 1

#define wxUSE_CONFIG_NATIVE 1

#define wxUSE_DIALUP_MANAGER 1

#define wxUSE_DYNLIB_CLASS 1

#define wxUSE_DYNAMIC_LOADER 1

#define wxUSE_SOCKETS 1

#define wxUSE_IPV6 1

#define wxUSE_FILESYSTEM 1

#define wxUSE_FS_ZIP 1

#define wxUSE_FS_ARCHIVE 1

#define wxUSE_FS_INET 1

#define wxUSE_ARCHIVE_STREAMS 1

#define wxUSE_ZIPSTREAM 1

#define wxUSE_TARSTREAM 1

#define wxUSE_ZLIB 1

#define wxUSE_LIBLZMA 0

#define wxUSE_APPLE_IEEE 1

#define wxUSE_JOYSTICK 1

#define wxUSE_FONTENUM 1

#define wxUSE_FONTMAP 1

#define wxUSE_MIMETYPE 1

#define wxUSE_WEBREQUEST 0

#ifdef __APPLE__
#define wxUSE_WEBREQUEST_URLSESSION wxUSE_WEBREQUEST
#else
#define wxUSE_WEBREQUEST_URLSESSION 1
#endif

#define wxUSE_WEBREQUEST_CURL 0

#define wxUSE_PROTOCOL 1

#define wxUSE_PROTOCOL_FILE 1
#define wxUSE_PROTOCOL_FTP 1
#define wxUSE_PROTOCOL_HTTP 1

#define wxUSE_URL 1

#define wxUSE_URL_NATIVE 0

#define wxUSE_VARIANT 1

#define wxUSE_ANY 1

#define wxUSE_REGEX 1

#define wxUSE_SYSTEM_OPTIONS 1

#define wxUSE_SOUND 1

#define wxUSE_MEDIACTRL 1

#define wxUSE_XRC 1

#define wxUSE_XML 1

#define wxUSE_AUI 1

#define wxUSE_RIBBON 1

#define wxUSE_PROPGRID 1

#define wxUSE_STC 1

#define wxUSE_WEBVIEW 0

#define wxUSE_WEBVIEW_CHROMIUM 0

#ifdef __WXMSW__
#define wxUSE_WEBVIEW_IE 1
#else
#define wxUSE_WEBVIEW_IE 1
#endif

#define wxUSE_WEBVIEW_EDGE 1

#define wxUSE_WEBVIEW_EDGE_STATIC 0

#if (defined(__WXGTK__) && !defined(__WXGTK3__)) || defined(__WXOSX__)
#define wxUSE_WEBVIEW_WEBKIT 1
#else
#define wxUSE_WEBVIEW_WEBKIT 1
#endif

#if defined(__WXGTK3__)
#define wxUSE_WEBVIEW_WEBKIT2 0
#else
#define wxUSE_WEBVIEW_WEBKIT2 0
#endif

#define wxUSE_GRAPHICS_CONTEXT 1

#define wxUSE_CAIRO 0



#define wxUSE_CONTROLS 1

#define wxUSE_MARKUP 1

#define wxUSE_POPUPWIN 1

#define wxUSE_TIPWINDOW 1

#define wxUSE_ACTIVITYINDICATOR 1
#define wxUSE_ANIMATIONCTRL 1
#define wxUSE_BANNERWINDOW 1
#define wxUSE_BUTTON 1
#define wxUSE_BMPBUTTON 1
#define wxUSE_CALENDARCTRL 1
#define wxUSE_CHECKBOX 1
#define wxUSE_CHECKLISTBOX 1
#define wxUSE_CHOICE 1
#define wxUSE_COLLPANE 1
#define wxUSE_COLOURPICKERCTRL 1
#define wxUSE_COMBOBOX 1
#define wxUSE_COMMANDLINKBUTTON 1
#define wxUSE_DATAVIEWCTRL 1
#define wxUSE_DATEPICKCTRL 1
#define wxUSE_DIRPICKERCTRL 1
#define wxUSE_EDITABLELISTBOX 1
#define wxUSE_FILECTRL 1
#define wxUSE_FILEPICKERCTRL 1
#define wxUSE_FONTPICKERCTRL 1
#define wxUSE_GAUGE 1
#define wxUSE_HEADERCTRL 1
#define wxUSE_HYPERLINKCTRL 1
#define wxUSE_LISTBOX 1
#define wxUSE_LISTCTRL 1
#define wxUSE_RADIOBOX 1
#define wxUSE_RADIOBTN 1
#define wxUSE_RICHMSGDLG 1
#define wxUSE_SCROLLBAR 1
#define wxUSE_SEARCHCTRL 1
#define wxUSE_SLIDER 1
#define wxUSE_SPINBTN 1
#define wxUSE_SPINCTRL 1
#define wxUSE_STATBOX 1
#define wxUSE_STATLINE 1
#define wxUSE_STATTEXT 1
#define wxUSE_STATBMP 1
#define wxUSE_TEXTCTRL 1
#define wxUSE_TIMEPICKCTRL 1
#define wxUSE_TOGGLEBTN 1
#define wxUSE_TREECTRL 1
#define wxUSE_TREELISTCTRL 1

#define wxUSE_NATIVE_DATAVIEWCTRL 1

#define wxUSE_STATUSBAR 1

#define wxUSE_NATIVE_STATUSBAR 1

#define wxUSE_TOOLBAR 1
#define wxUSE_TOOLBAR_NATIVE 1

#define wxUSE_NOTEBOOK 1

#define wxUSE_LISTBOOK 1

#define wxUSE_CHOICEBOOK 1

#define wxUSE_TREEBOOK 1

#define wxUSE_TOOLBOOK 1

#define wxUSE_TASKBARICON 1

#define wxUSE_GRID 1

#define wxUSE_MINIFRAME 1

#define wxUSE_COMBOCTRL 1

#define wxUSE_ODCOMBOBOX 1

#define wxUSE_BITMAPCOMBOBOX 1

#define wxUSE_REARRANGECTRL 1

#define wxUSE_ADDREMOVECTRL 1


#define wxUSE_ACCEL 1

#define wxUSE_ARTPROVIDER_STD 1

#define wxUSE_ARTPROVIDER_TANGO 1

#define wxUSE_HOTKEY 0

#define wxUSE_CARET 1

#define wxUSE_DISPLAY 1

#define wxUSE_IMAGLIST 1

#define wxUSE_INFOBAR 1

#define wxUSE_MENUS 1

#define wxUSE_MENUBAR 1

#define wxUSE_NOTIFICATION_MESSAGE 1

#define wxUSE_PREFERENCES_EDITOR 1

#define wxUSE_PRIVATE_FONTS 1

#define wxUSE_RICHTOOLTIP 1

#define wxUSE_SASH 1

#define wxUSE_SPLITTER 1

#define wxUSE_TOOLTIPS 1

#define wxUSE_VALIDATORS 1

#ifdef __WXMSW__
#define wxUSE_AUTOID_MANAGEMENT 0
#else
#define wxUSE_AUTOID_MANAGEMENT 0
#endif


#define wxUSE_BUSYINFO 1

#define wxUSE_CHOICEDLG 1

#define wxUSE_COLOURDLG 1

#define wxUSE_DIRDLG 1

#define wxUSE_FILEDLG 1

#define wxUSE_FINDREPLDLG 1

#define wxUSE_FONTDLG 1

#define wxUSE_MSGDLG 1

#define wxUSE_PROGRESSDLG 1

#define wxUSE_NATIVE_PROGRESSDLG 1

#define wxUSE_STARTUP_TIPS 1

#define wxUSE_TEXTDLG 1

#define wxUSE_NUMBERDLG 1

#define wxUSE_CREDENTIALDLG 1

#define wxUSE_SPLASH 1

#define wxUSE_WIZARDDLG 1

#define wxUSE_ABOUTDLG 1

#define wxUSE_FILE_HISTORY 1


#define wxUSE_METAFILE 0
#define wxUSE_ENH_METAFILE 0
#define wxUSE_WIN_METAFILES_ALWAYS 0


#define wxUSE_MDI 1

#define wxUSE_DOC_VIEW_ARCHITECTURE 1

#define wxUSE_MDI_ARCHITECTURE 1

#define wxUSE_PRINTING_ARCHITECTURE 1

#define wxUSE_HTML 1

#define wxUSE_GLCANVAS 1

#define wxUSE_RICHTEXT 1


#define wxUSE_CLIPBOARD 1

#define wxUSE_DATAOBJ 1

#define wxUSE_DRAG_AND_DROP 1

#ifdef __WXMSW__
#define wxUSE_ACCESSIBILITY 1
#else
#define wxUSE_ACCESSIBILITY 0
#endif


#define wxUSE_SNGLINST_CHECKER 1

#define wxUSE_DRAGIMAGE 1

#define wxUSE_IPC 1

#define wxUSE_HELP 1


#define wxUSE_MS_HTML_HELP 1


#define wxUSE_WXHTML_HELP 1

#define wxUSE_CONSTRAINTS 1


#define wxUSE_SPLINES 1


#define wxUSE_MOUSEWHEEL 1


#define wxUSE_UIACTIONSIMULATOR 1


#define wxUSE_POSTSCRIPT 1

#define wxUSE_AFM_FOR_POSTSCRIPT 1

#define wxUSE_SVG 1

#define wxUSE_DC_TRANSFORM_MATRIX 1


#define wxUSE_IMAGE 1

#define wxUSE_LIBPNG 1

#define wxUSE_LIBJPEG 1

#define wxUSE_LIBTIFF 1

#define wxUSE_NANOSVG 1

#define wxUSE_NANOSVG_EXTERNAL 0

#define wxUSE_LUNASVG 0

#define wxUSE_TGA 1

#define wxUSE_GIF 1

#define wxUSE_PNM 1

#define wxUSE_PCX 1

#define wxUSE_IFF 1

#define wxUSE_XPM 1

#define wxUSE_ICO_CUR 1

#define wxUSE_PALETTE 1

#define wxUSE_LIBWEBP 1


#define wxUSE_ALL_THEMES 0

#define wxUSE_THEME_GTK 0
#define wxUSE_THEME_METAL 0
#define wxUSE_THEME_MONO 0
#define wxUSE_THEME_WIN32 0

/* --- end common options --- */

/*
 * Unix-specific options
 */
#define wxUSE_SELECT_DISPATCHER 1
#define wxUSE_EPOLL_DISPATCHER 1

/*
   Use debug version of CEF in wxWebViewChromium.
 */
/* #undef wxHAVE_CEF_DEBUG */

/*
   Use GStreamer for Unix.

   Default is 0 as this requires a lot of dependencies which might not be
   available.

   Recommended setting: 1 (wxMediaCtrl won't work by default without it).
 */
#define wxUSE_GSTREAMER 0

#define wxUSE_GSTREAMER_PLAYER 0

/**
    Use wayland-client library.

    This is needed by any Wayland-specific code in wxGTK implementation.

    Define if wayland-client is available.
 */
/* #undef wxHAVE_WAYLAND_CLIENT */

/*
    Use Wayland session-management protocol.

    This is defined if GTK is new enough to support it.
 */
/* #undef wxHAVE_WAYLAND_SESSION_MANAGEMENT */

/*
    Use Wayland xdg-toplevel-drag protocol.

    This is defined if GTK is new enough to support it.
 */
/* #undef wxHAVE_WAYLAND_TOPLEVEL_DRAG */

/*
   Use XTest extension to implement wxUIActionSimulator?

   Default is 1, it is set to 0 if the necessary headers/libraries are not
   found by configure.

   Recommended setting: 1, wxUIActionSimulator won't work in wxGTK3 without it.
 */
#define wxUSE_XTEST 0

/* --- start MSW options --- */


#define wxUSE_GRAPHICS_GDIPLUS wxUSE_GRAPHICS_CONTEXT

#if defined(_MSC_VER)
    #define wxUSE_GRAPHICS_DIRECT2D wxUSE_GRAPHICS_CONTEXT
#else
    #define wxUSE_GRAPHICS_DIRECT2D 1
#endif

#define wxUSE_WEBREQUEST_WINHTTP 1


#define wxUSE_OLE 1

#define wxUSE_OLE_AUTOMATION 0

#define wxUSE_ACTIVEX 1

#if defined(_MSC_VER)
    #define wxUSE_WINRT 0
#else
    #define wxUSE_WINRT 0
#endif

#define wxUSE_DC_CACHEING 1

#define wxUSE_WXDIB 1

#define wxUSE_POSTSCRIPT_ARCHITECTURE_IN_MSW 1

#define wxUSE_REGKEY 1

#define wxUSE_RICHEDIT 1

#define wxUSE_RICHEDIT2 1

#define wxUSE_OWNER_DRAWN 1

#define wxUSE_TASKBARICON_BALLOONS 1

#define wxUSE_TASKBARBUTTON 1

#define wxUSE_INKEDIT 0

#define wxUSE_INICONF 1

#define wxUSE_WINSOCK2 0


#define wxUSE_DATEPICKCTRL_GENERIC 0

#define wxUSE_TIMEPICKCTRL_GENERIC 0


#if defined(__VISUALC__) || defined(__MINGW64_TOOLCHAIN__)
    #define wxUSE_DBGHELP 1
#else
    #define wxUSE_DBGHELP 1
#endif

#define wxUSE_CRASHREPORT 1
/* --- end MSW options --- */

/*
 * Define if your compiler has C99 va_copy
 */
#define HAVE_VA_COPY 1

/*
 * Define if va_list type is an array
 */
/* #undef VA_LIST_IS_ARRAY */

/*
 * Define if the compiler supports simple visibility declarations.
 */
#define HAVE_VISIBILITY 1

/*
 * Define if the compiler supports GCC's atomic memory access builtins
 */
#define HAVE_GCC_ATOMIC_BUILTINS 1

/*
 * Define if compiler's visibility support in libstdc++ is broken
 */
/* #undef HAVE_BROKEN_LIBSTDCXX_VISIBILITY */

/*
 * Use SDL for audio (Unix)
 */
#define wxUSE_LIBSDL 0

/*
 * Use SDL 3.x (rather than SDL 2.x or 1.x) for the SDL audio backend
 */
#define wxUSE_LIBSDL3 0

/*
 * Compile sound backends as plugins
 */
#define wxUSE_PLUGINS 0

/*
 * Use GTK print for printing under GTK+ 2.10+
 */
#define wxUSE_GTKPRINT 0
/*
 * Use GNOME VFS for MIME types
 */
#define wxUSE_LIBGNOMEVFS 0
/*
 * Use AppIndicator for wxTaskBarIcon (required for Wayland).
 */
#define wxUSE_APPINDICATOR 0
/*
 * Use libnotify library.
 */
#define wxUSE_LIBNOTIFY 0
/*
 * Use libnotify 0.7+ API.
 */
#define wxUSE_LIBNOTIFY_0_7 0
/*
 * Use libXpm
 */
#define wxHAVE_LIB_XPM 0
/*
 * Define if you have pthread_cleanup_push/pop()
 */
#define wxHAVE_PTHREAD_CLEANUP 1
/*
 * Define if large (64 bit file offsets) files are supported.
 */
#define HAVE_LARGEFILE_SUPPORT 1

/*
 * Use OpenGL
 */
#define wxUSE_OPENGL 1

/*
 * Use MS HTML Help via libmspack (Unix)
 */
#define wxUSE_LIBMSPACK 0

/*
 * Matthews garbage collection (used for MrEd?)
 */
#define WXGARBAGE_COLLECTION_ON 0

/*
 * wxWebKitCtrl
 */
#define wxUSE_WEBKIT 0

/*
 * use the session manager to detect KDE/GNOME
 */
#define wxUSE_DETECT_SM 0


/* define with the name of timezone variable */
#define WX_TIMEZONE timezone

/* The type of 3rd argument to getsockname() - usually size_t or int */
#define WX_SOCKLEN_T socklen_t

/* The type of 5th argument to getsockopt() - usually size_t or int */
#define SOCKOPTLEN_T socklen_t

/* The type of statvfs(2) argument */
#define WX_STATFS_T struct statvfs

/* gettimeofday() usually takes 2 arguments, but some really old systems might
 * have only one, in which case define WX_GETTIMEOFDAY_NO_TZ */
/* #undef WX_GETTIMEOFDAY_NO_TZ */

/* struct tm doesn't always have the tm_gmtoff field, define this if it does */
#define WX_GMTOFF_IN_TM 1

/* check if nl_langinfo() can be called with argument _NL_TIME_FIRST_WEEKDAY */
#define HAVE_NL_TIME_FIRST_WEEKDAY 1

/* Define if you have poll(2) function */
#define HAVE_POLL 1

/* Define if you have pw_gecos field in struct passwd */
#define HAVE_PW_GECOS 1

/* Define if you have __cxa_demangle() in <cxxabi.h> */
#define HAVE_CXA_DEMANGLE 1

/* Define if you have dlopen() */
#define HAVE_DLOPEN 1

/* Define if you have gettimeofday() */
#define HAVE_GETTIMEOFDAY 1

/* Define if fsync() is available */
#define HAVE_FSYNC 1

/* Define if you have ftime() */
#define HAVE_FTIME 1

/* Define if you have nanosleep() */
#define HAVE_NANOSLEEP 1

/* Define if you have sched_yield */
#define HAVE_SCHED_YIELD 1

/* Define if you have pthread_mutexattr_t and functions to work with it */
#define HAVE_PTHREAD_MUTEXATTR_T 1

/* Define if you have pthread_mutexattr_settype() declaration */
#define HAVE_PTHREAD_MUTEXATTR_SETTYPE_DECL 1

/* Define if you have PTHREAD_RECURSIVE_MUTEX_INITIALIZER_NP */
#define HAVE_PTHREAD_RECURSIVE_MUTEX_INITIALIZER 1

/* Define if you have pthread_cancel */
#define HAVE_PTHREAD_CANCEL 1

/* Define if you have pthread_mutex_timedlock */
#define HAVE_PTHREAD_MUTEX_TIMEDLOCK 1

/* Define if you have pthread_attr_setstacksize */
#define HAVE_PTHREAD_ATTR_SETSTACKSIZE 1

/* Define if you have snprintf() */
#define HAVE_SNPRINTF 1

/* Define if you have a snprintf() which supports positional arguments
   (defined in the unix98 standard) */
#define HAVE_UNIX98_PRINTF 1

/* define if you have statfs function */
#define HAVE_STATFS 1

/* define if you have statfs prototype */
#define HAVE_STATFS_DECL 1

/* define if you have statvfs function */
#define HAVE_STATVFS 1

/* Define if you have all functions to set thread priority */
#define HAVE_THREAD_PRIORITY_FUNCTIONS 1

/* Define if you have vsnprintf() */
#define HAVE_VSNPRINTF 1

/* Define if you have a _broken_ vsnprintf() declaration in the header,
 * with 'char*' for the 3rd parameter instead of 'const char*' */
/* #undef HAVE_BROKEN_VSNPRINTF_DECL */

/* Define if you have a _broken_ vsscanf() declaration in the header,
 * with 'char*' for the 1st parameter instead of 'const char*' */
/* #undef HAVE_BROKEN_VSSCANF_DECL */

/* Define if you have vsscanf() */
#define HAVE_VSSCANF 1

/* Define if you have usleep() */
#define HAVE_USLEEP 1

/* Define if you have wcscasecmp() function  */
#define HAVE_WCSCASECMP 1

/* Define if you have wcsncasecmp() function  */
#define HAVE_WCSNCASECMP 1

/* Define if you have wcslen function  */
#define HAVE_WCSLEN 1

/* Define if you have wcsdup function  */
#define HAVE_WCSDUP 1

/* Define if you have wcsftime() function  */
#define HAVE_WCSFTIME 1

/* Define if you have strnlen() function */
#define HAVE_STRNLEN 1

/* Define if you have wcsnlen() function */
#define HAVE_WCSNLEN 1

/* The number of bytes in a wchar_t.  */
#define SIZEOF_WCHAR_T __SIZEOF_WCHAR_T__

/* The number of bytes in a int.  */
#define SIZEOF_INT __SIZEOF_INT__

/* The number of bytes in a pointer.  */
#define SIZEOF_VOID_P __SIZEOF_POINTER__

/* The number of bytes in a long.  */
#define SIZEOF_LONG __SIZEOF_LONG__

/* The number of bytes in a long long.  */
#define SIZEOF_LONG_LONG __SIZEOF_LONG_LONG__

/* The number of bytes in a short.  */
#define SIZEOF_SHORT __SIZEOF_SHORT__

/* The number of bytes in a size_t.  */
#define SIZEOF_SIZE_T __SIZEOF_SIZE_T__

/* Define if size_t on your machine is the same type as unsigned int. */
/* #undef wxSIZE_T_IS_UINT */

/* Define if size_t on your machine is the same type as unsigned long. */
#define wxSIZE_T_IS_ULONG 1

/* Define if you have the dladdr function.  */
#define HAVE_DLADDR 1

/* Define if you have the dl_iterate_phdr function.  */
#define HAVE_DL_ITERATE_PHDR 1

/* Define if you have Posix fnctl() function. */
#define HAVE_FCNTL 1

/* Define if you have BSD flock() function. */
#define HAVE_FLOCK 1

/* Define if you have getaddrinfo function. */
#define HAVE_GETADDRINFO 1

/* Define if you have a gethostbyname_r function taking 6 arguments. */
#define HAVE_FUNC_GETHOSTBYNAME_R_6 1

/* Define if you have a gethostbyname_r function taking 5 arguments. */
/* #undef HAVE_FUNC_GETHOSTBYNAME_R_5 */

/* Define if you have the gethostname function.  */
#define HAVE_GETHOSTNAME 1

/* Define if you have a getservbyname_r function taking 6 arguments. */
#define HAVE_FUNC_GETSERVBYNAME_R_6 1

/* Define if you have a getservbyname_r function taking 5 arguments. */
/* #undef HAVE_FUNC_GETSERVBYNAME_R_5 */

/* Define if you have the gmtime_r function.  */
#define HAVE_GMTIME_R 1

/* Define if you have the inet_addr function.  */
#define HAVE_INET_ADDR 1

/* Define if you have the inet_aton function.  */
#define HAVE_INET_ATON 1

/* Define if you have the localtime_r function.  */
#define HAVE_LOCALTIME_R 1

/* Define if you have the mktemp function.  */
/* #undef HAVE_MKTEMP */

/* Define if you have the mkstemp function.  */
#define HAVE_MKSTEMP 1

/* Define if you have the putenv function.  */
#define HAVE_PUTENV 1

/* Define if you have the setenv function.  */
#define HAVE_SETENV 1

/* Define if you have strtok_r function. */
#define HAVE_STRTOK_R 1

/* Define if you have thr_setconcurrency function */
/* #undef HAVE_THR_SETCONCURRENCY */

/* Define if you have pthread_setconcurrency function */
#define HAVE_PTHREAD_SETCONCURRENCY 1

/* Define if you have the uname function.  */
#define HAVE_UNAME 1

/* Define if you have the unsetenv function.  */
#define HAVE_UNSETENV 1

/* Define if you have the <X11/XKBlib.h> header file.  */
/* #undef HAVE_X11_XKBLIB_H */

/* Define if you have the <X11/extensions/xf86vmode.h> header file.  */
/* #undef HAVE_X11_EXTENSIONS_XF86VMODE_H */

/* Define if you have the <sched.h> header file.  */
#define HAVE_SCHED_H 1

/* Define if you have the <unistd.h> header file.  */
#define HAVE_UNISTD_H 1

/* Define if you have the <iconv.h> header file and iconv() symbol.  */
#define HAVE_ICONV 1

/* Define as "const" if the declaration of iconv() needs const.  */
#define ICONV_CONST

/* Define if you have the <langinfo.h> header file.  */
#define HAVE_LANGINFO_H 1

/* Define if you have the <sys/soundcard.h> header file. */
#define HAVE_SYS_SOUNDCARD_H 1

/* Define if you have wcsrtombs() function */
#define HAVE_WCSRTOMBS 1

/* Define this if you have fputws() */
#define HAVE_FPUTWS 1

/* Define this if you have wprintf() and related functions */
#define HAVE_WPRINTF 1

/* Define this if you have vswprintf() and related functions */
#define HAVE_VSWPRINTF 1

/* Define this if you have _vsnwprintf */
/* #undef HAVE__VSNWPRINTF */

/* vswscanf() */
#define HAVE_VSWSCANF 1

/* Define if fseeko and ftello are available.  */
#define HAVE_FSEEKO 1

/* Define this if you are using gtk and gdk contains support for X11R6 XIM */
/* #undef HAVE_XIM */

/* Define this if you have X11/extensions/shape.h */
/* #undef HAVE_XSHAPE */

/* Define this if you have type SPBCDATA */
/* #undef HAVE_SPBCDATA */

/* Define if you have pango_font_family_is_monospace() (Pango >= 1.3.3) */
/* #undef HAVE_PANGO_FONT_FAMILY_IS_MONOSPACE */

/* Define if you have Pango xft support */
/* #undef HAVE_PANGO_XFT */

/* Define if you have the <sys/select.h> header file.  */
#define HAVE_SYS_SELECT_H 1

/* Define if you have abi::__forced_unwind in your <cxxabi.h>. */
/* #undef HAVE_ABI_FORCEDUNWIND */

/* Define if fdopen is available.  */
#define HAVE_FDOPEN 1

/* Define if sysconf is available. */
#define HAVE_SYSCONF 1

/* Define if getpwuid_r is available. */
#define HAVE_GETPWUID_R 1

/* Define if getgrgid_r is available. */
#define HAVE_GETGRGID_R 1

/* Define if setpriority() is available. */
#define HAVE_SETPRIORITY 1

/* Define if xkbcommon is available */
/* #undef HAVE_XKBCOMMON */

/* Define if xlocale.h header file exists. */
/* #undef HAVE_XLOCALE_H */

/* Define if locale_t is available */
#define HAVE_LOCALE_T 1

/* Define if you have EGL support */
/* #undef wxHAS_EGL */

/* Define if you have GLX support */
/* #undef wxHAS_GLX */

/* Define if you have inotify_xxx() functions. */
#define wxHAS_INOTIFY 1

/* Define if you have kqueu_xxx() functions. */
/* #undef wxHAS_KQUEUE */

/* -------------------------------------------------------------------------
   Win32 adjustments section
   ------------------------------------------------------------------------- */

#ifdef __WIN32__

/* When using an external jpeg library and the Windows headers already define
 * boolean, define to the type used by the jpeg library for boolean.  */
/* #undef wxHACK_BOOLEAN */

#endif /* __WIN32__ */

/* --------------------------------------------------------*
 *  This stuff is static, it doesn't get modified directly
 *  by configure.
*/

/*
   define some constants identifying wxWindows version in more details than
   just the version number
 */

/* wxLogChain class available */
#define wxHAS_LOG_CHAIN

/* define this when wxDC::Blit() respects SetDeviceOrigin() in wxGTK */
/* #undef wxHAS_WORKING_GTK_DC_BLIT */

#endif /* __WX_SETUP_H__ */


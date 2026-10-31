#ifndef XLINK_EXPORT_H
#define XLINK_EXPORT_H

#ifdef XLINK_STATIC_DEFINE
#  define XLINK_EXPORT
#  define XLINK_NO_EXPORT
#else
#  ifndef XLINK_EXPORT
#    ifdef _WIN32
#      ifdef XLink_EXPORTS
#        define XLINK_EXPORT __declspec(dllexport)
#      else
#        define XLINK_EXPORT __declspec(dllimport)
#      endif
#    else
#      define XLINK_EXPORT __attribute__((visibility("default")))
#    endif
#  endif
#  ifndef XLINK_NO_EXPORT
#    ifdef _WIN32
#      define XLINK_NO_EXPORT
#    else
#      define XLINK_NO_EXPORT __attribute__((visibility("hidden")))
#    endif
#  endif
#endif

#ifndef XLINK_DEPRECATED
#  ifdef _WIN32
#    define XLINK_DEPRECATED __declspec(deprecated)
#  else
#    define XLINK_DEPRECATED __attribute__((__deprecated__))
#  endif
#endif

#ifndef XLINK_DEPRECATED_EXPORT
#  define XLINK_DEPRECATED_EXPORT XLINK_EXPORT XLINK_DEPRECATED
#endif

#ifndef XLINK_DEPRECATED_NO_EXPORT
#  define XLINK_DEPRECATED_NO_EXPORT XLINK_NO_EXPORT XLINK_DEPRECATED
#endif

#endif /* XLINK_EXPORT_H */

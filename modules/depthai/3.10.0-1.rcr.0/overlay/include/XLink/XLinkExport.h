
#ifndef XLINK_EXPORT_H
#define XLINK_EXPORT_H

#ifdef XLINK_STATIC_DEFINE
#  define XLINK_EXPORT
#  define XLINK_NO_EXPORT
#else
#  ifndef XLINK_EXPORT
#    ifdef XLink_EXPORTS
        /* We are building this library */
#      define XLINK_EXPORT 
#    else
        /* We are using this library */
#      define XLINK_EXPORT 
#    endif
#  endif

#  ifndef XLINK_NO_EXPORT
#    define XLINK_NO_EXPORT 
#  endif
#endif

#ifndef XLINK_DEPRECATED
#  define XLINK_DEPRECATED __attribute__ ((__deprecated__))
#endif

#ifndef XLINK_DEPRECATED_EXPORT
#  define XLINK_DEPRECATED_EXPORT XLINK_EXPORT XLINK_DEPRECATED
#endif

#ifndef XLINK_DEPRECATED_NO_EXPORT
#  define XLINK_DEPRECATED_NO_EXPORT XLINK_NO_EXPORT XLINK_DEPRECATED
#endif

/* NOLINTNEXTLINE(readability-avoid-unconditional-preprocessor-if) */
#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef XLINK_NO_DEPRECATED
#    define XLINK_NO_DEPRECATED
#  endif
#endif

#endif /* XLINK_EXPORT_H */

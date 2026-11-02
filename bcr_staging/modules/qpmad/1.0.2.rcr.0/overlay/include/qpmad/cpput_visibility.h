/**
    @file
    @author  Alexander Sherikov

    @copyright 2019 Alexander Sherikov, Licensed under the Apache License, Version 2.0.
    (see @ref LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

    @brief Visibility defines, e.g., https://gcc.gnu.org/wiki/Visibility
*/

#pragma once

#ifndef H_QPMAD_UTILS_VISIBILITY
#    define H_QPMAD_UTILS_VISIBILITY

#    if defined _WIN32 || defined __CYGWIN__
#        define QPMAD_UTILS_LIB_IMPORT __declspec(dllimport)
#        define QPMAD_UTILS_LIB_EXPORT __declspec(dllexport)
#        define QPMAD_UTILS_LIB_LOCAL
#    else
#        if __GNUC__ >= 4
#            define QPMAD_UTILS_LIB_IMPORT __attribute__((visibility("default")))
#            define QPMAD_UTILS_LIB_EXPORT __attribute__((visibility("default")))
#            define QPMAD_UTILS_LIB_LOCAL __attribute__((visibility("hidden")))
#        else
#            define QPMAD_UTILS_LIB_IMPORT
#            define QPMAD_UTILS_LIB_EXPORT
#            define QPMAD_UTILS_LIB_LOCAL
#        endif
#    endif


#    ifdef QPMAD_UTILS_COMPILE_SHARED_LIB
// compiled as a shared library (the default)
#        define QPMAD_UTILS_LOCAL QPMAD_UTILS_LIB_LOCAL

#        ifdef QPMAD_UTILS_IMPORT_LIB
// this apparently makes sense only in WIN
#            define QPMAD_UTILS_API QPMAD_UTILS_LIB_IMPORT
#        else
#            define QPMAD_UTILS_API QPMAD_UTILS_LIB_EXPORT
#        endif
#    else
// compiled as a static library
#        define QPMAD_UTILS_API
#        define QPMAD_UTILS_LOCAL
#    endif

#endif

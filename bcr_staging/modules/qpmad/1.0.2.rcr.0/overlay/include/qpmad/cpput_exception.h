/**
    @file
    @author  Alexander Sherikov

    @copyright 2019 Alexander Sherikov, Licensed under the Apache License, Version 2.0.
    (see @ref LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

    @brief Throw & assert macro
*/

#ifndef H_QPMAD_UTILS_EXCEPTION
#define H_QPMAD_UTILS_EXCEPTION

#include <string>
#include <stdexcept>

#define QPMAD_UTILS_THROW_EXCEPTION(exception_type, message) throw exception_type((message))

#ifdef CMAKEUT_COMPILER_SUPPORTS_FUNC_
#    define QPMAD_UTILS_THROW(s) QPMAD_UTILS_THROW_EXCEPTION(std::runtime_error, (std::string("In ") + __func__ + "() // " + (s)))
#else  //
#    ifdef CMAKEUT_COMPILER_SUPPORTS_FUNCTION_
#        define QPMAD_UTILS_THROW(s)                                                                                         \
            QPMAD_UTILS_THROW_EXCEPTION(std::runtime_error, (std::string("In ") + __FUNCTION__ + "() // " + (s)))
#    else  //
#        define QPMAD_UTILS_THROW(s) QPMAD_UTILS_THROW_EXCEPTION(std::runtime_error, (s))
#    endif  //
#endif      //


#define QPMAD_UTILS_PERSISTENT_ASSERT(condition, message)                                                                    \
    if (!(condition))                                                                                                  \
    {                                                                                                                  \
        QPMAD_UTILS_THROW(message);                                                                                          \
    };

#ifdef DNDEBUG
#    define QPMAD_UTILS_ASSERT(condition, message)
#else
#    define QPMAD_UTILS_ASSERT(condition, message) QPMAD_UTILS_PERSISTENT_ASSERT(condition, message)
#endif

#endif

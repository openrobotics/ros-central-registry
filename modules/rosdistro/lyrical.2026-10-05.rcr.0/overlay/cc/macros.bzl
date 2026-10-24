# Copyright 2026 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

def ros_local_defines(name = None):
    """Common local defines for ROS nodes"""
    package_name = name or native.module_name()
    return [
        "ROS_PACKAGE_NAME=\\\"{}\\\"".format(package_name),
        "DEFAULT_RMW_IMPLEMENTATION=\"rmw_fastrtps_cpp\"",
        # Ament's visibility_control.h convention gates dllexport/dllimport
        # on <PACKAGE>_BUILDING_DLL: defined while compiling the library's
        # own sources (so its public API resolves to dllexport), absent for
        # everyone else who merely includes its headers (dllimport). This is
        # a no-op on non-Windows platforms, where that macro is never
        # consulted. local_defines (unlike defines) isn't propagated to
        # consumers, so this correctly only affects this target's own TUs.
        "{}_BUILDING_DLL".format(package_name.upper()),
        # A sizeable minority of packages (rcpputils, rcutils, class_loader,
        # ...) predate the _BUILDING_DLL convention and gate their visibility
        # macro on <PACKAGE>_BUILDING_LIBRARY instead. Define that spelling too
        # so their public API (including class vtables) resolves to dllexport
        # when building the library; the unused spelling is harmless.
        "{}_BUILDING_LIBRARY".format(package_name.upper()),
    ]

def ros_exports_header(name, out, library = None, base_name = None, **kwargs):
    """Create an exports header for a ros package"""
    if not library:
        library = native.module_name()
    library = library.upper()
    base = (base_name or library).upper()

    extra_deprecated = ""
    if base != library:
        extra_deprecated = """
#ifndef {0}_DEPRECATED
#  define {0}_DEPRECATED __attribute__ ((__deprecated__))
#endif

#ifndef {0}_DEPRECATED_EXPORT
#  define {0}_DEPRECATED_EXPORT {1}_EXPORT {0}_DEPRECATED
#endif

#ifndef {0}_DEPRECATED_NO_EXPORT
#  define {0}_DEPRECATED_NO_EXPORT {1}_NO_EXPORT {0}_DEPRECATED
#endif
""".format(base, library)

    content = """
#ifndef {0}_EXPORT_H
#define {0}_EXPORT_H

#ifdef {0}_STATIC_DEFINE
#  define {0}_EXPORT
#  define {0}_NO_EXPORT
#else
#  ifndef {0}_EXPORT
#    ifdef {0}_EXPORTS
        /* We are building this library */
#      define {0}_EXPORT __attribute__((visibility("default")))
#    else
        /* We are using this library */
#      define {0}_EXPORT __attribute__((visibility("default")))
#    endif
#  endif

#  ifndef {0}_NO_EXPORT
#    define {0}_NO_EXPORT __attribute__((visibility("hidden")))
#  endif
#endif

#ifndef {0}_DEPRECATED
#  define {0}_DEPRECATED __attribute__ ((__deprecated__))
#endif

#ifndef {0}_DEPRECATED_EXPORT
#  define {0}_DEPRECATED_EXPORT {0}_EXPORT {0}_DEPRECATED
#endif

#ifndef {0}_DEPRECATED_NO_EXPORT
#  define {0}_DEPRECATED_NO_EXPORT {0}_NO_EXPORT {0}_DEPRECATED
#endif
{1}
#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef {0}_NO_DEPRECATED
#    define {0}_NO_DEPRECATED
#  endif
#endif

#endif /* {0}_EXPORT_H */
""".format(library, extra_deprecated)

    native.genrule(
        name = name,
        outs = [out],
        cmd = "echo '{}' > $@".format(content),
        **kwargs
    )

def ros_version_header(name, out, package_xml = "package.xml", **kwargs):
    """Create a version header from package.xml matching ament_generate_version_header."""
    native.genrule(
        name = name,
        srcs = [package_xml],
        outs = [out],
        cmd = """python3 -c '
import sys, xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
pkg = root.find("name").text.strip().upper()
ver = root.find("version").text.strip()
parts = (ver.split("-")[0].split(".") + ["0", "0", "0"])[:3]
maj, min_, pat = [int(x) for x in parts]
sys.stdout.write(f\"\"\"// Copyright 2015 Open Source Robotics Foundation, Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#ifndef {pkg}__VERSION_H_
#define {pkg}__VERSION_H_

/// \\\\def {pkg}_VERSION_MAJOR
/// Defines {pkg} major version number
#define {pkg}_VERSION_MAJOR ({maj})

/// \\\\def {pkg}_VERSION_MINOR
/// Defines {pkg} minor version number
#define {pkg}_VERSION_MINOR ({min_})

/// \\\\def {pkg}_VERSION_PATCH
/// Defines {pkg} version patch number
#define {pkg}_VERSION_PATCH ({pat})

/// \\\\def {pkg}_VERSION_STR
/// Defines {pkg} version string
#define {pkg}_VERSION_STR "{ver}"

/// \\\\def {pkg}_VERSION_GTE
/// Defines a macro to check whether the version of {pkg} is greater than or equal to
/// the given version triple.
#define {pkg}_VERSION_GTE(major, minor, patch) ( \\\\
     (major < {pkg}_VERSION_MAJOR) ? true \\\\
     : ((major > {pkg}_VERSION_MAJOR) ? false \\\\
     : ((minor < {pkg}_VERSION_MINOR) ? true \\\\
     : ((minor > {pkg}_VERSION_MINOR) ? false \\\\
     : ((patch < {pkg}_VERSION_PATCH) ? true \\\\
     : ((patch > {pkg}_VERSION_PATCH) ? false \\\\
     : true))))))

#endif  // {pkg}__VERSION_H_
\"\"\")
' $(location """ + package_xml + """) > $@""",
        **kwargs
    )

def ros_jrl_headers(name, outs, package_xml = "package.xml", **kwargs):
    """Generate jrl-cmakemodules config/deprecated/warning headers from package.xml."""
    native.genrule(
        name = name,
        srcs = [package_xml],
        outs = outs,
        cmd = """python3 -c '
import os, sys, xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
pkg = root.find("name").text.strip()
U = pkg.upper()
ver = root.find("version").text.strip().split("-")[0]
parts = (ver.split(".") + ["0", "0", "0"])[:3]
maj, min_, pat = [int(x) for x in parts]
CONFIG = f\"\"\"/*
 * This file has been automatically generated by the jrl-cmakemodules.
 * Please see https://github.com/jrl-umi3218/jrl-cmakemodules/blob/master/config.hh.cmake for details.
*/

#ifndef {U}_CONFIG_HH
# define {U}_CONFIG_HH

// Package version (header).
# define {U}_VERSION_UNKNOWN_TAG 0 // Used to mention that the current version is unknown.
# define {U}_VERSION "{ver}"
# define {U}_MAJOR_VERSION {maj}
# define {U}_MINOR_VERSION {min_}
# define {U}_PATCH_VERSION {pat}

#define {U}_VERSION_AT_LEAST(major, minor, patch) ({U}_MAJOR_VERSION>major || ({U}_MAJOR_VERSION>=major && \\\\
                                                             ({U}_MINOR_VERSION>minor || ({U}_MINOR_VERSION>=minor && \\\\
                                                                                                     {U}_PATCH_VERSION>=patch))))

#define {U}_VERSION_AT_MOST(major, minor, patch) ({U}_MAJOR_VERSION<major || ({U}_MAJOR_VERSION<=major && \\\\
                                                            ({U}_MINOR_VERSION<minor || ({U}_MINOR_VERSION>=minor && \\\\
                                                                                                     {U}_PATCH_VERSION<=patch))))

# if defined _WIN32 || defined __CYGWIN__
#  define {U}_DLLIMPORT __declspec(dllimport)
#  define {U}_DLLEXPORT __declspec(dllexport)
#  define {U}_DLLLOCAL
#  define {U}_EXPLICIT_INSTANTIATION_DECLARATION_DLLIMPORT __declspec(dllimport)
#  define {U}_EXPLICIT_INSTANTIATION_DECLARATION_DLLEXPORT
#  define {U}_EXPLICIT_INSTANTIATION_DEFINITION_DLLIMPORT __declspec(dllimport)
#  define {U}_EXPLICIT_INSTANTIATION_DEFINITION_DLLEXPORT __declspec(dllexport)
# else
#  if __GNUC__ >= 4
#   define {U}_DLLIMPORT __attribute__ ((visibility("default")))
#   define {U}_DLLEXPORT __attribute__ ((visibility("default")))
#   define {U}_DLLLOCAL  __attribute__ ((visibility("hidden")))
#   define {U}_EXPLICIT_INSTANTIATION_DECLARATION_DLLIMPORT __attribute__ ((visibility("default")))
#   define {U}_EXPLICIT_INSTANTIATION_DECLARATION_DLLEXPORT __attribute__ ((visibility("default")))
#   define {U}_EXPLICIT_INSTANTIATION_DEFINITION_DLLIMPORT
#   define {U}_EXPLICIT_INSTANTIATION_DEFINITION_DLLEXPORT
#  else
#   define {U}_DLLIMPORT
#   define {U}_DLLEXPORT
#   define {U}_DLLLOCAL
#   define {U}_EXPLICIT_INSTANTIATION_DECLARATION_DLLIMPORT
#   define {U}_EXPLICIT_INSTANTIATION_DECLARATION_DLLEXPORT
#   define {U}_EXPLICIT_INSTANTIATION_DEFINITION_DLLIMPORT
#   define {U}_EXPLICIT_INSTANTIATION_DEFINITION_DLLEXPORT
#  endif // __GNUC__ >= 4
# endif // defined _WIN32 || defined __CYGWIN__

# ifdef {U}_STATIC
#  define {U}_DLLAPI
#  define {U}_LOCAL
#  define {U}_EXPLICIT_INSTANTIATION_DECLARATION extern template
# else
#  ifdef {pkg}_EXPORTS
#   define {U}_DLLAPI {U}_DLLEXPORT
#   define {U}_EXPLICIT_INSTANTIATION_DECLARATION_DLLAPI {U}_EXPLICIT_INSTANTIATION_DECLARATION_DLLEXPORT
#   define {U}_EXPLICIT_INSTANTIATION_DEFINITION_DLLAPI {U}_EXPLICIT_INSTANTIATION_DEFINITION_DLLEXPORT
#  else
#   define {U}_DLLAPI {U}_DLLIMPORT
#   define {U}_EXPLICIT_INSTANTIATION_DECLARATION_DLLAPI {U}_EXPLICIT_INSTANTIATION_DECLARATION_DLLIMPORT
#   define {U}_EXPLICIT_INSTANTIATION_DEFINITION_DLLAPI {U}_EXPLICIT_INSTANTIATION_DEFINITION_DLLIMPORT
#  endif // {U}_EXPORTS
#  define {U}_LOCAL {U}_DLLLOCAL
# endif // {U}_STATIC
#endif //! {U}_CONFIG_HH
\"\"\"
DEPRECATED = f\"\"\"/*
 * This file has been automatically generated by the jrl-cmakemodules.
 * Please see https://github.com/jrl-umi3218/jrl-cmakemodules/blob/master/deprecated.hh.cmake for details.
*/

#ifndef {U}_DEPRECATED_HH
# define {U}_DEPRECATED_HH

# if defined(__cplusplus) && (__cplusplus >= 201402L)
#  define {U}_DEPRECATED [[deprecated]]
#  define {U}_DEPRECATED_MESSAGE(message) [[deprecated(#message)]]
# elif defined(__GNUC__) || defined(__clang__)
#  define {U}_DEPRECATED __attribute__ ((deprecated))
#  define {U}_DEPRECATED_MESSAGE(message) __attribute__ (( deprecated(#message) ))
# else
#  if defined(_MSC_VER) && !defined(__INTEL_COMPILER)
#   define {U}_DEPRECATED __declspec (deprecated)
#   define {U}_DEPRECATED_MESSAGE(message) __declspec ( deprecated(#message) )
#  else
#   define {U}_DEPRECATED /* nothing */
#   define {U}_DEPRECATED_MESSAGE(message)
#  endif // __MSVC__
# endif // __cplusplus

# if defined(__GNUC__) || defined(__clang__)
#  ifndef {U}_PRAGMA
#   define {U}_PRAGMA(X) _Pragma(#X)
#  endif
#  define {U}_DEPRECATED_HEADER(MSG) {U}_PRAGMA(GCC warning MSG)
# elif defined(_MSC_VER) && !defined(__INTEL_COMPILER)
#  define {U}_STRINGIZE_(MSG) #MSG
#  define {U}_STRINGIZE(MSG) {U}_STRINGIZE_(MSG)
#  define {U}_DEPRECATED_HEADER(MSG) \\\\
    __pragma(message(__FILE__ "(" {U}_STRINGIZE(__LINE__) ") : Warning: " MSG))
# else
#  define {U}_DEPRECATED_HEADER(MSG)
# endif

#endif //! {U}_DEPRECATED_HH
\"\"\"
WARNING = f\"\"\"/*
 * This file has been automatically generated by the jrl-cmakemodules.
 * Please see https://github.com/jrl-umi3218/jrl-cmakemodules/blob/master/warning.hh.cmake for details.
*/

#ifndef {U}_WARNING_HH
# define {U}_WARNING_HH

# define {U}_WARN_STRINGISE_IMPL(x) #x
# define {U}_WARN_STRINGISE(x) \\\\
         {U}_WARN_STRINGISE_IMPL(x)
# ifdef __GNUC__
#   define {U}_WARN(exp) ("WARNING: " exp)
# else
#  ifdef _MSC_VER
#   define FILE_LINE_LINK __FILE__ "(" \\\\
           {U}_WARN_STRINGISE(__LINE__) ") : "
#   define {U}_WARN(exp) (FILE_LINE_LINK "WARNING: " exp)
#  else
#   define {U}_WARN(MSG) /* nothing */
#  endif // __MSVC__
# endif // __GNUC__

#endif //! {U}_WARNING_HH
\"\"\"
for out_path in sys.argv[2:]:
    base = os.path.basename(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        if base.startswith("config."):
            f.write(CONFIG)
        elif base.startswith("deprecated."):
            f.write(DEPRECATED)
        elif base.startswith("warning."):
            f.write(WARNING)
        else:
            raise ValueError(f"Unknown JRL header output: {out_path}")
' $(location """ + package_xml + ") " + " ".join(["$(location {})".format(o) for o in outs]),
        **kwargs
    )

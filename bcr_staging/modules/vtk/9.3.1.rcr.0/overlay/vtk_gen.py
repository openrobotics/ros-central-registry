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

"""Build-time code generator for VTK 9.3.1."""

import hashlib
import os
import re
import shutil
import sys


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def configure_cmake_file(src_path, dst_path, vars_dict):
    with open(src_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines(keepends=True)

    out_lines = []
    for line in lines:
        m01 = re.match(r"^(\s*)#cmakedefine01\s+([A-Za-z0-9_]+)(.*)$", line)
        if m01:
            indent, var_name, rest = m01.groups()
            val = 1 if vars_dict.get(var_name) else 0
            out_lines.append(f"{indent}#define {var_name} {val}{rest}\n")
            continue

        mdef = re.match(r"^(\s*)#cmakedefine\s+([A-Za-z0-9_]+)(.*)$", line)
        if mdef:
            indent, var_name, rest = mdef.groups()
            if vars_dict.get(var_name):
                rest_sub = replace_vars(rest, vars_dict)
                out_lines.append(f"{indent}#define {var_name}{rest_sub}\n")
            else:
                out_lines.append(f"{indent}/* #undef {var_name} */\n")
            continue

        out_lines.append(replace_vars(line, vars_dict))

    write_file(dst_path, "".join(out_lines))


def replace_vars(text, vars_dict):
    def repl_at(m):
        k = m.group(1)
        return str(vars_dict.get(k, ""))

    def repl_dollar(m):
        k = m.group(1)
        return str(vars_dict.get(k, ""))

    text = re.sub(r"@([A-Za-z0-9_]+)@", repl_at, text)
    text = re.sub(r"\$\{([A-Za-z0-9_]+)\}", repl_dollar, text)
    return text


def generate_vtksys_headers(vtk_root, gen_include):
    kwsys_dir = os.path.join(vtk_root, "Utilities/KWSys/vtksys")
    vtksys_out = os.path.join(gen_include, "vtksys")
    vars_dict = {
        "KWSYS_NAMESPACE": "vtksys",
        "KWSYS_BUILD_SHARED": 0,
        "KWSYS_NAME_IS_KWSYS": 0,
        "KWSYS_STL_HAVE_STD": 1,
        "KWSYS_IOS_USE_ANSI": 1,
        "KWSYS_IOS_USE_SSTREAM": 1,
        "KWSYS_IOS_USE_STRSTREAM_H": 0,
        "KWSYS_IOS_USE_STRSTREA_H": 0,
        "KWSYS_SYSTEMTOOLS_USE_TRANSLATION_MAP": 1,
        "KWSYS_CXX_HAS_ENVIRON_IN_STDLIB_H": 0,
        "KWSYS_CXX_HAS_SETENV": 1,
        "KWSYS_CXX_HAS_UNSETENV": 1,
        "KWSYS_CXX_HAS_PUTENV": 1,
        "KWSYS_CXX_HAS_UTIMES": 1,
        "KWSYS_CXX_HAS_UTIMENSAT": 1,
        "KWSYS_CXX_STAT_HAS_ST_MTIM": 1,
        "KWSYS_CXX_STAT_HAS_ST_MTIMESPEC": 0,
        "KWSYS_CXX_HAS_RLIMIT64": 1,
        "KWSYS_CXX_HAS_ATOL": 1,
        "KWSYS_CXX_HAS_ATOLL": 1,
        "KWSYS_CXX_HAS__ATOI64": 0,
        "KWSYS_SYSTEMINFORMATION_HAS_BACKTRACE": 1,
        "KWSYS_SYSTEMINFORMATION_HAS_CPP_DEMANGLE": 1,
        "KWSYS_SYSTEMINFORMATION_HAS_SYMBOL_LOOKUP": 1,
        "KWSYS_SYSTEMINFORMATION_HAS_DEBUG_BUILD": 0,
        "KWSYS_STL_HAS_WSTRING": 1,
        "KWSYS_CXX_HAS_EXT_STDIO_FILEBUF_H": 1,
        "KWSYS_CONSOLE_BUF_USE_ANSI": 1,
    }
    h_in_files = [
        "Configure.h",
        "Configure.hxx",
        "SharedForward.h",
        "String.hxx",
        "Directory.hxx",
        "DynamicLoader.hxx",
        "Encoding.hxx",
        "Glob.hxx",
        "RegularExpression.hxx",
        "SystemTools.hxx",
        "CommandLineArguments.hxx",
        "FStream.hxx",
        "SystemInformation.hxx",
        "Status.hxx",
        "Process.h",
        "Base64.h",
        "Encoding.h",
        "MD5.h",
        "System.h",
    ]
    for fn in h_in_files:
        configure_cmake_file(
            os.path.join(kwsys_dir, fn + ".in"),
            os.path.join(vtksys_out, fn),
            vars_dict,
        )


def generate_kwiml_headers(vtk_root, gen_include):
    kwiml_out = os.path.join(gen_include, "vtkkwiml")
    os.makedirs(kwiml_out, exist_ok=True)
    shutil.copyfile(
        os.path.join(vtk_root, "Utilities/KWIML/vtkkwiml/include/kwiml/abi.h"),
        os.path.join(kwiml_out, "abi.h"),
    )
    shutil.copyfile(
        os.path.join(vtk_root, "Utilities/KWIML/vtkkwiml/include/kwiml/int.h"),
        os.path.join(kwiml_out, "int.h"),
    )
    configure_cmake_file(
        os.path.join(vtk_root, "Utilities/KWIML/vtkkwiml/src/version.h.in"),
        os.path.join(kwiml_out, "version.h"),
        {"KWIML_VERSION_DECIMAL": "1000000", "KWIML_VERSION": "1.0.0"},
    )


def generate_thirdparty_headers(vtk_root, gen_include):
    # DICOMParser
    configure_cmake_file(
        os.path.join(vtk_root, "Utilities/DICOMParser/DICOMCMakeConfig.h.in"),
        os.path.join(gen_include, "DICOMCMakeConfig.h"),
        {"DICOM_DLL": 0, "DICOM_STATIC": 1, "DICOM_ANSI_STDLIB": 1},
    )

    # MetaIO
    configure_cmake_file(
        os.path.join(vtk_root, "Utilities/MetaIO/vtkmetaio/metaIOConfig.h.in"),
        os.path.join(gen_include, "vtkmetaio/metaIOConfig.h"),
        {"METAIO_FOR_ITK": 0, "METAIO_FOR_VTK": 1, "BUILD_SHARED_LIBS": 0},
    )

    # ThirdParty vtk_*.h.in
    tp_configs = [
        (
            "ThirdParty/diy2/vtk_diy2.h.in",
            "vtk_diy2.h",
            {"VTK_MODULE_USE_EXTERNAL_vtkdiy2": 0, "DIY_NO_MPI": 1},
        ),
        (
            "ThirdParty/doubleconversion/vtk_doubleconversion.h.in",
            "vtk_doubleconversion.h",
            {"VTK_MODULE_USE_EXTERNAL_vtkdoubleconversion": 0},
        ),
        ("ThirdParty/eigen/vtk_eigen.h.in", "vtk_eigen.h", {"VTK_MODULE_USE_EXTERNAL_vtkeigen": 1}),
        ("ThirdParty/expat/vtk_expat.h.in", "vtk_expat.h", {"VTK_MODULE_USE_EXTERNAL_vtkexpat": 1}),
        (
            "ThirdParty/exprtk/vtk_exprtk.h.in",
            "vtk_exprtk.h",
            {"VTK_MODULE_USE_EXTERNAL_vtkexprtk": 0},
        ),
        (
            "ThirdParty/fast_float/vtkfast_float.h.in",
            "vtkfast_float.h",
            {"VTK_MODULE_USE_EXTERNAL_vtkfast_float": 0},
        ),
        ("ThirdParty/fmt/vtk_fmt.h.in", "vtk_fmt.h", {"VTK_MODULE_USE_EXTERNAL_vtkfmt": 0}),
        (
            "ThirdParty/freetype/vtk_freetype.h.in",
            "vtk_freetype.h",
            {"VTK_MODULE_USE_EXTERNAL_vtkfreetype": 1, "VTK_FREETYPE_SHARED": 0},
        ),
        (
            "ThirdParty/glew/vtk_glew.h.in",
            "vtk_glew.h",
            {
                "VTK_MODULE_USE_EXTERNAL_vtkglew": 0,
                "VTK_OPENGL_ES_VERSION": 30,
                "VTK_USE_X": 1,
                "GLEW_USE_STATIC_LIBS": 1,
                "VTK_OPENGL_USE_GLES": 0,
                "APPLE": 0,
            },
        ),
        ("ThirdParty/jpeg/vtk_jpeg.h.in", "vtk_jpeg.h", {"VTK_MODULE_USE_EXTERNAL_vtkjpeg": 1}),
        (
            "ThirdParty/kissfft/vtk_kissfft.h.in",
            "vtk_kissfft.h",
            {"VTK_MODULE_USE_EXTERNAL_vtkkissfft": 0},
        ),
        ("ThirdParty/lz4/vtk_lz4.h.in", "vtk_lz4.h", {"VTK_MODULE_USE_EXTERNAL_vtklz4": 1}),
        (
            "ThirdParty/lzma/vtk_lzma.h.in",
            "vtk_lzma.h",
            {"VTK_MODULE_USE_EXTERNAL_vtklzma": 0, "LZMA_BUILT_AS_DYNAMIC_LIB": 0},
        ),
        (
            "ThirdParty/nlohmannjson/vtk_nlohmannjson.h.in",
            "vtk_nlohmannjson.h",
            {"VTK_MODULE_USE_EXTERNAL_vtknlohmannjson": 1},
        ),
        ("ThirdParty/png/vtk_png.h.in", "vtk_png.h", {"VTK_MODULE_USE_EXTERNAL_vtkpng": 1}),
        (
            "ThirdParty/pugixml/vtk_pugixml.h.in",
            "vtk_pugixml.h",
            {"VTK_MODULE_USE_EXTERNAL_vtkpugixml": 1},
        ),
        ("ThirdParty/tiff/vtk_tiff.h.in", "vtk_tiff.h", {"VTK_MODULE_USE_EXTERNAL_vtktiff": 1}),
        ("ThirdParty/utf8/vtk_utf8.h.in", "vtk_utf8.h", {"VTK_MODULE_USE_EXTERNAL_vtkutf8": 0}),
        (
            "ThirdParty/verdict/vtk_verdict.h.in",
            "vtk_verdict.h",
            {"VTK_MODULE_USE_EXTERNAL_vtkverdict": 0},
        ),
        ("ThirdParty/zlib/vtk_zlib.h.in", "vtk_zlib.h", {"VTK_MODULE_USE_EXTERNAL_vtkzlib": 1}),
    ]
    for src_rel, dst_rel, vdict in tp_configs:
        configure_cmake_file(
            os.path.join(vtk_root, src_rel),
            os.path.join(gen_include, dst_rel),
            vdict,
        )

    # doubleconversion export header
    write_file(
        os.path.join(
            gen_include,
            "vtkdoubleconversion/double-conversion/vtkdoubleconversion_export.h",
        ),
        """#ifndef VTKDOUBLECONVERSION_EXPORT_H
#define VTKDOUBLECONVERSION_EXPORT_H
#define VTKDOUBLECONVERSION_EXPORT
#define VTKDOUBLECONVERSION_NO_EXPORT
#endif
""",
    )

    # verdict config header
    configure_cmake_file(
        os.path.join(vtk_root, "ThirdParty/verdict/vtkverdict/verdict_config.h.in"),
        os.path.join(gen_include, "vtkverdict/verdict_config.h"),
        {"BUILD_SHARED_LIBS": 0, "verdict_EXPORTS": 0},
    )

    # lzma config.h
    lzma_vars = {
        "HAVE_STDINT_H": 1,
        "HAVE_INTTYPES_H": 1,
        "HAVE_LIMITS_H": 1,
        "HAVE_STDBOOL_H": 1,
        "HAVE_STRING_H": 1,
        "HAVE_STRINGS_H": 1,
        "HAVE_MEMORY_H": 1,
        "MYTHREAD_POSIX": 1,
        "MYTHREAD_VISTA": 0,
        "HAVE_DECODER_ARM": 1,
        "HAVE_DECODER_ARMTHUMB": 1,
        "HAVE_DECODER_DELTA": 1,
        "HAVE_DECODER_IA64": 1,
        "HAVE_DECODER_LZMA1": 1,
        "HAVE_DECODER_LZMA2": 1,
        "HAVE_DECODER_POWERPC": 1,
        "HAVE_DECODER_SPARC": 1,
        "HAVE_DECODER_X86": 1,
        "HAVE_ENCODERS": 1,
        "HAVE_ENCODER_ARM": 1,
        "HAVE_ENCODER_ARMTHUMB": 1,
        "HAVE_ENCODER_DELTA": 1,
        "HAVE_ENCODER_IA64": 1,
        "HAVE_ENCODER_LZMA1": 1,
        "HAVE_ENCODER_LZMA2": 1,
        "HAVE_ENCODER_POWERPC": 1,
        "HAVE_ENCODER_SPARC": 1,
        "HAVE_ENCODER_X86": 1,
        "HAVE_MF_BT2": 1,
        "HAVE_MF_BT3": 1,
        "HAVE_MF_BT4": 1,
        "HAVE_MF_HC3": 1,
        "HAVE_MF_HC4": 1,
        "HAVE_BSWAP_16": 1,
        "HAVE_BSWAP_32": 1,
        "HAVE_BSWAP_64": 1,
        "HAVE_BYTESWAP_H": 1,
        "HAVE_SYS_ENDIAN_H": 0,
        "HAVE_CHECK_CRC32": 1,
        "HAVE_CHECK_CRC64": 1,
        "HAVE_CHECK_SHA256": 1,
        "TUKLIB_SYMBOL_PREFIX": "vtklzma_",
        "TUKLIB_FAST_UNALIGNED_ACCESS": 1,
        "BUILD_SHARED_LIBS": 0,
    }
    configure_cmake_file(
        os.path.join(vtk_root, "ThirdParty/lzma/vtklzma/config.h.in"),
        os.path.join(gen_include, "vtklzma_config/config.h"),
        lzma_vars,
    )


VTK_MODULES = [
    "ChartsCore",
    "CommonColor",
    "CommonComputationalGeometry",
    "CommonCore",
    "CommonDataModel",
    "CommonExecutionModel",
    "CommonMath",
    "CommonMisc",
    "CommonSystem",
    "CommonTransforms",
    "DICOMParser",
    "FiltersCore",
    "FiltersExtraction",
    "FiltersGeneral",
    "FiltersGeometry",
    "FiltersHybrid",
    "FiltersHyperTree",
    "FiltersModeling",
    "FiltersSources",
    "FiltersStatistics",
    "FiltersTexture",
    "FiltersVerdict",
    "GUISupportQt",
    "IOCore",
    "IOGeometry",
    "IOImage",
    "IOLegacy",
    "IOPLY",
    "IOXML",
    "IOXMLParser",
    "ImagingColor",
    "ImagingCore",
    "ImagingGeneral",
    "ImagingHybrid",
    "ImagingMath",
    "ImagingSources",
    "InfovisCore",
    "InteractionImage",
    "InteractionStyle",
    "InteractionWidgets",
    "ParallelCore",
    "ParallelDIY",
    "RenderingAnnotation",
    "RenderingContext2D",
    "RenderingContextOpenGL2",
    "RenderingCore",
    "RenderingFreeType",
    "RenderingHyperTreeGrid",
    "RenderingLOD",
    "RenderingOpenGL2",
    "RenderingUI",
    "RenderingVolume",
    "RenderingVolumeOpenGL2",
    "ViewsContext2D",
    "ViewsCore",
]

AUTOINIT_DEPS = {
    "InteractionStyle": [],
    "RenderingContext2D": ["RenderingContextOpenGL2"],
    "RenderingContextOpenGL2": ["RenderingFreeType", "RenderingOpenGL2", "RenderingUI"],
    "RenderingCore": [
        "InteractionStyle",
        "RenderingFreeType",
        "RenderingOpenGL2",
        "RenderingUI",
    ],
    "RenderingFreeType": ["RenderingOpenGL2", "RenderingUI"],
    "RenderingOpenGL2": ["RenderingUI"],
    "RenderingUI": [],
    "RenderingVolume": [
        "InteractionStyle",
        "RenderingFreeType",
        "RenderingOpenGL2",
        "RenderingUI",
        "RenderingVolumeOpenGL2",
    ],
    "RenderingVolumeOpenGL2": [
        "InteractionStyle",
        "RenderingFreeType",
        "RenderingOpenGL2",
        "RenderingUI",
    ],
    "ChartsCore": ["RenderingContextOpenGL2", "RenderingFreeType", "RenderingOpenGL2", "RenderingUI"],
    "ViewsContext2D": ["RenderingContextOpenGL2", "RenderingFreeType", "RenderingOpenGL2", "RenderingUI"],
}


def generate_module_export_headers(gen_include):
    for mod in VTK_MODULES:
        upper = f"VTK{mod.upper()}"
        guard = f"{upper}_EXPORT_H"
        autoinit_block = ""
        if mod in AUTOINIT_DEPS:
            implements = [f"vtk{d}" for d in AUTOINIT_DEPS[mod]] + [f"vtk{mod}"]
            impl_list = ",".join(implements)
            count = len(implements)
            autoinit_block = f"""
/* AutoInit dependencies. */
"""
            for d in AUTOINIT_DEPS[mod]:
                autoinit_block += f'#include "vtk{d}Module.h"\n'
            autoinit_block += f"""
/* AutoInit implementations. */
#ifdef vtk{mod}_AUTOINIT_INCLUDE
#include vtk{mod}_AUTOINIT_INCLUDE
#endif
#ifdef vtk{mod}_AUTOINIT
#include "vtkAutoInit.h"
VTK_MODULE_AUTOINIT(vtk{mod})
#endif
"""
        content = f"""#ifndef {guard}
#define {guard}

#define {upper}_STATIC_DEFINE
#define {upper}_EXPORT
#define {upper}_NO_EXPORT
#define {upper}_DEPRECATED __attribute__ ((__deprecated__))
#define {upper}_DEPRECATED_EXPORT {upper}_EXPORT {upper}_DEPRECATED
#define {upper}_DEPRECATED_NO_EXPORT {upper}_NO_EXPORT {upper}_DEPRECATED

#include "vtkABINamespace.h"
{autoinit_block}
#endif /* {guard} */
"""
        write_file(os.path.join(gen_include, f"vtk{mod}Module.h"), content)


def generate_common_core(vtk_root, gen_include, gen_src):
    cc_dir = os.path.join(vtk_root, "Common/Core")

    # Compatibility vtkConfigure.h
    write_file(
        os.path.join(gen_include, "vtkConfigure.h"),
        """#ifndef vtkConfigure_h
#define vtkConfigure_h
#include "vtkBuild.h"
#include "vtkEndian.h"
#include "vtkFeatures.h"
#include "vtkLegacy.h"
#include "vtkOptions.h"
#include "vtkPlatform.h"
#include "vtkSMP.h"
#include "vtkThreads.h"
#include "vtkVersionMacros.h"
#endif
""",
    )

    vars_dict = {
        "VTK_ABI_NAMESPACE_BEGIN": "",
        "VTK_ABI_NAMESPACE_END": "",
        "VTK_BUILD_SHARED_LIBS": 0,
        "VTK_HAS_CXXABI_DEMANGLE": 1,
        "VTK_DEBUG_LEAKS": 0,
        "VTK_WARN_ON_DISPATCH_FAILURE": 0,
        "VTK_DEBUG_RANGE_ITERATORS": 0,
        "VTK_ALWAYS_OPTIMIZE_ARRAY_ITERATORS": 1,
        "VTK_WORDS_BIGENDIAN": 0,
        "VTK_ALL_NEW_OBJECT_FACTORY": 0,
        "VTK_USE_MEMKIND": 0,
        "VTK_HAS_FEENABLEEXCEPT": 1,
        "VTK_LEGACY_REMOVE": 0,
        "VTK_LEGACY_SILENT": 0,
        "VTK_HAS_ISNAN": 1,
        "VTK_HAS_STD_ISNAN": 1,
        "VTK_HAS__ISNAN": 0,
        "VTK_HAS_ISINF": 1,
        "VTK_HAS_STD_ISINF": 1,
        "VTK_HAS_ISFINITE": 1,
        "VTK_HAS_STD_ISFINITE": 1,
        "VTK_HAS_FINITE": 1,
        "VTK_HAS__FINITE": 0,
        "VTK_USE_64BIT_IDS": 1,
        "VTK_USE_64BIT_TIMESTAMPS": 1,
        "VTK_USE_FUTURE_CONST": 0,
        "VTK_USE_FUTURE_BOOL": 0,
        "VTK_REQUIRE_LARGE_FILE_SUPPORT": 1,
        "VTK_SMP_IMPLEMENTATION_TYPE": "STDThread",
        "VTK_SMP_ENABLE_OPENMP": 0,
        "VTK_SMP_ENABLE_SEQUENTIAL": 1,
        "VTK_SMP_ENABLE_STDTHREAD": 1,
        "VTK_SMP_ENABLE_TBB": 0,
        "VTK_SMP_DEFAULT_IMPLEMENTATION_OPENMP": 0,
        "VTK_SMP_DEFAULT_IMPLEMENTATION_SEQUENTIAL": 0,
        "VTK_SMP_DEFAULT_IMPLEMENTATION_STDTHREAD": 1,
        "VTK_SMP_DEFAULT_IMPLEMENTATION_TBB": 0,
        "VTK_USE_PTHREADS": 1,
        "VTK_USE_WIN32_THREADS": 0,
        "VTK_MAX_THREADS": 64,
        "VTK_DISPATCH_AFFINE_ARRAYS": 0,
        "VTK_DISPATCH_CONSTANT_ARRAYS": 0,
        "VTK_DISPATCH_STD_FUNCTION_ARRAYS": 0,
        "VTK_USE_SCALED_SOA_ARRAYS": 0,
        "VTK_VERSION_FULL": "9.3.1",
        "VTK_MAJOR_VERSION": 9,
        "VTK_MINOR_VERSION": 3,
        "VTK_BUILD_VERSION": 1,
        "VTK_VERSION": "9.3.1",
    }

    cc_headers = [
        "vtkABINamespace.h",
        "vtkBuild.h",
        "vtkCxxABIConfigure.h",
        "vtkDebug.h",
        "vtkDebugRangeIterators.h",
        "vtkEndian.h",
        "vtkFeatures.h",
        "vtkFloatingPointExceptionsConfigure.h",
        "vtkLegacy.h",
        "vtkMathConfigure.h",
        "vtkOptions.h",
        "vtkPlatform.h",
        "vtkSMP.h",
        "vtkThreads.h",
        "vtkVTK_DISPATCH_IMPLICIT_ARRAYS.h",
        "vtkVTK_USE_SCALED_SOA_ARRAYS.h",
        "vtkVersionFull.h",
        "vtkVersionMacros.h",
    ]
    for h in cc_headers:
        configure_cmake_file(
            os.path.join(cc_dir, h + ".in"),
            os.path.join(gen_include, h),
            vars_dict,
        )

    # Generate vtkTypeListMacros.h (from vtkCreateTypeListMacros.cmake)
    tl_lines = [
        "// SPDX-FileCopyrightText: Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen",
        "// SPDX-License-Identifier: BSD-3-Clause",
        "#ifndef vtkTypeListMacros_h",
        "#define vtkTypeListMacros_h",
        "",
        '#define vtkTypeList_Create_1(t1) vtkTypeList::TypeList<t1, vtkTypeList::NullType>',
    ]
    for i in range(2, 100):
        args = ", ".join(f"t{j}" for j in range(1, i + 1))
        prev_args = ", ".join(f"t{j}" for j in range(2, i + 1))
        tl_lines.append(
            f"#define vtkTypeList_Create_{i}({args}) "
            f"vtkTypeList::TypeList<t1, vtkTypeList_Create_{i - 1}({prev_args})>"
        )
    tl_lines.append("")
    tl_lines.append("#endif")
    tl_lines.append("")
    write_file(os.path.join(gen_include, "vtkTypeListMacros.h"), "\n".join(tl_lines))

    # Generate vtkArrayDispatchArrayList.h (from vtkCreateArrayDispatchArrayList.cmake)
    value_types = [
        "char",
        "double",
        "float",
        "int",
        "long",
        "long long",
        "short",
        "signed char",
        "unsigned char",
        "unsigned int",
        "unsigned long",
        "unsigned long long",
        "unsigned short",
        "vtkIdType",
    ]
    ad_lines = [
        "// SPDX-FileCopyrightText: Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen",
        "// SPDX-License-Identifier: BSD-3-Clause",
        "// This file is autogenerated by vtkCreateArrayDispatchArrayList.cmake.",
        "// Do not edit this file. Your changes will not be saved.",
        "",
        "#ifndef vtkArrayDispatchArrayList_h",
        "#define vtkArrayDispatchArrayList_h",
        "",
        '#include "vtkTypeList.h"',
        '#include "vtkAOSDataArrayTemplate.h"',
        "",
        "namespace vtkArrayDispatch {",
        "VTK_ABI_NAMESPACE_BEGIN",
        "",
        "typedef vtkTypeList::Unique<",
        f"  vtkTypeList_Create_{len(value_types)}(",
    ]
    for idx, vt in enumerate(value_types):
        comma = "," if idx + 1 < len(value_types) else ""
        ad_lines.append(f"    vtkAOSDataArrayTemplate<{vt}>{comma}")
    ad_lines.extend(
        [
            "  )",
            ">::Result Arrays;",
            "",
            "typedef vtkTypeList::Unique<",
            "  vtkTypeList::Create<",
            "  >",
            ">::Result ReadOnlyArrays;",
            "",
            "typedef vtkTypeList::Unique<",
            "  vtkTypeList::Append<Arrays, ReadOnlyArrays>::Result",
            ">::Result AllArrays;",
            "",
            "VTK_ABI_NAMESPACE_END",
            "} // end namespace vtkArrayDispatch",
            "",
            "#endif // vtkArrayDispatchArrayList_h",
            "",
        ]
    )
    write_file(os.path.join(gen_include, "vtkArrayDispatchArrayList.h"), "\n".join(ad_lines))

    # Generate vtkType*Array.h and consolidated vtkTypeArraysInstantiate.cxx
    # On 64-bit Linux (LP64): Int8=signed char, Int16=short, Int32=int, Int64=long long (or long)
    # Wait: let's check Common/Core/vtkType.h to see what VTK_TYPE_INT64 is on LP64!
    # In vtkTypeArrays.cmake, it uses #if VTK_TYPE_INT64 == VTK_LONG / VTK_LONG_LONG preprocessor checks!
    type_arrays = [
        (
            "Int8",
            """#if VTK_TYPE_INT8 == VTK_CHAR
# include "vtkCharArray.h"
# define vtkTypeArrayBase vtkCharArray
#else
# include "vtkSignedCharArray.h"
# define vtkTypeArrayBase vtkSignedCharArray
#endif""",
        ),
        (
            "Int16",
            """#if VTK_TYPE_INT16 == VTK_SHORT
# include "vtkShortArray.h"
# define vtkTypeArrayBase vtkShortArray
#endif""",
        ),
        (
            "Int32",
            """#if VTK_TYPE_INT32 == VTK_INT
# include "vtkIntArray.h"
# define vtkTypeArrayBase vtkIntArray
#endif""",
        ),
        (
            "Int64",
            """#if VTK_TYPE_INT64 == VTK_LONG
# include "vtkLongArray.h"
# define vtkTypeArrayBase vtkLongArray
#elif VTK_TYPE_INT64 == VTK_LONG_LONG
# include "vtkLongLongArray.h"
# define vtkTypeArrayBase vtkLongLongArray
#endif""",
        ),
        (
            "UInt8",
            """#if VTK_TYPE_UINT8 == VTK_UNSIGNED_CHAR
# include "vtkUnsignedCharArray.h"
# define vtkTypeArrayBase vtkUnsignedCharArray
#endif""",
        ),
        (
            "UInt16",
            """#if VTK_TYPE_UINT16 == VTK_UNSIGNED_SHORT
# include "vtkUnsignedShortArray.h"
# define vtkTypeArrayBase vtkUnsignedShortArray
#endif""",
        ),
        (
            "UInt32",
            """#if VTK_TYPE_UINT32 == VTK_UNSIGNED_INT
# include "vtkUnsignedIntArray.h"
# define vtkTypeArrayBase vtkUnsignedIntArray
#endif""",
        ),
        (
            "UInt64",
            """#if VTK_TYPE_UINT64 == VTK_UNSIGNED_LONG
# include "vtkUnsignedLongArray.h"
# define vtkTypeArrayBase vtkUnsignedLongArray
#elif VTK_TYPE_UINT64 == VTK_UNSIGNED_LONG_LONG
# include "vtkUnsignedLongLongArray.h"
# define vtkTypeArrayBase vtkUnsignedLongLongArray
#endif""",
        ),
        (
            "Float32",
            """#if VTK_TYPE_FLOAT32 == VTK_FLOAT
# include "vtkFloatArray.h"
# define vtkTypeArrayBase vtkFloatArray
#endif""",
        ),
        (
            "Float64",
            """#if VTK_TYPE_FLOAT64 == VTK_DOUBLE
# include "vtkDoubleArray.h"
# define vtkTypeArrayBase vtkDoubleArray
#endif""",
        ),
    ]
    with open(os.path.join(cc_dir, "vtkTypedArray.h.in"), "r", encoding="utf-8") as f:
        typed_h_in = f.read()
    with open(os.path.join(cc_dir, "vtkTypedArray.cxx.in"), "r", encoding="utf-8") as f:
        typed_cxx_in = f.read()

    all_typed_cxx = []
    for tname, tnative in type_arrays:
        v = {"VTK_TYPE_NAME": tname, "VTK_TYPE_NATIVE": tnative}
        write_file(
            os.path.join(gen_include, f"vtkType{tname}Array.h"),
            replace_vars(typed_h_in, v),
        )
        all_typed_cxx.append(replace_vars(typed_cxx_in, v))
    write_file(os.path.join(gen_src, "vtkTypeArraysInstantiate.cxx"), "\n".join(all_typed_cxx))

    def consolidate_instantiations(tmpl_in, types):
        sections = []
        preamble = []
        body = []
        for line in tmpl_in.splitlines():
            s = line.strip()
            if s.startswith("#") and body:
                sections.append((preamble, body))
                preamble = [line]
                body = []
            elif not body and (s.startswith("#") or s.startswith("//") or not s):
                preamble.append(line)
            else:
                body.append(line)
        if preamble or body:
            sections.append((preamble, body))
        out_lines = []
        for pre, bod in sections:
            out_lines.extend(pre)
            bod_str = "\n".join(bod)
            for vt in types:
                out_lines.append(replace_vars(bod_str, {"INSTANTIATION_VALUE_TYPE": vt}))
        return "\n".join(out_lines) + "\n"

    # Consolidated array template instantiations
    inst_types = [t for t in value_types if t != "vtkIdType"]
    inst_templates = [
        "vtkAffineArrayInstantiate",
        "vtkAffineImplicitBackendInstantiate",
        "vtkCompositeArrayInstantiate",
        "vtkCompositeImplicitBackendInstantiate",
        "vtkConstantArrayInstantiate",
        "vtkConstantImplicitBackendInstantiate",
        "vtkIndexedArrayInstantiate",
        "vtkIndexedImplicitBackendInstantiate",
        "vtkSOADataArrayTemplateInstantiate",
        "vtkStdFunctionArrayInstantiate",
        "vtkTypedDataArrayInstantiate",
    ]
    for tmpl in inst_templates:
        with open(os.path.join(cc_dir, f"{tmpl}.cxx.in"), "r", encoding="utf-8") as f:
            tmpl_in = f.read()
        write_file(
            os.path.join(gen_src, f"{tmpl}All.cxx"),
            consolidate_instantiations(tmpl_in, inst_types),
        )

    # vtkGenericDataArrayValueRangeInstantiate for long types
    long_types = ["long", "unsigned long", "long long", "unsigned long long"]
    with open(
        os.path.join(cc_dir, "vtkGenericDataArrayValueRangeInstantiate.cxx.in"),
        "r",
        encoding="utf-8",
    ) as f:
        gda_in = f.read()
    write_file(
        os.path.join(gen_src, "vtkGenericDataArrayValueRangeInstantiateAll.cxx"),
        consolidate_instantiations(gda_in, long_types),
    )


def generate_parallel_and_rendering(vtk_root, gen_include, gen_src):
    # Parallel/Core/vtkSocketCommunicatorHash.h
    sc_path = os.path.join(vtk_root, "Parallel/Core/vtkSocketCommunicator.cxx")
    with open(sc_path, "rb") as f:
        md5_hex = hashlib.md5(f.read()).hexdigest()
    write_file(
        os.path.join(gen_include, "vtkSocketCommunicatorHash.h"),
        f"""#ifndef vtkSocketCommunicatorHash_h
#define vtkSocketCommunicatorHash_h
#define vtkSocketCommunicatorHash "{md5_hex}"
#endif
""",
    )

    # Rendering/Core/vtkTDxConfigure.h
    write_file(
        os.path.join(gen_include, "vtkTDxConfigure.h"),
        "/* The TDx support has not been ported, this header defines nothing. */\n",
    )

    # Rendering/OpenGL2 configured headers
    ogl_dir = os.path.join(vtk_root, "Rendering/OpenGL2")
    configure_cmake_file(
        os.path.join(ogl_dir, "vtkOpenGLError.h.in"),
        os.path.join(gen_include, "vtkOpenGLError.h"),
        {
            "VTK_REPORT_OPENGL_ERRORS": 1,
            "VTK_REPORT_OPENGL_ERRORS_IN_RELEASE_BUILDS": 0,
        },
    )
    configure_cmake_file(
        os.path.join(ogl_dir, "vtkRenderingOpenGLConfigure.h.in"),
        os.path.join(gen_include, "vtkRenderingOpenGLConfigure.h"),
        {
            "VTK_USE_COCOA": 0,
            "VTK_USE_X": 1,
            "VTK_OPENGL_HAS_OSMESA": 0,
            "VTK_OPENGL_HAS_EGL": 0,
            "VTK_DEFAULT_RENDER_WINDOW_OFFSCREEN": 0,
            "VTK_OPENGL_ENABLE_STREAM_ANNOTATIONS": 0,
            "VTK_USE_DIRECTX": 0,
            "VTK_USE_CORE_GRAPHICS": 0,
            "VTK_USE_NVCONTROL": 0,
        },
    )

    # Encode shaders for Rendering/OpenGL2
    ogl_shaders = [
        "vtkDepthOfFieldPassFS",
        "vtkDepthPeelingPassFinalFS",
        "vtkDepthPeelingPassIntermediateFS",
        "vtkEDLBilateralFilterFS",
        "vtkEDLComposeFS",
        "vtkEDLShadeFS",
        "vtkFXAAFilterFS",
        "vtkFluidMapperDepthFilterBiGaussFS",
        "vtkFluidMapperDepthFilterNarrowRangeFS",
        "vtkFluidMapperSurfaceNormalFS",
        "vtkFluidMapperThicknessAndVolumeColorFilterFS",
        "vtkFluidMapperFS",
        "vtkFluidMapperFinalFS",
        "vtkFluidMapperGS",
        "vtkFluidMapperVS",
        "vtkGaussianBlurPassFS",
        "vtkGaussianBlurPassVS",
        "vtkGlyph3DVS",
        "vtkOrderIndependentTranslucentPassFinalFS",
        "vtkOutlineGlowBlurPassFS",
        "vtkOutlineGlowUpscalePassFS",
        "vtkPBRFunctions",
        "vtkPointFillPassFS",
        "vtkPointGaussianVS",
        "vtkPointGaussianGS",
        "vtkPolyData2DFS",
        "vtkPolyData2DVS",
        "vtkPolyDataFS",
        "vtkPolyDataVS",
        "vtkPolyDataEdgesGS",
        "vtkPolyDataWideLineGS",
        "vtkSSAAPassFS",
        "vtkSimpleMotionBlurPassFS",
        "vtkSobelGradientMagnitudePass1FS",
        "vtkSobelGradientMagnitudePass2FS",
        "vtkSphereMapperGS",
        "vtkStickMapperGS",
        "vtkTextureObjectFS",
        "vtkTextureObjectVS",
    ]
    ogl_cxx_chunks = ['#include "vtkABINamespace.h"\n']
    for sh in ogl_shaders:
        glsl_path = os.path.join(ogl_dir, "glsl", f"{sh}.glsl")
        with open(glsl_path, "r", encoding="utf-8") as f:
            glsl_text = f.read()
        is_pub = sh == "vtkTextureObjectVS"
        exp_inc = '#include "vtkRenderingOpenGL2Module.h"\n' if is_pub else ""
        exp_sym = "VTKRENDERINGOPENGL2_EXPORT " if is_pub else ""
        h_content = f"""#ifndef {sh}_h
#define {sh}_h
{exp_inc}#include "vtkABINamespace.h"
VTK_ABI_NAMESPACE_BEGIN
{exp_sym}extern const char *{sh};
VTK_ABI_NAMESPACE_END
#endif
"""
        write_file(os.path.join(gen_include, f"{sh}.h"), h_content)
        escaped_lines = []
        for line in glsl_text.splitlines():
            esc = line.replace("\\", "\\\\").replace('"', '\\"')
            escaped_lines.append(f'"{esc}\\n"')
        joined = "\n".join(escaped_lines) if escaped_lines else '""'
        ogl_cxx_chunks.append(
            f'#include "{sh}.h"\nVTK_ABI_NAMESPACE_BEGIN\nconst char *{sh} =\n{joined};\nVTK_ABI_NAMESPACE_END\n'
        )

    # Encode BlueNoiseTexture64x64.jpg as binary array
    jpg_path = os.path.join(ogl_dir, "textures/BlueNoiseTexture64x64.jpg")
    with open(jpg_path, "rb") as f:
        jpg_bytes = f.read()
    write_file(
        os.path.join(gen_include, "BlueNoiseTexture64x64.h"),
        f"""#ifndef BlueNoiseTexture64x64_h
#define BlueNoiseTexture64x64_h
#include "vtkABINamespace.h"
VTK_ABI_NAMESPACE_BEGIN
extern const unsigned char BlueNoiseTexture64x64[{len(jpg_bytes)}];
extern const unsigned int BlueNoiseTexture64x64_length;
VTK_ABI_NAMESPACE_END
#endif
""",
    )
    hex_bytes = ", ".join(f"0x{b:02x}" for b in jpg_bytes)
    ogl_cxx_chunks.append(
        f"""#include "BlueNoiseTexture64x64.h"
VTK_ABI_NAMESPACE_BEGIN
const unsigned char BlueNoiseTexture64x64[{len(jpg_bytes)}] = {{ {hex_bytes} }};
const unsigned int BlueNoiseTexture64x64_length = {len(jpg_bytes)};
VTK_ABI_NAMESPACE_END
"""
    )
    write_file(os.path.join(gen_src, "vtkOpenGL2ShadersAll.cxx"), "\n".join(ogl_cxx_chunks))

    # Encode shaders for Rendering/VolumeOpenGL2
    vol_dir = os.path.join(vtk_root, "Rendering/VolumeOpenGL2")
    vol_shaders = [
        "raycasterfs",
        "raycastervs",
        "vtkglProjectedTetrahedraFS",
        "vtkglProjectedTetrahedraVS",
    ]
    vol_cxx_chunks = ['#include "vtkABINamespace.h"\n']
    for sh in vol_shaders:
        glsl_path = os.path.join(vol_dir, "shaders", f"{sh}.glsl")
        with open(glsl_path, "r", encoding="utf-8") as f:
            glsl_text = f.read()
        write_file(
            os.path.join(gen_include, f"{sh}.h"),
            f"""#ifndef {sh}_h
#define {sh}_h
#include "vtkABINamespace.h"
VTK_ABI_NAMESPACE_BEGIN
extern const char *{sh};
VTK_ABI_NAMESPACE_END
#endif
""",
        )
        escaped_lines = []
        for line in glsl_text.splitlines():
            esc = line.replace("\\", "\\\\").replace('"', '\\"')
            escaped_lines.append(f'"{esc}\\n"')
        joined = "\n".join(escaped_lines) if escaped_lines else '""'
        vol_cxx_chunks.append(
            f'#include "{sh}.h"\nVTK_ABI_NAMESPACE_BEGIN\nconst char *{sh} =\n{joined};\nVTK_ABI_NAMESPACE_END\n'
        )
    write_file(os.path.join(gen_src, "vtkVolumeOpenGL2ShadersAll.cxx"), "\n".join(vol_cxx_chunks))


def generate_object_factories(vtk_root, gen_include, gen_src):
    with open(
        os.path.join(vtk_root, "CMake/vtkObjectFactory.h.in"), "r", encoding="utf-8"
    ) as f:
        of_h_in = f.read()
    with open(
        os.path.join(vtk_root, "CMake/vtkObjectFactory.cxx.in"), "r", encoding="utf-8"
    ) as f:
        of_cxx_in = f.read()

    factories = [
        (
            "InteractionStyle",
            "VTKINTERACTIONSTYLE_EXPORT",
            [("vtkInteractorStyleSwitchBase", "vtkInteractorStyleSwitch")],
        ),
        (
            "RenderingContextOpenGL2",
            "VTKRENDERINGCONTEXTOPENGL2_EXPORT",
            [
                ("vtkContextActor", "vtkOpenGLContextActor"),
                ("vtkContextDevice2D", "vtkOpenGLContextDevice2D"),
                ("vtkContextDevice3D", "vtkOpenGLContextDevice3D"),
                ("vtkPropItem", "vtkOpenGLPropItem"),
                ("vtkAbstractContextBufferId", "vtkOpenGLContextBufferId"),
            ],
        ),
        (
            "RenderingFreeType",
            "VTKRENDERINGFREETYPE_EXPORT",
            [("vtkTextRenderer", "vtkMathTextFreeTypeTextRenderer")],
        ),
        (
            "RenderingOpenGL2",
            "VTKRENDERINGOPENGL2_EXPORT",
            [
                ("vtkGPUInfoList", "vtkDummyGPUInfoList"),
                ("vtkActor", "vtkOpenGLActor"),
                (
                    "vtkCompositePolyDataMapperDelegator",
                    "vtkOpenGLCompositePolyDataMapperDelegator",
                ),
                ("vtkBillboardTextActor3D", "vtkOpenGLBillboardTextActor3D"),
                ("vtkCamera", "vtkOpenGLCamera"),
                ("vtkLabeledContourMapper", "vtkOpenGLLabeledContourMapper"),
                ("vtkHardwareSelector", "vtkOpenGLHardwareSelector"),
                ("vtkImageMapper", "vtkOpenGLImageMapper"),
                ("vtkImageSliceMapper", "vtkOpenGLImageSliceMapper"),
                ("vtkGlyph3DMapper", "vtkOpenGLGlyph3DMapper"),
                ("vtkHyperTreeGridMapper", "vtkOpenGLHyperTreeGridMapper"),
                ("vtkLight", "vtkOpenGLLight"),
                ("vtkPointGaussianMapper", "vtkOpenGLPointGaussianMapper"),
                ("vtkPolyDataMapper", "vtkOpenGLPolyDataMapper"),
                ("vtkPolyDataMapper2D", "vtkOpenGLPolyDataMapper2D"),
                ("vtkProperty", "vtkOpenGLProperty"),
                ("vtkShaderProperty", "vtkOpenGLShaderProperty"),
                ("vtkUniforms", "vtkOpenGLUniforms"),
                ("vtkRenderer", "vtkOpenGLRenderer"),
                ("vtkRenderTimerLog", "vtkOpenGLRenderTimerLog"),
                ("vtkSkybox", "vtkOpenGLSkybox"),
                ("vtkTextActor", "vtkOpenGLTextActor"),
                ("vtkTextActor3D", "vtkOpenGLTextActor3D"),
                ("vtkTextMapper", "vtkOpenGLTextMapper"),
                ("vtkTexture", "vtkOpenGLTexture"),
                ("vtkRenderWindow", "vtkXOpenGLRenderWindow"),
            ],
        ),
        (
            "RenderingUI",
            "VTKRENDERINGUI_EXPORT",
            [("vtkRenderWindowInteractor", "vtkXRenderWindowInteractor")],
        ),
        (
            "RenderingVolumeOpenGL2",
            "VTKRENDERINGVOLUMEOPENGL2_EXPORT",
            [
                ("vtkGPUVolumeRayCastMapper", "vtkOpenGLGPUVolumeRayCastMapper"),
                ("vtkProjectedTetrahedraMapper", "vtkOpenGLProjectedTetrahedraMapper"),
                ("vtkRayCastImageDisplayHelper", "vtkOpenGLRayCastImageDisplayHelper"),
            ],
        ),
    ]

    for mod_name, export_macro, overrides in factories:
        inc_lines = []
        create_lines = []
        register_lines = []
        for base_cls, over_cls in overrides:
            inc_lines.append(f'#include "{over_cls}.h"')
            create_lines.append(f"VTK_CREATE_CREATE_FUNCTION({over_cls})")
            register_lines.append(
                f"""  this->RegisterOverride("{base_cls}", "{over_cls}", "Override for VTK::{mod_name} module", 1, vtkObjectFactoryCreate{over_cls});"""
            )

        vdict = {
            "_vtk_object_factory_library_name": f"vtk{mod_name}",
            "_vtk_object_factory_configure_EXPORT_MACRO": export_macro,
            "_vtk_object_factory_includes": "\n".join(inc_lines),
            "_vtk_object_factory_functions": "\n".join(create_lines),
            "_vtk_object_factory_overrides": "\n".join(register_lines),
            "_vtk_object_factory_configure_INITIAL_CODE": "",
        }
        h_out = replace_vars(of_h_in, vdict)
        cxx_out = replace_vars(of_cxx_in, vdict)
        # Also add a static initializer in the object factory .cxx so that linking the library
        # automatically registers the object factory even if VTK_MODULE_INIT wasn't explicitly called!
        cxx_out += f"""
namespace {{
struct vtk{mod_name}StaticAutoInit {{
  vtk{mod_name}StaticAutoInit() {{
    vtk{mod_name}_AutoInit_Construct();
  }}
}} g_vtk{mod_name}StaticAutoInit;
}}
"""
        write_file(os.path.join(gen_include, f"vtk{mod_name}ObjectFactory.h"), h_out)
        write_file(os.path.join(gen_src, f"vtk{mod_name}ObjectFactory.cxx"), cxx_out)


def main():
    marker_file = sys.argv[1]
    out_dir = sys.argv[2]
    # marker_file is <vtk_root>/Common/Core/vtkBuild.h.in
    vtk_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(marker_file))))
    gen_include = os.path.join(out_dir, "gen_include")
    gen_src = os.path.join(out_dir, "gen_src")

    generate_vtksys_headers(vtk_root, gen_include)
    generate_kwiml_headers(vtk_root, gen_include)
    generate_thirdparty_headers(vtk_root, gen_include)
    generate_module_export_headers(gen_include)
    generate_common_core(vtk_root, gen_include, gen_src)
    generate_parallel_and_rendering(vtk_root, gen_include, gen_src)
    generate_object_factories(vtk_root, gen_include, gen_src)


if __name__ == "__main__":
    main()

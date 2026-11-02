"""Build configuration for @libtorch: generated headers, compile flags and DEF files.

Replaces the configure_file() steps of upstream's CMake build
(torch/headeronly/CMakeLists.txt and caffe2/CMakeLists.txt) so that the
pristine v2.14.1 source tree builds without any patches.
"""

load("@bazel_skylib//rules:expand_template.bzl", "expand_template")
load("@rules_cc//cc/common:cc_info.bzl", "CcInfo")

TORCH_VERSION_MAJOR = "2"
TORCH_VERSION_MINOR = "14"
TORCH_VERSION_PATCH = "1"

# Every @libtorch C++ target compiles as C++20, like upstream's
# CMAKE_CXX_STANDARD 20 (GNU extensions on, as with Clang's CMake default).
LIBTORCH_COPTS = ["-std=gnu++20"]

# Values of the `#cmakedefine`s in torch/headeronly/macros/cmake_macros.h.in.
#
# C10_BUILD_SHARED_LIBS stays undefined: with it, C10_EXPORT/C10_IMPORT become
# __declspec(dllexport/dllimport) on Windows, so linking :c10 statically would
# fail with unresolved __imp_ symbols. Without it they expand to default
# visibility on Linux/macOS and to nothing on Windows, where :c10_shared still
# exports every symbol (through a generated DEF file, see windows_def_file).
#
# C10_USE_GLOG: c10/util/Logging.cpp relies on glog's `int` log severities and
# glog_internal_namespace_::IsGoogleLoggingInitialized. The ROS Central
# Registry pins glog 0.7.1 for the whole distribution, so its staged
# glog/0.7.1.bcr.1.rcr.0 re-exports that internal symbol and
# patches/glog_0_7_log_severity.patch fixes the one int/enum std::min.
_CMAKE_MACROS = {
    "C10_BUILD_SHARED_LIBS": False,
    "C10_USE_GFLAGS": True,
    "C10_USE_GLOG": True,
    "C10_USE_MSVC_STATIC_RUNTIME": False,
    "C10_USE_NUMA": False,
    "C10_USE_ROCM_KERNEL_ASSERT": False,
}

def _cmakedefine_substitutions(macros):
    return {
        "#cmakedefine {}\n".format(name): (
            "#define {} 1\n".format(name) if enabled else "/* #undef {} */\n".format(name)
        )
        for name, enabled in macros.items()
    }

def libtorch_generated_headers(name):
    """Generates the configure_file() headers of torch/headeronly.

    Args:
        name: Name of a filegroup holding all generated headers.
    """
    expand_template(
        name = name + "_cmake_macros",
        out = "torch/headeronly/macros/cmake_macros.h",
        substitutions = _cmakedefine_substitutions(_CMAKE_MACROS),
        template = "torch/headeronly/macros/cmake_macros.h.in",
    )

    expand_template(
        name = name + "_version",
        out = "torch/headeronly/version.h",
        substitutions = {
            "@TORCH_VERSION_MAJOR@": TORCH_VERSION_MAJOR,
            "@TORCH_VERSION_MINOR@": TORCH_VERSION_MINOR,
            "@TORCH_VERSION_PATCH@": TORCH_VERSION_PATCH,
        },
        template = "torch/headeronly/version.h.in",
    )

    native.filegroup(
        name = name,
        srcs = [
            name + "_cmake_macros",
            name + "_version",
        ],
    )

def _windows_def_file_impl(ctx):
    # Only the library's own objects: the symbols of its dependencies (and of
    # the statically linked C++ runtime) stay private to the DLL.
    objects = []
    for linker_input in ctx.attr.library[CcInfo].linking_context.linker_inputs.to_list():
        if linker_input.owner != ctx.attr.library.label:
            continue
        for library in linker_input.libraries:
            objects.extend(library.pic_objects or library.objects)

    unfiltered_def_file = ctx.actions.declare_file(ctx.label.name + ".unfiltered.def")
    def_file = ctx.actions.declare_file(ctx.label.name + ".def")
    args = ctx.actions.args()
    args.add(unfiltered_def_file)
    args.add(ctx.attr.dll_name)
    objects_args = ctx.actions.args()
    objects_args.use_param_file("@%s", use_always = True)
    objects_args.set_param_file_format("shell")
    objects_args.add_all(objects)

    llvm_nm = ctx.executable._llvm_nm
    ctx.actions.run(
        executable = ctx.executable._def_file_generator,
        arguments = [args, objects_args],
        env = {"LLVM_NM": llvm_nm.path},
        inputs = objects,
        tools = [llvm_nm],
        outputs = [unfiltered_def_file],
        mnemonic = "DefFile",
        progress_message = "Generating DEF file %{output}",
    )
    ctx.actions.run(
        executable = ctx.executable._def_filter,
        arguments = [unfiltered_def_file.path, def_file.path],
        inputs = [unfiltered_def_file],
        outputs = [def_file],
        mnemonic = "DefFilter",
        progress_message = "Removing C++ standard library exports from %{output}",
    )
    return [DefaultInfo(files = depset([def_file]))]

windows_def_file = rule(
    doc = """Generates a DEF file exporting every symbol of a cc_library's objects.

    For the `win_def_file` of a cc_shared_library on Windows. rules_cc only
    generates DEF files (windows_export_all_symbols) for the DLLs of
    cc_library, and without one a cc_shared_library exports nothing unless its
    sources use __declspec(dllexport). Uses the same llvm-nm based generator
    as the MSVC flavor of the @llvm toolchain, which the MinGW flavor lacks,
    then drops the symbols of the C++ standard library (see
    tools/def_filter.c).
    """,
    implementation = _windows_def_file_impl,
    attrs = {
        "dll_name": attr.string(mandatory = True, doc = "File name of the DLL."),
        "library": attr.label(mandatory = True, providers = [CcInfo], doc = "The cc_library to export."),
        "_def_filter": attr.label(
            default = "//tools:def_filter",
            executable = True,
            cfg = "exec",
        ),
        "_def_file_generator": attr.label(
            default = "@llvm//tools:def_file_generator",
            executable = True,
            cfg = "exec",
        ),
        "_llvm_nm": attr.label(
            default = "@llvm//tools:llvm-nm",
            allow_single_file = True,
            executable = True,
            cfg = "exec",
        ),
    },
)

def _cc_header_copy_impl(ctx):
    matches = [
        hdr
        for hdr in ctx.attr.dep[CcInfo].compilation_context.headers.to_list()
        if hdr.basename == ctx.attr.header
    ]
    if len(matches) != 1:
        fail("expected exactly one header named {} in {}, found {}".format(
            ctx.attr.header,
            ctx.attr.dep.label,
            [hdr.path for hdr in matches],
        ))
    ctx.actions.symlink(output = ctx.outputs.out, target_file = matches[0])
    return [DefaultInfo(files = depset([ctx.outputs.out]))]

cc_header_copy = rule(
    doc = """Copies a header out of a cc_library's public headers.

    Unlike copy_file on the header's source file target, this only relies on
    the cc_library's visibility: source files of another repository are
    private unless it exports them (exports_files), which Bazel 10 enforces
    by default (--incompatible_no_implicit_file_export).
    """,
    implementation = _cc_header_copy_impl,
    attrs = {
        "dep": attr.label(mandatory = True, providers = [CcInfo], doc = "The cc_library."),
        "header": attr.string(mandatory = True, doc = "Basename of the header to copy."),
        "out": attr.output(mandatory = True, doc = "The copy."),
    },
)

# aten/src/ATen/Config.h.in. Every backend library that is not built yet is
# off: no BLAS/LAPACK (ATen's own GEMM fallback, and linear algebra ops raise
# at runtime), no MKL/oneDNN/NNPACK/KleidiAI, and ATen's native thread pool
# instead of OpenMP. pocketfft provides the FFTs.
_ATEN_CONFIG = {
    "@AT_BLAS_F2C@": "0",
    "@AT_BLAS_USE_CBLAS_DOT@": "0",
    "@AT_BUILD_WITH_BLAS@": "0",
    "@AT_BUILD_WITH_LAPACK@": "0",
    "@AT_KLEIDIAI_ENABLED@": "0",
    "@AT_MKLDNN_ACL_ENABLED@": "0",
    "@AT_MKLDNN_ENABLED@": "0",
    "@AT_MKL_ENABLED@": "0",
    "@AT_MKL_SEQUENTIAL@": "0",
    "@AT_NNPACK_ENABLED@": "0",
    "@AT_PARALLEL_NATIVE@": "1",
    "@AT_PARALLEL_OPENMP@": "0",
    "@AT_POCKETFFT_ENABLED@": "1",
    "@AT_USE_EIGEN_SPARSE@": "0",
    "@CAFFE2_STATIC_LINK_CUDA_INT@": "0",
}

# caffe2/core/macros.h.in.
_CAFFE2_MACROS = {
    "CAFFE2_BUILD_SHARED_LIBS": False,
    "CAFFE2_FORCE_FALLBACK_CUDA_MPI": False,
    "CAFFE2_HAS_MKL_DNN": False,
    "CAFFE2_HAS_MKL_SGEMM_PACK": False,
    "CAFFE2_PERF_WITH_AVX": False,
    "CAFFE2_PERF_WITH_AVX2": False,
    "CAFFE2_THREADPOOL_MAIN_IMBALANCE": False,
    "CAFFE2_THREADPOOL_STATS": False,
    "CAFFE2_USE_ACCELERATE": False,
    "CAFFE2_USE_CUDNN": False,
    "CAFFE2_USE_EIGEN_FOR_BLAS": False,
    "CAFFE2_USE_FBCODE": False,
    "CAFFE2_USE_GOOGLE_GLOG": True,
    "CAFFE2_USE_ITT": False,
    "CAFFE2_USE_LITE_PROTO": False,
    "CAFFE2_USE_MKL": False,
    "CAFFE2_USE_NVTX": False,
    "EIGEN_MPL2_ONLY": True,
    "USE_MKLDNN": False,
}

# The ${...} values in caffe2/core/macros.h.in's CAFFE2_BUILD_STRINGS
# (reported by torch::show_config()).
_CAFFE2_BUILD_STRINGS = {
    "${BLAS_INFO}": "",
    "${CMAKE_BUILD_TYPE}": "",
    "${CMAKE_CUDA_FLAGS}": "",
    "${CMAKE_CXX_COMPILER}": "clang++ (@llvm)",
    "${CMAKE_CXX_FLAGS}": "",
    "${COMMIT_SHA}": "",
    "${CUDA_VERSION}": "",
    "${CUDNN_VERSION}": "",
    "${LAPACK_INFO}": "",
    "${ROCM_VERSION}": "",
    "${SYCL_COMPILER_VERSION}": "",
    "${TORCH_VERSION}": "{}.{}.{}".format(TORCH_VERSION_MAJOR, TORCH_VERSION_MINOR, TORCH_VERSION_PATCH),
    "${USE_CUDA}": "OFF",
    "${USE_CUDNN}": "OFF",
    "${USE_CUSPARSELT}": "OFF",
    "${USE_GFLAGS}": "ON",
    "${USE_GLOG}": "ON",
    "${USE_GLOO}": "OFF",
    "${USE_HIPSPARSELT}": "OFF",
    "${USE_MKLDNN}": "OFF",
    "${USE_MPI}": "OFF",
    "${USE_NCCL}": "OFF",
    "${USE_NNPACK}": "OFF",
    "${USE_OPENMP}": "OFF",
    "${USE_ROCM}": "OFF",
    "${USE_ROCM_KERNEL_ASSERT}": "OFF",
    "${USE_XCCL}": "OFF",
    "${USE_XPU}": "OFF",
}

def libtorch_cpu_config_headers(name):
    """Generates aten/src/ATen/Config.h and caffe2/core/macros.h.

    Args:
        name: Name of a filegroup holding the generated headers.
    """
    expand_template(
        name = name + "_aten_config",
        out = "aten/src/ATen/Config.h",
        substitutions = _ATEN_CONFIG,
        template = "aten/src/ATen/Config.h.in",
    )

    expand_template(
        name = name + "_caffe2_macros",
        out = "caffe2/core/macros.h",
        # On x86_64, caffe2/perfkernels has AVX and AVX2 variants, and ITT
        # (Intel VTune) instrumentation is built.
        substitutions = select({
            "@platforms//cpu:x86_64": _cmakedefine_substitutions(_CAFFE2_MACROS | {
                "CAFFE2_PERF_WITH_AVX": True,
                "CAFFE2_PERF_WITH_AVX2": True,
                "CAFFE2_USE_ITT": True,
            }) | _CAFFE2_BUILD_STRINGS,
            "//conditions:default": _cmakedefine_substitutions(_CAFFE2_MACROS) | _CAFFE2_BUILD_STRINGS,
        }),
        template = "caffe2/core/macros.h.in",
    )

    native.filegroup(
        name = name,
        srcs = [
            name + "_aten_config",
            name + "_caffe2_macros",
        ],
    )

# aten/src/ATen/cuda/CUDAConfig.h.in. No cuDNN, cuSPARSELt or MAGMA: SDPA,
# convolutions and linear algebra use ATen's own CUDA kernels, CUTLASS,
# cuBLAS(Lt) and cuSOLVER.
_ATEN_CUDA_CONFIG = {
    "@AT_CUDNN_ENABLED@": "0",
    "@AT_CUSPARSELT_ENABLED@": "0",
    "@AT_HIPSPARSELT_ENABLED@": "0",
    "@AT_MAGMA_ENABLED@": "0",
    "@AT_ROCM_ENABLED@": "0",
    "@NVCC_FLAGS_EXTRA@": "",
}

def libtorch_cuda_config_headers(name):
    """Generates c10/cuda/impl/cuda_cmake_macros.h and aten/src/ATen/cuda/CUDAConfig.h.

    Args:
        name: Name of a filegroup holding the generated headers.
    """

    # Static c10_cuda, like c10 (see _CMAKE_MACROS).
    expand_template(
        name = name + "_c10_cuda_macros",
        out = "c10/cuda/impl/cuda_cmake_macros.h",
        substitutions = _cmakedefine_substitutions({"C10_CUDA_BUILD_SHARED_LIBS": False}),
        template = "c10/cuda/impl/cuda_cmake_macros.h.in",
    )

    expand_template(
        name = name + "_aten_cuda_config",
        out = "aten/src/ATen/cuda/CUDAConfig.h",
        substitutions = _ATEN_CUDA_CONFIG,
        template = "aten/src/ATen/cuda/CUDAConfig.h.in",
    )

    native.filegroup(
        name = name,
        srcs = [
            name + "_aten_cuda_config",
            name + "_c10_cuda_macros",
        ],
    )

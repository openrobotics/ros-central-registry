"""Sources of @libtorch//:torch_cpu, following upstream's CMake build.

Upstream's CMake reads most libtorch file lists from build_variables.bzl
(append_filelist() in cmake/Codegen.cmake), and globs ATen's directories
(aten/src/ATen/CMakeLists.txt). This file does the same.
"""

load(
    "//:build_variables.bzl",
    "jit_core_sources",
    "lazy_tensor_ts_sources",
    "libtorch_cmake_sources",
    "libtorch_cuda_core_sources",
    "libtorch_distributed_base_sources",
    "libtorch_distributed_extra_sources",
    "torch_cpp_srcs",
)

# aten/src/ATen/CMakeLists.txt: all_cpu_cpp (without the generated sources and
# the per-CPU-capability kernels, see ATEN_CPU_KERNEL_GLOBS).
ATEN_CPU_GLOBS = [
    "aten/src/ATen/*.cpp",
    "aten/src/ATen/accelerator/*.cpp",
    "aten/src/ATen/core/**/*.cpp",
    "aten/src/ATen/cpu/*.cpp",
    "aten/src/ATen/detail/*.cpp",
    "aten/src/ATen/functorch/*.cpp",
    "aten/src/ATen/metal/*.cpp",
    "aten/src/ATen/native/*.cpp",
    "aten/src/ATen/native/ao_sparse/*.cpp",
    "aten/src/ATen/native/ao_sparse/cpu/*.cpp",
    "aten/src/ATen/native/ao_sparse/quantized/*.cpp",
    "aten/src/ATen/native/ao_sparse/quantized/cpu/*.cpp",
    "aten/src/ATen/native/mkl/*.cpp",
    "aten/src/ATen/native/mkldnn/*.cpp",
    "aten/src/ATen/native/nested/*.cpp",
    "aten/src/ATen/native/quantized/*.cpp",
    "aten/src/ATen/native/quantized/cpu/*.cpp",
    "aten/src/ATen/native/sparse/*.cpp",
    "aten/src/ATen/native/transformers/*.cpp",
    "aten/src/ATen/native/utils/*.cpp",
    # Always built: without USE_XNNPACK, Shim.cpp provides stubs.
    "aten/src/ATen/native/xnnpack/*.cpp",
    "aten/src/ATen/nnapi/*.cpp",
    "aten/src/ATen/quantized/**/*.cpp",
    "aten/src/ATen/vulkan/*.cpp",
]

ATEN_CPU_EXCLUDES = [
    "aten/src/ATen/core/**/*_test.cpp",
    "aten/src/ATen/quantized/**/*_test.cpp",
]

# cmake/Codegen.cmake: cpu_kernel_cpp_in, compiled once per CPU capability.
ATEN_CPU_KERNEL_GLOBS = [
    "aten/src/ATen/native/cpu/*.cpp",
    "aten/src/ATen/native/quantized/cpu/kernels/*.cpp",
]

# caffe2/CMakeLists.txt: the TORCH_SRCS that are not in build_variables.bzl.
_TORCH_EXTRA_SOURCES = [
    # MOBILE_SRCS (the lite interpreter, built unless INTERN_DISABLE_MOBILE_INTERP).
    "torch/csrc/jit/mobile/compatibility/model_compatibility.cpp",
    "torch/csrc/jit/mobile/flatbuffer_loader.cpp",
    "torch/csrc/jit/mobile/function.cpp",
    "torch/csrc/jit/mobile/import.cpp",
    "torch/csrc/jit/mobile/import_data.cpp",
    "torch/csrc/jit/mobile/interpreter.cpp",
    "torch/csrc/jit/mobile/module.cpp",
    "torch/csrc/jit/mobile/observer.cpp",
    "torch/csrc/jit/mobile/parse_bytecode.cpp",
    "torch/csrc/jit/mobile/parse_operators.cpp",
    "torch/csrc/jit/mobile/quantization.cpp",
    "torch/csrc/jit/mobile/train/export_data.cpp",
    "torch/csrc/jit/mobile/train/optim/sgd.cpp",
    "torch/csrc/jit/mobile/train/random.cpp",
    "torch/csrc/jit/mobile/train/sequential.cpp",
    "torch/csrc/jit/mobile/upgrader_mobile.cpp",
    "torch/csrc/jit/serialization/flatbuffer_serializer.cpp",
    # Always built, like the generated Functions.cpp.
    "torch/csrc/autograd/FunctionsManual.cpp",
    "torch/csrc/utils/out_types.cpp",
    # Unless INTERN_DISABLE_AUTOGRAD.
    "torch/csrc/autograd/TraceTypeManual.cpp",
    "torch/csrc/autograd/VariableTypeManual.cpp",
    # Unless INTERN_BUILD_MOBILE. torch/csrc/jit/serialization/export.cpp and
    # onnx.cpp (ONNX export, used only by the Python bindings) are left out:
    # they need the onnx and protobuf libraries. export.cpp's one other
    # function is in bazel/src/export_without_onnx.cpp.
    "torch/csrc/api/src/jit.cpp",
    "torch/csrc/jit/api/module_save.cpp",
    "torch/csrc/jit/codegen/fuser/cpu/fused_kernel.cpp",
    "torch/csrc/jit/mobile/compatibility/backport.cpp",
    "torch/csrc/jit/mobile/compatibility/backport_manager.cpp",
    "torch/csrc/jit/serialization/export_bytecode.cpp",
    "torch/csrc/jit/serialization/export_module.cpp",
    "torch/csrc/utils/byte_order.cpp",
]

# caffe2/core, caffe2/perfkernels (the generic sources; the per-ISA ones are
# *_avx*.cc and *_sve.cc) and caffe2/serialize (whose miniz is the
# //third_party/miniz-3.0.2 target).
_CAFFE2_SOURCES = [
    "caffe2/core/common.cc",
    "caffe2/perfkernels/embedding_lookup_idx.cc",
    "caffe2/serialize/crc.cc",
    "caffe2/serialize/file_adapter.cc",
    "caffe2/serialize/inline_container.cc",
    "caffe2/serialize/istream_adapter.cc",
    "caffe2/serialize/read_adapter_interface.cc",
]

# The non-generated libtorch sources of torch_cpu, without duplicates (some
# files are in several of upstream's lists).
TORCH_CPU_SOURCES = {
    source: None
    for source in (
        # aten/src/ATen/CMakeLists.txt appends these to ATen's core sources.
        jit_core_sources +
        libtorch_cmake_sources +
        lazy_tensor_ts_sources +
        torch_cpp_srcs +
        _TORCH_EXTRA_SOURCES +
        _CAFFE2_SOURCES +
        ["//bazel:src/export_without_onnx.cpp"]
    )
}.keys()

# Headers of torch_cpu (and of everything built on it).
TORCH_HEADER_GLOBS = [
    "aten/src/ATen/**/*.cuh",
    "aten/src/ATen/**/*.h",
    "aten/src/ATen/**/*.hpp",
    "caffe2/**/*.h",
    "torch/*.h",
    "torch/csrc/**/*.cuh",
    "torch/csrc/**/*.h",
    "torch/csrc/**/*.hpp",
]

# caffe2/CMakeLists.txt: with USE_ITT (Intel x86 CPUs only, like upstream).
TORCH_CPU_ITT_SOURCES = [
    "torch/csrc/itt_wrapper.cpp",
    "torch/csrc/profiler/stubs/itt.cpp",
]

# c10/cuda/CMakeLists.txt.
C10_CUDA_SOURCES = [
    "c10/cuda/CUDAAllocatorConfig.cpp",
    "c10/cuda/CUDACachingAllocator.cpp",
    "c10/cuda/CUDADeviceAssertionHost.cpp",
    "c10/cuda/CUDAException.cpp",
    "c10/cuda/CUDAFunctions.cpp",
    "c10/cuda/CUDAMallocAsyncAllocator.cpp",
    "c10/cuda/CUDAMiscFunctions.cpp",
    "c10/cuda/CUDAStream.cpp",
    "c10/cuda/PeerToPeerAccess.cpp",
    "c10/cuda/driver_api.cpp",
    "c10/cuda/impl/CUDAGuardImpl.cpp",
    "c10/cuda/impl/CUDATest.cpp",
]

# aten/src/ATen/CMakeLists.txt: ATen_CUDA_CU_SRCS, the device code (including
# the CUTLASS-based memory-efficient attention, USE_MEM_EFF_ATTENTION).
# FlashAttention (USE_FLASH_ATTENTION) needs the third_party/flash-attention
# submodule and is not built.
ATEN_CUDA_KERNEL_GLOBS = [
    "aten/src/ATen/cuda/*.cu",
    "aten/src/ATen/cuda/detail/*.cu",
    "aten/src/ATen/cuda/tunable/*.cu",
    "aten/src/ATen/native/cuda/*.cu",
    "aten/src/ATen/native/nested/cuda/*.cu",
    "aten/src/ATen/native/quantized/cuda/*.cu",
    "aten/src/ATen/native/sparse/cuda/*.cu",
    "aten/src/ATen/native/transformers/cuda/*.cu",
    "aten/src/ATen/native/transformers/cuda/mem_eff_attention/*.cu",
    "aten/src/ATen/native/transformers/cuda/mem_eff_attention/kernels/*.cu",
]

# ATen_CUDA_CPP_SRCS (and the .cpp files of ATen_CUDA_CU_SRCS), without the
# NVRTC stub, which upstream builds into its own library (caffe2_nvrtc).
ATEN_CUDA_GLOBS = [
    "aten/src/ATen/cuda/*.cpp",
    "aten/src/ATen/cuda/detail/*.cpp",
    "aten/src/ATen/cuda/tunable/*.cpp",
    "aten/src/ATen/native/cuda/*.cpp",
    "aten/src/ATen/native/cuda/linalg/*.cpp",
    # Always built: without cuDNN (AT_CUDNN_ENABLED() is 0) or ROCm they
    # define stubs.
    "aten/src/ATen/native/cudnn/*.cpp",
    "aten/src/ATen/native/miopen/*.cpp",
    "aten/src/ATen/native/quantized/cudnn/*.cpp",
    "aten/src/ATen/native/nested/cuda/*.cpp",
    "aten/src/ATen/native/quantized/cuda/*.cpp",
    "aten/src/ATen/native/sparse/cuda/*.cpp",
    "aten/src/ATen/native/transformers/cuda/*.cpp",
    "aten/src/ATen/native/transformers/cuda/mem_eff_attention/*.cpp",
]

# caffe2/CMakeLists.txt: Caffe2_GPU_SRCS that are not in ATen.
TORCH_CUDA_SOURCES = libtorch_cuda_core_sources

# caffe2/CMakeLists.txt: with USE_DISTRIBUTED, c10d (the process groups, the
# stores and the control plane), and (as upstream except on Windows) the
# "extra" sources: c10d's HashStore, distributed autograd and RPC (whose
# TensorPipe agent is not built, as without USE_TENSORPIPE).
TORCH_DISTRIBUTED_SOURCES = libtorch_distributed_base_sources

TORCH_DISTRIBUTED_EXTRA_SOURCES = libtorch_distributed_extra_sources

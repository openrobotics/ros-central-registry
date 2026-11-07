"""Hipifies PyTorch's CUDA backend for ROCm, as tools/amd_build/build_amd.py
does in place, into a header tree and three source trees for Bazel (see
libtorch_hip.bzl).

Run from the root of the PyTorch source tree. The CUDA sources are copied to a
temporary project, hipified there with build_amd.py's settings, and every file
that hipify created or changed (and the few hand-written HIP files) is sorted
into:

  --out-headers every hipified header (and the configured HIPConfig.h,
                CUDAConfig.h and hip_cmake_macros.h), to take precedence over
                the original ones (-I<tree>)
  --out-c10     c10/hip's sources (c10_hip)
  --out-host    the host sources of torch_hip: ATen's hip/ .cpp files
                (aten/src/ATen/CMakeLists.txt's all_hip_cpp) and the hipified
                --torch-source files (caffe2/CMakeLists.txt's Caffe2_HIP_SRCS)
  --out-device  the device sources of torch_hip (ATen_HIP_SRCS's .hip files),
                as <name>.hip.cc for Bazel's C++ rules

The source trees hold sources only (Bazel's C++ rules reject other files, e.g.
.cuh headers, in a source directory), so the headers that sources include
relative to their own directory are found with -iquote<header tree>/<dir>.
"""

import argparse
import fnmatch
import hashlib
import os
import shutil
import sys
import tempfile

# The CUDA backend, as build_amd.py's `includes` (without what Bazel does not
# build: caffe2, tests, third_party and the Python bindings).
_HIPIFY_INCLUDES = [
    "c10/cuda/*",
    "aten/src/ATen/cuda/*",
    "aten/src/ATen/native/cuda/*",
    "aten/src/ATen/native/cudnn/*",
    "aten/src/ATen/native/quantized/cudnn/*",
    "aten/src/ATen/native/nested/cuda/*",
    "aten/src/ATen/native/sparse/cuda/*",
    "aten/src/ATen/native/quantized/cuda/*",
    "aten/src/ATen/native/transformers/cuda/attention_backward.cu",
    "aten/src/ATen/native/transformers/cuda/attention.cu",
    "aten/src/ATen/native/transformers/cuda/sdp_utils.cpp",
    "aten/src/ATen/native/transformers/cuda/sdp_utils.h",
    "aten/src/ATen/native/transformers/cuda/mem_eff_attention/debug_utils.h",
    "aten/src/ATen/native/transformers/cuda/mem_eff_attention/gemm_kernel_utils.h",
    "aten/src/ATen/native/transformers/cuda/mem_eff_attention/pytorch_utils.h",
    "torch/*",
]

# build_amd.py's `ignores`.
_HIPIFY_IGNORES = [
    "*/hip/*",
    "aten/src/ATen/core/*",
    "aten/src/ATen/cuda/CUDAConfig.h",
    "torch/csrc/jit/codegen/fuser/cuda/resource_strings.h",
    "torch/csrc/jit/tensorexpr/ir_printer.cpp",
    "torch/csrc/jit/ir/ir.h",
]

# The directories copied into the temporary project: the CUDA backend and the
# few hand-written HIP files (e.g. hip/impl/*MasqueradingAsCUDA*).
_INPUT_DIRS = [
    "aten/src/ATen/cuda",
    "aten/src/ATen/hip",
    "aten/src/ATen/native/cuda",
    "aten/src/ATen/native/cudnn",
    "aten/src/ATen/native/hip",
    "aten/src/ATen/native/nested/cuda",
    "aten/src/ATen/native/quantized/cuda",
    "aten/src/ATen/native/quantized/cudnn",
    "aten/src/ATen/native/sparse/cuda",
    "aten/src/ATen/native/transformers/cuda",
    "aten/src/ATen/native/transformers/hip",
    "c10/cuda",
    "c10/hip",
    "torch/csrc",
    "torch/headeronly",
]

_HEADER_EXTENSIONS = (".h", ".hpp", ".cuh", ".inl")

# aten/src/ATen/CMakeLists.txt: c10_hip's, and torch_hip's host and device
# sources (without the CK GEMM/SDPA and FlashAttention kernels, see
# libtorch_hip.bzl).
_C10_SOURCES = ["c10/hip/*.cpp", "c10/hip/impl/*.cpp"]

_HOST_SOURCES = [
    "aten/src/ATen/hip/*.cpp",
    "aten/src/ATen/hip/detail/*.cpp",
    "aten/src/ATen/hip/impl/*.cpp",
    "aten/src/ATen/hip/tunable/*.cpp",
    "aten/src/ATen/native/hip/*.cpp",
    "aten/src/ATen/native/hip/linalg/*.cpp",
    "aten/src/ATen/native/cudnn/hip/*.cpp",
    "aten/src/ATen/native/nested/hip/*.cpp",
    "aten/src/ATen/native/sparse/hip/*.cpp",
    "aten/src/ATen/native/quantized/hip/*.cpp",
    "aten/src/ATen/native/transformers/hip/*.cpp",
    "aten/src/ATen/native/quantized/cudnn/hip/*.cpp",
]

_HOST_EXCLUDES = [
    # The NVRTC stub, which upstream builds into its own library.
    "aten/src/ATen/hip/detail/LazyNVRTC.cpp",
]

_DEVICE_SOURCES = [
    "aten/src/ATen/hip/*.hip",
    "aten/src/ATen/hip/detail/*.hip",
    "aten/src/ATen/hip/impl/*.hip",
    "aten/src/ATen/hip/tunable/*.hip",
    "aten/src/ATen/native/hip/*.hip",
    "aten/src/ATen/native/nested/hip/*.hip",
    "aten/src/ATen/native/sparse/hip/*.hip",
    "aten/src/ATen/native/quantized/hip/*.hip",
    "aten/src/ATen/native/transformers/hip/*.hip",
]

_DEVICE_EXCLUDES = [
    # Composable Kernel GEMMs (USE_ROCM_CK_GEMM).
    "aten/src/ATen/native/hip/ck*.hip",
]


def _matches(path, patterns):
    # fnmatch's * also matches "/": compare directories exactly.
    return any(
        os.path.dirname(path) == os.path.dirname(p) and fnmatch.fnmatch(os.path.basename(path), os.path.basename(p))
        for p in patterns
    )


def _digest(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _snapshot(root):
    files = {}
    for directory, _, names in os.walk(root):
        for name in names:
            path = os.path.join(directory, name)
            files[os.path.relpath(path, root)] = _digest(path)
    return files


def _configure(template, out, substitutions):
    with open(template) as f:
        content = f.read()
    for key, value in substitutions.items():
        content = content.replace(key, value)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument("--out-headers", required = True)
    parser.add_argument("--out-c10", required = True)
    parser.add_argument("--out-host", required = True)
    parser.add_argument("--out-device", required = True)
    parser.add_argument("--torch-source", action = "append", default = [])
    args = parser.parse_args()

    sys.path.insert(0, os.path.join(os.getcwd(), "torch", "utils"))
    from hipify import hipify_python  # type: ignore[import]

    project = tempfile.mkdtemp(prefix = "libtorch_hipify_")
    for directory in _INPUT_DIRS:
        # Only the action's inputs exist (e.g. no c10/hip/CMakeLists.txt).
        if os.path.isdir(directory):
            shutil.copytree(directory, os.path.join(project, directory))
    for template in ["aten/src/ATen/cuda/CUDAConfig.h.in", "c10/cuda/impl/cuda_cmake_macros.h.in"]:
        shutil.copy(template, os.path.join(project, template))
    before = _snapshot(project)

    hipify_python.hipify(
        project_directory = project,
        output_directory = project,
        includes = [os.path.join(project, p) for p in _HIPIFY_INCLUDES],
        ignores = [os.path.join(project, p) for p in _HIPIFY_IGNORES],
        show_progress = False,
        hip_clang_launch = True,
    )
    after = _snapshot(project)
    hipified = sorted(path for path, digest in after.items() if before.get(path) != digest)

    # aten/src/ATen/CMakeLists.txt and c10/hip/CMakeLists.txt's
    # configure_file()s: ROCm without hipSPARSELt and MAGMA, and a static
    # c10_hip. CUDAConfig.h is configured likewise (ATen/jit_macros.h).
    config = {
        "@AT_CUDNN_ENABLED@": "0",
        "@AT_CUSPARSELT_ENABLED@": "0",
        "@AT_HIPSPARSELT_ENABLED@": "0",
        "@AT_MAGMA_ENABLED@": "0",
        "@AT_ROCM_ENABLED@": "1",
        "@NVCC_FLAGS_EXTRA@": "",
    }
    generated = {
        "aten/src/ATen/hip/HIPConfig.h": ("aten/src/ATen/hip/HIPConfig.h.in", config),
        "aten/src/ATen/cuda/CUDAConfig.h": ("aten/src/ATen/cuda/CUDAConfig.h.in", config),
        "c10/hip/impl/hip_cmake_macros.h": (
            "c10/hip/impl/hip_cmake_macros.h.in",
            {"#cmakedefine C10_CUDA_BUILD_SHARED_LIBS": "/* #undef C10_CUDA_BUILD_SHARED_LIBS */"},
        ),
    }
    for out, (template, substitutions) in generated.items():
        _configure(os.path.join(project, template), os.path.join(project, out), substitutions)
        hipified.append(out)

    # Every header that hipify wrote, and every file of a hip/ directory.
    files = sorted(set(hipified) | {p for p in after if "/hip/" in p})
    headers = [p for p in files if p.endswith(_HEADER_EXTENSIONS)]
    trees = {
        args.out_headers: headers,
        args.out_c10: [p for p in files if _matches(p, _C10_SOURCES)],
        args.out_host: [p for p in files if _matches(p, _HOST_SOURCES) and p not in _HOST_EXCLUDES] + args.torch_source,
        args.out_device: [p for p in files if _matches(p, _DEVICE_SOURCES) and not _matches(p, _DEVICE_EXCLUDES)],
    }
    for tree, paths in trees.items():
        os.makedirs(tree, exist_ok = True)
        for path in paths:
            out = os.path.join(tree, path + (".cc" if path.endswith(".hip") else ""))
            os.makedirs(os.path.dirname(out), exist_ok = True)
            shutil.copy(os.path.join(project, path), out)
    shutil.rmtree(project)


if __name__ == "__main__":
    main()

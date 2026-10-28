"""Build-time code generation for @libtorch.

Runs upstream's generators as Bazel actions on the exec platform, with the
hermetic Python toolchain:

- torchgen.gen (ATen operators, dispatcher registrations, AOTInductor shims),
- tools/setup_helpers/generate_code.py (autograd, TorchScript tracing and the
  lazy tensor TorchScript backend).

Nothing generated is checked in. Bazel needs the outputs up front, so they are
listed below, except for the ~7,000 per-operator headers (aten/src/ATen/ops,
upstream's AT_PER_OPERATOR_HEADERS mode), whose names depend on
native_functions.yaml: they are one directory output. `python -m torchgen.gen
... -o <file>` prints the list that torchgen writes, for when it changes.
"""

# torchgen.gen outputs, relative to aten/src/ATen.
ATEN_GENERATED_HEADERS = [
    "CPUFunctions.h",
    "CPUFunctions_inl.h",
    "CompositeExplicitAutogradFunctions.h",
    "CompositeExplicitAutogradFunctions_inl.h",
    "CompositeExplicitAutogradNonFunctionalFunctions.h",
    "CompositeExplicitAutogradNonFunctionalFunctions_inl.h",
    "CompositeImplicitAutogradFunctions.h",
    "CompositeImplicitAutogradFunctions_inl.h",
    "CompositeImplicitAutogradNestedTensorFunctions.h",
    "CompositeImplicitAutogradNestedTensorFunctions_inl.h",
    "FunctionalInverses.h",
    "Functions.h",
    "MetaFunctions.h",
    "MetaFunctions_inl.h",
    "MethodOperators.h",
    "NativeFunctions.h",
    "NativeMetaFunctions.h",
    "Operators.h",
    "RedispatchFunctions.h",
    "RegistrationDeclarations.h",
    "ViewMetaClasses.h",
    "VmapGeneratedPlumbing.h",
    "core/TensorBody.h",
    "core/aten_interned_strings.h",
]

ATEN_GENERATED_SOURCES = [
    "CompositeViewCopyKernels.cpp",
    "Functions.cpp",
    "Operators_0.cpp",
    "Operators_1.cpp",
    "Operators_2.cpp",
    "Operators_3.cpp",
    "Operators_4.cpp",
    "RegisterBackendSelect.cpp",
    "RegisterCPU_0.cpp",
    "RegisterCPU_1.cpp",
    "RegisterCPU_2.cpp",
    "RegisterCPU_3.cpp",
    "RegisterCompositeExplicitAutogradNonFunctional_0.cpp",
    "RegisterCompositeExplicitAutograd_0.cpp",
    "RegisterCompositeImplicitAutogradNestedTensor_0.cpp",
    "RegisterCompositeImplicitAutograd_0.cpp",
    "RegisterFunctionalization_0.cpp",
    "RegisterFunctionalization_1.cpp",
    "RegisterFunctionalization_2.cpp",
    "RegisterFunctionalization_3.cpp",
    "RegisterMeta_0.cpp",
    "RegisterMkldnnCPU_0.cpp",
    "RegisterNestedTensorCPU_0.cpp",
    "RegisterNestedTensorHPU_0.cpp",
    "RegisterNestedTensorMeta_0.cpp",
    "RegisterQuantizedCPU_0.cpp",
    "RegisterQuantizedMeta_0.cpp",
    "RegisterSchema.cpp",
    "RegisterSparseCPU_0.cpp",
    "RegisterSparseCsrCPU_0.cpp",
    "RegisterSparseCsrMeta_0.cpp",
    "RegisterSparseMeta_0.cpp",
    "RegisterZeroTensor_0.cpp",
    "UfuncCPU_add.cpp",
    "ViewMetaClasses.cpp",
    "core/ATenOpList.cpp",
    "core/TensorMethods.cpp",
]

# Compiled once per CPU capability, like aten/src/ATen/native/cpu/*.cpp.
ATEN_GENERATED_CPU_KERNEL_SOURCES = [
    "UfuncCPUKernel_add.cpp",
]

ATEN_GENERATED_CUDA_HEADERS = [
    "CUDAFunctions.h",
    "CUDAFunctions_inl.h",
]

ATEN_GENERATED_CUDA_SOURCES = [
    "RegisterCUDA_0.cpp",
    "RegisterNestedTensorCUDA_0.cpp",
    "RegisterQuantizedCUDA_0.cpp",
    "RegisterSparseCUDA_0.cpp",
    "RegisterSparseCsrCUDA_0.cpp",
]

ATEN_GENERATED_CUDA_KERNEL_SOURCES = [
    "UfuncCUDA_add.cu",
]

# With --mps (on :mps_enabled targets only: it also changes the declarations
# in NativeFunctions.h and RegistrationDeclarations.h).
ATEN_GENERATED_MPS_HEADERS = [
    "MPSFunctions.h",
    "MPSFunctions_inl.h",
    "SparseCsrMPSFunctions.h",
    "SparseCsrMPSFunctions_inl.h",
    "SparseMPSFunctions.h",
    "SparseMPSFunctions_inl.h",
]

ATEN_GENERATED_MPS_SOURCES = [
    "RegisterMPS_0.cpp",
    "RegisterSparseCsrMPS_0.cpp",
    "RegisterSparseMPS_0.cpp",
]

AOTI_GENERATED_MPS_SOURCES = [
    "torch/csrc/inductor/aoti_torch/generated/c_shim_mps.cpp",
]

# torchgen.gen outputs elsewhere in the tree.
TORCHGEN_OTHER_HEADERS = [
    "torch/headeronly/core/enum_tag.h",
]

AOTI_GENERATED_SOURCES = [
    "torch/csrc/inductor/aoti_torch/generated/c_shim_aten.cpp",
    "torch/csrc/inductor/aoti_torch/generated/c_shim_cpu.cpp",
]

AOTI_GENERATED_CUDA_SOURCES = [
    "torch/csrc/inductor/aoti_torch/generated/c_shim_cuda.cpp",
]

# tools/setup_helpers/generate_code.py --subset libtorch --gen-lazy-ts-backend
# outputs.
AUTOGRAD_GENERATED_HEADERS = [
    "torch/csrc/autograd/generated/Functions.h",
    "torch/csrc/autograd/generated/VariableType.h",
    "torch/csrc/autograd/generated/ViewFuncs.h",
    "torch/csrc/autograd/generated/variable_factories.h",
    "torch/csrc/lazy/generated/LazyIr.h",
    "torch/csrc/lazy/generated/LazyNativeFunctions.h",
    "torch/csrc/lazy/generated/LazyNonNativeIr.h",
]

AUTOGRAD_GENERATED_SOURCES = [
    "torch/csrc/autograd/generated/ADInplaceOrViewType_0.cpp",
    "torch/csrc/autograd/generated/ADInplaceOrViewType_1.cpp",
    "torch/csrc/autograd/generated/Functions.cpp",
    "torch/csrc/autograd/generated/ViewFuncs.cpp",
    "torch/csrc/lazy/generated/LazyNativeFunctions.cpp",
    "torch/csrc/lazy/generated/RegisterAutogradLazy.cpp",
    "torch/csrc/lazy/generated/RegisterLazy.cpp",
] + [
    "torch/csrc/autograd/generated/{}_{}.cpp".format(kind, shard)
    for kind in ["TraceType", "VariableType"]
    for shard in range(10)
]

def _codegen_impl(ctx):
    # A path ending in "/" is a directory of outputs (a tree artifact).
    outputs = {
        group: [
            ctx.actions.declare_directory(path[:-1]) if path.endswith("/") else ctx.actions.declare_file(path)
            for path in paths
        ]
        for group, paths in ctx.attr.output_groups.items()
    }
    source_root = ctx.label.workspace_root or "."
    bin_root = ctx.bin_dir.path + ("/" + ctx.label.workspace_root if ctx.label.workspace_root else "")
    all_outputs = [f for files in outputs.values() for f in files]
    outputs_file = ctx.actions.declare_file(ctx.label.name + ".outputs")
    ctx.actions.write(outputs_file, "\n".join([f.path for f in all_outputs if not f.is_directory]) + "\n")
    tool = ctx.attr.tool[DefaultInfo].files_to_run if ctx.attr.tool else None
    arguments = [
        ctx.attr.module,
        source_root,
        bin_root,
        outputs_file.path,
    ] + [
        argument.replace("{tool}", "{execroot}/" + tool.executable.path) if tool else argument
        for argument in ctx.attr.arguments
    ]
    ctx.actions.run(
        executable = ctx.executable._codegen,
        arguments = arguments,
        tools = [tool] if tool else [],
        inputs = ctx.files.srcs + [outputs_file],
        outputs = all_outputs,
        mnemonic = ctx.attr.mnemonic,
        progress_message = "Generating %{label}",
        # Upstream's scripts open files without an encoding, which on Windows
        # defaults to the ANSI code page and fails on non-ASCII sources.
        env = {"PYTHONUTF8": "1"},
    )
    return [
        DefaultInfo(files = depset(all_outputs)),
        OutputGroupInfo(**{group: depset(files) for group, files in outputs.items()}),
    ]

_codegen = rule(
    implementation = _codegen_impl,
    attrs = {
        "arguments": attr.string_list(
            doc = "Arguments of the module. {bin} is the repository's root in the bin directory.",
        ),
        "mnemonic": attr.string(mandatory = True),
        "module": attr.string(mandatory = True, doc = "The generator's Python module."),
        "output_groups": attr.string_list_dict(
            mandatory = True,
            doc = "Outputs (relative to the package) by output group; a path ending in / is a directory.",
        ),
        "srcs": attr.label_list(allow_files = True, doc = "Inputs of the generator."),
        "tool": attr.label(
            cfg = "exec",
            executable = True,
            doc = "A tool that the generator runs; {tool} in `arguments` is its path.",
        ),
        "_codegen": attr.label(
            default = "//tools:codegen",
            executable = True,
            cfg = "exec",
        ),
    },
)

def _aten(paths):
    return ["aten/src/ATen/" + path for path in paths]

def libtorch_aten_codegen(name, mps_enabled, rocm_enabled):
    """Runs torchgen.gen. Output groups: headers, sources, cpu_kernel_sources,
    cuda_headers, cuda_sources, cuda_kernel_sources, aoti_sources,
    aoti_cuda_sources, and where `mps_enabled` holds, mps_headers, mps_sources
    and aoti_mps_sources.

    Args:
        name: Name of the target.
        mps_enabled: The config_setting under which the MPS backend is built.
        rocm_enabled: The config_setting under which the CUDA outputs are
            generated for ROCm (with HIP includes, --rocm).
    """
    output_groups = {
        "aoti_cuda_sources": AOTI_GENERATED_CUDA_SOURCES,
        "aoti_sources": AOTI_GENERATED_SOURCES,
        "cpu_kernel_sources": _aten(ATEN_GENERATED_CPU_KERNEL_SOURCES),
        "cuda_headers": _aten(ATEN_GENERATED_CUDA_HEADERS),
        "cuda_kernel_sources": _aten(ATEN_GENERATED_CUDA_KERNEL_SOURCES),
        "cuda_sources": _aten(ATEN_GENERATED_CUDA_SOURCES),
        "headers": _aten(ATEN_GENERATED_HEADERS) + TORCHGEN_OTHER_HEADERS + ["aten/src/ATen/ops/"],
        "sources": _aten(ATEN_GENERATED_SOURCES),
    }
    _codegen(
        name = name,
        srcs = native.glob([
            "aten/src/ATen/native/*.yaml",
            "aten/src/ATen/templates/**",
        ]),
        arguments = [
            "--source-path=aten/src/ATen",
            "--install-dir={bin}/aten/src/ATen",
            "--aoti-install-dir={bin}/torch/csrc/inductor/aoti_torch/generated",
            "--headeronly-install-dir={bin}/torch/headeronly/core",
            "--per-operator-headers",
        ] + select({
            mps_enabled: ["--mps"],
            "//conditions:default": [],
        }) + select({
            rocm_enabled: ["--rocm"],
            "//conditions:default": [],
        }),
        mnemonic = "TorchGen",
        module = "torchgen.gen",
        output_groups = select({
            mps_enabled: output_groups | {
                "aoti_mps_sources": AOTI_GENERATED_MPS_SOURCES,
                "mps_headers": _aten(ATEN_GENERATED_MPS_HEADERS),
                "mps_sources": _aten(ATEN_GENERATED_MPS_SOURCES),
            },
            "//conditions:default": output_groups,
        }),
    )

def libtorch_autograd_codegen(name):
    """Runs tools/setup_helpers/generate_code.py. Output groups: headers and
    sources.

    Args:
        name: Name of the target.
    """
    _codegen(
        name = name,
        srcs = native.glob([
            "aten/src/ATen/native/*.yaml",
            "aten/src/ATen/templates/**",
            "torch/csrc/lazy/**/*.h",
            "torch/csrc/lazy/ts_backend/ts_native_functions.cpp",
        ]),
        arguments = [
            "--gen-dir={bin}",
            "--native-functions-path=aten/src/ATen/native/native_functions.yaml",
            "--tags-path=aten/src/ATen/native/tags.yaml",
            "--subset=libtorch",
            "--gen-lazy-ts-backend",
            # Like ATen (see libtorch_aten_codegen).
            "--per-operator-headers",
        ],
        mnemonic = "AutogradGen",
        module = "tools.setup_helpers.generate_code",
        output_groups = {
            "headers": AUTOGRAD_GENERATED_HEADERS,
            "sources": AUTOGRAD_GENERATED_SOURCES,
        },
    )

def libtorch_metallib_headers(name, srcs, deps, target_compatible_with = None):
    """Embeds Metal shaders in headers, like upstream's CMake build without a
    Metal compiler (cmake/Metal.cmake: metal_to_metallib_h), which then
    compiles them at runtime (PYTORCH_JIT_COMPILE_SHADERS).

    For each <dir>/<stem>.metal, generates
    aten/src/ATen/native/mps/<stem>_metallib.h with
    scripts/write_metallib_headers.py. No proprietary Apple tool is needed, so
    this works on any host.

    Args:
        name: Name of a filegroup holding the generated headers.
        srcs: The .metal shaders.
        deps: The headers that the shaders include (embedded in the output).
        target_compatible_with: Constraints for the generated targets.
    """
    headers = []
    for src in srcs:
        stem = src.rsplit("/", 1)[-1][:-len(".metal")]
        header = "aten/src/ATen/native/mps/{}_metallib.h".format(stem)
        _codegen(
            name = "{}_{}".format(name, stem),
            srcs = [src] + deps + [
                "scripts/write_metallib_headers.py",
                "torch/utils/_cpp_embed_headers.py",
            ],
            arguments = [
                src,
                "{bin}/" + header,
            ],
            mnemonic = "MetallibHeader",
            module = "scripts/write_metallib_headers.py",
            output_groups = {"headers": [header]},
            target_compatible_with = target_compatible_with,
        )
        headers.append("{}_{}".format(name, stem))
    native.filegroup(
        name = name,
        srcs = headers,
        target_compatible_with = target_compatible_with,
    )

def libtorch_vulkan_spv(name, target_compatible_with = None):
    """Compiles the Vulkan backend's GLSL compute shaders to SPIR-V and embeds
    them in vulkan/ATen/native/vulkan/spv.cpp (cmake/VulkanCodegen.cmake),
    with tools/gen_vulkan_spv.py and glslang's glslc-compatible compiler.

    Args:
        name: Name of the target. Output group: sources.
        target_compatible_with: Where the Vulkan backend is built.
    """
    _codegen(
        name = name,
        srcs = native.glob([
            "aten/src/ATen/native/vulkan/glsl/*.glsl",
            "aten/src/ATen/native/vulkan/glsl/*.h",
            "aten/src/ATen/native/vulkan/glsl/*.yaml",
        ]) + ["//tools:gen_vulkan_spv.py"],
        arguments = [
            "--glsl-path=aten/src/ATen/native/vulkan/glsl",
            "--output-path={bin}/vulkan/ATen/native/vulkan",
            "--glslc-path={tool}",
            "--tmp-dir-path={bin}/vulkan/spv",
            "--env",
            "FLOAT_IMAGE_FORMAT=rgba32f",
        ],
        mnemonic = "VulkanSpv",
        module = "tools/gen_vulkan_spv.py",
        # Only spv.cpp: in this version, the generator writes no spv.h.
        output_groups = {
            "sources": ["vulkan/ATen/native/vulkan/spv.cpp"],
        },
        target_compatible_with = target_compatible_with,
        tool = "@glslang//:glslc",
    )

# The directories that tools/libtorch_hipify.py reads (its _INPUT_DIRS).
_HIPIFY_INPUT_DIRS = [
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

def libtorch_hipify(name, torch_sources, target_compatible_with = None):
    """Hipifies the CUDA backend for ROCm (tools/libtorch_hipify.py).

    Args:
        name: Name of the target. Output groups (each a directory): headers
            (every hipified header), c10 (c10_hip's sources), host and device
            (torch_hip's host and device sources).
        torch_sources: torch/csrc sources of torch_hip, hipified in place.
        target_compatible_with: Where ROCm is built.
    """
    _codegen(
        name = name,
        srcs = native.glob([
            d + "/**/*" + ext
            for d in _HIPIFY_INPUT_DIRS
            for ext in [".cpp", ".cu", ".cuh", ".h", ".hip", ".hpp", ".inl"]
        ], allow_empty = True) + native.glob(["torch/utils/hipify/*.py"]) + [
            "aten/src/ATen/cuda/CUDAConfig.h.in",
            "c10/cuda/impl/cuda_cmake_macros.h.in",
            "//tools:libtorch_hipify.py",
        ],
        arguments = [
            "--out-headers={bin}/hip/headers",
            "--out-c10={bin}/hip/c10",
            "--out-host={bin}/hip/host",
            "--out-device={bin}/hip/device",
        ] + ["--torch-source=" + src for src in torch_sources],
        mnemonic = "Hipify",
        module = "tools/libtorch_hipify.py",
        output_groups = {
            "c10": ["hip/c10/"],
            "device": ["hip/device/"],
            "headers": ["hip/headers/"],
            "host": ["hip/host/"],
        },
        target_compatible_with = target_compatible_with,
    )

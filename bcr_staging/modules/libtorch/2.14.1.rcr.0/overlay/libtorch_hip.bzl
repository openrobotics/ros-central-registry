"""HIP compilation for the ROCm backend (c10_hip and torch_hip)."""

load("@bazel_skylib//rules:common_settings.bzl", "BuildSettingInfo")

def _rocm_offload_archs_impl(ctx):
    out = ctx.actions.declare_file(ctx.label.name + ".params")
    archs = ctx.attr.archs[BuildSettingInfo].value
    if not archs:
        fail("{} is empty".format(ctx.attr.archs.label))
    ctx.actions.write(out, "\n".join(["--offload-arch=" + arch for arch in archs]) + "\n")
    return [DefaultInfo(files = depset([out]))]

rocm_offload_archs = rule(
    implementation = _rocm_offload_archs_impl,
    doc = """A Clang response file (@file) with an --offload-arch per GPU of a
string_list_flag, so that the GPUs are set on the command line like
@rules_cuda's archs.""",
    attrs = {
        "archs": attr.label(mandatory = True, providers = [BuildSettingInfo]),
    },
)

# The directories of the hipified sources (tools/libtorch_hipify.py's
# _C10_SOURCES, _HOST_SOURCES and _DEVICE_SOURCES).
HIP_SOURCE_DIRS = [
    "aten/src/ATen/hip",
    "aten/src/ATen/hip/detail",
    "aten/src/ATen/hip/impl",
    "aten/src/ATen/hip/tunable",
    "aten/src/ATen/native/cudnn/hip",
    "aten/src/ATen/native/hip",
    "aten/src/ATen/native/hip/linalg",
    "aten/src/ATen/native/nested/hip",
    "aten/src/ATen/native/quantized/cudnn/hip",
    "aten/src/ATen/native/quantized/hip",
    "aten/src/ATen/native/sparse/hip",
    "aten/src/ATen/native/transformers/hip",
    "c10/hip",
    "c10/hip/impl",
]

def hip_include_copts(headers, source_dirs):
    """Include flags for the hipified headers (libtorch_hipify's headers).

    They take precedence over the original headers (-isystem, from
    cc_library's `includes`), and the headers that a hipified source includes
    relative to its directory are found with -iquote.

    Args:
        headers: The label of the hipified header tree.
        source_dirs: The directories of the sources that are compiled.

    Returns:
        A list of copts.
    """
    root = "$(execpath {})".format(headers)
    return [
        "-I" + root,
        "-I{}/aten/src".format(root),
    ] + ["-iquote{}/{}".format(root, d) for d in sorted(source_dirs)]

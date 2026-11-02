"""AMDGPU device library bitcode (cmake/OCL.cmake's opencl_bc_lib)."""

load("@rules_cc//cc:action_names.bzl", "C_COMPILE_ACTION_NAME")
load("@rules_cc//cc:find_cc_toolchain.bzl", "find_cc_toolchain", "use_cc_toolchain")
load("@rules_cc//cc/common:cc_common.bzl", "cc_common")

# CLANG_OCL_FLAGS of cmake/OCL.cmake.
_OCL_FLAGS = [
    "-x",
    "cl",
    "-Xclang",
    "-cl-std=CL2.0",
    "-target",
    "amdgcn-amd-amdhsa",
    "-fvisibility=hidden",
    "-fomit-frame-pointer",
    "-Xclang",
    "-finclude-default-header",
    "-nostdlibinc",
    "-Xclang",
    "-fexperimental-strict-floating-point",
    "-Xclang",
    "-fdenormal-fp-math=dynamic",
    "-nogpulib",
    "-cl-no-stdinc",
    # No code object version module flag: clang sets it in the user's code.
    "-Xclang",
    "-mcode-object-version=none",
    "-emit-llvm",
    "-c",
]

def _amdgcn_bitcode_library_impl(ctx):
    cc_toolchain = find_cc_toolchain(ctx)
    feature_configuration = cc_common.configure_features(
        ctx = ctx,
        cc_toolchain = cc_toolchain,
    )
    clang = cc_common.get_tool_for_action(
        feature_configuration = feature_configuration,
        action_name = C_COMPILE_ACTION_NAME,
    )
    includes = ["-I" + ctx.label.workspace_root + "/" + include if ctx.label.workspace_root else "-I" + include for include in ctx.attr.includes]
    linked = []
    for src in ctx.files.srcs:
        if src.extension == "ll":
            linked.append(src)
            continue
        bitcode = ctx.actions.declare_file("_objs/{}/{}.bc".format(ctx.label.name, src.short_path.replace("../", "").replace("/", "_")))
        ctx.actions.run(
            executable = clang,
            arguments = includes + _OCL_FLAGS + ctx.attr.copts + ctx.attr.per_file_copts.get(src.basename, []) + [
                src.path,
                "-o",
                bitcode.path,
            ],
            inputs = depset([src] + ctx.files.hdrs, transitive = [cc_toolchain.all_files]),
            outputs = [bitcode],
            mnemonic = "AmdgcnCompile",
            progress_message = "Compiling {} to AMDGPU bitcode".format(src.short_path),
        )
        linked.append(bitcode)

    # llvm-link, then prepare-builtins (see utils/link-builtins).
    out = ctx.actions.declare_file("amdgcn/bitcode/{}.bc".format(ctx.attr.library))
    args = ctx.actions.args()
    args.use_param_file("@%s", use_always = True)
    args.add("-o", out)
    args.add_all(linked)
    ctx.actions.run(
        executable = ctx.executable._link_builtins,
        arguments = [args],
        inputs = linked,
        outputs = [out],
        mnemonic = "AmdgcnLink",
        progress_message = "Linking AMDGPU bitcode %{output}",
    )
    return [DefaultInfo(files = depset([out]))]

amdgcn_bitcode_library = rule(
    implementation = _amdgcn_bitcode_library_impl,
    doc = "Compiles OpenCL (.cl) and LLVM IR (.ll) sources to amdgcn/bitcode/<library>.bc.",
    attrs = {
        "copts": attr.string_list(doc = "Extra Clang flags for every source."),
        "hdrs": attr.label_list(allow_files = [".h"]),
        "includes": attr.string_list(doc = "Include directories, relative to the repository root."),
        "library": attr.string(mandatory = True, doc = "The bitcode library's name (without .bc)."),
        "per_file_copts": attr.string_list_dict(doc = "Extra Clang flags, by source file basename."),
        "srcs": attr.label_list(allow_files = [".cl", ".ll"], mandatory = True),
        "_link_builtins": attr.label(
            default = "//utils/link-builtins",
            executable = True,
            cfg = "exec",
        ),
    },
    fragments = ["cpp"],
    toolchains = use_cc_toolchain(),
)

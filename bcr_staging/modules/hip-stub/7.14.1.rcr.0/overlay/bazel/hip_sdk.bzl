"""A ROCm installation directory for Clang's HIP driver (--rocm-path)."""

load("@rules_cc//cc:action_names.bzl", "CPP_COMPILE_ACTION_NAME")
load("@rules_cc//cc:find_cc_toolchain.bzl", "find_cc_toolchain", "use_cc_toolchain")
load("@rules_cc//cc/common:cc_common.bzl", "cc_common")

def _hip_sdk_impl(ctx):
    sdk = ctx.actions.declare_directory(ctx.label.name)
    commands = ["set -e"]
    inputs = []

    def copy(files, destination):
        commands.append("mkdir -p {}/{}".format(sdk.path, destination))
        for f in files:
            inputs.append(f)
            commands.append("cp {} {}/{}/".format(f.path, sdk.path, destination))

    # The tools that Clang runs for HIP (found with -B<sdk>/bin), and the
    # toolchain's Clang, which clang-linker-wrapper runs from its own directory
    # to link device code (with the ld.lld beside it). The toolchain's Clang is
    # LLVM's multicall binary, so it also serves as the llvm-objcopy that
    # clang-offload-bundler runs.
    cc_toolchain = find_cc_toolchain(ctx)
    clang = cc_common.get_tool_for_action(
        feature_configuration = cc_common.configure_features(ctx = ctx, cc_toolchain = cc_toolchain),
        action_name = CPP_COMPILE_ACTION_NAME,
    )
    commands.append("mkdir -p {}/bin".format(sdk.path))
    commands.append("cp -L {} {}/bin/clang".format(clang, sdk.path))
    commands.append("ln -s clang {}/bin/llvm-objcopy".format(sdk.path))
    for tool, name in [
        (ctx.attr.linker_wrapper, "clang-linker-wrapper"),
        (ctx.attr.offload_bundler, "clang-offload-bundler"),
        (ctx.attr.offload_binary, "llvm-offload-binary"),
        (ctx.attr.lld, "ld.lld"),
    ]:
        executable = tool[DefaultInfo].files_to_run.executable
        inputs.append(executable)
        commands.append("mkdir -p {}/bin".format(sdk.path))
        commands.append("cp {} {}/bin/{}".format(executable.path, sdk.path, name))

    # include/hip/..., keeping each header's path below its include directory.
    for hdr in ctx.files.hdrs:
        relative = None
        for include in ctx.attr.include_prefixes:
            marker = "/" + include + "/hip/"
            if marker in "/" + hdr.short_path:
                relative = "hip/" + ("/" + hdr.short_path).split(marker, 1)[1]
                break
        if relative == None:
            fail("{} is not below any of {}".format(hdr.short_path, ctx.attr.include_prefixes))
        inputs.append(hdr)
        directory = "{}/include/{}".format(sdk.path, relative.rpartition("/")[0])
        commands.append("mkdir -p {} && cp {} {}/".format(directory, hdr.path, directory))

    copy(ctx.files.bitcode, "amdgcn/bitcode")

    # Clang's HIP version detection (share/hip/version, as hipcc installs it).
    commands.append("mkdir -p {}/share/hip".format(sdk.path))
    commands.append("printf 'HIP_VERSION_MAJOR={}\\nHIP_VERSION_MINOR={}\\nHIP_VERSION_PATCH={}\\n' > {}/share/hip/version".format(
        ctx.attr.version_major,
        ctx.attr.version_minor,
        ctx.attr.version_patch,
        sdk.path,
    ))

    ctx.actions.run_shell(
        command = "\n".join(commands),
        inputs = depset(inputs, transitive = [cc_toolchain.all_files]),
        outputs = [sdk],
        mnemonic = "HipSdk",
        progress_message = "Assembling the HIP SDK %{output}",
    )
    return [DefaultInfo(files = depset([sdk]))]

hip_sdk = rule(
    implementation = _hip_sdk_impl,
    doc = """A directory laid out like a ROCm installation, for Clang's
--rocm-path (and -B<sdk>/bin): the HIP headers, the device libraries'
bitcode and the offloading tools that Clang runs, built for the exec
platform.""",
    attrs = {
        "bitcode": attr.label_list(allow_files = [".bc"], mandatory = True),
        "hdrs": attr.label_list(allow_files = True, mandatory = True),
        "include_prefixes": attr.string_list(
            mandatory = True,
            doc = "Include directories of `hdrs` (each holding a hip/ directory).",
        ),
        "linker_wrapper": attr.label(mandatory = True, executable = True, cfg = "exec"),
        "lld": attr.label(mandatory = True, executable = True, cfg = "exec"),
        "offload_binary": attr.label(mandatory = True, executable = True, cfg = "exec"),
        "offload_bundler": attr.label(mandatory = True, executable = True, cfg = "exec"),
        "version_major": attr.int(mandatory = True),
        "version_minor": attr.int(mandatory = True),
        "version_patch": attr.int(mandatory = True),
    },
    fragments = ["cpp"],
    toolchains = use_cc_toolchain(),
)

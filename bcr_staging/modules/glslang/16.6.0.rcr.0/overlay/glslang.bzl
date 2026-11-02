"""glslang's generated sources (CMakeLists.txt, StandAlone/CMakeLists.txt)."""

def _glsl_intrinsic_header_impl(ctx):
    ctx.actions.run(
        executable = ctx.executable._generator,
        arguments = [
            "-i",
            ctx.files.srcs[0].dirname,
            "-o",
            ctx.outputs.out.path,
        ],
        inputs = ctx.files.srcs,
        outputs = [ctx.outputs.out],
        mnemonic = "GlslangIntrinsicHeader",
        progress_message = "Generating %{output}",
    )

# glslang/glsl_intrinsic_header.h, from the shaders in one directory
# (gen_extension_headers.py -i <dir>).
glsl_intrinsic_header = rule(
    implementation = _glsl_intrinsic_header_impl,
    attrs = {
        "out": attr.output(mandatory = True),
        "srcs": attr.label_list(allow_files = [".glsl"], mandatory = True),
        "_generator": attr.label(
            default = "//bazel:gen_extension_headers",
            executable = True,
            cfg = "exec",
        ),
    },
)

"""Code generation for sleef (src/libm/CMakeLists.txt), without a shell."""

def _generate_impl(ctx):
    ctx.actions.run(
        executable = ctx.executable.tool,
        arguments = [ctx.outputs.out.path] + ctx.attr.arguments,
        outputs = [ctx.outputs.out],
        mnemonic = "SleefGenerate",
        progress_message = "Generating %{output}",
    )

# Writes the output of one of the generators (see bazel/tool_main.c).
sleef_generate = rule(
    implementation = _generate_impl,
    attrs = {
        "arguments": attr.string_list(),
        "out": attr.output(mandatory = True),
        "tool": attr.label(mandatory = True, executable = True, cfg = "exec"),
    },
)

def _concat_impl(ctx):
    ctx.actions.run(
        executable = ctx.executable._concat,
        arguments = [ctx.outputs.out.path] + [f.path for f in ctx.files.srcs],
        inputs = ctx.files.srcs,
        outputs = [ctx.outputs.out],
        mnemonic = "SleefConcat",
        progress_message = "Generating %{output}",
    )

# Concatenates files (sleef_concat_files() in upstream's CMake build).
sleef_concat = rule(
    implementation = _concat_impl,
    attrs = {
        "out": attr.output(mandatory = True),
        "srcs": attr.label_list(allow_files = True),
        "_concat": attr.label(default = "//bazel:concat", executable = True, cfg = "exec"),
    },
)

"""Lazily-forwarding shims of ROCm shared libraries (see gen_shim.py)."""

load("@rules_cc//cc:cc_binary.bzl", "cc_binary")
load("@rules_cc//cc:cc_import.bzl", "cc_import")
load("@rules_cc//cc:cc_library.bzl", "cc_library")

def _rocm_shim_sources_impl(ctx):
    asm = ctx.actions.declare_file(ctx.label.name + ".S")
    loader = ctx.actions.declare_file(ctx.label.name + ".c")
    version_script = ctx.actions.declare_file(ctx.label.name + ".lds")
    args = ctx.actions.args()
    args.add("--soname", ctx.attr.soname)
    args.add("--prefix", ctx.attr.prefix)
    if ctx.attr.error:
        args.add("--error", ctx.attr.error)
    else:
        args.add("--abort")
    if not ctx.attr.load_library:
        args.add("--no-load")
    args.add_all(ctx.files.maps, before_each = "--map")
    args.add_all(ctx.files.headers, before_each = "--header")
    if ctx.attr.export_macro:
        args.add("--export-macro", ctx.attr.export_macro)
    args.add_all(ctx.attr.symbols, before_each = "--symbol")
    args.add_all(ctx.attr.fallbacks, before_each = "--fallback")
    args.add_all(ctx.attr.excludes, before_each = "--exclude")
    args.add("--out", asm.path[:-len(".S")])
    ctx.actions.run(
        executable = ctx.executable._generator,
        arguments = [args],
        inputs = ctx.files.maps + ctx.files.headers,
        outputs = [asm, loader, version_script],
        mnemonic = "RocmShim",
        progress_message = "Generating the shim of " + ctx.attr.soname,
    )
    return [
        DefaultInfo(files = depset([asm, loader])),
        OutputGroupInfo(version_script = depset([version_script])),
    ]

_rocm_shim_sources = rule(
    implementation = _rocm_shim_sources_impl,
    attrs = {
        "error": attr.string(),
        "excludes": attr.string_list(),
        "export_macro": attr.string(),
        "fallbacks": attr.string_list(),
        "headers": attr.label_list(allow_files = True),
        "load_library": attr.bool(default = True),
        "maps": attr.label_list(allow_files = True),
        "prefix": attr.string(mandatory = True),
        "soname": attr.string(mandatory = True),
        "symbols": attr.string_list(),
        "_generator": attr.label(
            default = Label("//bazel:gen_shim"),
            executable = True,
            cfg = "exec",
        ),
    },
)

_LINUX_X86_64 = [
    "@platforms//os:linux",
    "@platforms//cpu:x86_64",
]

def rocm_shim_library(
        name,
        soname,
        error = None,
        load_library = True,
        maps = [],
        headers = [],
        export_macro = None,
        symbols = [],
        fallbacks_src = None,
        fallbacks = [],
        excludes = [],
        version_script = True,
        deps = [],
        visibility = None):
    """A ROCm library to link against: a shim of `soname`, and `deps`.

    Args:
        name: The cc_library to link against.
        soname: The real library's SONAME (and the shim's file name).
        error: What the library's functions return without ROCm. Without it,
            they abort instead (for C++ functions that return objects).
        load_library: Whether to load the real library at runtime (False when it is
            built for another C++ ABI, e.g. libstdc++'s).
        maps: GNU version scripts of the real library (its symbols and versions).
        headers: Headers declaring the library's functions with `export_macro`.
        export_macro: The library's export macro (e.g. ROCBLAS_EXPORT).
        symbols: Other symbols to export (e.g. mangled C++ names).
        fallbacks_src: Another source: shim_fallback_<symbol> functions, or
            definitions that the shim exports as they are.
        fallbacks: The symbols that fallbacks_src defines a fallback for.
        excludes: Symbols not to export.
        version_script: Whether to export only the shim's symbols, with the
            real library's symbol versions (otherwise, every global symbol).
        deps: The library's headers (and other libraries it needs).
        visibility: Visibility of `name`.
    """
    _rocm_shim_sources(
        name = name + "_shim",
        soname = soname,
        prefix = name.replace("-", "_"),
        error = error,
        load_library = load_library,
        maps = maps,
        headers = headers,
        export_macro = export_macro,
        symbols = symbols,
        fallbacks = fallbacks,
        excludes = excludes,
        target_compatible_with = _LINUX_X86_64,
    )
    native.filegroup(
        name = name + "_version_script",
        srcs = [":" + name + "_shim"],
        output_group = "version_script",
    )
    cc_binary(
        name = soname,
        srcs = [":" + name + "_shim"] + ([fallbacks_src] if fallbacks_src else []),
        additional_linker_inputs = [":" + name + "_version_script"],
        linkopts = [
            "-Wl,-soname," + soname,
            "-ldl",
            "-lpthread",
        ] + ([
            "-Wl,--version-script=$(location :{}_version_script)".format(name),
        ] if version_script else []),
        linkshared = True,
        target_compatible_with = _LINUX_X86_64,
        # The headers of fallbacks_src (and the libraries the real one needs).
        deps = deps,
    )
    cc_import(
        name = name + "_import",
        shared_library = ":" + soname,
        target_compatible_with = _LINUX_X86_64,
    )
    cc_library(
        name = name,
        visibility = visibility,
        deps = [":" + name + "_import"] + deps,
    )

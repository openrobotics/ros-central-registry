load("@rules_cc//cc/common:cc_info.bzl", "CcInfo")
load("@rules_pkg//pkg:providers.bzl", "PackageFilesInfo")

def _include_relative(path):
    parts = path.split("/")
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] == "include":
            return "/".join(parts[i + 1:])
    return parts[-1]

def _vendor_install_tree_impl(ctx):
    prefix = ctx.attr.prefix.strip("/")
    p = (prefix + "/") if prefix else ""
    dest_src_map = {}
    for target in ctx.attr.deps:
        cc_info = target[CcInfo]
        comp = cc_info.compilation_context
        for h in comp.direct_public_headers:
            dest_src_map[p + "include/" + _include_relative(h.path)] = h
        for linker_input in cc_info.linking_context.linker_inputs.to_list():
            for lib in linker_input.libraries:
                f = lib.dynamic_library or lib.static_library or lib.pic_static_library
                if f != None and f.basename.startswith("lib"):
                    base = f.basename.split(".")[0] + ".so"
                    dest_src_map[p + "lib/" + base] = f
                    dest_src_map[p + "lib/" + base + ".1"] = f
                    dest_src_map[p + "lib/" + base + ".1.8.3"] = f
    return [
        DefaultInfo(files = depset(dest_src_map.values())),
        PackageFilesInfo(dest_src_map = dest_src_map, attributes = {}),
    ]

vendor_install_tree = rule(
    implementation = _vendor_install_tree_impl,
    attrs = {
        "deps": attr.label_list(providers = [CcInfo], mandatory = True),
        "prefix": attr.string(default = ""),
    },
)

"""Custom Bazel rule to register an arbitrary resource in the ament index.

This works by placing the resource file at the exact path expected by
ament_index_cpp/ament_index_python inside the runfiles directory of the test.
"""

load(":ament_index.bzl", "AmentIndexInfo", "strip_gen_prefix")

def _register_ament_resource_impl(ctx):
    package = ctx.attr.package_name if ctx.attr.package_name else ctx.label.workspace_name.removesuffix("+")
    resource_file = ctx.actions.declare_file(ctx.label.name + "_resource")
    ctx.actions.write(
        output = resource_file,
        content = ctx.attr.content,
    )
    symlinks = {}
    path = "share/ament_index/resource_index/{category}/{package}".format(
        category = ctx.attr.category,
        package = package,
    )
    symlinks[path] = resource_file
    return [
        DefaultInfo(
            files = depset([resource_file]),
            runfiles = ctx.runfiles(symlinks = symlinks),
        ),
        AmentIndexInfo(
            package_name = ctx.label.workspace_name.removesuffix("+"),
            symlinks = symlinks,
        ),
    ]

register_ament_resource = rule(
    implementation = _register_ament_resource_impl,
    attrs = {
        "category": attr.string(mandatory = True),
        "content": attr.string(mandatory = True),
        "package_name": attr.string(),
    },
)

def _register_ament_files_impl(ctx):
    package = ctx.attr.package_name if ctx.attr.package_name else ctx.label.workspace_name.removesuffix("+")
    renames = {}
    if ctx.attr.renames:
        for target, new_name in ctx.attr.renames.items():
            for f in target.files.to_list():
                renames[f] = new_name
    symlinks = {}
    for f in ctx.files.files:
        if f in renames:
            rel_path = renames[f].lstrip("/")
        else:
            rel_path = f.short_path
            if rel_path.startswith("../"):
                parts = rel_path.split("/")
                rel_path = "/".join(parts[2:])
            else:
                pkg_prefix = ctx.label.package + "/"
                if pkg_prefix != "/" and rel_path.startswith(pkg_prefix):
                    rel_path = rel_path[len(pkg_prefix):]
            stripped, was_gen = strip_gen_prefix(rel_path)
            if was_gen:
                rel_path = stripped
                if rel_path.startswith("share/" + package + "/"):
                    rel_path = rel_path[len("share/" + package + "/"):]
            if ctx.attr.strip_prefix == "*":
                rel_path = f.basename
            elif ctx.attr.strip_prefix:
                prefix = ctx.attr.strip_prefix
                if not prefix.endswith("/"):
                    prefix += "/"
                if rel_path.startswith(prefix):
                    rel_path = rel_path[len(prefix):]
        sub = ctx.attr.prefix.strip("/") if ctx.attr.prefix else ""
        if sub.startswith("lib/") or sub.startswith("share/") or sub.startswith("bin/") or sub.startswith("include/") or sub in ("lib", "share", "bin", "include"):
            path = sub + "/" + rel_path
        else:
            if sub:
                rel_path = sub + "/" + rel_path
            path = "share/{package}/{rel_path}".format(
                package = package,
                rel_path = rel_path,
            )
        symlinks[path] = f
    return [
        DefaultInfo(
            files = depset(ctx.files.files),
            runfiles = ctx.runfiles(symlinks = symlinks),
        ),
        AmentIndexInfo(
            package_name = ctx.label.workspace_name.removesuffix("+"),
            symlinks = symlinks,
        ),
    ]

register_ament_files = rule(
    implementation = _register_ament_files_impl,
    attrs = {
        "files": attr.label_list(allow_files = True, mandatory = True),
        "strip_prefix": attr.string(),
        "prefix": attr.string(),
        "renames": attr.label_keyed_string_dict(allow_files = True),
        "package_name": attr.string(),
    },
)

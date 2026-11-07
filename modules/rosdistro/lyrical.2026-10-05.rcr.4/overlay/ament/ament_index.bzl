# Copyright 2025 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
The general idea behind ament_index is to organize runfile data in such a way that
makes it looks like a ROS underlay. We do this by creating a symlink tree that
replicates the intended structure. For example

<runfile>
    + bin/ <-------------------------- where all the executables go
        + foo
        + bar
    + lib/ <-------------------------- where all the shared libraries go
        + libfoo.so
        + libbar.so
    + share <------------------------- where all the data goes
        + ament_index/
            + resource_index/
                + rclcpp_components/
                    + bar
                    + foo
                + packages/
                    + bar/
                        + config/
                    + foo/
                        + images/

To do this for some module "foo":

    ament_index(
        name = "data",
        components = [":component"],
        data = glob(["images/*"]),
        deps = [
            "@bar//:ament_index
        ]
    )

Importantly, the libraries in "lib" may not be dynamically linked to anything. But they
may be dlopened() by shared_library.c in rcutils. Our implementation of this logic uses
bazel runfiles to locate the "lib" subfolder when it searches for the library.

The neat thing about the ament_index is that it can be a direct layer of pkg_tar, which
makes it easy to transitively collect ament index layers into something that looks a lot
like an underlay (getting it to this point requires more work, though).
"""

load("@rules_cc//cc/common:cc_shared_library_info.bzl", "CcSharedLibraryInfo")
load("@rules_pkg//pkg:providers.bzl", "PackageFilesInfo")

# Shared library suffixes across the platforms we build for: ELF (.so, .so.1.2.3),
# Mach-O (.dylib), and PE (.dll).
def is_shared_library(basename):
    return (
        basename.endswith(".so") or
        ".so." in basename or
        basename.endswith(".dylib") or
        basename.endswith(".dll")
    )

_is_shared_library = is_shared_library

def strip_gen_prefix(path):
    """Strip a leading generated-file directory segment (_gen/, _meta/, _gen_*/, _meta_*/).

    Args:
      path: Package-relative file path.

    Returns:
      A tuple of (stripped_path, was_generated).
    """
    slash = path.find("/")
    if slash > 0:
        first = path[:slash]
        if first == "_gen" or first == "_meta" or first.startswith("_gen_") or first.startswith("_meta_"):
            return path[slash + 1:], True
    return path, False

def _prefix_sort_key(p):
    return len(p.split("->", 1)[0])

def _package_relative(ctx, f):
    """Path of a file relative to the root of the repository that owns this target."""
    root = ctx.label.workspace_root
    path = f.short_path
    if path.startswith("../"):
        # external repo: ../<repo>/<path>
        return "/".join(path.split("/")[2:])
    if root and path.startswith(root + "/"):
        return path[len(root) + 1:]
    return path

def _ament_index_impl(ctx):
    return ament_index_providers(ctx)

def ament_index_package_name(ctx):
    """The ROS package name an ament_index/ament_package target describes."""

    # When we use local path overrides for the module name, Bazel appends
    # a plus sign to the end. We must remove this, or the ament_index
    # paths will not be correct and we won't be able to resolve files.
    return ctx.attr.export_name if ctx.attr.export_name else ctx.label.workspace_name.removesuffix("+")

def ament_index_symlinks(ctx):
    """Compute the runfiles symlink tree (underlay layout) for this package.

    Returns a dict of runfiles-relative path -> File for exactly this
    package's own contribution (dependencies are merged separately).
    """
    package_name = ament_index_package_name(ctx)

    # Create a new, empty file for the ament index. This is a shim to help
    # the ament_index_{cpp, python, ...} discover packages. We use the
    # ctx.index.write call because it's platform independent.
    ament_index_file = ctx.actions.declare_file("_" + package_name)
    ctx.actions.write(output = ament_index_file, content = "")

    # Make sure that we have at lease
    symlinks = {}

    # Absorb any same-package AmentIndexInfo targets in deps (e.g. from
    # register_ament_resource or register_ament_files).
    for dep in ctx.attr.deps:
        if AmentIndexInfo in dep and dep[AmentIndexInfo].package_name == package_name:
            symlinks.update(dep[AmentIndexInfo].symlinks)

    # FILE: package.xml
    if ctx.file.package_xml:
        symlinks["share/" + package_name + "/package.xml"] = ctx.file.package_xml

    # SHARED DATA
    rosidl_interfaces = []
    ament_index_path = "share/ament_index/resource_index/packages/{0}".format(package_name)
    symlinks[ament_index_path] = ament_index_file
    if ctx.attr.data:
        sorted_data_prefixes = sorted(getattr(ctx.attr, "data_strip_prefixes", []), key = _prefix_sort_key, reverse = True)
        for target in ctx.attr.data:
            if AmentIndexInfo in target and target[AmentIndexInfo].package_name == package_name:
                symlinks.update(target[AmentIndexInfo].symlinks)
                continue
            if PackageFilesInfo in target:
                for dest, file in target[PackageFilesInfo].dest_src_map.items():
                    dest = dest.lstrip("/")
                    if dest.startswith("share/") or dest.startswith("lib/") or dest.startswith("bin/"):
                        symlinks[dest] = file
                    else:
                        symlinks["share/" + package_name + "/" + dest] = file
                continue
            for file in target.files.to_list():
                file_path = _package_relative(ctx, file)
                stripped, was_gen = strip_gen_prefix(file_path)

                # A generated file that already names its install location
                # (_gen/share/<pkg>/...) is placed verbatim, without applying
                # data_strip_prefix(es) meant for source-tree paths.
                install_relative = False
                if was_gen:
                    file_path = stripped
                    if file_path.startswith("share/" + package_name + "/"):
                        file_path = file_path[len("share/" + package_name + "/"):]
                        install_relative = True
                matched_prefix = install_relative
                for p in ([] if install_relative else sorted_data_prefixes):
                    if not p:
                        continue
                    if "->" in p:
                        src_p, dst_p = p.split("->", 1)
                        sp = (src_p if src_p.endswith("/") else src_p + "/") if src_p else ""
                        if not sp or file_path.startswith(sp):
                            rem = file_path[len(sp):]
                            file_path = (dst_p.rstrip("/") + "/" + rem) if dst_p else rem
                            matched_prefix = True
                            break
                        continue
                    sp = p if p.endswith("/") else p + "/"
                    if file_path.startswith(sp):
                        file_path = file_path[len(sp):]
                        matched_prefix = True
                        break
                if not matched_prefix and ctx.attr.data_strip_prefix:
                    prefix = ctx.attr.data_strip_prefix
                    if not prefix.endswith("/"):
                        prefix += "/"
                    file_path = file_path.removeprefix(prefix)
                symlinks["share/" + package_name + "/" + file_path] = file
                if file_path.endswith(".msg") or file_path.endswith(".srv") or file_path.endswith(".action") or file_path.endswith(".idl"):
                    rosidl_interfaces.append(file_path)

    if rosidl_interfaces:
        rosidl_file = ctx.actions.declare_file(package_name + "_rosidl_interfaces")
        ctx.actions.write(output = rosidl_file, content = "\n".join(rosidl_interfaces))
        symlinks["share/ament_index/resource_index/rosidl_interfaces/" + package_name] = rosidl_file

    # EXECUTABLES
    for target in ctx.attr.executables:
        for file in target.files.to_list():
            symlinks["bin/" + file.basename] = file

    # LIBRARIES
    sonames = getattr(ctx.attr, "sonames", {})
    for target in ctx.attr.libraries:
        for file in target.files.to_list():
            symlinks["lib/" + file.basename] = file
            for key in (target.label.name, file.basename):
                for alias in sonames.get(key, []):
                    if not alias.endswith("."):
                        symlinks["lib/" + alias] = file

    # A library in lib/ may be dlopen()ed through that path (e.g. as a
    # component or plugin), in which case its RUNPATH (relative to where Bazel
    # built it) does not resolve; make its shared-library dependencies
    # available next to it, as an install tree would.
    for target in ctx.attr.libraries:
        if CcSharedLibraryInfo not in target:
            continue
        for dep in target[CcSharedLibraryInfo].dynamic_deps.to_list():
            for library in dep.linker_input.libraries:
                dynamic_library = library.resolved_symlink_dynamic_library or library.dynamic_library
                if dynamic_library and "lib/" + dynamic_library.basename not in symlinks:
                    symlinks["lib/" + dynamic_library.basename] = dynamic_library
        if DefaultInfo in target and target[DefaultInfo].default_runfiles:
            for file in target[DefaultInfo].default_runfiles.files.to_list():
                if _is_shared_library(file.basename) and "lib/" + file.basename not in symlinks:
                    symlinks["lib/" + file.basename] = file

    # LIB_DATA
    if hasattr(ctx.attr, "lib_data"):
        for target in ctx.attr.lib_data:
            if PackageFilesInfo in target:
                for dest, file in target[PackageFilesInfo].dest_src_map.items():
                    dest = dest.lstrip("/")
                    if dest.startswith("lib/"):
                        symlinks[dest] = file
                    else:
                        symlinks["lib/" + package_name + "/" + dest] = file
                continue
            for file in target.files.to_list():
                rel_path = _package_relative(ctx, file)
                stripped, was_gen = strip_gen_prefix(rel_path)
                if was_gen and stripped.startswith("lib/" + package_name + "/"):
                    symlinks[stripped] = file
                else:
                    symlinks["lib/" + package_name + "/" + file.basename] = file

    # COMPONENTS
    if ctx.attr.components:
        component_files = []
        for target in ctx.attr.components:
            all_files = depset(
                target.files.to_list(),
                transitive = [
                    target[DefaultInfo].default_runfiles.files,
                ],
            ).to_list()
            for file in all_files:
                if file.path.endswith(".component"):
                    if file not in component_files:
                        component_files.append(file)
                elif _is_shared_library(file.basename):
                    # The component library itself: lib/ only (never under
                    # share/<pkg>/, where its runfiles solib path would leak).
                    symlinks["lib/" + file.basename] = file
                else:
                    symlinks["share/" + package_name + "/" + file.short_path] = file
        if component_files:
            out_comp_file = ctx.actions.declare_file("share/ament_index/resource_index/rclcpp_components/" + package_name)
            ctx.actions.run_shell(
                inputs = component_files,
                outputs = [out_comp_file],
                command = "cat " + " ".join([f.path for f in component_files]) + " > " + out_comp_file.path,
            )
            symlinks["share/ament_index/resource_index/rclcpp_components/" + package_name] = out_comp_file

    # PLUGINS
    plugins_by_cat = {}
    if ctx.files.plugins:
        default_cat = ctx.attr.plugin_category if ctx.attr.plugin_category else package_name
        plugins_by_cat[default_cat] = list(ctx.files.plugins)
    if hasattr(ctx.attr, "plugin_categories") and ctx.attr.plugin_categories:
        for target, cat in ctx.attr.plugin_categories.items():
            resolved_cat = cat if cat else package_name
            plugins_by_cat.setdefault(resolved_cat, []).extend(target.files.to_list())

    for plugin_category, cat_files in plugins_by_cat.items():
        desc_paths = []
        for f in cat_files:
            # pluginlib_export_plugin_description_file() installs the xml at its
            # path relative to the package root (e.g. share/<pkg>/test/<pkg>/x.xml).
            rel_path = _package_relative(ctx, f)
            stripped, was_gen = strip_gen_prefix(rel_path)
            if was_gen:
                rel_path = stripped
                if rel_path.startswith("share/" + package_name + "/"):
                    rel_path = rel_path[len("share/" + package_name + "/"):]
            target_path = "share/" + package_name + "/" + rel_path
            symlinks[target_path] = f
            if target_path not in desc_paths:
                desc_paths.append(target_path)
        suffix = "_resource" if len(plugins_by_cat) == 1 else ("_" + plugin_category + "_resource")
        resource_file = ctx.actions.declare_file(ctx.label.name + "_" + package_name + suffix)
        ctx.actions.write(output = resource_file, content = "\n".join(desc_paths))
        symlinks["share/ament_index/resource_index/" + plugin_category + "__pluginlib__plugin/" + package_name] = resource_file

    return symlinks

AmentIndexInfo = provider(
    doc = "The underlay-layout symlink map contributed by one ament_index target (not transitive).",
    fields = {
        "package_name": "ROS package name.",
        "symlinks": "dict: runfiles-relative path -> File.",
    },
)

def ament_index_providers(ctx, extra_files = []):
    """Build the DefaultInfo (and AmentIndexInfo) for an ament_index-like target."""
    symlinks = ament_index_symlinks(ctx)

    # Return a collection of runfiles with manipulated symlinks.
    transitive_runfiles = [
        target[DefaultInfo].default_runfiles
        for attr_name in ("deps", "executables", "libraries", "data", "lib_data", "components")
        for target in getattr(ctx.attr, attr_name, [])
    ]
    return [
        DefaultInfo(
            files = depset(
                direct = symlinks.values() + extra_files,
                transitive = [dep[DefaultInfo].files for dep in ctx.attr.deps],
            ),
            runfiles = ctx.runfiles(
                symlinks = symlinks,
            ).merge_all(transitive_runfiles),
        ),
        AmentIndexInfo(
            package_name = ament_index_package_name(ctx),
            symlinks = symlinks,
        ),
    ]

AMENT_INDEX_ATTRS = {
    "deps": attr.label_list(providers = [DefaultInfo]),
    "export_name": attr.string(),
    "package_xml": attr.label(allow_single_file = True),
    "executables": attr.label_list(allow_files = True),
    "headers": attr.label_list(allow_files = True),
    "libraries": attr.label_list(allow_files = True),
    "sonames": attr.string_list_dict(doc = "Optional mapping of library target/basename to versioned SONAME filenames in lib/."),
    "data": attr.label_list(allow_files = True),
    "data_strip_prefix": attr.string(),
    "data_strip_prefixes": attr.string_list(),
    "lib_data": attr.label_list(allow_files = True),
    "components": attr.label_list(allow_files = True),
    "plugins": attr.label_list(allow_files = True),
    "plugin_category": attr.string(),
    "plugin_categories": attr.label_keyed_string_dict(allow_files = True, doc = "Mapping of plugin XML label to pluginlib category when a package exports multiple categories."),
}

ament_index_rule = rule(
    implementation = _ament_index_impl,
    attrs = AMENT_INDEX_ATTRS,
)

def ament_index(name = None, **kwargs):
    ament_index_rule(name = name if name else "ament_index", **kwargs)

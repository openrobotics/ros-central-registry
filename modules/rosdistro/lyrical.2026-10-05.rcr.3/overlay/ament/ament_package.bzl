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

"""ament_package: the downstream-facing bundle of one ROS package.

Besides the runfiles tree `ament_index` provides (so tests and binaries can
find data at runtime), `ament_package` describes how this package is laid out
in an installed underlay -- `include/`, `lib/`, `bin/`, `share/`,
`lib/pythonX.Y/site-packages/` -- exactly like `colcon build` would install it
in isolated layout (`install/<pkg>/...`). That description is exposed as:

- `AmentPackageInfo`, consumed by `ament_underlay` to produce one tarball for
  a whole distribution variant (see underlay.bzl), and
- a `:tar` target next to every `:ament_package`, containing *only* this
  package's files under `<install_prefix>/<pkg>/`.

The ament_cmake/colcon metadata files (`share/<pkg>/cmake/*.cmake`,
`local_setup.*`, `package.*`, `hook/`, `environment/`, ament_index resources)
are rendered by //ament:install_gen from the package.xml and this target's
attributes, so the result is a drop-in replacement for a colcon install.
"""

load("@bazel_skylib//rules:common_settings.bzl", "BuildSettingInfo")
load("@rules_pkg//pkg:providers.bzl", "PackageFilesInfo")
load("@rules_pkg//pkg:tar.bzl", "pkg_tar")
load(":ament_index.bzl", "AMENT_INDEX_ATTRS", "AmentIndexInfo", "ament_index_package_name", "ament_index_providers", "ament_index_symlinks", "is_shared_library", "strip_gen_prefix")
load(":providers.bzl", "AmentCMakeExportsInfo", "AmentPackageInfo")

_PY_TOOLCHAIN = "@rules_python//python:toolchain_type"

def _strip(path, prefix):
    if not prefix:
        return path
    if not prefix.endswith("/"):
        prefix += "/"
    return path.removeprefix(prefix)

def _prefix_sort_key(p):
    return len(p.split("->", 1)[0])

def _strip_any(path, prefix, prefixes):
    for p in prefixes:
        if not p:
            continue
        if "->" in p:
            src_p, dst_p = p.split("->", 1)
            sp = (src_p if src_p.endswith("/") else src_p + "/") if src_p else ""
            if not sp or path.startswith(sp):
                rem = path[len(sp):]
                return (dst_p.rstrip("/") + "/" + rem) if dst_p else rem
            continue
        sp = p if p.endswith("/") else p + "/"
        if path.startswith(sp):
            return path[len(sp):]
    return _strip(path, prefix)

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

_is_shared_library = is_shared_library

def _shared_library_name(basename):
    """libfoo.so / libfoo.so.1 / libfoo.dylib / libfoo.a -> foo"""
    name = basename
    if name.startswith("lib"):
        name = name[3:]
    for ext in (".dylib", ".dll", ".a"):
        if name.endswith(ext):
            return name[:-len(ext)]
    if ".so" in name:
        return name[:name.index(".so")]
    return name

def _python_version(ctx):
    tc = ctx.toolchains[_PY_TOOLCHAIN]
    if tc and tc.py3_runtime and tc.py3_runtime.interpreter_version_info:
        v = tc.py3_runtime.interpreter_version_info
        return "python{}.{}".format(v.major, v.minor)
    return "python3"

def _ament_package_impl(ctx):
    package_name = ament_index_package_name(ctx)
    install_prefix = ctx.attr._install_prefix[BuildSettingInfo].value.rstrip("/")
    pyver = _python_version(ctx)

    # The runfiles tree (what ament_index provides) doubles as the base of
    # the install tree: bin/, lib/, share/ are laid out identically.
    files = {}
    symlinks = {}

    # Packages commonly declare their data/libraries/plugins on a separate
    # `:ament_index` target (used as test data) and merely depend on it from
    # `:ament_package`; absorb those same-package contributions too.
    for dep in ctx.attr.deps:
        if AmentIndexInfo in dep and AmentPackageInfo not in dep and dep[AmentIndexInfo].package_name == package_name:
            symlinks.update(dep[AmentIndexInfo].symlinks)
    symlinks.update(ament_index_symlinks(ctx))
    if ctx.attr.build_type == "cmake":
        # Plain CMake packages are not ament packages: no resource_index entry.
        symlinks.pop("share/ament_index/resource_index/packages/" + package_name, None)
    if not ctx.attr.install_package_xml:
        symlinks.pop("share/" + package_name + "/package.xml", None)
    for path, f in symlinks.items():
        if path.startswith("bin/"):
            # ament installs executables into lib/<pkg>/; only `programs`
            # (below) land in bin/.
            path = "lib/" + package_name + "/" + path[len("bin/"):]
        files[path] = f

    # bin/: user facing programs (e.g. the `ros2` CLI).
    for target in ctx.attr.programs:
        for f in target.files.to_list():
            files["bin/" + f.basename] = f

    # Arbitrary extra files (ament_vendor-style opt/<pkg>/ trees etc.), laid
    # out by rules_pkg's pkg_files(prefix = ..., strip_prefix = ...).
    for target in ctx.attr.install:
        for dest, f in target[PackageFilesInfo].dest_src_map.items():
            files[dest.lstrip("/")] = f

    # Python console_scripts entry points, rendered the way setuptools /
    # ament_python install them (lib/<pkg>/<name> by default, bin/<name> for
    # packages whose setup.cfg sets install_scripts to bin).
    for dest_dir, scripts in (("lib/" + package_name, ctx.attr.console_scripts), ("bin", ctx.attr.console_programs)):
        for script_name, entry_point in scripts.items():
            module, _, func = entry_point.partition(":")
            script = ctx.actions.declare_file(ctx.label.name + "_scripts/" + dest_dir + "/" + script_name)
            ctx.actions.write(
                script,
                "#!/usr/bin/env python3\n" +
                "# EASY-INSTALL-ENTRY-SCRIPT: '{pkg}','console_scripts','{name}'\n".format(pkg = package_name, name = script_name) +
                "import sys\n" +
                "from {module} import {func}\n".format(module = module, func = func.split(".")[0] if func else "main") +
                "if __name__ == '__main__':\n" +
                "    sys.exit({func}())\n".format(func = func or "main"),
                is_executable = True,
            )
            files[dest_dir + "/" + script_name] = script

    # include/<pkg>/...: exported headers. Modern ament installs headers to
    # include/<pkg>/<pkg>/foo.hpp; legacy packages use include/foo.hpp and
    # set include_prefix = "".
    include_prefix = ctx.attr.include_prefix if ctx.attr.include_prefix_set else package_name
    include_dirs = []
    sorted_hdr_prefixes = sorted(ctx.attr.headers_strip_prefixes, key = _prefix_sort_key, reverse = True)
    for target in ctx.attr.headers:
        if PackageFilesInfo in target:
            for dest, f in target[PackageFilesInfo].dest_src_map.items():
                dest = dest.lstrip("/")
                if dest.startswith("include/"):
                    files[dest] = f
                else:
                    files["include/" + (include_prefix + "/" if include_prefix else "") + dest] = f
            continue
        for f in target.files.to_list():
            rel_path = _package_relative(ctx, f)
            stripped, was_gen = strip_gen_prefix(rel_path)
            if was_gen and stripped.startswith("include/"):
                dest = stripped
            else:
                rel = _strip_any(stripped if was_gen else rel_path, ctx.attr.headers_strip_prefix, sorted_hdr_prefixes)
                dest = "include/" + (include_prefix + "/" if include_prefix else "") + rel
            files[dest] = f
    if ctx.attr.headers:
        include_dirs.append("include/" + include_prefix if include_prefix else "include")

    # lib/pythonX.Y/site-packages/...: python modules.
    site_packages = "lib/" + pyver + "/site-packages/"
    for target in ctx.attr.python:
        for f in target.files.to_list():
            if f.basename.endswith(".pyc"):
                continue
            rel = _strip(_package_relative(ctx, f), ctx.attr.python_strip_prefix)
            files[site_packages + rel] = f

    # Exported libraries (lib<name>.so / lib<name>.a in lib/).
    libraries = []
    static_libs = {}
    for target in ctx.attr.libraries:
        for f in target.files.to_list():
            lib_name = _shared_library_name(f.basename)
            libraries.append(lib_name)
            if f.basename.endswith(".a"):
                static_libs[lib_name] = True

    # Dependencies that are themselves ament packages.
    dep_infos = [dep[AmentPackageInfo] for dep in ctx.attr.deps if AmentPackageInfo in dep]
    dependencies = sorted([d.name for d in dep_infos if d.name != package_name and d.name != "rosdistro"])
    dep_targets = {}
    for d in dep_infos:
        for t in d.cmake_targets:
            dep_targets[d.name] = dep_targets.get(d.name, []) + [t]

    # colcon only registers the LD_LIBRARY_PATH hook when lib/ directly holds
    # shared libraries -- not for lib/<pkg>/ executables or plugins,
    # lib/pythonX.Y/, lib/pkgconfig/ or lib/<pkg>/cmake/ alone.
    has_lib = any([
        p.startswith("lib/") and p.count("/") == 1 and
        _is_shared_library(p.split("/")[-1])
        for p in files.keys()
    ])
    has_bin = any([p.startswith("bin/") for p in files.keys()])
    has_pkgconfig = ctx.attr.pkgconfig_hook and any([p.startswith("lib/pkgconfig/") for p in files.keys()])
    has_python = any([p.startswith(site_packages) for p in files.keys()])

    # CMake exported targets: one export set (named after
    # ament_export_targets(<export_name>), default <pkg>) with one
    # <pkg>::<lib> target per exported library -- or, for header-only
    # packages (add_library(<pkg> INTERFACE)), a single INTERFACE target.
    cmake_targets = []
    exports = []
    export_name = ctx.attr.cmake_export_name or package_name
    export_dependencies_list = ctx.attr.cmake_export_dependencies_list
    link_libraries = []
    for d in dependencies:
        link_libraries.extend(dep_targets.get(d, []))
    if not ctx.attr.cmake_export_targets:
        pass
    elif ctx.attr.cmake_export_interface_targets:
        targets = []
        for tgt in ctx.attr.cmake_export_interface_targets:
            cmake_targets.append(package_name + "::" + tgt)
            targets.append({
                "name": tgt,
                "type": "INTERFACE",
                "include_dirs": include_dirs,
                "link_libraries": link_libraries,
            })
        exports.append({"export": export_name, "namespace": package_name, "targets": targets})
    elif ctx.attr.cmake_export_sets:
        for set_name, set_libs in ctx.attr.cmake_export_sets.items():
            targets = []
            for lib in set_libs:
                cmake_targets.append(package_name + "::" + lib)
                is_static = lib in static_libs
                targets.append({
                    "name": lib,
                    "type": "STATIC" if is_static else "SHARED",
                    "location": "lib/lib" + lib + (".a" if is_static else ".so"),
                    "include_dirs": include_dirs,
                    "link_libraries": link_libraries,
                })
            exports.append({"export": set_name, "namespace": package_name, "targets": targets})
    elif libraries:
        targets = []
        for lib in libraries:
            cmake_targets.append(package_name + "::" + lib)
            is_static = lib in static_libs
            targets.append({
                "name": lib,
                "type": "STATIC" if is_static else "SHARED",
                "location": "lib/lib" + lib + (".a" if is_static else ".so"),
                "include_dirs": include_dirs,
                "link_libraries": link_libraries,
            })
        exports.append({"export": export_name, "namespace": package_name, "targets": targets})
    elif ctx.attr.cmake_export_interface and include_dirs:
        cmake_targets.append(package_name + "::" + package_name)
        exports.append({"export": export_name, "namespace": package_name, "targets": [{
            "name": package_name,
            "type": "INTERFACE",
            "include_dirs": include_dirs,
            "link_libraries": link_libraries,
        }]})
    if ctx.attr.cmake_exports:
        # Explicit export sets (e.g. rosidl's nine per-typesupport sets).
        exports = ctx.attr.cmake_exports[AmentCMakeExportsInfo].exports
        extra_deps = getattr(ctx.attr.cmake_exports[AmentCMakeExportsInfo], "dependencies", None) or []
        if extra_deps:
            export_dependencies_list = {d: None for d in list(ctx.attr.cmake_export_dependencies_list or dependencies) + list(extra_deps)}.keys()
        cmake_targets = [e["namespace"] + "::" + t["name"] for e in exports for t in e["targets"]]

    spec = {
        "name": package_name,
        "prefix": install_prefix + "/" + package_name,
        "pyver": pyver,
        "has_lib": has_lib,
        "has_bin": has_bin,
        "has_pkgconfig": has_pkgconfig,
        "has_python": has_python,
        "colcon_hooks": ctx.attr.colcon_hooks,
        "cmake_prefix_path_hook": ctx.attr.cmake_prefix_path_hook,
        "pkg_config_path_hook": ctx.attr.pkg_config_path_hook,
        "python_env_hook": ctx.attr.python_env_hook,
        "libraries": libraries,
        "include_dirs": include_dirs,
        "dependencies": dependencies,
        "exports": exports,
        "env_hooks": ctx.attr.env_hooks,
        "extra_cmake": ctx.attr.cmake_extras,
        "export_include_directories": ctx.attr.cmake_export_include_directories,
        "export_libraries": ctx.attr.cmake_export_libraries,
        "export_library_path": ctx.attr.cmake_export_has_library_target,
        "export_dependencies": ctx.attr.cmake_export_dependencies,
        "export_dependencies_list": list(export_dependencies_list),
        # Python distribution metadata (<pkg>-<ver>-py<X.Y>.egg-info), only
        # for packages that install python modules.
        "console_scripts": dict(ctx.attr.console_scripts.items() + ctx.attr.console_programs.items()),
        "python_top_level": sorted({p[len(site_packages):].split("/")[0]: None for p in files.keys() if p.startswith(site_packages)}.keys()),
    }
    if ctx.attr.build_type:
        spec["build_type"] = ctx.attr.build_type

    # The package's own CMake modules (install(DIRECTORY cmake ...) in ament
    # terms): installed under share/<pkg>/cmake/ preserving their layout
    # relative to `cmake_strip_prefix`.
    for target in ctx.attr.cmake:
        if PackageFilesInfo in target:
            for dest, f in target[PackageFilesInfo].dest_src_map.items():
                dest = dest.lstrip("/")
                if dest.startswith("share/"):
                    files[dest] = f
                else:
                    files["share/" + package_name + "/cmake/" + dest] = f
            continue
        for f in target.files.to_list():
            rel_path = _package_relative(ctx, f)
            stripped, was_gen = strip_gen_prefix(rel_path)
            if was_gen and stripped.startswith("share/" + package_name + "/cmake/"):
                files[stripped] = f
            else:
                rel = _strip(stripped if was_gen else rel_path, ctx.attr.cmake_strip_prefix)
                files["share/" + package_name + "/cmake/" + rel] = f

    spec_file = ctx.actions.declare_file(ctx.label.name + "_install_spec.json")
    ctx.actions.write(spec_file, json.encode(spec))
    generated = ctx.actions.declare_directory(ctx.label.name + "_install/share")
    outputs = [generated]
    args = ctx.actions.args()
    args.add("--spec", spec_file)
    args.add("--out", generated.path)
    if has_python and ctx.attr.egg_info:
        # The egg-info directory is named after the package.xml version, so
        # the generator produces it as a tree rooted at the site-packages dir.
        egg_info = ctx.actions.declare_directory(ctx.label.name + "_install/site-packages")
        args.add("--egg-info-out", egg_info.path)
        outputs.append(egg_info)
        files[site_packages.rstrip("/")] = egg_info
    inputs = [spec_file]
    if ctx.file.package_xml:
        args.add("--package-xml", ctx.file.package_xml)
        inputs.append(ctx.file.package_xml)
    if ctx.file.setup_cfg:
        args.add("--setup-cfg", ctx.file.setup_cfg)
        inputs.append(ctx.file.setup_cfg)
    ctx.actions.run(
        executable = ctx.executable._install_gen,
        arguments = [args],
        inputs = inputs,
        outputs = outputs,
        mnemonic = "AmentInstallGen",
        progress_message = "Generating ament install metadata for %s" % package_name,
    )
    files["share"] = generated

    dest_src_map = {install_prefix + "/" + package_name + "/" + k: v for k, v in files.items()}
    providers = ament_index_providers(ctx, extra_files = files.values())
    return providers + [
        AmentPackageInfo(
            name = package_name,
            files = files,
            deps = ctx.attr.deps,
            cmake_targets = cmake_targets,
        ),
        PackageFilesInfo(dest_src_map = dest_src_map, attributes = {}),
    ]

AMENT_PACKAGE_ATTRS = dict(AMENT_INDEX_ATTRS)
AMENT_PACKAGE_ATTRS.update({
    "programs": attr.label_list(
        allow_files = True,
        doc = "Executables installed to bin/ (user facing CLIs). `executables` go to lib/<pkg>/.",
    ),
    "console_scripts": attr.string_dict(
        doc = "Python entry points {script_name: 'module:function'} installed as lib/<pkg>/<script_name> (ament_python default).",
    ),
    "console_programs": attr.string_dict(
        doc = "Python entry points {script_name: 'module:function'} installed as bin/<script_name>.",
    ),
    "cmake_exports": attr.label(
        providers = [AmentCMakeExportsInfo],
        doc = "Explicit CMake export sets, replacing the single <pkg>::<lib> set derived from `libraries`.",
    ),
    "cmake_export_sets": attr.string_list_dict(
        doc = "Optional mapping of {export_set_name: [lib_names]} when a package splits its `libraries` across multiple ament_export_targets() export sets.",
    ),
    "setup_cfg": attr.label(
        allow_single_file = True,
        doc = "Optional setup.cfg file providing [options.entry_points] for egg-info.",
    ),
    "install": attr.label_list(
        providers = [PackageFilesInfo],
        doc = "Extra files installed verbatim at arbitrary paths under the package's install prefix " +
              "(e.g. opt/<vendor_pkg>/lib/libgz-sim.so for ament_vendor-style packages). Targets must provide " +
              "rules_pkg's PackageFilesInfo (pkg_files / pkg_mklink); each dest_src_map key is taken relative " +
              "to <install_prefix>/<pkg>/ (leading '/' stripped), so pkg_files(prefix = ..., strip_prefix = ...) " +
              "controls the layout.",
    ),
    "python": attr.label_list(
        allow_files = True,
        doc = "py_library targets (or files) installed to lib/pythonX.Y/site-packages/.",
    ),
    "python_strip_prefix": attr.string(doc = "Prefix stripped from python files before installing to site-packages."),
    "headers_strip_prefix": attr.string(default = "include", doc = "Prefix stripped from header paths."),
    "headers_strip_prefixes": attr.string_list(doc = "Optional list of prefixes stripped from header paths (for multi-subdirectory packages)."),
    "include_prefix": attr.string(doc = "Directory under include/ to install headers to; defaults to the package name."),
    "include_prefix_set": attr.bool(default = False),
    "cmake": attr.label_list(allow_files = True, doc = "The package's own CMake modules/files, installed under share/<pkg>/cmake/ (layout preserved relative to cmake_strip_prefix)."),
    "cmake_strip_prefix": attr.string(default = "cmake", doc = "Prefix stripped from `cmake` file paths."),
    "cmake_extras": attr.string_list(doc = "Files (relative to share/<pkg>/cmake/) that <pkg>Config.cmake must include, e.g. ['<pkg>-extras.cmake'] for packages calling ament_package(CONFIG_EXTRAS ...)."),
    "egg_info": attr.bool(default = True, doc = "Generate <pkg>-<version>-py<X.Y>.egg-info (PKG-INFO, top_level.txt, entry_points.txt, ...) next to the installed python modules, like setuptools does."),
    "cmake_export_targets": attr.bool(default = True, doc = "Whether upstream calls ament_export_targets(); set False for packages that only ament_export_libraries()/ament_export_dependencies()."),
    "cmake_export_name": attr.string(doc = "Export set name passed to ament_export_targets() upstream (e.g. 'export_<pkg>'); defaults to the package name."),
    "cmake_export_interface": attr.bool(default = True, doc = "For packages with `headers` but no `libraries`, export a single <pkg>::<pkg> INTERFACE target the way add_library(<pkg> INTERFACE) + ament_export_targets() does."),
    "cmake_export_interface_targets": attr.string_list(doc = "Explicit INTERFACE target names exported by ament_export_targets() (when upstream exports custom or multiple INTERFACE targets)."),
    "cmake_export_include_directories": attr.bool(default = True, doc = "Whether upstream calls ament_export_include_directories() (emits ament_cmake_export_include_directories-extras.cmake)."),
    "cmake_export_libraries": attr.bool(default = True, doc = "Whether upstream calls ament_export_libraries() (emits ament_cmake_export_libraries-extras.cmake and the library_path environment hook)."),
    "cmake_export_has_library_target": attr.bool(default = False, doc = "Whether upstream calls ament_export_targets(... HAS_LIBRARY_TARGET), which adds the library_path environment hook even without ament_export_libraries()."),
    "cmake_export_dependencies": attr.bool(default = True, doc = "Whether upstream calls ament_export_dependencies() (emits ament_cmake_export_dependencies-extras.cmake)."),
    "cmake_export_dependencies_list": attr.string_list(doc = "Explicit ament_export_dependencies() list; defaults to the package.xml build-export dependencies present in `deps`."),
    "env_hooks": attr.string_list(doc = "Extra environment hooks (paths relative to share/<pkg>/) listed in package.dsv."),
    "build_type": attr.string(doc = "Override the build type (ament_cmake / ament_python) read from package.xml."),
    "install_package_xml": attr.bool(default = True, doc = "Whether to install package.xml under share/<pkg>/package.xml."),
    "colcon_hooks": attr.bool(default = True, doc = "Whether to emit colcon hook/* files for plain cmake packages (set False for empty ament_vendor stub packages)."),
    "cmake_prefix_path_hook": attr.bool(default = True, doc = "Whether to emit hook/cmake_prefix_path.{dsv,ps1,sh}."),
    "pkg_config_path_hook": attr.bool(default = True, doc = "Whether to emit hook/pkg_config_path*.{dsv,ps1,sh} for cmake packages."),
    "pkgconfig_hook": attr.bool(default = True, doc = "Whether to emit hook/pkg_config.{dsv,ps1,sh} for cmake packages with lib/pkgconfig/."),
    "python_env_hook": attr.bool(default = True, doc = "Whether to emit environment/pythonpath.{dsv,sh} for ament_cmake packages that install python files without ament_python_install_package()."),
    "_install_prefix": attr.label(default = "@rosdistro//:install_prefix"),
    "_install_gen": attr.label(default = "@rosdistro//ament:install_gen", executable = True, cfg = "exec"),
})

ament_package_rule = rule(
    implementation = _ament_package_impl,
    attrs = AMENT_PACKAGE_ATTRS,
    toolchains = [config_common.toolchain_type(_PY_TOOLCHAIN, mandatory = False)],
    provides = [AmentPackageInfo, PackageFilesInfo],
)

def ament_package(name = None, tar_name = "tar", include_prefix = None, visibility = None, **kwargs):
    """Declare the downstream bundle of this package plus a `:tar` of it.

    Args:
        name: target name (default "ament_package").
        tar_name: name of the per-package tarball target (default "tar").
        include_prefix: directory under include/ for exported headers
            (default: the package name; pass "" for legacy flat layouts).
        visibility: visibility for both targets.
        **kwargs: see ament_index plus programs/python/cmake/env_hooks.
    """
    name = name if name else "ament_package"
    if include_prefix != None:
        kwargs["include_prefix"] = include_prefix
        kwargs["include_prefix_set"] = True
    ament_package_rule(name = name, visibility = visibility, **kwargs)
    pkg_tar(
        name = tar_name,
        srcs = [":" + name],
        extension = "tar.gz",
        visibility = visibility,
        tags = ["manual"],
    )

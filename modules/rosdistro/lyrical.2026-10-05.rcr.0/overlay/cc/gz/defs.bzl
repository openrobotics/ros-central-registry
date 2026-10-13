# Copyright 2026 Open Source Robotics Foundation, Inc.
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

"""Helpers for the gz_*_vendor / sdformat_vendor packages.

colcon's `ament_vendor()` packages install the vendored Gazebo library into
`opt/<vendor_pkg>/{include,lib,share,...}` and add environment hooks that
put those directories on CMAKE_PREFIX_PATH / LD_LIBRARY_PATH / PYTHONPATH /
GZ_CONFIG_PATH. The rules below describe that layout as rules_pkg
`PackageFilesInfo` so it can be fed to `ament_package(install = [...])`.

- `gz_install_headers`: the public headers of cc_library targets (from
  CcInfo), re-rooted under `prefix` (e.g. opt/gz_sim_vendor/include/gz/sim10).
- `gz_install_files`: arbitrary files re-rooted under `prefix`.
- `gz_runfiles`: pick files out of a target's runfiles (e.g. the pybind
  extension a py_library carries in `data`).
- `gz_proto_descriptor_set`: a FileDescriptorSet (with imports) of a
  proto_library, i.e. what gz-msgs ships as `<name>.gz_desc`.
- `gz_vendor_hooks`: the ament_cmake_vendor_package environment hooks.
"""

load("@bazel_skylib//rules:write_file.bzl", "write_file")
load("@protobuf//bazel/common:proto_info.bzl", "ProtoInfo")
load("@rules_cc//cc/common:cc_info.bzl", "CcInfo")
load("@rules_pkg//pkg:providers.bzl", "PackageFilesInfo")

def _repo_relative(f):
    """Path of a file relative to the root of the repository that owns it."""
    path = f.short_path
    if path.startswith("../"):
        return "/".join(path.split("/")[2:])
    return path

def _strip(path, prefixes):
    for prefix in prefixes:
        if not prefix:
            continue
        if not prefix.endswith("/"):
            prefix += "/"
        if path.startswith(prefix):
            return path[len(prefix):]
    return path

def _dest(ctx, rel):
    prefix = ctx.attr.prefix.strip("/")
    return prefix + "/" + rel if prefix else rel

def _strip_include_root(path, prefixes):
    """Drop the include root: an explicit prefix, else everything up to the first `include/`."""
    stripped = _strip(path, prefixes)
    if stripped != path:
        return stripped
    parts = path.split("/")
    for i, part in enumerate(parts[:-1]):
        if part == "include":
            return "/".join(parts[i + 1:])
    return path

def _gz_install_headers_impl(ctx):
    dest_src_map = {}
    for dep in ctx.attr.deps:
        cc = dep[CcInfo].compilation_context
        repo = dep.label.workspace_name
        for h in cc.headers.to_list():
            # Only this library's own headers, not those of its dependencies
            # (which the respective vendor package installs).
            if h.owner.workspace_name != repo and not ctx.attr.all_repositories:
                continue
            rel = _strip_include_root(_repo_relative(h), ctx.attr.strip_prefixes)
            if ctx.attr.include_only and not rel.startswith(ctx.attr.include_only):
                continue
            if rel.endswith((".cc", ".cpp", ".c", ".inc.in")):
                continue
            dest_src_map[_dest(ctx, rel)] = h
    return [
        DefaultInfo(files = depset(dest_src_map.values())),
        PackageFilesInfo(dest_src_map = dest_src_map, attributes = {}),
    ]

gz_install_headers = rule(
    implementation = _gz_install_headers_impl,
    attrs = {
        "deps": attr.label_list(providers = [CcInfo], doc = "cc_library targets whose (transitive) headers are installed."),
        "prefix": attr.string(mandatory = True, doc = "Install directory, e.g. opt/gz_sim_vendor/include/gz/sim10."),
        "strip_prefixes": attr.string_list(
            doc = "Repository-relative prefixes removed from header paths (first match wins); " +
                  "by default everything up to the first `include/` directory is removed.",
        ),
        "include_only": attr.string(doc = "If set, only headers whose stripped path starts with this are installed."),
        "all_repositories": attr.bool(default = False, doc = "Also install headers owned by other repositories."),
    },
    doc = "Installs the headers of cc_library targets (those owned by the same repository) under `prefix`.",
)

def _gz_install_files_impl(ctx):
    dest_src_map = {}
    files = list(ctx.files.srcs)
    for target in ctx.attr.srcs:
        # proto_library: install the .proto sources, not the descriptor set.
        if ProtoInfo in target:
            files.extend(target[ProtoInfo].direct_sources)
    for f in files:
        if ctx.attr.flatten:
            rel = f.basename
        else:
            rel = _strip(_repo_relative(f), ctx.attr.strip_prefixes)
        if ctx.attr.shared_library_prefix and not rel.rsplit("/", 1)[-1].startswith("lib"):
            parts = rel.rsplit("/", 1)
            parts[-1] = "lib" + parts[-1]
            rel = "/".join(parts)
        if ctx.attr.suffix_filter and not rel.endswith(tuple(ctx.attr.suffix_filter)):
            continue
        dest_src_map[_dest(ctx, rel)] = f
    return [
        DefaultInfo(files = depset(dest_src_map.values())),
        PackageFilesInfo(dest_src_map = dest_src_map, attributes = {}),
    ]

gz_install_files = rule(
    implementation = _gz_install_files_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True, doc = "Files (or targets producing files) to install."),
        "prefix": attr.string(mandatory = True, doc = "Install directory, e.g. opt/gz_sim_vendor/lib."),
        "strip_prefixes": attr.string_list(doc = "Repository-relative prefixes removed from file paths (first match wins)."),
        "flatten": attr.bool(default = False, doc = "Install every file directly under `prefix` (basename only)."),
        "shared_library_prefix": attr.bool(
            default = False,
            doc = "Prepend `lib` to file names that lack it (BCR gz plugins are named gz-sim-foo-system.so, colcon installs libgz-sim-foo-system.so).",
        ),
        "suffix_filter": attr.string_list(doc = "If set, only files with one of these suffixes are installed."),
    },
    doc = "Installs files under `prefix`, keeping their repository-relative layout.",
)

def _gz_runfiles_impl(ctx):
    files = []
    for dep in ctx.attr.srcs:
        all_files = depset(
            dep[DefaultInfo].files.to_list(),
            transitive = [dep[DefaultInfo].default_runfiles.files],
        ).to_list()
        for f in all_files:
            if ctx.attr.suffixes and not f.basename.endswith(tuple(ctx.attr.suffixes)):
                continue
            if ctx.attr.exclude_suffixes and f.basename.endswith(tuple(ctx.attr.exclude_suffixes)):
                continue
            if ctx.attr.owner_repo and not f.owner.workspace_name.startswith(ctx.attr.owner_repo):
                continue
            files.append(f)
    return [DefaultInfo(files = depset(files))]

gz_runfiles = rule(
    implementation = _gz_runfiles_impl,
    attrs = {
        "srcs": attr.label_list(),
        "suffixes": attr.string_list(doc = "Keep only files with one of these suffixes."),
        "exclude_suffixes": attr.string_list(doc = "Drop files with one of these suffixes."),
        "owner_repo": attr.string(doc = "Keep only files owned by a repository whose (canonical) name starts with this."),
    },
    doc = "Collects (a filtered subset of) the files and runfiles of targets, e.g. a py_library's pybind extension.",
)

def _gz_proto_descriptor_set_impl(ctx):
    out = ctx.actions.declare_file(ctx.attr.out or ctx.label.name + ".gz_desc")
    sets = depset(transitive = [d[ProtoInfo].transitive_descriptor_sets for d in ctx.attr.deps]).to_list()

    # A FileDescriptorSet is `repeated FileDescriptorProto file = 1;`, so the
    # concatenation of several serialized sets is itself a valid set
    # containing the union of their files (= `protoc --include_imports`).
    ctx.actions.run_shell(
        inputs = sets,
        outputs = [out],
        command = "cat " + " ".join(["'%s'" % s.path for s in sets]) + " > '%s'" % out.path,
        mnemonic = "GzProtoDescriptorSet",
    )
    return [DefaultInfo(files = depset([out]))]

gz_proto_descriptor_set = rule(
    implementation = _gz_proto_descriptor_set_impl,
    attrs = {
        "deps": attr.label_list(providers = [ProtoInfo]),
        "out": attr.string(doc = "Output file name (default <name>.gz_desc)."),
    },
    doc = "Serialized FileDescriptorSet of proto_library targets including all imports.",
)

_VENDOR_SH = """# generated from ament_cmake_vendor_package/cmake/templates/vendor_package.sh.in

if [ -d "$AMENT_CURRENT_PREFIX/opt/{vendor}/bin" ]; then
  ament_prepend_unique_value PATH "$AMENT_CURRENT_PREFIX/opt/{vendor}/bin"
fi

if [ -d "$AMENT_CURRENT_PREFIX/opt/{vendor}/lib" ]; then
  ament_prepend_unique_value LD_LIBRARY_PATH "$AMENT_CURRENT_PREFIX/opt/{vendor}/lib"
fi

if [ -d "$AMENT_CURRENT_PREFIX/opt/{vendor}/lib64" ]; then
  ament_prepend_unique_value LD_LIBRARY_PATH "$AMENT_CURRENT_PREFIX/opt/{vendor}/lib64"
fi
"""

_VENDOR_DSV = """prepend-non-duplicate-if-exists;PATH;opt/{vendor}/bin
prepend-non-duplicate-if-exists;LD_LIBRARY_PATH;opt/{vendor}/lib
prepend-non-duplicate-if-exists;LD_LIBRARY_PATH;opt/{vendor}/lib64
"""

_CMAKE_PREFIX_SH = """# generated from ament_cmake_vendor_package/cmake/templates/vendor_package_cmake_prefix.sh.in

ament_prepend_unique_value CMAKE_PREFIX_PATH "$AMENT_CURRENT_PREFIX/opt/{vendor}"
"""

_CMAKE_PREFIX_DSV = "prepend-non-duplicate;CMAKE_PREFIX_PATH;opt/{vendor}\n"

_HOOK_CMAKE_PREFIX_SH = """# generated from colcon_core/shell/template/hook_prepend_value.sh.em

_colcon_prepend_unique_value CMAKE_PREFIX_PATH "$COLCON_CURRENT_PREFIX"
"""

_HOOK_CMAKE_PREFIX_DSV = "prepend-non-duplicate;CMAKE_PREFIX_PATH;\n"

_DUMMY_SH = "# Dummy .sh file needed for .dsv file to be sourced.\n"

_CONFIG_PATH_DSV = "prepend-non-duplicate-if-exists;GZ_CONFIG_PATH;opt/{vendor}/share/gz\n"

_PYTHONPATH_DSV = "prepend-non-duplicate-if-exists;PYTHONPATH;opt/{vendor}/lib/python\n"

_VENDOR_BAT = """:: generated from ament_cmake_vendor_package/cmake/templates/vendor_package.bat.in
@echo off

call:ament_prepend_unique_value PATH "%AMENT_CURRENT_PREFIX%\\opt\\{vendor}\\bin"
call:ament_prepend_unique_value LD_LIBRARY_PATH "%AMENT_CURRENT_PREFIX%\\opt\\{vendor}\\lib"
call:ament_prepend_unique_value LD_LIBRARY_PATH "%AMENT_CURRENT_PREFIX%\\opt\\{vendor}\\lib64"

goto:eof

:: Prepend non-duplicate values to environment variables
:: using semicolons as separators and avoiding trailing separators.
:: first argument: the name of the result variable
:: second argument: the value
:ament_prepend_unique_value
  setlocal enabledelayedexpansion
  :: arguments
  set "listname=%~1"
  set "value=%~2"
  :: skip if path doesn't exist
  if NOT EXIST "%value%" (
    goto:eof
  )
  :: expand the list variable
  set "list=!%listname%!"
  :: check if the list contains the value
  set "is_duplicate="
  if "%list%" NEQ "" (
    for %%v in ("%list:;=";"%") do (
      if "%%~v" == "%value%" set "is_duplicate=1"
    )
  )
  :: if it is not a duplicate prepend it
  if "%is_duplicate%" == "" (
    :: if not empty, prepend a semi-colon
    if "!list!" NEQ "" set "list=;!list!"
    :: prepend the value
    set "list=%value%!list!"
  )
  endlocal & (
    :: set result variable in parent scope
    set "%~1=%list%"
  )
goto:eof
"""

_CMAKE_PREFIX_BAT = """:: generated from ament_cmake_vendor_package/cmake/templates/vendor_package_cmake_prefix.bat.in
@echo off

call:ament_prepend_unique_value CMAKE_PREFIX_PATH "%AMENT_CURRENT_PREFIX%\\opt\\{vendor}"

goto:eof

:: Prepend non-duplicate values to environment variables
:: using semicolons as separators and avoiding trailing separators.
:: first argument: the name of the result variable
:: second argument: the value
:ament_prepend_unique_value
  setlocal enabledelayedexpansion
  :: arguments
  set "listname=%~1"
  set "value=%~2"
  :: skip if path doesn't exist
  if NOT EXIST "%value%" (
    goto:eof
  )
  :: expand the list variable
  set "list=!%listname%!"
  :: check if the list contains the value
  set "is_duplicate="
  if "%list%" NEQ "" (
    for %%v in ("%list:;=";"%") do (
      if "%%~v" == "%value%" set "is_duplicate=1"
    )
  )
  :: if it is not a duplicate prepend it
  if "%is_duplicate%" == "" (
    :: if not empty, prepend a semi-colon
    if "!list!" NEQ "" set "list=;!list!"
    :: prepend the value
    set "list=%value%!list!"
  )
  endlocal & (
    :: set result variable in parent scope
    set "%~1=%list%"
  )
goto:eof
"""

def gz_vendor_hooks(name, vendor, gz_config_path = True, pythonpath = True, visibility = None):
    """The environment hooks `ament_vendor()` installs for a vendor package.

    Declares a `gz_install_files` target `name` (pass it to
    `ament_package(install = [...])`) and returns the list to pass as
    `ament_package(env_hooks = ...)`.

    Args:
        name: name of the resulting install target.
        vendor: the vendor package name (e.g. "gz_sim_vendor"); the vendored
            library lives under opt/<vendor>/.
        gz_config_path: also export GZ_CONFIG_PATH=opt/<vendor>/share/gz.
        pythonpath: also export PYTHONPATH=opt/<vendor>/lib/python.
        visibility: visibility of the install target.

    Returns:
        The hook paths (relative to share/<vendor>/) for `env_hooks`.
    """
    files = {
        "hook/cmake_prefix_path.sh": _HOOK_CMAKE_PREFIX_SH,
        "hook/cmake_prefix_path.dsv": _HOOK_CMAKE_PREFIX_DSV,
        "environment/vendor_package.bat": _VENDOR_BAT.format(vendor = vendor),
        "environment/vendor_package.sh": _VENDOR_SH.format(vendor = vendor),
        "environment/vendor_package.dsv": _VENDOR_DSV.format(vendor = vendor),
        "environment/vendor_package_cmake_prefix.bat": _CMAKE_PREFIX_BAT.format(vendor = vendor),
        "environment/vendor_package_cmake_prefix.sh": _CMAKE_PREFIX_SH.format(vendor = vendor),
        "environment/vendor_package_cmake_prefix.dsv": _CMAKE_PREFIX_DSV.format(vendor = vendor),
    }
    env_hooks = [
        "hook/cmake_prefix_path.sh",
        "hook/cmake_prefix_path.dsv",
        "environment/vendor_package.sh",
        "environment/vendor_package.dsv",
        "environment/vendor_package_cmake_prefix.sh",
        "environment/vendor_package_cmake_prefix.dsv",
    ]
    if gz_config_path:
        files["environment/%s.sh" % vendor] = _DUMMY_SH
        files["environment/%s.dsv" % vendor] = _CONFIG_PATH_DSV.format(vendor = vendor)
        env_hooks.extend([
            "environment/%s.sh" % vendor,
            "environment/%s.dsv" % vendor,
        ])
    if pythonpath:
        files["environment/%s_pythonpath.dsv" % vendor] = _PYTHONPATH_DSV.format(vendor = vendor)
        env_hooks.append("environment/%s_pythonpath.dsv" % vendor)
    outs = []
    for rel, content in files.items():
        out = "_" + name + "/" + vendor + "/" + rel
        write_file(
            name = (name + "_" + rel).replace("/", "_").replace(".", "_"),
            out = out,
            content = content.split("\n"),
            visibility = ["//visibility:private"],
        )
        outs.append(out)
    vp_out = "_" + name + "/ament_index/resource_index/vendor_packages/" + vendor
    write_file(
        name = (name + "_vendor_package_index").replace("/", "_").replace(".", "_"),
        out = vp_out,
        content = [""],
        visibility = ["//visibility:private"],
    )
    outs.append(vp_out)
    gz_install_files(
        name = name,
        srcs = outs,
        prefix = "share",
        strip_prefixes = ["_" + name],
        visibility = visibility,
    )
    return sorted(env_hooks)

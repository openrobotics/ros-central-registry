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

"""Bazel rules for running ROS launch files."""

load("@rules_python//python:defs.bzl", "PyInfo", _py_binary = "py_binary")
load("@rules_python//python/api:api.bzl", "py_common")

def _launch_deps_impl(ctx):
    py_info = py_common.get(ctx).merge_py_infos(
        transitive = [
            dep[PyInfo]
            for dep in ctx.attr.deps
            if PyInfo in dep
        ],
    )
    symlinks = {}
    runfiles_list = []
    for dep in ctx.attr.deps:
        runfiles_list.append(dep[DefaultInfo].default_runfiles)
        runfiles_list.append(ctx.runfiles(transitive_files = dep[DefaultInfo].files))

    # Executables can be listed in either `deps` or `data`; both must be
    # reachable as lib/<pkg>/<name> so that launch_ros' Node(package=...,
    # executable=...) can find them. (Runfiles of `data` are added by the
    # py_binary itself.)
    for dep in ctx.attr.deps + ctx.attr.data_executables:
        exec_file = dep[DefaultInfo].files_to_run.executable if dep[DefaultInfo].files_to_run else None
        if exec_file:
            pkg_name = dep.label.workspace_name.removesuffix("+")
            if not pkg_name:
                pkg_name = ctx.label.workspace_name.removesuffix("+")
            names = {exec_file.basename: True}
            target_basename = dep.label.name.rsplit("/", 1)[-1]
            if target_basename:
                names[target_basename] = True
                if pkg_name and target_basename == pkg_name + "_main":
                    names[pkg_name] = True
            for n in names:
                symlinks["bin/" + n] = exec_file
                if pkg_name:
                    symlinks["lib/" + pkg_name + "/" + n] = exec_file
    return [
        py_info,
        DefaultInfo(
            runfiles = ctx.runfiles(symlinks = symlinks).merge_all(runfiles_list),
        ),
    ]

_launch_deps = rule(
    implementation = _launch_deps_impl,
    attrs = {
        "data_executables": attr.label_list(allow_files = True),
        "deps": attr.label_list(providers = [DefaultInfo]),
    } | py_common.API_ATTRS,
    provides = [PyInfo, DefaultInfo],
)

def _normalize_dep_key(dep):
    s = str(dep)
    if s.startswith("@@"):
        s = "@" + s[2:]
    if s.startswith(":") and native.package_name() == "":
        repo = native.repository_name().lstrip("@").rstrip("+")
        if repo:
            return "@" + repo + "//" + s
    if "//" not in s and s.startswith("@"):
        repo = s[1:].rstrip("+")
        return "@" + repo + "//:" + repo
    if "//" in s and s.startswith("@"):
        repo, _, pkg_target = s[1:].partition("//")
        repo = repo.rstrip("+")
        if ":" not in pkg_target:
            default_target = pkg_target.rsplit("/", 1)[-1] if pkg_target else repo
            pkg_target = pkg_target + ":" + default_target
        return "@" + repo + "//" + pkg_target
    return s

def _merge_deps(deps, extra_deps):
    result = []
    seen = {}
    for d in list(deps) + list(extra_deps):
        key = _normalize_dep_key(d)
        if key not in seen:
            seen[key] = True
            result.append(d)
    return result

def _src_label(src):
    if src.startswith((":", "@", "/")):
        return src
    return ":" + src

def _normalize_data_key(item):
    s = str(item)
    if s.startswith(":"):
        return s[1:]
    return s

def _merge_data(data, extra_data):
    result = list(data)
    seen = {_normalize_data_key(d): True for d in result}
    for d in extra_data:
        key = _normalize_data_key(d)
        if key not in seen:
            seen[key] = True
            result.append(d)
    return result

def launch_binary(name, src, data = [], deps = [], args = [], **kwargs):
    """Define a runnable Bazel target for a launch file.

    Args:
        name: Name of the target (e.g. "example.launch").
        src: Path or label of the launch file (.py, .xml, or .yaml).
        data: Runtime data dependencies (typically :ament_index targets).
        deps: Additional Python library dependencies.
        args: Additional arguments passed to the launch runner.
        **kwargs: Additional keyword arguments forwarded to py_binary.
    """
    src_label = _src_label(src)
    extra_deps = [
        Label("@launch//:launch"),
        Label("@launch//bazel:rcr_launch_guard"),
        Label("@rules_python//python/runfiles"),
    ]
    if src.endswith(".xml"):
        extra_deps.append(Label("@launch_xml"))
    elif src.endswith((".yaml", ".yml")):
        extra_deps.append(Label("@launch_yaml"))

    imports = kwargs.pop("imports", ["."])
    main_script = Label("@launch//bazel:launch_main.py")

    deps_target = "_" + name + "_launch_deps"
    _launch_deps(
        name = deps_target,
        data_executables = data,
        deps = _merge_deps(deps, extra_deps),
        visibility = ["//visibility:private"],
    )

    _py_binary(
        name = name,
        main = main_script,
        srcs = [main_script],
        args = ["$(location %s)" % src_label] + list(args),
        data = _merge_data(data, [src_label]),
        deps = [":" + deps_target],
        imports = imports,
        **kwargs
    )

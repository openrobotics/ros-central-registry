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

"""Bazel rules for running ROS launch tests."""

load("@rules_python//python:defs.bzl", _py_test = "py_test")

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

def launch_test(name, src, data = [], deps = [], args = [], **kwargs):
    """Define a Bazel test target for a launch test file.

    Args:
        name: Name of the test target (e.g. "test_example.launch").
        src: Path or label of the launch test file.
        data: Runtime data dependencies (typically :ament_index targets).
        deps: Additional Python library dependencies.
        args: Additional arguments passed to launch_test (e.g. "key:=value").
        **kwargs: Additional keyword arguments forwarded to py_test.
    """
    src_label = _src_label(src)
    extra_deps = [
        Label("@launch//:launch"),
        Label("@launch_testing//:launch_testing"),
        Label("@launch_xml//:launch_xml"),
        Label("@launch_yaml//:launch_yaml"),
        Label("@rules_python//python/runfiles"),
    ]

    tags = list(kwargs.pop("tags", []))
    if "launch" not in tags:
        tags.append("launch")

    imports = kwargs.pop("imports", ["."])
    main_script = Label("@launch_testing//bazel:launch_test_main.py")

    _py_test(
        name = name,
        main = main_script,
        srcs = [main_script],
        args = ["$(location %s)" % src_label] + list(args),
        data = _merge_data(data, [src_label]),
        deps = _merge_deps(deps, extra_deps),
        imports = imports,
        tags = tags,
        **kwargs
    )

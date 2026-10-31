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
"""Install-layout rules for rosidl interface packages.

The per-message aspects (rosidl_generator_c, rosidl_typesupport_*, ...) each
produce one small shared library per interface, which is what in-tree Bazel
consumers link/dlopen. `colcon`/`ament_cmake` instead installs ONE shared
library per typesupport kind and package:

    lib/lib<pkg>__rosidl_generator_c.so
    lib/lib<pkg>__rosidl_generator_py.so
    lib/lib<pkg>__rosidl_typesupport_c.so
    lib/lib<pkg>__rosidl_typesupport_cpp.so
    lib/lib<pkg>__rosidl_typesupport_fastrtps_c.so
    lib/lib<pkg>__rosidl_typesupport_fastrtps_cpp.so
    lib/lib<pkg>__rosidl_typesupport_introspection_c.so
    lib/lib<pkg>__rosidl_typesupport_introspection_cpp.so

The rules in this file reproduce that layout for `ament_package` without
changing what in-tree consumers use:

- `rosidl_bundled_library` links the static archives of exactly this
  package's interfaces for one typesupport kind into one `lib<pkg>__<kind>.so`
  (whole-archive), dynamically linked against the sibling-kind bundles of the
  same package, the runtime shared libraries (rosidl_runtime_c, fastcdr, ...)
  and the bundles of the interface packages it depends on.
- `rosidl_install` lays out headers, python modules, interface definition
  files and the rosidl-specific cmake extras exactly like colcon
  (`include/<pkg>/<pkg>/msg/*.h`, `lib/pythonX.Y/site-packages/<pkg>/msg/*.py`,
  `share/<pkg>/msg/*.msg|.idl|.json`, `share/<pkg>/cmake/*.cmake`).
- `rosidl_cmake_exports` describes the nine CMake export sets colcon ships so
  `ament_package` renders matching `*Export.cmake` files.
"""

load("@rosdistro//ament:defs.bzl", "AmentCMakeExportsInfo")
load("@rosidl_adapter//:defs.bzl", "ROSIDL_COMMON_ATTRS", "RosIdlInfo", "RosInterfaceInfo", "rosidl_adapter_aspect", "rosidl_link_shared_library")
load("@rosidl_generator_c//:defs.bzl", "RosCBindingsInfo", "RosTypeDescriptionInfo", "rosidl_generator_c_aspect", "rosidl_generator_type_description_aspect")
load("@rosidl_generator_cpp//:defs.bzl", "RosCcBindingsInfo", "rosidl_generator_cpp_aspect")
load("@rosidl_generator_py//:defs.bzl", "RosPyBindingsInfo", "rosidl_generator_py_aspect")
load("@rosidl_typesupport_c//:defs.bzl", "RosCTypesupportInfo", "rosidl_typesupport_c_aspect")
load("@rosidl_typesupport_cpp//:defs.bzl", "RosCcTypesupportInfo", "rosidl_typesupport_cpp_aspect")
load("@rosidl_typesupport_fastrtps_c//:defs.bzl", "RosCTypesupportFastRTPSInfo", "rosidl_typesupport_fastrtps_c_aspect")
load("@rosidl_typesupport_fastrtps_cpp//:defs.bzl", "RosCcTypesupportFastRTPSInfo", "rosidl_typesupport_fastrtps_cpp_aspect")
load("@rosidl_typesupport_introspection_c//:defs.bzl", "RosCTypesupportIntrospectionInfo", "rosidl_typesupport_introspection_c_aspect")
load("@rosidl_typesupport_introspection_cpp//:defs.bzl", "RosCcTypesupportIntrospectionInfo", "rosidl_typesupport_introspection_cpp_aspect")
load("@rules_cc//cc:defs.bzl", "CcInfo", "cc_common")
load("@rules_cc//cc:find_cc_toolchain.bzl", "find_cc_toolchain", "use_cc_toolchain")
load("@rules_cc//cc/common:cc_shared_library_info.bzl", "CcSharedLibraryInfo")
load("@rules_pkg//pkg:providers.bzl", "PackageFilesInfo")
load(":rules.bzl", "RosidlSharedLibraryInfo")

# Typesupport kinds, in the order ament_cmake_export_targets lists them.
# `provider` is the per-message aspect provider carrying the kind's CcInfo.
KINDS = [
    "rosidl_generator_c",
    "rosidl_typesupport_fastrtps_c",
    "rosidl_generator_cpp",
    "rosidl_typesupport_fastrtps_cpp",
    "rosidl_typesupport_introspection_c",
    "rosidl_typesupport_c",
    "rosidl_typesupport_introspection_cpp",
    "rosidl_typesupport_cpp",
    "rosidl_generator_py",
]

# Kinds that produce a shared library (rosidl_generator_cpp is header only).
LIBRARY_KINDS = [k for k in KINDS if k != "rosidl_generator_cpp"]

# Kinds that install headers under include/<pkg>/<pkg>/.
HEADER_KINDS = [
    "rosidl_generator_c",
    "rosidl_generator_cpp",
    "rosidl_typesupport_fastrtps_c",
    "rosidl_typesupport_fastrtps_cpp",
    "rosidl_typesupport_introspection_c",
    "rosidl_typesupport_introspection_cpp",
]

# Kinds whose CMake export set is named export_<pkg>__<kind> (the others are
# named <pkg>__<kind>), mirroring rosidl_cmake.
_EXPORT_PREFIXED_KINDS = [
    "rosidl_generator_c",
    "rosidl_generator_cpp",
    "rosidl_typesupport_fastrtps_c",
    "rosidl_typesupport_fastrtps_cpp",
    "rosidl_generator_py",
]

# Python typesupport extension modules colcon installs next to the package.
PY_TYPESUPPORTS = [
    "rosidl_typesupport_c",
    "rosidl_typesupport_fastrtps_c",
    "rosidl_typesupport_introspection_c",
]

_KIND_PROVIDERS = {
    "rosidl_generator_c": RosCBindingsInfo,
    "rosidl_generator_cpp": RosCcBindingsInfo,
    "rosidl_generator_py": RosPyBindingsInfo,
    "rosidl_typesupport_c": RosCTypesupportInfo,
    "rosidl_typesupport_cpp": RosCcTypesupportInfo,
    "rosidl_typesupport_fastrtps_c": RosCTypesupportFastRTPSInfo,
    "rosidl_typesupport_fastrtps_cpp": RosCcTypesupportFastRTPSInfo,
    "rosidl_typesupport_introspection_c": RosCTypesupportIntrospectionInfo,
    "rosidl_typesupport_introspection_cpp": RosCcTypesupportIntrospectionInfo,
}

# INTERFACE_LINK_LIBRARIES of the exported CMake targets, per kind, as
# rosidl_cmake/ament_cmake emit them. `<pkg>` is replaced with the package
# name; dependency interface packages are appended as <dep>::<dep>__<kind>.
_CMAKE_LINK_LIBRARIES = {
    "rosidl_generator_c": [
        "rosidl_runtime_c::rosidl_runtime_c",
        "rosidl_typesupport_interface::rosidl_typesupport_interface",
        "rcutils::rcutils",
    ],
    "rosidl_typesupport_fastrtps_c": [
        "fastcdr",
        "rosidl_runtime_c::rosidl_runtime_c",
        "rosidl_typesupport_fastrtps_c::rosidl_typesupport_fastrtps_c",
        "rosidl_typesupport_interface::rosidl_typesupport_interface",
        "<pkg>::<pkg>__rosidl_generator_c",
    ],
    "rosidl_generator_cpp": [
        "rosidl_runtime_c::rosidl_runtime_c",
        "rosidl_runtime_cpp::rosidl_runtime_cpp",
        "rosidl_typesupport_interface::rosidl_typesupport_interface",
        "<pkg>::<pkg>__rosidl_generator_c",
    ],
    "rosidl_typesupport_fastrtps_cpp": [
        "fastcdr",
        "rmw::rmw",
        "rosidl_runtime_c::rosidl_runtime_c",
        "rosidl_runtime_cpp::rosidl_runtime_cpp",
        "rosidl_typesupport_interface::rosidl_typesupport_interface",
        "rosidl_typesupport_fastrtps_cpp::rosidl_typesupport_fastrtps_cpp",
        "<pkg>::<pkg>__rosidl_generator_c",
        "<pkg>::<pkg>__rosidl_generator_cpp",
    ],
    "rosidl_typesupport_introspection_c": [
        "<pkg>::<pkg>__rosidl_generator_c",
        "rosidl_runtime_c::rosidl_runtime_c",
        "rosidl_typesupport_interface::rosidl_typesupport_interface",
        "rosidl_typesupport_introspection_c::rosidl_typesupport_introspection_c",
    ],
    "rosidl_typesupport_c": [
        "<pkg>::<pkg>__rosidl_generator_c",
    ],
    "rosidl_typesupport_introspection_cpp": [
        "<pkg>::<pkg>__rosidl_generator_c",
        "<pkg>::<pkg>__rosidl_generator_cpp",
        "rosidl_runtime_c::rosidl_runtime_c",
        "rosidl_typesupport_interface::rosidl_typesupport_interface",
        "rosidl_typesupport_introspection_cpp::rosidl_typesupport_introspection_cpp",
    ],
    "rosidl_typesupport_cpp": [
        "<pkg>::<pkg>__rosidl_generator_c",
        "<pkg>::<pkg>__rosidl_generator_cpp",
    ],
    "rosidl_generator_py": [
        "<pkg>::<pkg>__rosidl_generator_c",
        "<pkg>::<pkg>__rosidl_typesupport_c",
    ],
}

# Kinds that only exist to carry CMake metadata for the python bindings.
_CMAKE_EXPORT_INCLUDE_KINDS = HEADER_KINDS

RosidlBundledLibraryInfo = provider(
    "One colcon-style `lib<pkg>__<kind>` library bundling a package's interfaces.",
    fields = {
        "kind": "typesupport kind, one of KINDS",
        "package_name": "ROS package name",
        "library": "File: the shared library (None for header-only kinds)",
        "linker_input": "LinkerInput to dynamically link against the library (None for header-only kinds)",
        "dep_packages": "list of interface package names this kind's code depends on",
    },
)

# Bundled libraries of other kinds of the same package each kind links
# against, in dependency order (a kind only lists kinds declared before it).
BUNDLE_LIB_DEPS = [
    ("rosidl_generator_c", []),
    ("rosidl_generator_cpp", []),
    ("rosidl_typesupport_c", ["rosidl_generator_c"]),
    ("rosidl_typesupport_cpp", ["rosidl_generator_c"]),
    ("rosidl_typesupport_fastrtps_c", ["rosidl_generator_c"]),
    ("rosidl_typesupport_fastrtps_cpp", ["rosidl_generator_c", "rosidl_typesupport_fastrtps_c"]),
    ("rosidl_typesupport_introspection_c", ["rosidl_generator_c"]),
    ("rosidl_typesupport_introspection_cpp", ["rosidl_generator_c"]),
    ("rosidl_generator_py", ["rosidl_generator_c", "rosidl_typesupport_c"]),
]

def kind_closure(kind):
    """Kinds a bundle of `kind` (transitively) links against, plus `kind`.

    Args:
        kind: typesupport kind.

    Returns:
        The kinds, in BUNDLE_LIB_DEPS (i.e. dependency) order.
    """
    needed = {kind: True}
    for k, lib_deps in reversed(BUNDLE_LIB_DEPS):
        if k in needed:
            for lib_dep in lib_deps:
                needed[lib_dep] = True
    return [k for k, _ in BUNDLE_LIB_DEPS if k in needed]

_PY_TOOLCHAIN = "@rules_python//python:toolchain_type"

_RosidlPackageGraphInfo = provider(
    "Transitive (package, dep_package) edges across an interface dependency graph.",
    fields = ["edges"],
)

def _rosidl_package_graph_aspect_impl(target, ctx):
    if RosIdlInfo not in target:
        return []
    package_name = target[RosIdlInfo].package_name
    direct = []
    transitive = []
    for dep in getattr(ctx.rule.attr, "deps", []):
        if RosIdlInfo in dep and dep[RosIdlInfo].package_name != package_name:
            direct.append((package_name, dep[RosIdlInfo].package_name))
        if _RosidlPackageGraphInfo in dep:
            transitive.append(dep[_RosidlPackageGraphInfo].edges)
    return [
        _RosidlPackageGraphInfo(
            edges = depset(direct = direct, transitive = transitive),
        ),
    ]

_rosidl_package_graph_aspect = aspect(
    implementation = _rosidl_package_graph_aspect_impl,
    attr_aspects = ["deps"],
    required_providers = [RosInterfaceInfo],
    required_aspect_providers = [RosIdlInfo],
    provides = [_RosidlPackageGraphInfo],
)

# All aspects any of the rules below need; superset of what the per-language
# `*_ros_library` rules apply, in an order satisfying every aspect's
# required_aspect_providers (fastrtps_c before fastrtps_cpp, c before py ...).
_ALL_ASPECTS = [
    rosidl_adapter_aspect,
    _rosidl_package_graph_aspect,
    rosidl_generator_type_description_aspect,
    rosidl_generator_c_aspect,
    rosidl_generator_cpp_aspect,
    rosidl_typesupport_introspection_c_aspect,
    rosidl_typesupport_introspection_cpp_aspect,
    rosidl_typesupport_fastrtps_c_aspect,
    rosidl_typesupport_fastrtps_cpp_aspect,
    rosidl_typesupport_c_aspect,
    rosidl_typesupport_cpp_aspect,
    rosidl_generator_py_aspect,
]

def _is_darwin(cc_toolchain):
    return "apple" in cc_toolchain.target_gnu_system_name or "darwin" in cc_toolchain.target_gnu_system_name

def _is_windows(cc_toolchain):
    return "windows" in cc_toolchain.target_gnu_system_name or "mingw" in cc_toolchain.target_gnu_system_name

def shared_library_name(package_name, kind, cc_toolchain):
    """Platform file name of a bundled library.

    Args:
        package_name: ROS package name.
        kind: typesupport kind.
        cc_toolchain: the C++ toolchain, to pick the platform suffix.

    Returns:
        lib<pkg>__<kind>.so / lib<pkg>__<kind>.dylib / <pkg>__<kind>.dll
    """
    if _is_windows(cc_toolchain):
        return "{}__{}.dll".format(package_name, kind)
    ext = ".dylib" if _is_darwin(cc_toolchain) else ".so"
    return "lib{}__{}{}".format(package_name, kind, ext)

def _dynamic_linker_inputs(targets):
    inputs = []
    for target in targets:
        if RosidlBundledLibraryInfo in target:
            if target[RosidlBundledLibraryInfo].linker_input:
                inputs.append(target[RosidlBundledLibraryInfo].linker_input)
        elif CcSharedLibraryInfo in target:
            inputs.append(target[CcSharedLibraryInfo].linker_input)
        else:
            fail("{} is neither a rosidl_bundled_library nor a cc_shared_library".format(target.label))
    return inputs

def _dep_packages(deps, package_name):
    """Interface packages the package's interfaces (transitively) depend on."""
    merged = depset(
        transitive = [dep[_RosidlPackageGraphInfo].edges for dep in deps if _RosidlPackageGraphInfo in dep],
    )
    edges = {}
    for pkg, dep_pkg in merged.to_list():
        edges.setdefault(pkg, {})[dep_pkg] = True
    packages = {}
    todo = edges.get(package_name, {}).keys()
    for _ in range(len(edges) + 1):
        if not todo:
            break
        next_todo = []
        for pkg in todo:
            if pkg in packages or pkg == package_name:
                continue
            packages[pkg] = True
            next_todo.extend(edges.get(pkg, {}).keys())
        todo = next_todo
    return sorted(packages.keys())

def _rosidl_bundled_library_impl(ctx):
    kind = ctx.attr.kind
    package_name = ctx.attr.package_name
    dep_packages = _dep_packages(ctx.attr.deps, package_name)

    if kind not in LIBRARY_KINDS:
        # Header-only kind: nothing to link, but the CMake export still
        # needs to know which dependency packages it links against.
        return [
            DefaultInfo(files = depset()),
            RosidlBundledLibraryInfo(
                kind = kind,
                package_name = package_name,
                library = None,
                linker_input = None,
                dep_packages = dep_packages,
            ),
        ]

    cc_toolchain = find_cc_toolchain(ctx)
    soname = shared_library_name(package_name, kind, cc_toolchain)

    if kind != "rosidl_generator_py":
        # The C/C++ kinds are exactly the libraries cc_ros_shared_library
        # (`:cc_shared`) links -- same names, same contents, already linked
        # against the dependency packages' libraries.
        shared = ctx.attr.shared[RosidlSharedLibraryInfo]
        if kind not in shared.libraries:
            fail("{}: {} has no {} library".format(ctx.label, ctx.attr.shared.label, kind))
        library = shared.libraries[kind]
        if library.basename != soname:
            fail("{}: {} is {} but expected {}".format(ctx.label, ctx.attr.shared.label, library.basename, soname))
        return [
            DefaultInfo(files = depset([library])),
            RosidlBundledLibraryInfo(
                kind = kind,
                package_name = package_name,
                library = library,
                linker_input = shared.linker_inputs[kind],
                dep_packages = dep_packages,
            ),
        ]

    # lib<pkg>__rosidl_generator_py.so: all of the package's Python
    # typesupport code in one library (the per-interface extension modules
    # py_ros_library links are the Bazel-side equivalent). It calls into the
    # dependency packages' libraries of the same kind, which they install
    # themselves (`py_deps`).
    archives = [
        dep[RosPyBindingsInfo].static_library
        for dep in ctx.attr.deps
        if RosPyBindingsInfo in dep and dep[RosPyBindingsInfo].static_library
    ]
    if not archives:
        fail("{}: found no {} archives for package '{}' in deps".format(ctx.label, kind, package_name))
    linked = rosidl_link_shared_library(
        ctx,
        name = "{}__{}".format(package_name, kind),
        static_libraries = archives,
        linker_inputs = _dynamic_linker_inputs(ctx.attr.lib_deps + ctx.attr.py_deps + ctx.attr.dynamic_deps),
        allow_undefined_symbols = True,
        symlink_dir = "rosidl_" + package_name,
    )
    if linked.file.basename != soname:
        fail("{}: linked {} but expected {}".format(ctx.label, linked.file.basename, soname))
    return [
        DefaultInfo(files = depset([linked.file])),
        RosidlBundledLibraryInfo(
            kind = kind,
            package_name = package_name,
            library = linked.file,
            linker_input = linked.linker_input,
            dep_packages = dep_packages,
        ),
    ]

rosidl_bundled_library = rule(
    implementation = _rosidl_bundled_library_impl,
    doc = "Links one package's interfaces for one typesupport kind into lib<pkg>__<kind>.so, like colcon installs.",
    toolchains = use_cc_toolchain(),
    fragments = ["cpp"],
    attrs = {
        "deps": attr.label_list(
            aspects = _ALL_ASPECTS,
            providers = [RosInterfaceInfo],
            doc = "This package's interfaces (the same list as core_generators' deps).",
        ),
        "kind": attr.string(mandatory = True, values = KINDS),
        "package_name": attr.string(mandatory = True),
        "shared": attr.label(
            mandatory = True,
            providers = [RosidlSharedLibraryInfo],
            doc = "The package's cc_ros_shared_library, which links the C/C++ kinds.",
        ),
        "lib_deps": attr.label_list(
            providers = [RosidlBundledLibraryInfo],
            doc = "Bundled libraries of other kinds of the same package this one links against.",
        ),
        "py_deps": attr.label_list(
            providers = [RosidlBundledLibraryInfo],
            doc = "The dependency packages' bundled libraries of the same kind (rosidl_generator_py only).",
        ),
        "dynamic_deps": attr.label_list(
            doc = "Runtime shared libraries (cc_shared_library / collect_transitive_dynamic_deps) to link against.",
        ),
    } | ROSIDL_COMMON_ATTRS,
    provides = [RosidlBundledLibraryInfo],
)

# ---------------------------------------------------------------------------
# Install layout
# ---------------------------------------------------------------------------

def _python_version(ctx):
    tc = ctx.toolchains[_PY_TOOLCHAIN]
    if tc and tc.py3_runtime and tc.py3_runtime.interpreter_version_info:
        v = tc.py3_runtime.interpreter_version_info
        return "python{}.{}".format(v.major, v.minor)
    return "python3"

def _dep_relative(dep, f):
    """Path of an aspect-generated file relative to the interface's package dir.

    Aspects declare their outputs under the message target's package (e.g.
    msg/std_msgs/msg/detail/bool__struct.h for //msg:Bool), so strip the
    repository and package prefixes to get std_msgs/msg/detail/bool__struct.h.
    """
    path = f.short_path
    if path.startswith("../"):
        path = "/".join(path.split("/")[2:])
    package = dep.label.package
    if package and path.startswith(package + "/"):
        path = path[len(package) + 1:]
    return path

def _interface_members(interface_type, name):
    """All messages/services/actions an interface definition expands to.

    Returns a list of (kind, Name) with kind in msg/srv/action, in the order
    rosidl_generator_py's entry point template registers them.
    """
    if interface_type == "msg":
        return [("msg", name)]
    if interface_type == "srv":
        return [
            ("msg", name + "_Request"),
            ("msg", name + "_Response"),
            ("msg", name + "_Event"),
            ("srv", name),
        ]
    if interface_type == "action":
        members = [
            ("msg", name + "_Goal"),
            ("msg", name + "_Result"),
            ("msg", name + "_Feedback"),
        ]
        for srv in ("SendGoal", "GetResult"):
            members += [
                ("msg", "{}_{}_Request".format(name, srv)),
                ("msg", "{}_{}_Response".format(name, srv)),
                ("msg", "{}_{}_Event".format(name, srv)),
                ("srv", "{}_{}".format(name, srv)),
            ]
        members += [
            ("msg", name + "_FeedbackMessage"),
            ("action", name),
        ]
        return members
    fail("unknown interface type " + interface_type)

def _snake_case(pascal_case):
    """rosidl_pycommon.convert_camel_case_to_lower_case_underscore."""
    result = ""
    padded = " " + pascal_case + " "
    for i in range(len(pascal_case)):
        prev_char, char, next_char = padded[i:i + 3].elems()
        if char.isupper() and next_char.islower() and prev_char != " ":
            result += "_"
        elif char.isupper() and (prev_char.islower() or prev_char.isdigit()):
            result += "_"
        result += char.lower()
    return result

def _py_init_lines(package_name, interface_type, module_name, name):
    """Lines rosidl_generator_py writes to <pkg>/<type>/__init__.py for one interface."""
    line = "from {}.{}.{} import {{0}} as {{0}}  # noqa: F401\n".format(package_name, interface_type, module_name)
    names = [name]
    if interface_type == "srv":
        names += [name + "_Event", name + "_Request", name + "_Response"]
    elif interface_type == "action":
        names += [
            name + "_GetResult_Event",
            name + "_GetResult_Request",
            name + "_GetResult_Response",
            name + "_SendGoal_Event",
            name + "_SendGoal_Request",
            name + "_SendGoal_Response",
        ]
    return "".join([line.format(n) for n in names])

def _py_typesupport_c_entry_point(package_name, interfaces):
    """C source of <pkg>_s__rosidl_typesupport_c: the union of the per-interface modules.

    The per-interface python typesupport modules (<pkg>__<type>__<code>_s__rosidl_typesupport_c,
    produced by rosidl_generator_py's aspect and bundled into lib<pkg>__rosidl_generator_py)
    each register the create/destroy/convert/type_support capsules of one
    interface. The package level module colcon ships merges them.
    """
    inits = [
        "{}__{}__{}_s__rosidl_typesupport_c".format(package_name, i.interface_type, i.interface_code)
        for i in interfaces
    ]
    lines = [
        "// generated by rosidl_core_generators (rosidl_bundled_python_module)",
        "// generated code does not contain a copyright notice",
        "#include <Python.h>",
        "",
    ]
    lines += ["PyMODINIT_FUNC PyInit_{}(void);".format(i) for i in inits]
    lines += [
        "",
        "static PyMethodDef {}__methods[] = {{".format(package_name),
        "  {NULL, NULL, 0, NULL}  /* sentinel */",
        "};",
        "",
        "static struct PyModuleDef {}__module = {{".format(package_name),
        "  PyModuleDef_HEAD_INIT,",
        '  "_{}_support",'.format(package_name),
        '  "_{}_doc",'.format(package_name),
        "  -1,  /* -1 means that the module keeps state in global variables */",
        "  {}__methods,".format(package_name),
        "  NULL,",
        "  NULL,",
        "  NULL,",
        "  NULL,",
        "};",
        "",
        "static int merge_module(PyObject * pymodule, PyObject * (* init)(void))",
        "{",
        "  PyObject * other = init();",
        "  if (!other) {",
        "    return -1;",
        "  }",
        "  PyObject * src = PyModule_GetDict(other);",
        "  PyObject * dst = PyModule_GetDict(pymodule);",
        "  PyObject * key = NULL;",
        "  PyObject * value = NULL;",
        "  Py_ssize_t pos = 0;",
        "  int err = 0;",
        "  while (!err && PyDict_Next(src, &pos, &key, &value)) {",
        "    if (!PyCapsule_CheckExact(value)) {",
        "      continue;  // skip __name__, __doc__, ...",
        "    }",
        "    err = PyDict_SetItem(dst, key, value);",
        "  }",
        "  Py_DECREF(other);",
        "  return err;",
        "}",
        "",
        "PyMODINIT_FUNC",
        "PyInit_{}_s__rosidl_typesupport_c(void)".format(package_name),
        "{",
        "  PyObject * pymodule = NULL;",
        "  pymodule = PyModule_Create(&{}__module);".format(package_name),
        "  if (!pymodule) {",
        "    return NULL;",
        "  }",
    ]
    for init in inits:
        lines += [
            "  if (merge_module(pymodule, PyInit_{})) {{".format(init),
            "    Py_XDECREF(pymodule);",
            "    return NULL;",
            "  }",
        ]
    lines += [
        "  return pymodule;",
        "}",
        "",
    ]
    return "\n".join(lines)

def _py_typesupport_entry_point(package_name, typesupport, interfaces):
    """C source of <pkg>_s__<typesupport>: type_support_* capsules for every interface.

    Mirrors rosidl_generator_py/resource/_idl_pkg_typesupport_entry_point.c.em
    for the non-default typesupports, which only expose the typesupport handles.
    """
    lines = [
        "// generated by rosidl_core_generators (rosidl_bundled_python_module)",
        "// generated code does not contain a copyright notice",
        "#include <Python.h>",
        "",
        "static PyMethodDef {}__methods[] = {{".format(package_name),
        "  {NULL, NULL, 0, NULL}  /* sentinel */",
        "};",
        "",
        "static struct PyModuleDef {}__module = {{".format(package_name),
        "  PyModuleDef_HEAD_INIT,",
        '  "_{}_support",'.format(package_name),
        '  "_{}_doc",'.format(package_name),
        "  -1,  /* -1 means that the module keeps state in global variables */",
        "  {}__methods,".format(package_name),
        "  NULL,",
        "  NULL,",
        "  NULL,",
        "  NULL,",
        "};",
        "",
    ]
    entries = []  # (symbol, capsule name)
    for i in interfaces:
        for member_type, member_name in _interface_members(i.interface_type, i.interface_name):
            symbol = "{ts}__get_{what}_type_support_handle__{pkg}__{type}__{name}".format(
                ts = typesupport,
                what = {"msg": "message", "srv": "service", "action": "action"}[member_type],
                pkg = package_name,
                type = i.interface_type,
                name = member_name,
            )
            capsule = "type_support_{}__{}__{}".format(member_type, i.interface_type, _snake_case(member_name))
            entries.append((symbol, capsule))
            lines.append("const void * {}(void);".format(symbol))
    lines += [
        "",
        "PyMODINIT_FUNC",
        "PyInit_{}_s__{}(void)".format(package_name, typesupport),
        "{",
        "  PyObject * pymodule = NULL;",
        "  pymodule = PyModule_Create(&{}__module);".format(package_name),
        "  if (!pymodule) {",
        "    return NULL;",
        "  }",
        "  PyObject * capsule = NULL;",
    ]
    for symbol, capsule in entries:
        lines += [
            "",
            "  capsule = PyCapsule_New((void *){}(), NULL, NULL);".format(symbol),
            "  if (!capsule) {",
            "    Py_XDECREF(pymodule);",
            "    return NULL;",
            "  }",
            '  if (PyModule_AddObject(pymodule, "{}", capsule)) {{'.format(capsule),
            "    Py_XDECREF(capsule);",
            "    Py_XDECREF(pymodule);",
            "    return NULL;",
            "  }",
        ]
    lines += [
        "",
        "  return pymodule;",
        "}",
        "",
    ]
    return "\n".join(lines)

def _rosidl_bundled_python_module_impl(ctx):
    package_name = ctx.attr.package_name
    typesupport = ctx.attr.typesupport
    interfaces = [dep[RosIdlInfo] for dep in ctx.attr.deps]

    source = ctx.actions.declare_file("{}/_{}_s.ep.{}.c".format(ctx.label.name, package_name, typesupport))
    if typesupport == "rosidl_typesupport_c":
        content = _py_typesupport_c_entry_point(package_name, interfaces)
    else:
        content = _py_typesupport_entry_point(package_name, typesupport, interfaces)
    ctx.actions.write(source, content)

    cc_toolchain = find_cc_toolchain(ctx)
    feature_configuration = cc_common.configure_features(
        ctx = ctx,
        cc_toolchain = cc_toolchain,
        requested_features = ctx.features,
        unsupported_features = ctx.disabled_features,
    )
    _, compilation_outputs = cc_common.compile(
        name = ctx.label.name,
        actions = ctx.actions,
        feature_configuration = feature_configuration,
        cc_toolchain = cc_toolchain,
        srcs = [source],
        compilation_contexts = [dep[CcInfo].compilation_context for dep in ctx.attr.python_headers],
    )
    is_darwin = _is_darwin(cc_toolchain)
    linking_outputs = cc_common.link(
        name = "{}/{}_s__{}".format(ctx.label.name, package_name, typesupport),
        actions = ctx.actions,
        feature_configuration = feature_configuration,
        cc_toolchain = cc_toolchain,
        output_type = "dynamic_library",
        compilation_outputs = compilation_outputs,
        linking_contexts = [
            cc_common.create_linking_context(
                linker_inputs = depset(_dynamic_linker_inputs(ctx.attr.lib_deps), order = "topological"),
            ),
            ctx.attr._link_extra_lib[CcInfo].linking_context,
        ],
        user_link_flags = ["-Wl,-undefined,dynamic_lookup"] if is_darwin else [],
    )
    lib_to_link = linking_outputs.library_to_link
    linked = lib_to_link.resolved_symlink_dynamic_library or lib_to_link.dynamic_library

    # Python extension modules are not prefixed with "lib".
    module = ctx.actions.declare_file("{}/{}_s__{}.so".format(ctx.label.name, package_name, typesupport))
    ctx.actions.symlink(output = module, target_file = linked)
    return [
        DefaultInfo(files = depset([module, source])),
        OutputGroupInfo(module = depset([module]), source = depset([source])),
    ]

rosidl_bundled_python_module = rule(
    implementation = _rosidl_bundled_python_module_impl,
    doc = "The package level python typesupport extension module <pkg>_s__<typesupport> colcon installs into site-packages/<pkg>/.",
    toolchains = use_cc_toolchain(),
    fragments = ["cpp"],
    attrs = {
        "_link_extra_lib": attr.label(
            default = Label("@bazel_tools//tools/cpp:link_extra_lib"),
            providers = [CcInfo],
        ),
        "deps": attr.label_list(
            aspects = [rosidl_adapter_aspect],
            providers = [RosInterfaceInfo],
        ),
        "package_name": attr.string(mandatory = True),
        "typesupport": attr.string(mandatory = True, values = PY_TYPESUPPORTS),
        "lib_deps": attr.label_list(providers = [RosidlBundledLibraryInfo]),
        "python_headers": attr.label_list(
            providers = [CcInfo],
            default = [Label("@rules_python//python/cc:current_py_cc_headers")],
        ),
    },
)

_INCLUDE_DIRS_EXTRAS = """# generated from ament_cmake_export_include_directories/cmake/ament_cmake_export_include_directories-extras.cmake.in

set(_exported_include_dirs "${{{pkg}_DIR}}/../../../include/{pkg}")

# append include directories to {pkg}_INCLUDE_DIRS
# warn about not existing paths
if(NOT _exported_include_dirs STREQUAL "")
  find_package(ament_cmake_core QUIET REQUIRED)
  foreach(_exported_include_dir ${{_exported_include_dirs}})
    if(NOT IS_DIRECTORY "${{_exported_include_dir}}")
      message(WARNING "Package '{pkg}' exports the include directory '${{_exported_include_dir}}' which doesn't exist")
    endif()
    normalize_path(_exported_include_dir "${{_exported_include_dir}}")
    list(APPEND {pkg}_INCLUDE_DIRS "${{_exported_include_dir}}")
  endforeach()
endif()
"""

_ROSIDL_CMAKE_EXTRAS = """# generated from rosidl_cmake/cmake/rosidl_cmake-extras.cmake.in

set({pkg}_IDL_FILES "{idl_files}")
set({pkg}_INTERFACE_FILES "{interface_files}")
"""

_ROSIDL_AGGREGATE_TARGET_EXTRAS = """# generated from rosidl_cmake/cmake/rosidl_cmake_aggregate_target-extras.cmake.in

# Create a convenience aggregate target {pkg}::{pkg}
# that links all generated interface targets, so downstream packages can use
# a single modern CMake target name instead of ${{{pkg}_TARGETS}}.
if({pkg}_TARGETS AND NOT TARGET {pkg}::{pkg})
  add_library({pkg}::{pkg} INTERFACE IMPORTED)
  set_target_properties({pkg}::{pkg} PROPERTIES
    INTERFACE_LINK_LIBRARIES "${{{pkg}_TARGETS}}")
endif()
"""

_ROSIDL_TYPESUPPORT_LIBRARIES_EXTRAS = """# generated from
# rosidl_cmake/cmake/template/rosidl_cmake_export_typesupport_libraries.cmake.in

set(_exported_typesupport_libraries
  "{typesupport_libraries}")

# populate {pkg}_LIBRARIES_<suffix>
if(NOT _exported_typesupport_libraries STREQUAL "")
  # loop over typesupport libraries
  foreach(_tuple ${{_exported_typesupport_libraries}})
    string(REPLACE ":" ";" _tuple "${{_tuple}}")
    list(GET _tuple 0 _suffix)
    list(GET _tuple 1 _library)

    if(NOT IS_ABSOLUTE "${{_library}}")
      # search for library target relative to this CMake file
      set(_lib "NOTFOUND")
      find_library(
        _lib NAMES "${{_library}}"
        PATHS "${{{pkg}_DIR}}/../../../lib"
        NO_DEFAULT_PATH NO_CMAKE_FIND_ROOT_PATH
      )

      if(NOT _lib)
        # the library wasn't found
        message(FATAL_ERROR
          "Package '{pkg}' exports the typesupport library '${{_library}}' which couldn't be found")
      elseif(NOT IS_ABSOLUTE "${{_lib}}")
        # the found library must be an absolute path
        message(FATAL_ERROR
          "Package '{pkg}' found the typesupport library '${{_library}}' at '${{_lib}}' "
          "which is not an absolute path")
      elseif(NOT EXISTS "${{_lib}}")
        # the found library must exist
        message(FATAL_ERROR "Package '{pkg}' found the typesupport library '${{_lib}}' which doesn't exist")
      else()
        list(APPEND {pkg}_LIBRARIES${{_suffix}} ${{_cfg}} "${{_lib}}")
      endif()

    else()
      if(NOT EXISTS "${{_library}}")
        # the found library must exist
        message(WARNING "Package '{pkg}' exports the typesupport library '${{_library}}' which doesn't exist")
      else()
        list(APPEND {pkg}_LIBRARIES${{_suffix}} "${{_library}}")
      endif()
    endif()
  endforeach()
endif()
"""

_ROSIDL_TYPESUPPORT_TARGETS_EXTRAS = """# generated from
# rosidl_cmake/cmake/template/rosidl_cmake_export_typesupport_targets.cmake.in

set(_exported_typesupport_targets
  "{typesupport_targets}")

# populate {pkg}_TARGETS_<suffix>
if(NOT _exported_typesupport_targets STREQUAL "")
  # loop over typesupport targets
  foreach(_tuple ${{_exported_typesupport_targets}})
    string(REPLACE ":" ";" _tuple "${{_tuple}}")
    list(GET _tuple 0 _suffix)
    list(GET _tuple 1 _target)

    set(_target "{pkg}::${{_target}}")
    if(NOT TARGET "${{_target}}")
      # the exported target must exist
      message(WARNING "Package '{pkg}' exports the typesupport target '${{_target}}' which doesn't exist")
    else()
      list(APPEND {pkg}_TARGETS${{_suffix}} "${{_target}}")
    endif()
  endforeach()
endif()
"""

def _rosidl_install_impl(ctx):
    package_name = ctx.attr.package_name
    site_packages = "lib/{}/site-packages/".format(_python_version(ctx))
    files = {}  # install path relative to <prefix>/<pkg>/ -> File

    def add(dest, f):
        if dest not in files:
            files[dest] = f

    # Interface definitions: share/<pkg>/<type>/Foo.{msg,srv,action,idl,json}
    interface_files = []
    idl_files = []
    py_inits = {}  # interface type -> list of (module, lines)
    for dep in ctx.attr.deps:
        info = dep[RosIdlInfo]
        interface_type = info.interface_type
        share = "share/{}/{}/".format(package_name, interface_type)
        src = dep[RosInterfaceInfo].src
        add(share + src.basename, src)
        interface_files.append(interface_type + "/" + src.basename)
        add(share + info.idl.basename, info.idl)
        idl_files.append(interface_type + "/" + info.idl.basename)
        for json_file in dep[RosTypeDescriptionInfo].jsons.to_list():
            if json_file.owner == dep.label and json_file.basename == info.interface_name + ".json":
                add(share + json_file.basename, json_file)

        # Headers: include/<pkg>/<pkg>/<type>/...
        for kind in HEADER_KINDS:
            provider = _KIND_PROVIDERS[kind]
            for hdr in dep[provider].cc_info.compilation_context.direct_public_headers:
                add("include/{}/{}".format(package_name, _dep_relative(dep, hdr)), hdr)

        # Python: lib/pythonX.Y/site-packages/<pkg>/<type>/_foo.py (+ _foo_s.c)
        py_info = dep[RosPyBindingsInfo]
        for f in py_info.transitive_sources.to_list():
            if f.owner != dep.label:
                continue
            if f.extension == "py":
                add(site_packages + _dep_relative(dep, f), f)
        if hasattr(py_info, "sources"):
            for f in py_info.sources.to_list():
                if f.owner == dep.label and f.basename.endswith("_s.c"):
                    add(site_packages + _dep_relative(dep, f), f)
        module_name = "_" + info.interface_code
        py_inits.setdefault(interface_type, []).append(
            (module_name, _py_init_lines(package_name, interface_type, module_name, info.interface_name)),
        )

    # Rust crate sources: share/<pkg>/rust/{Cargo.toml,build.rs,src/...}
    if ctx.attr.deps:
        rust_dir = ctx.actions.declare_directory(ctx.label.name + "/rust")
        rs_templates = ctx.files._rs_templates
        rs_template_dir = rs_templates[0].dirname
        for f in rs_templates:
            if f.basename == "Cargo.toml.em":
                rs_template_dir = f.dirname
                break
        rs_idls = []
        rs_idl_tuples = []
        rs_interface_files = []
        rs_dep_pkgs = {}
        for dep in ctx.attr.deps:
            idl = dep[RosIdlInfo].idl
            rel = "{}/{}".format(dep[RosIdlInfo].interface_type, idl.basename)
            base = idl.path[:-len(rel) - 1]
            rs_idls.append(idl)
            rs_idl_tuples.append(base + ":" + rel)
            rs_interface_files.append(idl.path)
            for json_file in dep[RosTypeDescriptionInfo].jsons.to_list():
                owner_pkg = json_file.owner.workspace_name.removesuffix("+")
                if owner_pkg and owner_pkg != package_name:
                    rs_dep_pkgs[owner_pkg] = json_file.path
        rs_args_file = ctx.actions.declare_file(ctx.label.name + "/rosidl_generator_rs_args.json")
        ctx.actions.write(rs_args_file, json.encode({
            "package_name": package_name,
            "package_version": "0.0.0",
            "output_dir": rust_dir.dirname,
            "template_dir": "__PWD__/" + rs_template_dir,
            "idl_tuples": rs_idl_tuples,
            "ros_interface_files": rs_interface_files,
            "ros_interface_dependencies": ["{}:{}".format(pkg, p) for pkg, p in sorted(rs_dep_pkgs.items())],
            "target_dependencies": [],
        }))
        ctx.actions.run_shell(
            tools = [ctx.executable._rs_generator],
            inputs = depset([rs_args_file] + rs_idls + rs_templates),
            outputs = [rust_dir],
            command = """
sed "s|__PWD__|$(pwd)|g" "{args}" > "${{TMPDIR:-/tmp}}/rs_args_$$.json"
"{gen}" --generator-arguments-file "${{TMPDIR:-/tmp}}/rs_args_$$.json" --typesupport-impls rosidl_typesupport_c
rm -f "${{TMPDIR:-/tmp}}/rs_args_$$.json"
""".format(
                args = rs_args_file.path,
                gen = ctx.executable._rs_generator.path,
            ),
            env = {"ROS_DISTRO": "lyrical"},
            mnemonic = "RosidlInstallRust",
            progress_message = "Generating Rust sources for %s" % package_name,
        )
        add("share/{}/rust".format(package_name), rust_dir)

    # Python package __init__.py files.
    pkg_init = ctx.actions.declare_file(ctx.label.name + "/python/__init__.py")
    ctx.actions.write(pkg_init, "")
    add(site_packages + package_name + "/__init__.py", pkg_init)
    for interface_type, entries in py_inits.items():
        init = ctx.actions.declare_file("{}/python/{}/__init__.py".format(ctx.label.name, interface_type))
        ctx.actions.write(init, "".join([lines for _, lines in sorted(entries)]))
        add("{}{}/{}/__init__.py".format(site_packages, package_name, interface_type), init)

    # Package level python typesupport modules and their sources.
    for target in ctx.attr.python_modules:
        for f in target[OutputGroupInfo].module.to_list():
            add(site_packages + package_name + "/" + f.basename, f)
        for f in target[OutputGroupInfo].source.to_list():
            add(site_packages + package_name + "/" + f.basename, f)

    # Bundled libraries not exported through ament_package's `libraries`.
    for target in ctx.attr.libraries:
        for f in target.files.to_list():
            add("lib/" + f.basename, f)

    # ament_index resource listing the interface files.
    rosidl_interfaces = ctx.actions.declare_file(ctx.label.name + "/rosidl_interfaces")
    ctx.actions.write(rosidl_interfaces, "\n".join(sorted(idl_files + interface_files)))
    add("share/ament_index/resource_index/rosidl_interfaces/" + package_name, rosidl_interfaces)

    # rosidl specific cmake extras (listed in <pkg>Config.cmake by ament_package).
    cmake_files = []

    def cmake(name, content):
        f = ctx.actions.declare_file("{}/cmake/{}".format(ctx.label.name, name))
        ctx.actions.write(f, content)
        cmake_files.append(f)
        add("share/{}/cmake/{}".format(package_name, name), f)

    typesupport_libraries = ";".join([
        "__{0}:{1}__{0}".format(kind, package_name)
        for kind in ["rosidl_typesupport_fastrtps_c", "rosidl_typesupport_fastrtps_cpp"]
    ])
    typesupport_targets = ";".join([
        "{suffix}:{pkg}__{kind}".format(
            suffix = "" if kind == "rosidl_generator_py" else "__" + kind,
            pkg = package_name,
            kind = kind,
        )
        for kind in KINDS
    ])
    cmake("rosidl_cmake-extras.cmake", _ROSIDL_CMAKE_EXTRAS.format(
        pkg = package_name,
        idl_files = ";".join(idl_files),
        interface_files = ";".join(interface_files),
    ))
    cmake("ament_cmake_export_include_directories-extras.cmake", _INCLUDE_DIRS_EXTRAS.format(pkg = package_name))
    cmake("rosidl_cmake_export_typesupport_targets-extras.cmake", _ROSIDL_TYPESUPPORT_TARGETS_EXTRAS.format(
        pkg = package_name,
        typesupport_targets = typesupport_targets,
    ))
    cmake("rosidl_cmake_export_typesupport_libraries-extras.cmake", _ROSIDL_TYPESUPPORT_LIBRARIES_EXTRAS.format(
        pkg = package_name,
        typesupport_libraries = typesupport_libraries,
    ))
    cmake("rosidl_cmake_aggregate_target-extras.cmake", _ROSIDL_AGGREGATE_TARGET_EXTRAS.format(pkg = package_name))

    return [
        DefaultInfo(files = depset(files.values())),
        OutputGroupInfo(cmake = depset(cmake_files)),
        PackageFilesInfo(dest_src_map = files, attributes = {}),
    ]

rosidl_install = rule(
    implementation = _rosidl_install_impl,
    doc = "Everything colcon installs for an interface package besides the exported libraries, as a PackageFilesInfo for ament_package(install = ...).",
    toolchains = [config_common.toolchain_type(_PY_TOOLCHAIN, mandatory = False)],
    attrs = {
        "deps": attr.label_list(
            aspects = _ALL_ASPECTS,
            providers = [RosInterfaceInfo],
        ),
        "package_name": attr.string(mandatory = True),
        "libraries": attr.label_list(allow_files = True, doc = "Bundled libraries to install to lib/."),
        "python_modules": attr.label_list(providers = [OutputGroupInfo]),
        "_rs_generator": attr.label(
            default = Label("@rosidl_generator_rs//:cli"),
            executable = True,
            cfg = "exec",
        ),
        "_rs_templates": attr.label(
            default = Label("@rosidl_generator_rs//:interface_templates"),
            allow_files = True,
        ),
    },
    provides = [PackageFilesInfo],
)

def _rosidl_skip_install_impl(ctx):
    package_name = ctx.attr.package_name
    files = {}

    def cmake(name, content):
        f = ctx.actions.declare_file("{}/cmake/{}".format(ctx.label.name, name))
        ctx.actions.write(f, content)
        files["share/{}/cmake/{}".format(package_name, name)] = f

    cmake("rosidl_cmake-extras.cmake", _ROSIDL_CMAKE_EXTRAS.format(
        pkg = package_name,
        idl_files = "",
        interface_files = "",
    ))
    cmake("rosidl_cmake_aggregate_target-extras.cmake", _ROSIDL_AGGREGATE_TARGET_EXTRAS.format(pkg = package_name))
    return [
        DefaultInfo(files = depset(files.values())),
        PackageFilesInfo(dest_src_map = files, attributes = {}),
    ]

rosidl_skip_install = rule(
    implementation = _rosidl_skip_install_impl,
    doc = "CMake extras colcon still installs when a package calls rosidl_generate_interfaces(... SKIP_INSTALL).",
    attrs = {
        "package_name": attr.string(mandatory = True),
    },
    provides = [PackageFilesInfo],
)

# ament_export_dependencies() rosidl_generate_interfaces() always declares
# for an interface package (in the order rosidl_cmake emits them), after the
# interface packages it depends on.
_CMAKE_EXPORT_DEPENDENCIES = [
    "rosidl_runtime_c",
    "rosidl_typesupport_interface",
    "rcutils",
    "fastcdr",
    "rosidl_runtime_c",
    "rosidl_runtime_cpp",
    "rosidl_typesupport_fastrtps_c",
    "rosidl_typesupport_fastrtps_cpp",
    "rosidl_typesupport_interface",
    "rosidl_runtime_cpp",
    "fastcdr",
    "rmw",
    "rosidl_runtime_c",
    "rosidl_runtime_cpp",
    "rosidl_typesupport_fastrtps_cpp",
    "rosidl_typesupport_interface",
    "rosidl_runtime_c",
    "rosidl_typesupport_c",
    "rosidl_typesupport_interface",
    "rosidl_runtime_c",
    "rosidl_runtime_cpp",
    "rosidl_typesupport_c",
    "rosidl_typesupport_cpp",
    "rosidl_typesupport_interface",
    "rosidl_default_runtime",
]

def _rosidl_cmake_exports_impl(ctx):
    package_name = ctx.attr.package_name
    bundles = {b[RosidlBundledLibraryInfo].kind: b[RosidlBundledLibraryInfo] for b in ctx.attr.bundles}
    exports = []
    dep_packages = []
    for kind in KINDS:
        if kind not in bundles:
            continue
        bundle = bundles[kind]
        for dep in bundle.dep_packages:
            if dep not in dep_packages:
                dep_packages.append(dep)
        link_libraries = [lib.replace("<pkg>", package_name) for lib in _CMAKE_LINK_LIBRARIES[kind]]
        link_libraries += ["{0}::{0}__{1}".format(dep, kind) for dep in bundle.dep_packages]
        target_name = "{}__{}".format(package_name, kind)
        target = {
            "name": target_name,
            "type": "SHARED" if bundle.library else "INTERFACE",
            "include_dirs": ["include/" + package_name] if kind in _CMAKE_EXPORT_INCLUDE_KINDS else [],
            "link_libraries": link_libraries,
        }
        if bundle.library:
            target["location"] = "lib/" + bundle.library.basename
        exports.append({
            "export": ("export_" + target_name) if kind in _EXPORT_PREFIXED_KINDS else target_name,
            "namespace": package_name,
            "targets": [target],
        })
    if ctx.attr.interface_library:
        # Additional CMake target some interface/mixed packages export alongside
        # their messages (e.g. sensor_msgs::sensor_msgs_library INTERFACE or
        # rmw_dds_common::rmw_dds_common_library SHARED).
        extra_target = {
            "name": ctx.attr.interface_library,
            "type": "SHARED" if ctx.attr.interface_library_location else "INTERFACE",
            "include_dirs": ["include/" + package_name],
            "link_libraries": ctx.attr.interface_library_link_libraries,
        }
        if ctx.attr.interface_library_location:
            extra_target["location"] = ctx.attr.interface_library_location
        exports.append({
            "export": ctx.attr.interface_library_export or ("export_" + package_name),
            "namespace": package_name,
            "targets": [extra_target],
        })
    return [AmentCMakeExportsInfo(
        exports = exports,
        dependencies = sorted(dep_packages) + _CMAKE_EXPORT_DEPENDENCIES,
    )]

rosidl_cmake_exports = rule(
    implementation = _rosidl_cmake_exports_impl,
    doc = "The CMake export sets (one per typesupport kind) for ament_package(cmake_exports = ...).",
    attrs = {
        "bundles": attr.label_list(providers = [RosidlBundledLibraryInfo]),
        "package_name": attr.string(mandatory = True),
        "interface_library": attr.string(
            doc = "Name of an additional CMake target exported alongside messages (e.g. sensor_msgs_library).",
        ),
        "interface_library_export": attr.string(
            doc = "Export set name for `interface_library` (defaults to 'export_<pkg>').",
        ),
        "interface_library_location": attr.string(
            doc = "Relative path (e.g. 'lib/libfoo.so') if `interface_library` is a SHARED target; empty for INTERFACE.",
        ),
        "interface_library_link_libraries": attr.string_list(
            doc = "INTERFACE_LINK_LIBRARIES of `interface_library` (e.g. sensor_msgs::sensor_msgs__rosidl_typesupport_cpp).",
        ),
    },
    provides = [AmentCMakeExportsInfo],
)

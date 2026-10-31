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
"""Starlark rules for compiling ROS message generator libraries.

Every interface (`ros_interface` target) is turned into generated code by a
chain of aspects, one per typesupport *kind* (rosidl_generator_c,
rosidl_typesupport_fastrtps_cpp, ...). Each kind produces one static archive
per interface. `rosidl_cc_aspect`, applied last, folds all C/C++ kinds of one
interface into a `CcInfo` whose linker input is owned by the interface target
-- the `cc_library` half, at interface granularity, so a static link keeps
only the interfaces a binary references.

`cc_ros_library` (`:cc`/`:c`) merges those for a package. `cc_ros_shared_library`
(`:cc_shared`/`:c_shared`) is the `cc_shared_library` half: it links the
package's archives into one shared library per kind (`lib<pkg>__<kind>.so`,
the layout colcon installs) and exports every interface target, so consumers
link them exactly like any other library in the registry:

    cc_library(name = "foo_library", deps = ["@std_msgs//:cc"])
    cc_shared_library(name = "foo", dynamic_deps = ["@std_msgs//:cc_shared"], ...)

`cc_shared_library` and `cc_binary` decide per target whether it is linked
statically or satisfied by a `dynamic_dep` by walking the graph of
CcInfo-providing targets, which is why `ros_interface` advertises an (empty)
CcInfo and why the generated code's linker inputs are owned by the interface
target rather than by a synthetic label.

Shared libraries are per package (not per interface) because the dynamic
loader's start-up cost grows with the number of objects in a process -- per
interface and kind that reached thousands of objects and multi-second
start-ups. Interface packages name the packages they depend on
(`default_generators(dependencies = [...])`) so a package's libraries can
link against its dependencies' libraries, exactly like hand-written
`cc_shared_library` targets list theirs in `dynamic_deps`.
"""

load("@protobuf//bazel/common:proto_info.bzl", "ProtoInfo")
load("@rosdistro//rust:defs.bzl", "CrateInfo")
load("@rosidl_adapter//:defs.bzl", "ROSIDL_COMMON_ATTRS", "RosInterfaceInfo", "rosidl_adapter_aspect", "rosidl_export_dynamic_link_flags", "rosidl_link_shared_library", "rosidl_runtime_dynamic_libraries", "rosidl_shared_library_name", "rosidl_static_typesupport")
load("@rosidl_adapter_proto//:defs.bzl", "RosProtoInfo", "merge_proto_infos", "rosidl_adapter_proto_aspect")
load("@rosidl_generator_c//:defs.bzl", "RosCBindingsInfo", "rosidl_generator_c_aspect", "rosidl_generator_type_description_aspect")
load("@rosidl_generator_cpp//:defs.bzl", "RosCcBindingsInfo", "rosidl_generator_cpp_aspect")
load("@rosidl_generator_py//:defs.bzl", "RosPyBindingsInfo", "rosidl_generator_py_aspect")
load("@rosidl_generator_rs//:defs.bzl", "RosRsBindingsInfo", "rosidl_generator_rs_aspect")
load("@rosidl_typesupport_c//:defs.bzl", "RosCTypesupportInfo", "rosidl_typesupport_c_aspect")
load("@rosidl_typesupport_cpp//:defs.bzl", "RosCcTypesupportInfo", "rosidl_typesupport_cpp_aspect")
load("@rosidl_typesupport_fastrtps_c//:defs.bzl", "RosCTypesupportFastRTPSInfo", "rosidl_typesupport_fastrtps_c_aspect")
load("@rosidl_typesupport_fastrtps_cpp//:defs.bzl", "RosCcTypesupportFastRTPSInfo", "rosidl_typesupport_fastrtps_cpp_aspect")
load("@rosidl_typesupport_introspection_c//:defs.bzl", "RosCTypesupportIntrospectionInfo", "rosidl_typesupport_introspection_c_aspect")
load("@rosidl_typesupport_introspection_cpp//:defs.bzl", "RosCcTypesupportIntrospectionInfo", "rosidl_typesupport_introspection_cpp_aspect")
load("@rosidl_typesupport_protobuf_cpp//:defs.bzl", "RosCcTypesupportProtobufInfo", "rosidl_typesupport_protobuf_cpp_aspect")
load("@rules_cc//cc:defs.bzl", "CcInfo", "cc_common")
load("@rules_cc//cc:find_cc_toolchain.bzl", "find_cc_toolchain", "use_cc_toolchain")
load("@rules_cc//cc/common:cc_shared_library_info.bzl", "CcSharedLibraryInfo")
load("@rules_python//python:defs.bzl", "PyInfo")
load("@rules_python//python/api:api.bzl", "py_common")

# The C/C++ typesupport kinds `:cc`/`:c` carry, in dependency order. They
# are the same for both languages on purpose: the kind aspects are shared
# between every rule that applies them, so one aggregate per interface (with
# one owner label) means `:c` and `:cc` of a package can meet in one binary
# without the generated code being linked twice.
#
# `lib_deps` are the other kinds of the same package whose shared library
# the kind's library links against (mirroring the upstream CMake targets'
# link dependencies). `runtime` is the kind's runtime closure
# (cc_shared_library / collect_transitive_dynamic_deps) and `library` the
# matching cc_library, like the DEPENDENCIES dicts in hand-written packages.
# rosidl_runtime_c/cpp are not dependencies of this package; the generators
# that need them re-export them under the rosidl_generator_c/cpp aliases.
_CC_KINDS = [
    struct(
        name = "rosidl_generator_c",
        provider = RosCBindingsInfo,
        lib_deps = [],
        runtime = Label("@rosidl_generator_c//:runtime_dynamic_deps"),
        library = Label("@rosidl_generator_c//:runtime_library"),
    ),
    struct(
        name = "rosidl_generator_cpp",
        provider = RosCcBindingsInfo,
        lib_deps = ["rosidl_generator_c"],
        runtime = Label("@rosidl_generator_cpp//:runtime_dynamic_deps"),
        library = Label("@rosidl_generator_cpp//:runtime_library"),
    ),
    struct(
        name = "rosidl_typesupport_introspection_c",
        provider = RosCTypesupportIntrospectionInfo,
        lib_deps = ["rosidl_generator_c"],
        runtime = Label("@rosidl_typesupport_introspection_c//:transitive_dynamic_deps"),
        library = Label("@rosidl_typesupport_introspection_c//:rosidl_typesupport_introspection_c_library"),
    ),
    struct(
        name = "rosidl_typesupport_introspection_cpp",
        provider = RosCcTypesupportIntrospectionInfo,
        lib_deps = ["rosidl_generator_c", "rosidl_generator_cpp"],
        runtime = Label("@rosidl_typesupport_introspection_cpp//:transitive_dynamic_deps"),
        library = Label("@rosidl_typesupport_introspection_cpp//:rosidl_typesupport_introspection_cpp_library"),
    ),
    struct(
        name = "rosidl_typesupport_fastrtps_c",
        provider = RosCTypesupportFastRTPSInfo,
        lib_deps = ["rosidl_generator_c"],
        runtime = Label("@rosidl_typesupport_fastrtps_c//:transitive_dynamic_deps"),
        library = Label("@rosidl_typesupport_fastrtps_c//:rosidl_typesupport_fastrtps_c_library"),
    ),
    struct(
        name = "rosidl_typesupport_fastrtps_cpp",
        provider = RosCcTypesupportFastRTPSInfo,
        lib_deps = ["rosidl_generator_c", "rosidl_generator_cpp", "rosidl_typesupport_fastrtps_c"],
        runtime = Label("@rosidl_typesupport_fastrtps_cpp//:transitive_dynamic_deps"),
        library = Label("@rosidl_typesupport_fastrtps_cpp//:rosidl_typesupport_fastrtps_cpp_library"),
    ),
    struct(
        name = "rosidl_typesupport_c",
        provider = RosCTypesupportInfo,
        lib_deps = ["rosidl_generator_c"],
        runtime = Label("@rosidl_typesupport_c//:transitive_dynamic_deps"),
        library = Label("@rosidl_typesupport_c//:rosidl_typesupport_c_library"),
    ),
    struct(
        name = "rosidl_typesupport_cpp",
        provider = RosCcTypesupportInfo,
        lib_deps = ["rosidl_generator_c", "rosidl_generator_cpp", "rosidl_typesupport_c"],
        runtime = Label("@rosidl_typesupport_cpp//:transitive_dynamic_deps"),
        library = Label("@rosidl_typesupport_cpp//:rosidl_typesupport_cpp_library"),
    ),
]

_CC_KIND_PROVIDERS = [kind.provider for kind in _CC_KINDS]

_CC_KIND_ASPECTS = [
    # Adapters
    rosidl_adapter_aspect,
    rosidl_generator_type_description_aspect,
    # Bindings
    rosidl_generator_c_aspect,
    rosidl_generator_cpp_aspect,
    # Typesupports
    rosidl_typesupport_introspection_c_aspect,
    rosidl_typesupport_introspection_cpp_aspect,
    # fastrtps_c must run before fastrtps_cpp: the generated C++
    # typesupport consumes the C typesupport's has_buffer_fields_*()
    # helper for the same interface.
    rosidl_typesupport_fastrtps_c_aspect,
    rosidl_typesupport_fastrtps_cpp_aspect,
    rosidl_typesupport_c_aspect,
    rosidl_typesupport_cpp_aspect,
]

# The runtime closures, in _CC_KINDS order (label_list attributes cannot be
# keyed, so _runtime_shared_deps is read back positionally).
_CC_RUNTIME_SHARED_DEPENDENCIES = [kind.runtime for kind in _CC_KINDS]
_CC_RUNTIME_DEPENDENCIES = [kind.library for kind in _CC_KINDS]

RosidlCcInfo = provider(
    "The C/C++ generated code of one interface and of the interfaces it depends on.",
    fields = {
        "cc_info": "CcInfo: compilation context and static archives (owned by the interface targets).",
        "static_libraries": "dict: kind name -> LibraryToLink, this interface's static archive per kind (header-only kinds absent).",
        "package_name": "str: the ROS package the interface belongs to.",
        "dep_packages": "depset[str]: the other packages whose interfaces this one (transitively) depends on.",
        "transitive_interfaces": "depset[struct(label, package_name, static_libraries, dep_packages)]: this interface and, transitively, the ones it depends on.",
    },
)

RosidlSharedLibraryInfo = provider(
    "A package's generated code as shared libraries, one per typesupport kind.",
    fields = {
        "package_name": "str: ROS package name.",
        "libraries": "dict: kind name -> File, lib<pkg>__<kind>.so.",
        "linker_inputs": "dict: kind name -> LinkerInput to link against that library.",
        "transitive_packages": "depset[struct(package_name, kinds)]: this package and, transitively, the ones it depends on; `kinds` is a tuple of (kind name, LinkerInput).",
        "transitive_files": "depset[File]: the shared libraries of this package and of the ones it depends on.",
    },
)

def _rosidl_cc_aspect_impl(target, ctx):
    kinds = [(kind.name, target[kind.provider]) for kind in _CC_KINDS if kind.provider in target]
    deps = [dep[RosidlCcInfo] for dep in ctx.rule.attr.deps if RosidlCcInfo in dep]

    static_libraries = {name: info.static_library for name, info in kinds if info.static_library}

    cc_info = CcInfo(
        compilation_context = cc_common.merge_compilation_contexts(
            compilation_contexts = [info.cc_info.compilation_context for _, info in kinds],
        ),
        linking_context = cc_common.merge_linking_contexts(
            linking_contexts = [
                cc_common.create_linking_context(
                    linker_inputs = depset([
                        cc_common.create_linker_input(
                            owner = ctx.label,
                            libraries = depset(static_libraries.values()),
                        ),
                    ]),
                ),
            ] + [dep.cc_info.linking_context for dep in deps],
        ),
    )
    package_name = target[RosInterfaceInfo].package
    direct_dep_packages = [dep.package_name for dep in deps if dep.package_name != package_name]
    entry = struct(
        label = str(target.label),
        package_name = package_name,
        static_libraries = tuple(static_libraries.items()),
        dep_packages = tuple(direct_dep_packages),
    )
    return [
        RosidlCcInfo(
            cc_info = cc_info,
            static_libraries = static_libraries,
            package_name = package_name,
            dep_packages = depset(
                direct = direct_dep_packages,
                transitive = [dep.dep_packages for dep in deps],
            ),
            transitive_interfaces = depset(
                direct = [entry],
                transitive = [dep.transitive_interfaces for dep in deps],
            ),
        ),
    ]

rosidl_cc_aspect = aspect(
    implementation = _rosidl_cc_aspect_impl,
    attr_aspects = ["deps"],
    required_providers = [RosInterfaceInfo],
    required_aspect_providers = [[provider] for provider in _CC_KIND_PROVIDERS],
    provides = [RosidlCcInfo],
)

_CC_ASPECTS = _CC_KIND_ASPECTS + [rosidl_cc_aspect]

def _shared_library_entry(info):
    """The entry shape cc_shared_library keeps in CcSharedLibraryInfo.dynamic_deps."""
    return struct(
        exports = info.exports,
        linker_input = info.linker_input,
        link_once_static_libs = info.link_once_static_libs,
    )

def _merge_shared_library_infos(infos):
    return depset(
        direct = [_shared_library_entry(info) for info in infos],
        transitive = [info.dynamic_deps for info in infos],
        order = "topological",
    )

def _runtime_shared_library_files(ctx):
    """The shared libraries of the runtime closures (rosidl_runtime_c, rcutils, ...).

    The generated shared libraries link against these by soname; consumers
    that load them with dlopen (Python extension modules, Rust bindings)
    need them on the loader path too.
    """
    return depset(transitive = [dep[DefaultInfo].files for dep in ctx.attr._runtime_shared_deps])

def _solib_files(linker_inputs):
    """The `_solib_<cpu>/...` symlink artifacts of the shared libraries in `linker_inputs`.

    Consumers' RUNPATHs point at these (that is what cc_shared_library puts
    in its runfiles too); shipping them makes the loader independent of the
    cwd-relative LD_LIBRARY_PATH=lib convention.
    """
    files = []
    for linker_input in linker_inputs:
        for library in linker_input.libraries:
            if library.dynamic_library:
                files.append(library.dynamic_library)
    return depset(files)

def _library_symlinks(ctx, dynamic_libraries, extra_files = []):
    """Runfiles exposing shared libraries under lib/ (the LD_LIBRARY_PATH .bazelrc sets).

    The rosidl_typesupport_c/cpp dispatch falls back to loading a typesupport
    by file name (lib<pkg>__<kind>.so) when its symbols are not already in
    the process; this keeps that working for code that was linked statically.
    """
    symlinks = {}
    for file in dynamic_libraries.to_list():
        symlinks["lib/" + file.basename] = file
    return ctx.runfiles(symlinks = symlinks, transitive_files = depset(transitive = [dynamic_libraries] + extra_files))

def _order_packages(entries):
    """Group interface entries by package and topologically sort packages (dependencies first)."""
    by_package = {}
    edges = {}
    for entry in entries:
        by_package.setdefault(entry.package_name, []).append(entry)
        edges.setdefault(entry.package_name, {})
        for dep_pkg in entry.dep_packages:
            if dep_pkg != entry.package_name:
                edges[entry.package_name][dep_pkg] = True
    for _ in range(len(edges)):
        for pkg in edges:
            for dep_pkg in list(edges[pkg].keys()):
                for trans_pkg in edges.get(dep_pkg, {}):
                    if trans_pkg != pkg:
                        edges[pkg][trans_pkg] = True
    ordered = []
    done = {}
    for _ in range(len(by_package)):
        progressed = False
        for pkg in by_package:
            if pkg in done:
                continue
            if all([dep in done or dep not in by_package for dep in edges[pkg]]):
                ordered.append(pkg)
                done[pkg] = True
                progressed = True
        if not progressed:
            break
    if len(ordered) != len(by_package):
        fail("cyclic interface package dependencies among {}".format(sorted(by_package.keys())))
    dep_packages = {pkg: [d for d in ordered if d in edges[pkg]] for pkg in ordered}
    return ordered, by_package, dep_packages

def _target_symlink_dir(ctx, pkg, is_canonical):
    if is_canonical:
        return "rosidl_" + pkg
    pkg_prefix = ctx.label.package.replace("/", "_")
    return "rosidl_{}_{}_{}".format(pkg_prefix, ctx.label.name, pkg) if pkg_prefix else "rosidl_{}_{}".format(ctx.label.name, pkg)

def _target_link_names(ctx, pkg, kind_name, cc_toolchain, is_canonical, is_direct_pkg):
    if is_canonical:
        return "{}__{}".format(pkg, kind_name), None
    if is_direct_pkg:
        stem = "{}__{}".format(pkg, kind_name)
    else:
        stem = "{}__{}__{}".format(ctx.label.name, pkg, kind_name)
    soname = rosidl_shared_library_name(stem, cc_toolchain)
    return "{}/{}".format(ctx.label.name, stem), "{}/{}".format(ctx.label.name, soname)

# IDL files

def _ros_library(ctx):
    default_info = DefaultInfo(
        files = depset(transitive = [dep[DefaultInfo].files for dep in ctx.attr.deps]),
    )
    return [default_info]

ros_library = rule(
    implementation = _ros_library,
    attrs = {
        "deps": attr.label_list(
            aspects = [rosidl_adapter_aspect],
            providers = [RosInterfaceInfo],
            allow_files = False,
        ),
    },
    provides = [DefaultInfo],
)

# C and C++

def _cc_ros_library(ctx):
    infos = [dep[RosidlCcInfo] for dep in ctx.attr.deps]
    cc_toolchain = find_cc_toolchain(ctx)
    static_typesupport = rosidl_static_typesupport(ctx)

    linker_inputs = []
    if static_typesupport:
        # Typesupports are alwayslink'd into the binary; the dispatch finds
        # them with dlsym(dlopen(NULL)), which needs them exported.
        linker_inputs.append(
            cc_common.create_linker_input(
                owner = ctx.label,
                user_link_flags = depset(rosidl_export_dynamic_link_flags(cc_toolchain)),
            ),
        )
    cc_info = cc_common.merge_cc_infos(
        direct_cc_infos = [info.cc_info for info in infos] +
                          [dep[CcInfo] for dep in ctx.attr._runtime_deps] +
                          [CcInfo(linking_context = cc_common.create_linking_context(linker_inputs = depset(linker_inputs)))],
    )

    # Statically linked consumers still need the package's shared libraries
    # on the loader path for the typesupport dispatch's by-name fallback;
    # `shared` only contributes runfiles, never link inputs.
    runfiles = ctx.runfiles()
    if ctx.attr.shared and not static_typesupport:
        runfiles = ctx.attr.shared[DefaultInfo].default_runfiles
    return [
        cc_info,
        DefaultInfo(
            files = depset(),
            runfiles = runfiles,
        ),
    ]

_CC_ROS_LIBRARY_ATTRS = {
    "deps": attr.label_list(
        aspects = _CC_ASPECTS,
        providers = [RosInterfaceInfo],
        allow_files = False,
    ),
    "shared": attr.label(
        providers = [RosidlSharedLibraryInfo],
        doc = "The package's cc_ros_shared_library; its shared libraries become runfiles.",
    ),
    "_runtime_deps": attr.label_list(
        default = _CC_RUNTIME_DEPENDENCIES,
        providers = [CcInfo],
    ),
} | ROSIDL_COMMON_ATTRS

cc_ros_library = rule(
    implementation = _cc_ros_library,
    doc = """The generated C and C++ code of a set of interfaces, as a cc_library would provide it.

Put it in `deps`. Pair it with `cc_ros_shared_library` over the same
interfaces in `dynamic_deps` to link the generated code dynamically; without
that it is linked statically into the consumer.""",
    toolchains = use_cc_toolchain(),
    fragments = ["cpp"],
    attrs = _CC_ROS_LIBRARY_ATTRS,
    provides = [CcInfo, DefaultInfo],
)

c_ros_library = cc_ros_library

def _runtime_inputs(ctx, kinds):
    return {
        kind.name: [dep[CcSharedLibraryInfo].linker_input]
        for kind, dep in zip(kinds, ctx.attr._runtime_shared_deps)
    }

def _cc_ros_shared_library(ctx):
    infos = [dep[RosidlCcInfo] for dep in ctx.attr.deps]
    dependencies = [dep[RosidlSharedLibraryInfo] for dep in ctx.attr.dynamic_deps]
    runtime_infos = [dep[CcSharedLibraryInfo] for dep in ctx.attr._runtime_shared_deps]
    runtime_inputs = _runtime_inputs(ctx, _CC_KINDS)
    cc_toolchain = find_cc_toolchain(ctx)

    available = {}
    for dep in dependencies:
        for entry in dep.transitive_packages.to_list():
            available[entry.package_name] = dict(entry.kinds)

    entries = depset(transitive = [info.transitive_interfaces for info in infos]).to_list()
    ordered_packages, by_package, dep_packages = _order_packages(entries)
    direct_packages = {info.package_name: True for info in infos}
    primary_package = infos[0].package_name if len(direct_packages) == 1 else (ordered_packages[-1] if ordered_packages else "")

    own_by_pkg = {}
    all_own_linked = []
    exported_labels = []
    linked_packages = []

    for pkg in ordered_packages:
        if pkg in available:
            continue
        pkg_entries = by_package[pkg]
        is_canonical = ctx.label.name == "cc_shared" and pkg == primary_package
        is_direct_pkg = pkg in direct_packages
        if is_direct_pkg:
            for entry in pkg_entries:
                exported_labels.append(entry.label)
        symlink_dir = _target_symlink_dir(ctx, pkg, is_canonical)
        pkg_own = {}
        for kind in _CC_KINDS:
            archives = []
            for entry in pkg_entries:
                static_map = dict(entry.static_libraries)
                if kind.name in static_map:
                    archives.append(static_map[kind.name])
            if not archives:
                continue
            closure = [kind.name] + kind.lib_deps
            inputs = []
            for name in kind.lib_deps:
                if name in pkg_own:
                    inputs.append(pkg_own[name].linker_input)
            for dep_pkg in dep_packages[pkg]:
                dep_kinds = available.get(dep_pkg, {})
                for name in closure:
                    if name in dep_kinds:
                        inputs.append(dep_kinds[name])
            for name in closure:
                inputs.extend(runtime_inputs.get(name, []))
            link_name, output_name = _target_link_names(ctx, pkg, kind.name, cc_toolchain, is_canonical, is_direct_pkg)
            linked = rosidl_link_shared_library(
                ctx,
                name = link_name,
                static_libraries = archives,
                linker_inputs = inputs,
                output_name = output_name,
                symlink_dir = symlink_dir,
            )
            pkg_own[kind.name] = linked
            all_own_linked.append(linked)
        own_by_pkg[pkg] = pkg_own
        available[pkg] = {name: linked.linker_input for name, linked in pkg_own.items()}
        linked_packages.append(pkg)

    primary_own = own_by_pkg.get(primary_package, {})
    libraries = {name: linked.file for name, linked in primary_own.items()}
    linker_inputs = {name: linked.linker_input for name, linked in primary_own.items()}
    all_own_files = [linked.file for linked in all_own_linked]
    files = depset(all_own_files)
    transitive_files = depset(all_own_files, transitive = [dep.transitive_files for dep in dependencies])
    dynamic_deps = _merge_shared_library_infos(
        [dep[CcSharedLibraryInfo] for dep in ctx.attr.dynamic_deps] + runtime_infos,
    )
    solib_files = _solib_files([linked.linker_input for linked in all_own_linked] + [entry.linker_input for entry in dynamic_deps.to_list()])
    return [
        CcSharedLibraryInfo(
            dynamic_deps = dynamic_deps,
            exports = exported_labels,
            link_once_static_libs = exported_labels,
            linker_input = cc_common.create_linker_input(
                owner = ctx.label,
                libraries = depset([linked.library_to_link for linked in all_own_linked]),
            ),
        ),
        RosidlSharedLibraryInfo(
            package_name = primary_package,
            libraries = libraries,
            linker_inputs = linker_inputs,
            transitive_packages = depset(
                direct = [struct(package_name = pkg, kinds = tuple(available[pkg].items())) for pkg in linked_packages],
                transitive = [dep.transitive_packages for dep in dependencies],
                order = "topological",
            ),
            transitive_files = transitive_files,
        ),
        DefaultInfo(
            files = files,
            runfiles = _library_symlinks(ctx, transitive_files, [solib_files, _runtime_shared_library_files(ctx), depset(rosidl_runtime_dynamic_libraries(ctx))]),
        ),
    ]

cc_ros_shared_library = rule(
    implementation = _cc_ros_shared_library,
    doc = """The generated C and C++ code of a set of interfaces, as cc_shared_library would provide it.

One shared library per typesupport kind (lib<pkg>__<kind>.so). Put it in
`dynamic_deps` (directly, or through collect_transitive_dynamic_deps)
alongside the matching `cc_ros_library` in `deps`.""",
    toolchains = use_cc_toolchain(),
    fragments = ["cpp"],
    attrs = {
        "deps": attr.label_list(
            aspects = _CC_ASPECTS,
            providers = [RosInterfaceInfo],
            allow_files = False,
            doc = "The package's interfaces.",
        ),
        "dynamic_deps": attr.label_list(
            providers = [CcSharedLibraryInfo, RosidlSharedLibraryInfo],
            doc = "The cc_ros_shared_library of every interface package these interfaces depend on.",
        ),
        "_runtime_shared_deps": attr.label_list(
            default = _CC_RUNTIME_SHARED_DEPENDENCIES,
            providers = [CcSharedLibraryInfo],
        ),
    } | ROSIDL_COMMON_ATTRS,
    provides = [CcSharedLibraryInfo, RosidlSharedLibraryInfo, DefaultInfo],
)

c_ros_shared_library = cc_ros_shared_library

# Protobuf

_PROTOBUF_KIND = struct(
    name = "rosidl_typesupport_protobuf_cpp",
    provider = RosCcTypesupportProtobufInfo,
    lib_deps = ["rosidl_generator_c", "rosidl_generator_cpp"],
    runtime = Label("@rosidl_typesupport_protobuf_cpp//:transitive_dynamic_deps"),
    library = Label("@rosidl_typesupport_protobuf_cpp//:rosidl_typesupport_protobuf_cpp_library"),
)

RosidlProtoInfo = provider(
    "The protobuf C++ and protobuf typesupport of one interface and the interfaces it depends on.",
    fields = {
        "transitive_interfaces": "depset[struct(label, package_name, proto_static_library, typesupport_static_library, typesupport_cc_info, dep_packages)]",
    },
)

def _rosidl_proto_aspect_impl(target, ctx):
    package_name = target[RosInterfaceInfo].package
    deps = [dep[RosidlProtoInfo] for dep in ctx.rule.attr.deps if RosidlProtoInfo in dep]
    cc_deps = [dep[RosidlCcInfo] for dep in ctx.rule.attr.deps if RosidlCcInfo in dep]
    direct_dep_packages = [dep.package_name for dep in cc_deps if dep.package_name != package_name]
    entry = struct(
        label = str(target.label),
        package_name = package_name,
        proto_static_library = target[RosProtoInfo].static_library if RosProtoInfo in target else None,
        typesupport_static_library = target[RosCcTypesupportProtobufInfo].static_library if RosCcTypesupportProtobufInfo in target else None,
        typesupport_cc_info = target[RosCcTypesupportProtobufInfo].cc_info if RosCcTypesupportProtobufInfo in target else None,
        dep_packages = tuple(direct_dep_packages),
    )
    return [
        RosidlProtoInfo(
            transitive_interfaces = depset(
                direct = [entry],
                transitive = [dep.transitive_interfaces for dep in deps],
            ),
        ),
    ]

rosidl_proto_aspect = aspect(
    implementation = _rosidl_proto_aspect_impl,
    attr_aspects = ["deps"],
    required_providers = [RosInterfaceInfo],
    required_aspect_providers = [
        [RosProtoInfo],
        [RosCcTypesupportProtobufInfo],
        [RosidlCcInfo],
    ],
    provides = [RosidlProtoInfo],
)

def _cc_proto_ros_library(ctx):
    proto_info, _ = merge_proto_infos(
        ctx = ctx,
        name = ctx.label.name,
        deps = ctx.attr.deps,
    )
    infos = [dep[RosidlCcInfo] for dep in ctx.attr.deps]
    proto_aspect_infos = [dep[RosidlProtoInfo] for dep in ctx.attr.deps]
    entries = depset(transitive = [info.transitive_interfaces for info in proto_aspect_infos]).to_list()
    ordered_packages, by_package, dep_packages = _order_packages(entries)
    direct_packages = {info.package_name: True for info in infos}
    primary_package = infos[0].package_name if len(direct_packages) == 1 else (ordered_packages[-1] if ordered_packages else "")

    # lib<pkg>__rosidl_typesupport_protobuf_cpp.so: the typesupport plus the
    # protobuf C++ for the package's interfaces (which has no shared-library
    # form of its own), linked against the package's other kinds, the
    # dependency packages' protobuf libraries and the protobuf runtime.
    shared = ctx.attr.shared[RosidlSharedLibraryInfo]
    shared_packages = {entry.package_name: dict(entry.kinds) for entry in shared.transitive_packages.to_list()}
    dependencies = [dep[RosidlSharedLibraryInfo] for dep in ctx.attr.dynamic_deps]
    runtime_linker_inputs = [dep[CcSharedLibraryInfo].linker_input for dep in ctx.attr._runtime_shared_deps]
    cc_toolchain = find_cc_toolchain(ctx)

    available = {}
    for dep in dependencies:
        for entry in dep.transitive_packages.to_list():
            available[entry.package_name] = dict(entry.kinds)

    own_by_pkg = {}
    all_own_linked = []
    linked_packages = []

    for pkg in ordered_packages:
        if pkg in available:
            continue
        pkg_entries = by_package[pkg]
        static_libs = [e.typesupport_static_library for e in pkg_entries if e.typesupport_static_library] + [
            e.proto_static_library
            for e in pkg_entries
            if e.proto_static_library
        ]
        if not static_libs:
            continue
        pkg_shared = shared_packages.get(pkg, {})
        inputs = [pkg_shared[name] for name in _PROTOBUF_KIND.lib_deps if name in pkg_shared]
        for dep_pkg in dep_packages[pkg]:
            inputs.extend(available.get(dep_pkg, {}).values())
        inputs.extend(runtime_linker_inputs)
        is_canonical = ctx.label.name == "proto" and pkg == primary_package
        is_direct_pkg = pkg in direct_packages
        link_name, output_name = _target_link_names(ctx, pkg, _PROTOBUF_KIND.name, cc_toolchain, is_canonical, is_direct_pkg)
        linked = rosidl_link_shared_library(
            ctx,
            name = link_name,
            static_libraries = static_libs,
            linker_inputs = inputs,
            output_name = output_name,
            symlink_dir = _target_symlink_dir(ctx, pkg, is_canonical),
        )
        own_by_pkg[pkg] = linked
        all_own_linked.append(linked)
        available[pkg] = {_PROTOBUF_KIND.name: linked.linker_input}
        linked_packages.append(pkg)

    # Consumers get the typesupport as a precompiled dynamic library through
    # this target's own linker input (cc_shared_library/cc_binary link it
    # dynamically); the interfaces' static archives stay owned by the
    # interface targets, which the package's `:cc_shared` exports. When
    # typesupport is linked statically (--dynamic_mode=off or static RMW),
    # link the protobuf typesupport archives directly with --export-dynamic.
    static_typesupport = rosidl_static_typesupport(ctx)
    if static_typesupport:
        extra_linker_inputs = [
            cc_common.create_linker_input(
                owner = ctx.label,
                libraries = depset([e.typesupport_static_library for e in entries if e.typesupport_static_library]),
                user_link_flags = depset(rosidl_export_dynamic_link_flags(cc_toolchain)),
            ),
        ]
        cc_info = cc_common.merge_cc_infos(
            direct_cc_infos = [info.cc_info for info in infos] +
                              [e.typesupport_cc_info for e in entries if e.typesupport_cc_info] +
                              [dep[CcInfo] for dep in ctx.attr._runtime_deps] +
                              [CcInfo(linking_context = cc_common.create_linking_context(linker_inputs = depset(extra_linker_inputs)))],
        )
    else:
        shared_linker_inputs = []
        for pkg in ordered_packages:
            pkg_shared = shared_packages.get(pkg, {})
            for kind in _CC_KINDS:
                if kind.name in pkg_shared:
                    shared_linker_inputs.append(pkg_shared[kind.name])
        extra_linker_inputs = [linked.linker_input for linked in all_own_linked] + [
            available[pkg][_PROTOBUF_KIND.name]
            for pkg in ordered_packages
            if pkg in available and pkg not in own_by_pkg and _PROTOBUF_KIND.name in available[pkg]
        ] + shared_linker_inputs + runtime_linker_inputs
        compilation_cc_info = cc_common.merge_cc_infos(
            direct_cc_infos = [info.cc_info for info in infos] +
                              [e.typesupport_cc_info for e in entries if e.typesupport_cc_info] +
                              [dep[CcInfo] for dep in ctx.attr._runtime_deps],
        )
        cc_info = CcInfo(
            compilation_context = compilation_cc_info.compilation_context,
            linking_context = cc_common.create_linking_context(
                linker_inputs = depset([
                    cc_common.create_linker_input(
                        owner = ctx.label,
                        libraries = depset(
                            [lib for li in extra_linker_inputs for lib in li.libraries],
                            order = "topological",
                        ),
                    ),
                ]),
            ),
        )
    primary_linked = own_by_pkg.get(primary_package)
    all_own_files = [linked.file for linked in all_own_linked]
    transitive_files = depset(all_own_files, transitive = [dep.transitive_files for dep in dependencies])
    dynamic_deps = _merge_shared_library_infos(
        [ctx.attr.shared[CcSharedLibraryInfo]] +
        [dep[CcSharedLibraryInfo] for dep in ctx.attr.dynamic_deps] +
        [dep[CcSharedLibraryInfo] for dep in ctx.attr._runtime_shared_deps],
    )
    runfiles = ctx.runfiles() if static_typesupport else _library_symlinks(
        ctx,
        transitive_files,
        [_solib_files(extra_linker_inputs), _runtime_shared_library_files(ctx), depset(rosidl_runtime_dynamic_libraries(ctx))],
    ).merge(
        ctx.attr.shared[DefaultInfo].default_runfiles,
    )
    return [
        proto_info,
        cc_info,
        CcSharedLibraryInfo(
            dynamic_deps = dynamic_deps,
            exports = [str(ctx.label)],
            link_once_static_libs = [],
            linker_input = cc_common.create_linker_input(
                owner = ctx.label,
                libraries = depset([linked.library_to_link for linked in all_own_linked]),
            ),
        ),
        RosidlSharedLibraryInfo(
            package_name = primary_package,
            libraries = {_PROTOBUF_KIND.name: primary_linked.file} if primary_linked else {},
            linker_inputs = {_PROTOBUF_KIND.name: primary_linked.linker_input} if primary_linked else {},
            transitive_packages = depset(
                direct = [struct(package_name = pkg, kinds = tuple(available[pkg].items())) for pkg in linked_packages],
                transitive = [dep.transitive_packages for dep in dependencies],
                order = "topological",
            ),
            transitive_files = transitive_files,
        ),
        DefaultInfo(
            files = depset() if static_typesupport else depset(all_own_files),
            runfiles = runfiles,
        ),
    ]

cc_proto_ros_library = rule(
    implementation = _cc_proto_ros_library,
    toolchains = use_cc_toolchain() + ["@protobuf//bazel/private:proto_toolchain_type"],
    fragments = ["proto", "cpp"],
    attrs = {
        "deps": attr.label_list(
            aspects = [
                rosidl_adapter_aspect,
                rosidl_adapter_proto_aspect,
            ] + _CC_KIND_ASPECTS[1:] + [
                rosidl_typesupport_protobuf_cpp_aspect,
                rosidl_cc_aspect,
                rosidl_proto_aspect,
            ],
            providers = [RosInterfaceInfo],
            allow_files = False,
        ),
        "shared": attr.label(
            mandatory = True,
            providers = [CcSharedLibraryInfo, RosidlSharedLibraryInfo],
            doc = "The package's cc_ros_shared_library.",
        ),
        "dynamic_deps": attr.label_list(
            providers = [CcSharedLibraryInfo, RosidlSharedLibraryInfo],
            doc = "The cc_proto_ros_library of every interface package these interfaces depend on.",
        ),
        "_runtime_deps": attr.label_list(
            default = _CC_RUNTIME_DEPENDENCIES + [_PROTOBUF_KIND.library],
            providers = [CcInfo],
        ),
        "_runtime_shared_deps": attr.label_list(
            # The typesupport runtime closure, and libprotobuf itself for the
            # embedded protobuf C++ (the proto toolchain's runtime is the
            # static library).
            default = [_PROTOBUF_KIND.runtime, Label("@rosdistro//cc:protobuf")],
            providers = [CcSharedLibraryInfo],
        ),
    } | ROSIDL_COMMON_ATTRS,
    provides = [ProtoInfo, CcInfo, CcSharedLibraryInfo, RosidlSharedLibraryInfo, DefaultInfo],
)

def _proto_ros_library(ctx):
    proto_info, _ = merge_proto_infos(
        ctx = ctx,
        name = ctx.label.name,
        deps = ctx.attr.deps,
    )
    proto_files = depset(
        transitive = [
            dep[RosProtoInfo].protos
            for dep in ctx.attr.deps
            if RosProtoInfo in dep
        ],
    )
    default_info = DefaultInfo(files = proto_files)
    return [proto_info, default_info]

proto_ros_library = rule(
    implementation = _proto_ros_library,
    toolchains = ["@protobuf//bazel/private:proto_toolchain_type"],
    fragments = ["proto"],
    attrs = {
        "deps": attr.label_list(
            aspects = [
                rosidl_adapter_aspect,
                rosidl_adapter_proto_aspect,
            ],
            providers = [RosInterfaceInfo],
            allow_files = False,
        ),
    },
    provides = [ProtoInfo, DefaultInfo],
)

# Python

RosidlPyInfo = provider(
    "A package's Python typesupport extension modules.",
    fields = {
        "modules": "dict: str(interface label) -> LinkerInput of the interface's extension module.",
        "transitive_modules": "depset[struct(label, linker_input)]: modules of this package and of the ones it depends on.",
        "transitive_files": "depset[File]: the extension modules of this package and of the ones it depends on.",
    },
)

RosidlPyAspectInfo = provider(
    "The Python bindings of one interface and the interfaces it depends on.",
    fields = {
        "transitive_interfaces": "depset[struct(label, package_name, py_info)]",
    },
)

def _rosidl_py_aspect_impl(target, ctx):
    deps = [dep[RosidlPyAspectInfo] for dep in ctx.rule.attr.deps if RosidlPyAspectInfo in dep]
    entry = struct(
        label = str(target.label),
        package_name = target[RosInterfaceInfo].package,
        py_info = target[RosPyBindingsInfo],
    )
    return [
        RosidlPyAspectInfo(
            transitive_interfaces = depset(
                direct = [entry],
                transitive = [dep.transitive_interfaces for dep in deps],
            ),
        ),
    ]

rosidl_py_aspect = aspect(
    implementation = _rosidl_py_aspect_impl,
    attr_aspects = ["deps"],
    required_providers = [RosInterfaceInfo],
    required_aspect_providers = [[RosPyBindingsInfo]],
    provides = [RosidlPyAspectInfo],
)

def _dependencies_first(items, dep_labels):
    """Order interfaces so every one follows the interfaces it depends on."""
    ordered = []
    done = {}
    for _ in range(len(items)):
        progressed = False
        for label, item in items:
            if label in done:
                continue
            if all([dep in done or dep not in dict(items) for dep in dep_labels[label]]):
                ordered.append((label, item))
                done[label] = True
                progressed = True
        if not progressed:
            break
    if len(ordered) != len(items):
        fail("cyclic interface dependencies among {}".format([label for label, _ in items]))
    return ordered

def _py_ros_library_rule_impl(ctx):
    shared = ctx.attr.shared[RosidlSharedLibraryInfo]
    shared_packages = {entry.package_name: dict(entry.kinds) for entry in shared.transitive_packages.to_list()}
    dependencies = [dep[RosidlPyInfo] for dep in ctx.attr.dynamic_deps]

    # Modules of the dependency packages, by interface label.
    foreign = {}
    for dep in dependencies:
        for entry in dep.transitive_modules.to_list():
            foreign[entry.label] = entry.linker_input

    # Each interface's extension module links against the package's C
    # bindings and C typesupport libraries, the modules of the interfaces it
    # nests (their <type>__convert_from_py/_to_py are called by symbol) and
    # the typesupport_c runtime closure. The Python C API comes from the
    # interpreter that loads the module.
    runtime_inputs = [dep[CcSharedLibraryInfo].linker_input for dep in ctx.attr._runtime_shared_deps]
    all_entries = depset(
        transitive = [dep[RosidlPyAspectInfo].transitive_interfaces for dep in ctx.attr.deps if RosidlPyAspectInfo in dep],
    ).to_list()
    items = [(entry.label, entry) for entry in all_entries if entry.label not in foreign]
    dep_labels = {label: [str(dep_label) for dep_label in entry.py_info.dep_labels] for label, entry in items}
    direct_packages = {dep[RosInterfaceInfo].package: True for dep in ctx.attr.deps}
    primary_package = ctx.attr.deps[0][RosInterfaceInfo].package if len(direct_packages) == 1 else ""
    ws_prefix = ctx.label.workspace_root.removeprefix("external/") if ctx.label.workspace_root else "_main"
    own_imports = []
    modules = {}
    module_files = []
    for label, entry in _dependencies_first(items, dep_labels):
        info = entry.py_info
        if not info.static_library:
            continue
        pkg_name = entry.package_name
        is_canonical = ctx.label.name == "py" and pkg_name == primary_package
        pkg_shared = shared_packages.get(pkg_name, {})
        package_inputs = [pkg_shared[name] for name in ("rosidl_generator_c", "rosidl_typesupport_c") if name in pkg_shared]
        nested = []
        for dep_label in dep_labels[label]:
            if dep_label in modules:
                nested.append(modules[dep_label])
            elif dep_label in foreign:
                nested.append(foreign[dep_label])
            else:
                fail("{}: {} nests {}, whose package is not in `dependencies`".format(ctx.label, label, dep_label))
        if is_canonical:
            output_dir = info.module_package
            if ctx.label.package and output_dir.startswith(ctx.label.package + "/"):
                output_dir = output_dir[len(ctx.label.package) + 1:]
            link_name = info.module_name
        else:
            output_dir = ctx.label.name
            link_name = "{}/{}".format(ctx.label.name, info.module_name)
        own_import = "/".join([p for p in [ws_prefix, ctx.label.package, output_dir] if p])
        if own_import not in own_imports:
            own_imports.append(own_import)
        linked = rosidl_link_shared_library(
            ctx,
            name = link_name,
            static_libraries = [info.static_library],
            linker_inputs = package_inputs + nested + runtime_inputs,
            output_name = (output_dir + "/" if output_dir else "") + info.module_name + ".so",
            allow_undefined_symbols = True,
            symlink_dir = _target_symlink_dir(ctx, pkg_name, is_canonical),
        )
        modules[label] = linked.linker_input
        module_files.append(linked.file)

    transitive_files = depset(module_files, transitive = [dep.transitive_files for dep in dependencies])
    solib_files = _solib_files(modules.values())
    runfiles = _library_symlinks(ctx, depset(module_files), [solib_files])
    runfiles = runfiles.merge(ctx.attr.shared[DefaultInfo].default_runfiles)
    for dep in ctx.attr.dynamic_deps + ctx.attr._py_deps + ctx.attr.deps:
        if DefaultInfo in dep:
            runfiles = runfiles.merge(dep[DefaultInfo].default_runfiles)

    default_info = DefaultInfo(
        files = depset(module_files),
        runfiles = runfiles,
    )
    rosidl_py_info = PyInfo(
        imports = depset(
            direct = own_imports,
            transitive = [
                dep[RosPyBindingsInfo].imports
                for dep in ctx.attr.deps
                if RosPyBindingsInfo in dep
            ],
        ),
        transitive_sources = depset(
            direct = module_files,
            transitive = [
                dep[RosPyBindingsInfo].transitive_sources
                for dep in ctx.attr.deps
                if RosPyBindingsInfo in dep
            ],
        ),
    )

    # Merge py_info structs.
    py_info = py_common.get(ctx).merge_py_infos(
        direct = [rosidl_py_info],
        transitive = [
            dep[PyInfo]
            for dep in ctx.attr._py_deps + ctx.attr.dynamic_deps
            if PyInfo in dep
        ],
    )

    cc_info = cc_common.merge_cc_infos(
        direct_cc_infos = [
            dep[RosPyBindingsInfo].cc_info
            for dep in ctx.attr.deps
            if RosPyBindingsInfo in dep
        ],
    )

    return [
        py_info,
        cc_info,
        default_info,
        RosidlPyInfo(
            modules = modules,
            transitive_modules = depset(
                direct = [struct(label = label, linker_input = linker_input) for label, linker_input in modules.items()],
                transitive = [dep.transitive_modules for dep in dependencies],
            ),
            transitive_files = transitive_files,
        ),
    ]

py_ros_library = rule(
    implementation = _py_ros_library_rule_impl,
    toolchains = use_cc_toolchain(),
    fragments = ["cpp"],
    attrs = {
        "deps": attr.label_list(
            aspects = [
                # Adapters
                rosidl_adapter_aspect,
                rosidl_generator_type_description_aspect,
                # Generators
                rosidl_generator_c_aspect,
                rosidl_generator_cpp_aspect,
                # Typesupports
                rosidl_typesupport_introspection_c_aspect,
                # fastrtps_c must run before fastrtps_cpp: the generated C++
                # typesupport consumes the C typesupport's has_buffer_fields_*()
                # helper for the same interface.
                rosidl_typesupport_fastrtps_c_aspect,
                rosidl_typesupport_fastrtps_cpp_aspect,
                rosidl_typesupport_c_aspect,
                # Python
                rosidl_generator_py_aspect,
                rosidl_py_aspect,
            ],
            providers = [RosInterfaceInfo],
            allow_files = False,
            doc = "The package's interfaces.",
        ),
        "shared": attr.label(
            mandatory = True,
            providers = [RosidlSharedLibraryInfo],
            doc = "The package's cc_ros_shared_library.",
        ),
        "dynamic_deps": attr.label_list(
            providers = [RosidlPyInfo],
            doc = "The py_ros_library of every interface package these interfaces depend on.",
        ),
        "_py_deps": attr.label_list(
            default = [
                Label("@rosidl_generator_py"),
            ],
            providers = [PyInfo],
        ),
        "_runtime_shared_deps": attr.label_list(
            default = [Label("@rosidl_typesupport_c//:transitive_dynamic_deps")],
            providers = [CcSharedLibraryInfo],
        ),
    } | ROSIDL_COMMON_ATTRS | py_common.API_ATTRS,
    provides = [PyInfo, CcInfo, DefaultInfo, RosidlPyInfo],
)

# Rust

def _rs_ros_library_rule_impl(ctx):
    # Crate dependencies.
    deps = []
    for dep in ctx.attr.deps:
        if RosRsBindingsInfo in dep:
            deps.append(dep[RosRsBindingsInfo].crate_info)

    # Generate a dummy lib.rs
    lib_rs = ctx.actions.declare_file(ctx.label.name + "_lib.rs")
    ctx.actions.write(
        output = lib_rs,
        content = "// Generated by rs_ros_library\n",
    )

    # Merge everything into a CrateInfo for consumption by the callee.
    crate_info = CrateInfo(
        name = ctx.label.name,
        type = "lib",
        root = lib_rs,
        srcs = [lib_rs],
        deps = deps,
        proc_macro_deps = [],
        aliases = {},
        edition = "2021",
    )

    # The generated bindings load lib<pkg>__rosidl_typesupport_c.so and the
    # C bindings by name at runtime: the package's shared libraries (and,
    # through them, their dependencies and the runtime closure) are the
    # runfiles.
    shared = ctx.attr.shared[RosidlSharedLibraryInfo]
    default_info = DefaultInfo(
        files = shared.transitive_files,
        runfiles = ctx.attr.shared[DefaultInfo].default_runfiles,
    )
    return [crate_info, default_info]

rs_ros_library = rule(
    implementation = _rs_ros_library_rule_impl,
    attrs = {
        "deps": attr.label_list(
            aspects = [
                # Adapters
                rosidl_adapter_aspect,
                rosidl_generator_type_description_aspect,
                # Generators
                rosidl_generator_c_aspect,
                rosidl_generator_cpp_aspect,
                # Typesupports
                rosidl_typesupport_introspection_c_aspect,
                # fastrtps_c must run before fastrtps_cpp: the generated C++
                # typesupport consumes the C typesupport's has_buffer_fields_*()
                # helper for the same interface.
                rosidl_typesupport_fastrtps_c_aspect,
                rosidl_typesupport_fastrtps_cpp_aspect,
                rosidl_typesupport_c_aspect,
                # Rust
                rosidl_generator_rs_aspect,
            ],
            providers = [RosInterfaceInfo],
            allow_files = False,
        ),
        "shared": attr.label(
            mandatory = True,
            providers = [RosidlSharedLibraryInfo],
            doc = "The package's cc_ros_shared_library.",
        ),
    },
    provides = [DefaultInfo, CrateInfo],
)

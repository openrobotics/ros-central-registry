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
"""Starlark functions for compiling ROS message adapters."""

load("@bazel_skylib//rules:common_settings.bzl", "BuildSettingInfo")
load("@rules_cc//cc:defs.bzl", "CcInfo", "cc_common")
load("@rules_cc//cc:find_cc_toolchain.bzl", "find_cc_toolchain")
load(":types.bzl", "RosIdlInfo")

def pkg_name_and_base_from_path(path):
    """
    Extract a package name and base from a path
    """
    package_parts = path.split("/")
    package_name = package_parts[-3]
    package_base = "/".join(package_parts[:-2])
    return package_name, package_base

def snake_case_from_pascal_case(pascal_case):
    """
    # This would be better expressed as a regex operation, but unfortunately Bazel's
    # starlark language does not yet support this, and so it would require a module.
    # For example: https://github.com/magnetde/starlark-re/tree/master
    """
    result = ""
    pascal_case_padded = " " + pascal_case + " "
    for i in range(len(pascal_case)):
        prev_char, char, next_char = pascal_case_padded[i:i + 3].elems()
        if char.isupper() and next_char.islower() and prev_char != " ":
            # Insert an underscore before any upper case letter which is not
            # followed by another upper case letter.
            result += "_"
        elif char.isupper() and (prev_char.islower() or prev_char.isdigit()):
            # Insert an underscore before any upper case letter which is
            # preseded by a lower case letter or number.
            result += "_"
        result += char.lower()
    return result

def _get_stem(path):
    return path.basename[:-len(path.extension) - 1]

def idl_tuple_from_path(path):
    idl_parts = path.split("/")
    return "/".join(idl_parts[:-2]) + ":" + idl_parts[-2] + "/" + idl_parts[-1]

def type_description_tuple_from_path(path):
    idl_parts = path.split("/")
    idl_type = idl_parts[-2]
    idl_name = idl_parts[-1].replace(".json", ".idl")
    return "{}/{}:".format(idl_type, idl_name) + path

def generate_sources(
        target,
        ctx,
        executable,
        mnemonic,
        input_idls,
        input_templates,
        input_templates_dir,
        templates_hdrs,
        templates_srcs,
        input_type_descriptions = [],
        template_visibility_control = None,
        additional = [],
        message_is_pascal_case = True,
        debug = False):
    """
    Generic function for calling CLI tools to generate language-specific soruce files.
    """

    # Extract message metadata from the IdlInfo provider, where it was calculated.
    package_name = target[RosIdlInfo].package_name
    message_type = target[RosIdlInfo].interface_type
    message_name = target[RosIdlInfo].interface_name
    message_code = target[RosIdlInfo].interface_code

    # Some message generation retains the message case.
    if not message_is_pascal_case:
        message_code = message_name

    # The first output file is the JSON file used as args to the generator.
    input_args = ctx.actions.declare_file(
        "{}/{}_{}_{}.json".format(package_name, message_type, message_name, mnemonic),
    )

    # Prepare hdrs and srcs lists for output.
    output_hdrs = [
        ctx.actions.declare_file(
            "{}/{}/{}".format(package_name, message_type, t.format(message_code)),
        )
        for t in templates_hdrs
    ]
    output_srcs = [
        ctx.actions.declare_file(
            "{}/{}/{}".format(package_name, message_type, t.format(message_code)),
        )
        for t in templates_srcs
    ]

    # Write the generator query
    ctx.actions.write(
        input_args,
        json.encode(
            struct(
                package_name = package_name,
                idl_tuples = [idl_tuple_from_path(idl.path) for idl in input_idls],
                output_dir = input_args.dirname,
                template_dir = input_templates_dir,
                type_description_tuples = [
                    type_description_tuple_from_path(idl.path)
                    for idl in input_type_descriptions
                ],
                target_dependencies = [],
            ),
        ),
    )

    # Pass the query through the generator
    ctx.actions.run_shell(
        command = "{exec} {genfile} {extra} {out}".format(
            exec = executable.path,
            genfile = "--generator-arguments-file={}".format(input_args.path),
            extra = " ".join(additional),
            out = "" if debug else "> /dev/null 2>&1",
        ),
        tools = [executable],
        inputs = input_idls + input_type_descriptions + input_templates + [input_args],
        outputs = output_hdrs + output_srcs,
        mnemonic = mnemonic,
        progress_message = "Running {} for {}".format(mnemonic, ctx.label.name),
    )

    # Optionally include
    if template_visibility_control:
        output_c_visibility_control_stem = _get_stem(template_visibility_control)
        output_c_visibility_control_h = ctx.actions.declare_file(
            "{}/msg/{}".format(package_name, output_c_visibility_control_stem),
        )
        ctx.actions.expand_template(
            template = template_visibility_control,
            output = output_c_visibility_control_h,
            substitutions = {
                "@PROJECT_NAME@": package_name,
                "@PROJECT_NAME_UPPER@": package_name.upper(),
            },
        )
        output_hdrs.append(output_c_visibility_control_h)

    # Collect include directories
    include_dirs = [_get_parent_dir(input_args.dirname)]

    # Return the headers and sources
    return output_hdrs, output_srcs, include_dirs

def _get_parent_dir(path):
    return "/".join(path.split("/")[:-1])

# Attributes every rosidl code-generation aspect (and the rules in
# rosidl_core_generators that aggregate them) splices into its own `attrs`,
# so `rosidl_static_typesupport(ctx)` can be evaluated anywhere in the
# pipeline.
ROSIDL_COMMON_ATTRS = {
    "_rosidl_rmw": attr.label(
        default = Label("@rosdistro//:rmw"),
        doc = "The --@rosdistro//:rmw build setting; anything other than " +
              "'dynamic' pins one middleware and makes typesupports alwayslink.",
    ),
    # What cc_binary/cc_shared_library link implicitly (the C++ runtime on
    # toolchains that provide it that way, see
    # --@bazel_tools//tools/cpp:link_extra_libs); the generated shared
    # libraries are linked with cc_common.link, which does not add it.
    "_rosidl_link_extra_lib": attr.label(
        default = Label("@bazel_tools//tools/cpp:link_extra_lib"),
        providers = [CcInfo],
    ),
}

def rosidl_static_typesupport(ctx):
    """Whether typesupports are expected to be linked statically into binaries.

    True when `--@rosdistro//:rmw` pins a single middleware (the README's
    "static compilation" mode). The generated typesupport archives are then
    marked alwayslink, because nothing references their symbols directly:
    the rosidl_typesupport_c/cpp dispatch finds them through
    dlsym(dlopen(NULL)) at runtime.

    Args:
        ctx: a rule or aspect context whose attrs include ROSIDL_COMMON_ATTRS.

    Returns:
        bool
    """
    return ctx.attr._rosidl_rmw[BuildSettingInfo].value != "dynamic"

def rosidl_export_dynamic_link_flags(cc_toolchain):
    """Linker flags that keep statically linked typesupport symbols dlsym-able.

    Args:
        cc_toolchain: the resolved C++ toolchain.

    Returns:
        list of user link flags for an executable.
    """
    system = cc_toolchain.target_gnu_system_name
    if "windows" in system or "mingw" in system:
        return []
    if "apple" in system:
        return ["-Wl,-export_dynamic"]
    return ["-rdynamic"]

def generate_compilation_information(
        ctx,
        name,
        hdrs,
        srcs,
        include_dirs = [],
        deps = [],
        header_only_deps = [],
        embed_deps = [],
        local_defines = [],
        alwayslink = False):
    """Compile one generated code fragment into a static archive.

    Every rosidl aspect produces one *fragment* per interface and typesupport
    kind (e.g. `std_msgs/msg/Header` x `rosidl_typesupport_fastrtps_cpp`),
    compiled here into a static archive (`lib<name>_link.a`). The archives
    are what consumers link statically (a `cc_binary` without
    `dynamic_deps`, or a `cc_shared_library` that absorbs the fragment), and
    what `cc_ros_shared_library` links whole-archive into the package's
    `lib<pkg>__<kind>.so` (see rosidl_link_shared_library). The fragment
    itself never gets a shared library of its own: one object per package
    and kind keeps the number of libraries a process loads proportional to
    the packages it uses, not to the interfaces.

    Args:
        ctx: aspect context.
        name: fragment name, e.g. `std_msgs__msg__header__rosidl_generator_c`.
            The archive is `lib<name>_link.a` (install.bzl's bundling relies
            on this naming).
        hdrs: generated public headers.
        srcs: generated sources.
        include_dirs: include directories for the generated headers.
        deps: CcInfos of other generated fragments this one depends on. Their
            compilation contexts are used to compile, and their (static)
            linking contexts are propagated in the returned `cc_info`.
        header_only_deps: CcInfos of the runtime libraries the fragment calls
            into (e.g. `rosidl_runtime_c_library`). Treated like `deps`; the
            name records that the package shared library links against the
            runtime's *shared* library instead (its archives are never
            linked into generated code, so no runtime global state is
            duplicated).
        embed_deps: CcInfos of ordinary static code the fragment needs
            linked wherever it goes (e.g. the protobuf C++ generated for the
            interface, which has no shared-library form of its own).
        local_defines: extra defines for compilation, e.g. the
            `*_BUILDING_DLL_<pkg>` export macro the generated visibility
            control header expects.
        alwayslink: mark the static archive alwayslink (whole-archive).

    Returns:
        struct with fields:
          cc_info: CcInfo (compilation context + static linking context).
          static_library: LibraryToLink of the archive, or None without srcs.
    """

    cc_toolchain = find_cc_toolchain(ctx)

    feature_configuration = cc_common.configure_features(
        ctx = ctx,
        cc_toolchain = cc_toolchain,
        requested_features = ctx.features,
        unsupported_features = ctx.disabled_features,
    )

    (compilation_context, compilation_outputs) = cc_common.compile(
        name = name + "_compile",
        actions = ctx.actions,
        feature_configuration = feature_configuration,
        cc_toolchain = cc_toolchain,
        srcs = srcs,
        public_hdrs = hdrs,
        compilation_contexts = [dep.compilation_context for dep in deps + header_only_deps + embed_deps],
        includes = include_dirs,
        local_defines = local_defines,
    )

    static_linking_contexts = [dep.linking_context for dep in deps + header_only_deps + embed_deps]

    if not srcs:
        return struct(
            cc_info = CcInfo(
                compilation_context = compilation_context,
                linking_context = cc_common.merge_linking_contexts(
                    linking_contexts = static_linking_contexts,
                ),
            ),
            static_library = None,
        )

    static_linking_context, static_linking_outputs = cc_common.create_linking_context_from_compilation_outputs(
        actions = ctx.actions,
        feature_configuration = feature_configuration,
        cc_toolchain = cc_toolchain,
        compilation_outputs = compilation_outputs,
        linking_contexts = static_linking_contexts,
        name = name + "_link",
        alwayslink = alwayslink,
        disallow_dynamic_library = True,
    )

    return struct(
        cc_info = CcInfo(
            compilation_context = compilation_context,
            linking_context = static_linking_context,
        ),
        static_library = static_linking_outputs.library_to_link,
    )

def rosidl_is_darwin(cc_toolchain):
    system = cc_toolchain.target_gnu_system_name
    return "apple" in system or "darwin" in system

def rosidl_is_windows(cc_toolchain):
    system = cc_toolchain.target_gnu_system_name
    return "windows" in system or "mingw" in system

def rosidl_shared_library_name(stem, cc_toolchain):
    """Platform file name of a shared library: lib<stem>.so / lib<stem>.dylib / <stem>.dll."""
    if rosidl_is_windows(cc_toolchain):
        return stem + ".dll"
    return "lib" + stem + (".dylib" if rosidl_is_darwin(cc_toolchain) else ".so")

def rosidl_whole_archive(ctx, feature_configuration, cc_toolchain, library):
    """`library` (a static LibraryToLink) marked alwayslink, so a link keeps all of it."""
    return cc_common.create_library_to_link(
        actions = ctx.actions,
        feature_configuration = feature_configuration,
        cc_toolchain = cc_toolchain,
        static_library = library.static_library,
        pic_static_library = library.pic_static_library,
        alwayslink = True,
    )

def rosidl_runtime_dynamic_libraries(ctx):
    """The shared libraries every link gets implicitly (e.g. the C++ runtime).

    Toolchains that provide the C++ runtime as shared libraries deliver them
    through @bazel_tools//tools/cpp:link_extra_lib (see ROSIDL_COMMON_ATTRS);
    their `_solib` symlinks belong in the runfiles of anything that loads a
    rosidl shared library from outside a cc_binary (Python, Rust).

    Args:
        ctx: rule context whose attrs include ROSIDL_COMMON_ATTRS.

    Returns:
        list of Files.
    """
    files = []
    for linker_input in ctx.attr._rosidl_link_extra_lib[CcInfo].linking_context.linker_inputs.to_list():
        for library in linker_input.libraries:
            if library.dynamic_library and not library.static_library and not library.pic_static_library:
                files.append(library.dynamic_library)
                if library.resolved_symlink_dynamic_library:
                    files.append(library.resolved_symlink_dynamic_library)
    return files

def rosidl_link_shared_library(
        ctx,
        name,
        static_libraries,
        linker_inputs,
        output_name = None,
        allow_undefined_symbols = False,
        symlink_dir = None):
    """Link static archives (whole-archive) into one shared library.

    The shared library links only against *shared* libraries (`linker_inputs`
    are expected to carry dynamic libraries: the package libraries this one
    depends on and the runtime closures), never against their static
    archives, so no runtime library global state is duplicated into it. On
    ELF platforms it is linked with `-z defs` unless `allow_undefined_symbols`,
    so a missing dependency fails the link on every platform, the way ld64's
    two-level namespace does on macOS.

    Args:
        ctx: rule context (needs the C++ toolchain and `_rosidl_link_extra_lib`,
            see ROSIDL_COMMON_ATTRS).
        name: library stem; the output is lib<name>.so (or the platform
            equivalent) unless `output_name` is given.
        static_libraries: static LibraryToLinks linked whole-archive.
        linker_inputs: LinkerInputs (dynamic libraries) to link against.
        output_name: optional exact output file name, relative to the rule's
            package (e.g. a Python extension module, which the interpreter
            imports by file name).
        allow_undefined_symbols: let the library reference symbols none of
            its dependencies define (Python extension modules get the C API
            from the interpreter that loads them).
        symlink_dir: optional `_solib_<cpu>/` sub directory for the
            library's solib symlink; every distinct directory is one RUNPATH
            entry of everything linking the library, so libraries that are
            always loaded together should share one. Must be a single path
            component: the RUNPATHs Bazel writes assume the symlink sits
            exactly one directory below `_solib_<cpu>/`.

    Returns:
        struct with fields:
          file: the shared library File.
          library_to_link: LibraryToLink of the shared library.
          linker_input: LinkerInput (owned by the rule) holding it.
    """
    cc_toolchain = find_cc_toolchain(ctx)
    feature_configuration = cc_common.configure_features(
        ctx = ctx,
        cc_toolchain = cc_toolchain,
        requested_features = ctx.features,
        unsupported_features = ctx.disabled_features,
    )
    main_output = None
    soname = output_name.split("/")[-1] if output_name else rosidl_shared_library_name(name, cc_toolchain)
    if output_name:
        main_output = ctx.actions.declare_file(output_name)
    user_link_flags = []
    if rosidl_is_darwin(cc_toolchain):
        user_link_flags.append("-Wl,-install_name,@rpath/" + soname)
        if allow_undefined_symbols:
            user_link_flags.append("-Wl,-undefined,dynamic_lookup")
    elif not rosidl_is_windows(cc_toolchain):
        user_link_flags.append("-Wl,-soname," + soname)
        if not allow_undefined_symbols:
            user_link_flags.append("-Wl,-z,defs")
    own_input = cc_common.create_linker_input(
        owner = ctx.label,
        libraries = depset([
            rosidl_whole_archive(ctx, feature_configuration, cc_toolchain, library)
            for library in static_libraries
        ]),
        user_link_flags = depset(user_link_flags),
    )
    linking_outputs = cc_common.link(
        name = name,
        actions = ctx.actions,
        feature_configuration = feature_configuration,
        cc_toolchain = cc_toolchain,
        output_type = "dynamic_library",
        main_output = main_output,
        linking_contexts = [
            cc_common.create_linking_context(
                linker_inputs = depset([own_input] + linker_inputs, order = "topological"),
            ),
            ctx.attr._rosidl_link_extra_lib[CcInfo].linking_context,
        ],
    )
    lib_to_link = linking_outputs.library_to_link
    library = lib_to_link.resolved_symlink_dynamic_library or lib_to_link.dynamic_library
    interface_library = lib_to_link.resolved_symlink_interface_library or lib_to_link.interface_library
    kwargs = {}
    if symlink_dir:
        if "/" in symlink_dir:
            fail("symlink_dir must be a single path component, got {}".format(symlink_dir))
        kwargs["dynamic_library_symlink_path"] = symlink_dir + "/" + library.basename
        if interface_library:
            kwargs["interface_library_symlink_path"] = symlink_dir + "/" + interface_library.basename
    library_to_link = cc_common.create_library_to_link(
        actions = ctx.actions,
        feature_configuration = feature_configuration,
        cc_toolchain = cc_toolchain,
        dynamic_library = library,
        interface_library = interface_library,
        **kwargs
    )
    return struct(
        file = library,
        library_to_link = library_to_link,
        linker_input = cc_common.create_linker_input(
            owner = ctx.label,
            libraries = depset([library_to_link]),
        ),
    )

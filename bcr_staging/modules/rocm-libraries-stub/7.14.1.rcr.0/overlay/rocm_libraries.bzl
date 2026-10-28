"""What the ROCm libraries' CMake configures (version and export headers)."""

load("@bazel_skylib//rules:write_file.bzl", "write_file")

def rocm_version_substitutions(library, version):
    """The @<library>_VERSION_*@ substitutions of a <library>-version.h.in.

    Args:
        library: The library's CMake project name (e.g. "rocblas").
        version: Its "major.minor.patch" version.

    Returns:
        A dict for expand_template's substitutions.
    """
    major, minor, patch = version.split(".")
    return {
        "@{}_VERSION_MAJOR@".format(library): major,
        "@{}_VERSION_MINOR@".format(library): minor,
        # rocm_setup_version()'s version number.
        "@{}_VERSION_NUMBER@".format(library): str(int(major) * 100000 + int(minor) * 100 + int(patch)),
        "@{}_VERSION_PATCH@".format(library): patch,
        # The git commit of a release build (unknown for a source archive).
        "@{}_VERSION_TWEAK@".format(library): "0",
    }

def cmake_export_header(name, out, base_name):
    """CMake's generate_export_header() output for a shared library.

    Args:
        name: The target name.
        out: The header's path.
        base_name: The macros' prefix (<base_name>_EXPORT, ...).
    """
    write_file(
        name = name,
        out = out,
        content = [
            "// Generated as CMake's generate_export_header() does.",
            "#ifndef {}_EXPORT_H".format(base_name),
            "#define {}_EXPORT_H".format(base_name),
            "",
            "#ifdef {}_STATIC_DEFINE".format(base_name),
            "#  define {}_EXPORT".format(base_name),
            "#  define {}_NO_EXPORT".format(base_name),
            "#else",
            "#  ifndef {}_EXPORT".format(base_name),
            "#    define {}_EXPORT __attribute__((visibility(\"default\")))".format(base_name),
            "#  endif",
            "#  ifndef {}_NO_EXPORT".format(base_name),
            "#    define {}_NO_EXPORT __attribute__((visibility(\"hidden\")))".format(base_name),
            "#  endif",
            "#endif",
            "",
            "#ifndef {}_DEPRECATED".format(base_name),
            "#  define {}_DEPRECATED __attribute__ ((__deprecated__))".format(base_name),
            "#endif",
            "",
            "#ifndef {}_DEPRECATED_EXPORT".format(base_name),
            "#  define {0}_DEPRECATED_EXPORT {0}_EXPORT {0}_DEPRECATED".format(base_name),
            "#endif",
            "",
            "#ifndef {}_DEPRECATED_NO_EXPORT".format(base_name),
            "#  define {0}_DEPRECATED_NO_EXPORT {0}_NO_EXPORT {0}_DEPRECATED".format(base_name),
            "#endif",
            "",
            "#endif",
            "",
        ],
    )

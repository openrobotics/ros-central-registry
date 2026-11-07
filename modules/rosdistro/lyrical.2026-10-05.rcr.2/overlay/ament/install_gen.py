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

"""Generate the ament_cmake / ament_python / colcon metadata files for a package.

This emulates the files that `ament_package()` (ament_cmake_core), the
`ament_cmake_export_*` helpers, `ament_package` (the Python package providing
the package-level `local_setup.*` templates) and colcon's shell extensions
write into an install prefix, so that a Bazel-built underlay is a drop-in
replacement for a colcon-built one.

Usage: install_gen.py --spec spec.json --package-xml package.xml --out <dir>

The output directory is the `share/` directory of the *package prefix* (e.g.
`<prefix>/rclcpp/share/`); everything ament/colcon generate lives below it
(`<pkg>/cmake/...`, `ament_index/...`, `colcon-core/...`).
"""

import argparse
import configparser
import json
import os
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(HERE, "templates")


def _render(template, subs):
    with open(os.path.join(TEMPLATES, template)) as f:
        content = f.read()
    for key, value in subs.items():
        content = content.replace("@%s@" % key, value)
    return content


def _write(out, rel, content):
    # Paths are expressed relative to the package prefix for readability, but
    # the output directory *is* the share/ directory.
    assert rel.startswith("share/"), rel
    path = os.path.join(out, rel[len("share/"):])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def parse_package_xml(path):
    """Return a dict with name, version, build_type and dependency lists."""
    tree = ET.parse(path)
    root = tree.getroot()

    def texts(*tags):
        # Document order matters: ament/colcon preserve package.xml ordering.
        return [e.text.strip() for e in root if e.tag in tags and e.text]

    build_type = "ament_cmake"
    export = root.find("export")
    if export is not None:
        bt = export.find("build_type")
        if bt is not None and bt.text:
            build_type = bt.text.strip()
    name = root.findtext("name", default="").strip()
    version = root.findtext("version", default="0.0.0").strip()
    return {
        "name": name,
        "version": version,
        "build_type": build_type,
        "description": " ".join((root.findtext("description") or "").split()),
        "maintainer": ", ".join(e.text.strip() for e in root.findall("maintainer") if e.text),
        "license": ", ".join(e.text.strip() for e in root.findall("license") if e.text),
        "exec_depends": _unique(texts("depend", "exec_depend")),
        "build_export_depends": _unique(texts("depend", "build_export_depend")),
        "test_depends": _unique(texts("test_depend")),
    }


def _unique(items):
    seen = []
    for i in items:
        if i not in seen:
            seen.append(i)
    return seen


def generate(spec, pkg, out):
    name = spec.get("name") or pkg["name"]
    version = pkg["version"]
    prefix = spec["prefix"]
    pyver = spec.get("pyver", "python3")
    build_type = spec.get("build_type") or pkg["build_type"]
    is_python = build_type == "ament_python"
    # Plain CMake packages (colcon's `cmake` build type): colcon only writes
    # its own package.* / hook/ files for them; nothing from ament_cmake.
    is_cmake = build_type == "cmake"
    has_lib = spec.get("has_lib", False)
    has_bin = spec.get("has_bin", False)
    has_pkgconfig = spec.get("has_pkgconfig", False)
    has_python = spec.get("has_python", False)
    # The ament_export_*() calls are CMake-side decisions we can't observe from
    # Bazel; the ament_package rule reports whether upstream makes them (they
    # all default to "yes"), and approximates ament_export_dependencies() with
    # the package.xml's build-export dependencies that are also ament packages
    # in the Bazel graph unless an explicit list is given.
    all_libraries = spec.get("libraries", [])
    libraries = all_libraries if spec.get("export_libraries", True) else []
    # ament_export_targets(... HAS_LIBRARY_TARGET) registers the library_path
    # environment hook without ament_export_libraries().
    library_path_hook = bool(libraries) or bool(spec.get("export_library_path", False))
    include_dirs = spec.get("include_dirs", []) if spec.get("export_include_directories", True) else []
    if spec.get("export_dependencies_list"):
        dependencies = list(spec["export_dependencies_list"])
    elif spec.get("export_dependencies", True):
        dependencies = [d for d in spec.get("dependencies", []) if d in pkg["build_export_depends"]]
    else:
        dependencies = []
    exports = spec.get("exports", [])
    extra_env_hooks = spec.get("env_hooks", [])
    share = "share/%s" % name

    base = {
        "PKG": name,
        "VERSION": version,
        "PREFIX": prefix,
        "PYVER": pyver,
    }

    # ---- ament_index / colcon resources -------------------------------------
    if not is_cmake:
        _write(out, "share/ament_index/resource_index/packages/%s" % name, "")
    run_deps = sorted(set(pkg["exec_depends"] + pkg["build_export_depends"]))
    _write(out, "share/colcon-core/packages/%s" % name, ":".join(run_deps))
    if not is_python and not is_cmake:
        _write(
            out,
            "share/ament_index/resource_index/package_run_dependencies/%s" % name,
            ";".join(_unique(pkg["build_export_depends"] + pkg["exec_depends"] + pkg["test_depends"])),
        )
        _write(out, "share/ament_index/resource_index/parent_prefix_path/%s" % name, "")

    # ---- colcon package.* (all build types) ---------------------------------
    package_dsv = []
    hooks_sh = []
    hooks_ps1 = []

    def add_hook(hook_dir, hook, template_dir):
        for ext in ("ps1", "dsv", "sh"):
            tpl = "%s/%s.%s.in" % (template_dir, hook, ext)
            if os.path.exists(os.path.join(TEMPLATES, tpl)):
                _write(out, "%s/%s/%s.%s" % (share, hook_dir, hook, ext), _render(tpl, base))
            package_dsv.append("source;%s/%s/%s.%s" % (share, hook_dir, hook, ext))
        hooks_sh.append('_colcon_package_sh_source_script "$COLCON_CURRENT_PREFIX/%s/%s/%s.sh"' % (share, hook_dir, hook))
        hooks_ps1.append('colcon_package_source_powershell_script "$env:COLCON_CURRENT_PREFIX/%s/%s/%s.ps1"' % (share, hook_dir, hook))

    if is_python:
        if has_bin:
            add_hook("hook", "path", "python_hook")
        add_hook("hook", "pythonpath", "python_hook")
        if has_bin:
            add_hook("hook", "pythonscriptspath", "python_hook")
        add_hook("hook", "ament_prefix_path", "python_hook")
        local_setup_bash = ""
        local_setup_zsh = ""
    elif is_cmake:
        # colcon-cmake: shell hooks only, in colcon's registration order.
        if spec.get("colcon_hooks", True):
            if spec.get("cmake_prefix_path_hook", True):
                add_hook("hook", "cmake_prefix_path", "hook")
            if has_lib:
                add_hook("hook", "ld_library_path_lib", "hook")
            if has_bin:
                add_hook("hook", "path", "python_hook")
            if has_pkgconfig:
                add_hook("hook", "pkg_config", "cmake_hook")
            if has_bin:
                add_hook("hook", "pythonscriptspath", "python_hook")
            if spec.get("pkg_config_path_hook", True):
                add_hook("hook", "pkg_config_path", "cmake_hook")
                add_hook("hook", "pkg_config_path_multiarch", "cmake_hook")
        local_setup_bash = ""
        local_setup_zsh = ""
    else:
        if spec.get("cmake_prefix_path_hook", True):
            add_hook("hook", "cmake_prefix_path", "hook")
        if has_lib:
            add_hook("hook", "ld_library_path_lib", "hook")
        if has_bin:
            add_hook("hook", "path", "python_hook")
        if has_python:
            add_hook("hook", "pythonpath", "python_hook")
        if has_bin:
            add_hook("hook", "pythonscriptspath", "python_hook")
        for ext in ("bash", "dsv", "ps1", "sh", "zsh"):
            package_dsv.append("source;%s/local_setup.%s" % (share, ext))
        hooks_sh.append('_colcon_package_sh_source_script "$COLCON_CURRENT_PREFIX/%s/local_setup.sh"' % share)
        hooks_ps1.append('colcon_package_source_powershell_script "$env:COLCON_CURRENT_PREFIX/%s/local_setup.ps1"' % share)
        local_setup_bash = (
            "# setting COLCON_CURRENT_PREFIX avoids determining the prefix in the sourced scripts\n"
            'COLCON_CURRENT_PREFIX="$_colcon_package_bash_COLCON_CURRENT_PREFIX"\n\n'
            "# source bash hooks\n"
            '_colcon_package_bash_source_script "$COLCON_CURRENT_PREFIX/%s/local_setup.bash"\n\n'
            "unset COLCON_CURRENT_PREFIX\n\n" % share
        )
        local_setup_zsh = local_setup_bash.replace("bash", "zsh")

    for hook in extra_env_hooks:
        package_dsv.append("source;%s/%s" % (share, hook))

    _write(out, "%s/package.dsv" % share, _render("package.dsv.in", dict(base, PACKAGE_DSV="\n".join(package_dsv))))
    _write(out, "%s/package.sh" % share, _render("package.sh.in", dict(base, HOOKS_SH="\n".join(hooks_sh))))
    _write(out, "%s/package.ps1" % share, _render("package.ps1.in", dict(base, HOOKS_PS1="\n".join(hooks_ps1))))
    _write(out, "%s/package.bash" % share, _render("package.bash.in", dict(base, LOCAL_SETUP_BASH=local_setup_bash)))
    _write(out, "%s/package.zsh" % share, _render("package.zsh.in", dict(base, LOCAL_SETUP_ZSH=local_setup_zsh)))

    if is_python or is_cmake:
        return

    # ---- ament_cmake environment hooks + local_setup.* ---------------------
    env_hooks = ["ament_prefix_path"]
    if library_path_hook:
        env_hooks.append("library_path")
    env_hooks.append("path")
    if has_python and spec.get("python_env_hook", True):
        env_hooks.append("pythonpath")
    for hook in env_hooks:
        for ext in ("dsv", "sh"):
            _write(out, "%s/environment/%s.%s" % (share, hook, ext), _render("environment/%s.%s.in" % (hook, ext), base))
    env_hooks_sh = "\n".join(
        'ament_append_value AMENT_ENVIRONMENT_HOOKS "$AMENT_CURRENT_PREFIX/%s/environment/%s.sh"' % (share, h)
        for h in env_hooks
    )
    env_hooks_dsv = "\n".join("source;%s/environment/%s.sh" % (share, h) for h in env_hooks)
    _write(out, "%s/local_setup.sh" % share, _render("local_setup.sh.in", dict(base, ENV_HOOKS_SH=env_hooks_sh)))
    _write(out, "%s/local_setup.dsv" % share, _render("local_setup.dsv.in", dict(base, ENV_HOOKS_DSV=env_hooks_dsv)))
    for ext in ("bash", "zsh", "fish"):
        _write(out, "%s/local_setup.%s" % (share, ext), _render("local_setup.%s.in" % ext, base))

    # ---- CMake config -------------------------------------------------------
    extras = []
    cmake = "%s/cmake" % share
    if include_dirs:
        extras.append("ament_cmake_export_include_directories-extras.cmake")
        dirs = ";".join("${%s_DIR}/../../../%s" % (name, d) for d in include_dirs)
        _write(out, "%s/ament_cmake_export_include_directories-extras.cmake" % cmake,
               _render("cmake/ament_cmake_export_include_directories-extras.cmake.in", dict(base, INCLUDE_DIRS=dirs)))
    if libraries:
        extras.append("ament_cmake_export_libraries-extras.cmake")
        _write(out, "%s/ament_cmake_export_libraries-extras.cmake" % cmake,
               _render("cmake/ament_cmake_export_libraries-extras.cmake.in", dict(base, LIBRARIES=";".join(libraries))))
    if exports:
        extras.append("ament_cmake_export_targets-extras.cmake")
        _write(out, "%s/ament_cmake_export_targets-extras.cmake" % cmake,
               _render("cmake/ament_cmake_export_targets-extras.cmake.in",
                       dict(base, TARGETS=";".join(e["export"] for e in exports))))
        for export in exports:
            _write_export(out, cmake, base, export)
    if dependencies:
        extras.append("ament_cmake_export_dependencies-extras.cmake")
        _write(out, "%s/ament_cmake_export_dependencies-extras.cmake" % cmake,
               _render("cmake/ament_cmake_export_dependencies-extras.cmake.in",
                       dict(base, DEPENDENCIES=";".join(dependencies))))
    extras += spec.get("extra_cmake", [])
    _write(out, "%s/%sConfig.cmake" % (cmake, name), _render("cmake/PKGConfig.cmake.in", dict(base, EXTRAS=";".join(extras))))
    _write(out, "%s/%sConfig-version.cmake" % (cmake, name), _render("cmake/PKGConfig-version.cmake.in", base))


def _write_export(out, cmake, base, export):
    """Write <export>Export.cmake and <export>Export-noconfig.cmake."""
    export_name = export["export"] + "Export"
    namespace = export.get("namespace", base["PKG"])
    targets = export["targets"]
    expected = " ".join("%s::%s" % (namespace, t["name"]) for t in targets)
    definitions = []
    imports = []
    for t in targets:
        full = "%s::%s" % (namespace, t["name"])
        kind = t.get("type", "SHARED")
        definitions.append("# Create imported target %s" % full)
        definitions.append("add_library(%s %s IMPORTED)\n" % (full, kind))  # SHARED, STATIC or INTERFACE
        props = []
        if t.get("include_dirs"):
            props.append('  INTERFACE_INCLUDE_DIRECTORIES "%s"' % ";".join("${_IMPORT_PREFIX}/%s" % d for d in t["include_dirs"]))
        if t.get("link_libraries"):
            props.append('  INTERFACE_LINK_LIBRARIES "%s"' % ";".join(t["link_libraries"]))
        if props:
            definitions.append("set_target_properties(%s PROPERTIES\n%s\n)\n" % (full, "\n".join(props)))
        if t.get("location"):
            imports.append('# Import target "%s" for configuration ""' % full)
            imports.append("set_property(TARGET %s APPEND PROPERTY IMPORTED_CONFIGURATIONS NOCONFIG)" % full)
            imports.append("set_target_properties(%s PROPERTIES" % full)
            if kind == "STATIC":
                imports.append('  IMPORTED_LINK_INTERFACE_LANGUAGES_NOCONFIG "CXX"')
                imports.append('  IMPORTED_LOCATION_NOCONFIG "${_IMPORT_PREFIX}/%s"' % t["location"])
            else:
                imports.append('  IMPORTED_LOCATION_NOCONFIG "${_IMPORT_PREFIX}/%s"' % t["location"])
                imports.append('  IMPORTED_SONAME_NOCONFIG "%s"' % os.path.basename(t["location"]))
            imports.append("  )\n")
            imports.append("list(APPEND _cmake_import_check_targets %s )" % full)
            imports.append('list(APPEND _cmake_import_check_files_for_%s "${_IMPORT_PREFIX}/%s" )\n' % (full, t["location"]))
    _write(out, "%s/%s.cmake" % (cmake, export_name),
           _render("cmake/Export.cmake.in", dict(base, EXPECTED_TARGETS=expected, TARGET_DEFINITIONS="\n".join(definitions), EXPORT=export_name)))
    if imports:
        _write(out, "%s/%s-noconfig.cmake" % (cmake, export_name),
               _render("cmake/Export-noconfig.cmake.in", dict(base, TARGET_IMPORTS="\n".join(imports))))


def generate_egg_info(spec, pkg, out, setup_cfg=None):
    """Write <pkg>-<version>-py<X.Y>.egg-info/ under `out` (the site-packages dir)."""
    name = spec.get("name") or pkg["name"]
    pyver = spec.get("pyver", "python3").replace("python", "")
    egg = os.path.join(out, "%s-%s-py%s.egg-info" % (name, pkg["version"], pyver))
    os.makedirs(egg, exist_ok=True)
    with open(os.path.join(egg, "PKG-INFO"), "w") as f:
        f.write("Metadata-Version: 2.1\nName: %s\nVersion: %s\n" % (name, pkg["version"]))
        if pkg.get("description"):
            f.write("Summary: %s\n" % pkg["description"])
        if pkg.get("maintainer"):
            f.write("Maintainer: %s\n" % pkg["maintainer"])
        if pkg.get("license"):
            f.write("License: %s\n" % pkg["license"])
    with open(os.path.join(egg, "dependency_links.txt"), "w") as f:
        f.write("\n")
    with open(os.path.join(egg, "top_level.txt"), "w") as f:
        f.write("".join("%s\n" % t for t in spec.get("python_top_level", [])))
    with open(os.path.join(egg, "SOURCES.txt"), "w") as f:
        f.write("package.xml\nsetup.py\n")
    entry_groups = {}
    if setup_cfg and os.path.exists(setup_cfg):
        cfg = configparser.ConfigParser()
        cfg.optionxform = str
        cfg.read(setup_cfg)
        if cfg.has_section("options.entry_points"):
            for group, raw_val in cfg.items("options.entry_points"):
                lines = [ln.strip() for ln in raw_val.splitlines() if ln.strip()]
                if lines:
                    entry_groups[group] = lines
    scripts = spec.get("console_scripts", {})
    if scripts:
        entry_groups.setdefault("console_scripts", [])
        for script_name, entry in sorted(scripts.items()):
            line = "%s = %s" % (script_name, entry)
            if line not in entry_groups["console_scripts"]:
                entry_groups["console_scripts"].append(line)
    if entry_groups:
        with open(os.path.join(egg, "entry_points.txt"), "w") as f:
            for group, lines in entry_groups.items():
                f.write("[%s]\n" % group)
                for ln in lines:
                    f.write("%s\n" % ln)
                f.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--package-xml", required=False)
    parser.add_argument("--setup-cfg", required=False)
    parser.add_argument("--out", required=True)
    parser.add_argument("--egg-info-out", required=False)
    args = parser.parse_args()
    with open(args.spec) as f:
        spec = json.load(f)
    if args.package_xml:
        pkg = parse_package_xml(args.package_xml)
    else:
        pkg = {
            "name": spec["name"],
            "version": spec.get("version", "0.0.0"),
            "build_type": spec.get("build_type", "ament_cmake"),
            "exec_depends": spec.get("exec_depends", []),
            "build_export_depends": [],
            "test_depends": [],
        }
    os.makedirs(args.out, exist_ok=True)
    generate(spec, pkg, args.out)
    if args.egg_info_out:
        os.makedirs(args.egg_info_out, exist_ok=True)
        generate_egg_info(spec, pkg, args.egg_info_out, args.setup_cfg)


if __name__ == "__main__":
    main()


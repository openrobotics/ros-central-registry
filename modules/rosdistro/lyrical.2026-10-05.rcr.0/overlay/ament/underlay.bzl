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

"""ament_underlay: aggregate a dependency tree of ament_package targets into
one installable underlay tarball.

    load("@rosdistro//ament:defs.bzl", "ament_underlay")

    ament_underlay(
        name = "desktop_full",
        deps = ["@desktop_full//:ament_package"],
    )

`bazel build //:desktop_full` then produces `desktop_full.tar.gz` whose
content is `<install_prefix>/<pkg>/{bin,lib,include,share}` for every package
reachable from the given roots -- the same layout `colcon build` produces with
its default (isolated) install layout, rooted at `/opt/ros/<distro>`.

An aspect walks the `deps` edges of every ament_package/ament_index target
collecting each package's own `AmentPackageInfo`; the rule then merges all of
them into a single `PackageFilegroupInfo` that rules_pkg turns into the tar.
"""

load("@bazel_skylib//rules:common_settings.bzl", "BuildSettingInfo")
load("@rules_pkg//pkg:providers.bzl", "PackageFilegroupInfo", "PackageFilesInfo")
load("@rules_pkg//pkg:tar.bzl", "pkg_tar")
load(":providers.bzl", "AmentPackageInfo")

AmentUnderlayInfo = provider(
    doc = "Transitive set of ament packages reachable through `deps`.",
    fields = {
        "packages": "depset of struct(name, files, label) -- one entry per ament package.",
    },
)

def _underlay_aspect_impl(target, ctx):
    transitive = []
    for dep in getattr(ctx.rule.attr, "deps", []):
        if AmentUnderlayInfo in dep:
            transitive.append(dep[AmentUnderlayInfo].packages)
    direct = []
    if AmentPackageInfo in target:
        info = target[AmentPackageInfo]

        # Tuples are hashable and can live in a depset; dicts cannot.
        direct.append(struct(
            name = info.name,
            label = str(target.label),
            files = tuple(info.files.items()),
        ))
    return [AmentUnderlayInfo(packages = depset(direct, transitive = transitive))]

ament_underlay_aspect = aspect(
    implementation = _underlay_aspect_impl,
    attr_aspects = ["deps"],
    doc = "Collects AmentPackageInfo from every ament_package reachable via deps.",
)

def _ament_underlay_files_impl(ctx):
    install_prefix = ctx.attr._install_prefix[BuildSettingInfo].value.rstrip("/")
    packages = depset(transitive = [
        dep[AmentUnderlayInfo].packages
        for dep in ctx.attr.deps
        if AmentUnderlayInfo in dep
    ]).to_list()

    pkg_files = []
    all_files = []
    seen = {}
    manifest = []
    for pkg in packages:
        if pkg.name in seen:
            # The same package can be reached through several labels (e.g.
            # :ament_index and :ament_package of one module); first one wins.
            continue
        seen[pkg.name] = pkg.label
        dest_src_map = {}
        for dest, f in pkg.files:
            dest_src_map[install_prefix + "/" + pkg.name + "/" + dest] = f
            all_files.append(f)
        pkg_files.append((PackageFilesInfo(dest_src_map = dest_src_map, attributes = {}), ctx.label))
        manifest.append(pkg.name)

    # Top-level colcon underlay files at <install_prefix>/ (setup.*, local_setup.*,
    # _local_setup_util_*.py, .colcon_install_layout, COLCON_IGNORE).
    top_map = {}
    layout_file = ctx.actions.declare_file(ctx.label.name + "_underlay/.colcon_install_layout")
    ctx.actions.write(layout_file, "isolated\n")
    top_map[install_prefix + "/.colcon_install_layout"] = layout_file

    ignore_file = ctx.actions.declare_file(ctx.label.name + "_underlay/COLCON_IGNORE")
    ctx.actions.write(ignore_file, "")
    top_map[install_prefix + "/COLCON_IGNORE"] = ignore_file

    abs_prefix = "/" + install_prefix
    setup_sh = ctx.actions.declare_file(ctx.label.name + "_underlay/setup.sh")
    ctx.actions.expand_template(
        template = ctx.file._setup_sh_tpl,
        output = setup_sh,
        substitutions = {"@INSTALL_PREFIX@": abs_prefix},
    )
    top_map[install_prefix + "/setup.sh"] = setup_sh

    local_setup_sh = ctx.actions.declare_file(ctx.label.name + "_underlay/local_setup.sh")
    ctx.actions.expand_template(
        template = ctx.file._local_setup_sh_tpl,
        output = local_setup_sh,
        substitutions = {"@INSTALL_PREFIX@": abs_prefix},
    )
    top_map[install_prefix + "/local_setup.sh"] = local_setup_sh

    for f in ctx.files._underlay_static_files:
        top_map[install_prefix + "/" + f.basename] = f

    all_files.extend(top_map.values())
    pkg_files.append((PackageFilesInfo(dest_src_map = top_map, attributes = {}), ctx.label))

    manifest_file = ctx.actions.declare_file(ctx.label.name + ".packages.txt")
    ctx.actions.write(manifest_file, "\n".join(sorted(manifest)) + "\n")

    return [
        DefaultInfo(files = depset(all_files)),
        PackageFilegroupInfo(pkg_files = pkg_files, pkg_dirs = [], pkg_symlinks = []),
        OutputGroupInfo(manifest = depset([manifest_file])),
    ]

ament_underlay_files = rule(
    implementation = _ament_underlay_files_impl,
    attrs = {
        "deps": attr.label_list(aspects = [ament_underlay_aspect], doc = "Root ament_package targets."),
        "_install_prefix": attr.label(default = "@rosdistro//:install_prefix"),
        "_setup_sh_tpl": attr.label(
            default = "@rosdistro//ament:templates/underlay/setup.sh.in",
            allow_single_file = True,
        ),
        "_local_setup_sh_tpl": attr.label(
            default = "@rosdistro//ament:templates/underlay/local_setup.sh.in",
            allow_single_file = True,
        ),
        "_underlay_static_files": attr.label_list(
            default = [
                "@rosdistro//ament:templates/underlay/_local_setup_util_ps1.py",
                "@rosdistro//ament:templates/underlay/_local_setup_util_sh.py",
                "@rosdistro//ament:templates/underlay/local_setup.bash",
                "@rosdistro//ament:templates/underlay/local_setup.ps1",
                "@rosdistro//ament:templates/underlay/local_setup.zsh",
                "@rosdistro//ament:templates/underlay/setup.bash",
                "@rosdistro//ament:templates/underlay/setup.ps1",
                "@rosdistro//ament:templates/underlay/setup.zsh",
            ],
            allow_files = True,
        ),
    },
    provides = [PackageFilegroupInfo],
)

def ament_underlay(name, deps, visibility = None, **kwargs):
    """Produce <name>.tar.gz containing the underlay for all packages reachable from deps."""
    ament_underlay_files(
        name = name + "_files",
        deps = deps,
        visibility = visibility,
    )
    pkg_tar(
        name = name,
        srcs = [":" + name + "_files"],
        extension = "tar.gz",
        visibility = visibility,
        **kwargs
    )

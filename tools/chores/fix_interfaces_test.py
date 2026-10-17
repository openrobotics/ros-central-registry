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

import tempfile
import unittest
from pathlib import Path

from tools.chores import fix_interfaces as fi
from tools.chores import vendor_lib as vl


class TestParseTypes(unittest.TestCase):
    def test_primitives_are_builtin(self):
        for t in ("int32", "float64[]", "string<=10", "uint8[4]", "wstring"):
            self.assertIsNone(fi.parse_type_token(t, "pkg"), t)

    def test_time_maps_to_builtin_interfaces(self):
        self.assertEqual(fi.parse_type_token("time", "pkg"), fi.InterfaceRef("builtin_interfaces", "msg", "Time"))

    def test_qualified_and_bare(self):
        self.assertEqual(fi.parse_type_token("std_msgs/Header", "pkg"), fi.InterfaceRef("std_msgs", "msg", "Header"))
        self.assertEqual(fi.parse_type_token("Foo[<=3]", "pkg"), fi.InterfaceRef("pkg", "msg", "Foo"))

    def test_invalid(self):
        with self.assertRaises(ValueError):
            fi.parse_type_token("a/b/c/d", "pkg")

    def test_scan_rosidl_skips_comments_constants_separators(self):
        text = "# comment\nint32 FOO=1\nstd_msgs/Header header\n---\nFoo foo  # trailing\n---\nFoo again\n"
        self.assertEqual(fi.scan_rosidl_text(text, "pkg"), [
            fi.InterfaceRef("std_msgs", "msg", "Header"),
            fi.InterfaceRef("pkg", "msg", "Foo"),
        ])

    def test_scan_idl(self):
        text = '#include "std_msgs/msg/Header.idl"\n#include <pkg/srv/Bar.idl>\nmodule pkg {};\n'
        self.assertEqual(fi.scan_idl_text(text), [
            fi.InterfaceRef("std_msgs", "msg", "Header"),
            fi.InterfaceRef("pkg", "srv", "Bar"),
        ])

    def test_scan_idl_relative_includes(self):
        # rosbag2_test_msgdefs/msg/ComplexWithRelativeDep.idl does `#include "BasicIdl.idl"`.
        text = '#include "BasicIdl.idl"\n#include "../srv/Baz.idl"\n#include "../../outside.idl"\n'
        self.assertEqual(fi.scan_idl_text(text, "pkg", "msg"), [
            fi.InterfaceRef("pkg", "msg", "BasicIdl"),
            fi.InterfaceRef("pkg", "srv", "Baz"),
        ])
        self.assertEqual(fi.scan_idl_text(text), [])


class TestLabels(unittest.TestCase):
    def test_label_for(self):
        self.assertEqual(fi.label_for(fi.InterfaceRef("p", "msg", "A"), "p", "msg"), ":A")
        self.assertEqual(fi.label_for(fi.InterfaceRef("p", "msg", "A"), "p", "srv"), "//msg:A")
        self.assertEqual(fi.label_for(fi.InterfaceRef("q", "msg", "A"), "p", "msg"), "@q//msg:A")

    def test_select_generator(self):
        self.assertEqual(fi.select_generator({"rosidl_core_generators"}), (fi.CORE, True))
        self.assertEqual(fi.select_generator({"rosidl_default_generators"}), (fi.DEFAULT, True))
        self.assertEqual(fi.select_generator(set()), (fi.DEFAULT, False))

    def test_core_srv_requires_service_event_info(self):
        f = fi.InterfaceFile("srv", "S", Path("S.srv"))
        self.assertEqual(fi.required_labels(f, [], fi.CORE, "p"), ["@service_msgs//msg:ServiceEventInfo"])
        self.assertEqual(fi.required_labels(f, [], fi.DEFAULT, "p"), [])


class TestBuildChecks(unittest.TestCase):
    def setUp(self):
        self.files = [fi.InterfaceFile("msg", "A", Path("A.msg")), fi.InterfaceFile("msg", "B", Path("B.msg"))]
        self.required = {"A": [":B"], "B": []}

    def test_render_roundtrip_is_clean(self):
        text = fi.render_interface_build("p", "msg", self.files, self.required, fi.DEFAULT, None, "BSD")
        check = fi.check_interface_build("p", "msg", self.files, self.required, fi.DEFAULT, text)
        self.assertEqual(check.problems, [])

    def test_missing_build_counts_new(self):
        check = fi.check_interface_build("p", "msg", self.files, self.required, fi.DEFAULT, None)
        self.assertEqual(check.stats[fi.STAT_NEW], 2)
        self.assertIsNotNone(check.fixed_text)

    def test_old_new_buggy_stats(self):
        text = (
            'load("@rosidl_default_generators//:defs.bzl", "ros_message")\n'
            'ros_message(name = "A", src = "A.msg")\n'
            'ros_message(name = "Gone", src = "Gone.msg")\n'
        )
        check = fi.check_interface_build("p", "msg", self.files, self.required, fi.DEFAULT, text)
        self.assertEqual(dict(check.stats), {fi.STAT_BUGGY: 1, fi.STAT_NEW: 1, fi.STAT_OLD: 1})
        fixed = fi.check_interface_build("p", "msg", self.files, self.required, fi.DEFAULT, check.fixed_text)
        self.assertEqual(fixed.problems, [])

    def test_root_build_rewrite(self):
        text = (
            'load("@rosidl_default_generators//:defs.bzl", "default_generators")\n'
            'default_generators(\n    name = "x",\n    deps = [\n        "//msg:Old",\n        ":other",\n    ],\n)\n'
        )
        check = fi.check_root_build(text, fi.DEFAULT, ["//msg:A"])
        self.assertIn('"//msg:A"', check.fixed_text)
        self.assertIn('":other"', check.fixed_text)
        self.assertNotIn("//msg:Old", check.fixed_text)
        self.assertEqual(fi.check_root_build(check.fixed_text, fi.DEFAULT, ["//msg:A"]).problems, [])


class TestFormatting(unittest.TestCase):
    def test_package_line(self):
        r = fi.InterfaceResult("sensor_msgs", generator=fi.DEFAULT, interface_count=40)
        r.fixed_files.append("msg/BUILD.bazel")
        r.stats.update({fi.STAT_OLD: 1, fi.STAT_NEW: 3, fi.STAT_BUGGY: 2})
        self.assertEqual(vl.format_package_line("sensor_msgs", r, fi.STAT_KEYS),
                         "✎ fixed sensor_msgs (1 old, 3 new, 2 buggy) [40 default interfaces; rewrote msg/BUILD.bazel]")


class TestRootBuild(unittest.TestCase):
    def test_license_kind(self):
        cases = {
            "Apache License 2.0": "Apache-2.0", "Apache License, Version 2.0": "Apache-2.0", "ALv2": "Apache-2.0",
            "BSD": "BSD-3-Clause", "BSD 3-Clause License": "BSD-3-Clause", "BSD-2": "BSD-2-Clause",
            "MIT License": "MIT", "GPLv2+ license": "GPL-2.0-or-later", "LGPL v2.1": "LGPL-2.1-only",
            "BSD, GPL": "BSD-3-Clause", "GPL": None, None: None,
        }
        for text, want in cases.items():
            self.assertEqual(fi.license_kind(text), want, text)

    def test_insert_generators_and_license(self):
        text = (
            "# header\n\n"
            'load("@rosdistro//ament:defs.bzl", "ament_package")\n\n'
            'package(default_visibility = ["//visibility:public"])\n\n'
            'ament_package(\n    name = "ament_package",\n    package_xml = "package.xml",\n)\n'
        )
        check = fi.check_root_build(text, fi.DEFAULT, ["//msg:A", "//srv:B"], "BSD")
        self.assertEqual(check.problems[0][0], "no-generators")
        new = check.fixed_text
        self.assertIsNotNone(new, check.manual_reason)
        self.assertIn('load("@rosidl_default_generators//:defs.bzl", "default_generators")', new)
        self.assertIn('load("@rules_license//rules:license.bzl", "license")', new)
        self.assertIn("@rules_license//licenses/spdx:BSD-3-Clause", new)
        self.assertLess(new.index("default_generators("), new.index("ament_package("))
        self.assertLess(new.index("load(\"@rules_license"), new.index("package("))
        self.assertEqual(fi.check_root_build(new, fi.DEFAULT, ["//msg:A", "//srv:B"], "BSD").problems, [])

    def test_insert_generators_clash_is_manual(self):
        text = 'cc_library(name = "cc")\n'
        check = fi.check_root_build(text, fi.DEFAULT, ["//msg:A"])
        self.assertIsNone(check.fixed_text)
        self.assertIn("clash", check.manual_reason)

    def test_render_root_build(self):
        text = fi.render_root_build(fi.CORE, ["//srv:B", "//msg:A"], "Apache-2.0", ["@rosdistro//:ament_package"])
        self.assertIn("core_generators(", text)
        self.assertLess(text.index('"//msg:A"'), text.index('"//srv:B"'))
        self.assertIn("@rules_license//licenses/spdx:Apache-2.0", text)
        self.assertEqual(fi.check_root_build(text, fi.CORE, ["//msg:A", "//srv:B"], "Apache-2.0").problems, [])


class TestEndToEnd(unittest.TestCase):
    def _make_pkg(self, tmp, root_build):
        pkg = Path(tmp) / "p+"
        (pkg / "msg").mkdir(parents=True)
        (pkg / "srv").mkdir()
        (pkg / "package.xml").write_text(
            "<package><name>p</name><license>BSD</license>"
            "<depend>rosidl_default_generators</depend></package>")
        (pkg / "MODULE.bazel").write_text(
            'bazel_dep(name = "rosidl_default_generators", version = "1")\n'
            'bazel_dep(name = "rosdistro", version = "1")\n')
        (pkg / "msg" / "A.msg").write_text("B b\n")
        (pkg / "msg" / "B.msg").write_text("int32 x\n")
        (pkg / "srv" / "S.srv").write_text("A a\n---\nbool ok\n")
        if root_build is not None:
            (pkg / "BUILD.bazel").write_text(root_build)
        return pkg

    def _fix_then_clean(self, root_build):
        with tempfile.TemporaryDirectory() as tmp:
            pkg = self._make_pkg(tmp, root_build)
            packages = vl.discover_packages(Path(tmp))
            first = fi.InterfaceAuditor(packages, fix=True, buildifier=None).audit("p")
            self.assertEqual(first.status, "fixed", first.issues)
            self.assertEqual(first.stats[fi.STAT_NEW], 3)
            second = fi.InterfaceAuditor(packages, fix=False, buildifier=None).audit("p")
            self.assertEqual(second.status, "clean", second.issues)
            return (pkg / "BUILD.bazel").read_text(), (pkg / "srv" / "BUILD.bazel").read_text()

    def test_fix_existing_root(self):
        self._fix_then_clean(
            'load("@rosidl_default_generators//:defs.bzl", "default_generators")\n'
            'default_generators(\n    name = "p",\n    deps = [],\n)\n')

    def test_create_missing_root(self):
        root, srv = self._fix_then_clean(None)
        self.assertIn('"@rosdistro//:ament_package"', root)
        self.assertIn('"//srv:S"', root)
        self.assertIn('"//msg:A"', srv)
        self.assertIn("spdx:BSD-3-Clause", srv)

    def test_subfolder_gets_its_own_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            pkg = self._make_pkg(tmp, None)
            (pkg / "msg" / "fields").mkdir()
            (pkg / "msg" / "fields" / "Q.msg").write_text("Header header\n")
            (pkg / "msg" / "B.msg").write_text("Q q\n")  # bare Q resolves to msg/fields via the catalogue
            std = Path(tmp) / "std_msgs+"
            (std / "msg").mkdir(parents=True)
            (std / "package.xml").write_text("<package><name>std_msgs</name></package>")
            (std / "MODULE.bazel").write_text('module(name = "std_msgs", version = "5.0.0")\n')
            (std / "msg" / "Header.msg").write_text("int32 x\n")
            packages = vl.discover_packages(Path(tmp))
            first = fi.InterfaceAuditor(packages, fix=True, buildifier=None).audit("p")
            self.assertEqual(first.status, "fixed", first.issues)
            second = fi.InterfaceAuditor(packages, fix=False, buildifier=None).audit("p")
            self.assertEqual(second.status, "clean", second.issues)
            fields = (pkg / "msg" / "fields" / "BUILD.bazel").read_text()
            self.assertIn('src = "Q.msg"', fields)
            self.assertIn('"@std_msgs//msg:Header"', fields)
            self.assertIn('"//msg/fields:Q"', (pkg / "msg" / "BUILD.bazel").read_text())
            self.assertIn('"//msg/fields:Q"', (pkg / "BUILD.bazel").read_text())
            self.assertIn('version = "5.0.0"', (pkg / "MODULE.bazel").read_text())
            self.assertIn("<depend>std_msgs</depend>", (pkg / "package.xml").read_text())

    def test_manual_issue_blocks_all_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            pkg = self._make_pkg(tmp, None)
            (pkg / "msg" / "A.msg").write_text("Missing m\n")  # unresolved own-package type => manual
            result = fi.InterfaceAuditor(vl.discover_packages(Path(tmp)), fix=True, buildifier=None).audit("p")
            self.assertEqual(result.status, "manual")
            self.assertEqual(result.fixed_files, [])
            self.assertFalse((pkg / "BUILD.bazel").exists())
            self.assertFalse((pkg / "msg" / "BUILD.bazel").exists())

    def test_package_without_generator_is_left_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            pkg = self._make_pkg(tmp, None)
            (pkg / "package.xml").write_text("<package><name>p</name><license>BSD</license></package>")
            result = fi.InterfaceAuditor(vl.discover_packages(Path(tmp)), fix=True, buildifier=None).audit("p")
            self.assertEqual(result.status, "clean")
            self.assertEqual([i.code for i in result.issues], ["no-generator"])
            self.assertFalse((pkg / "BUILD.bazel").exists())


class TestDiscovery(unittest.TestCase):
    def test_bare_header_is_std_msgs(self):
        self.assertEqual(fi.parse_type_token("Header", "pkg"), fi.InterfaceRef("std_msgs", "msg", "Header"))
        self.assertEqual(fi.parse_type_token("Header[]", "pkg"), fi.InterfaceRef("std_msgs", "msg", "Header"))

    def test_kind_for_path(self):
        P = fi.PurePosixPath
        self.assertEqual(fi.kind_for_path(P("msg-ros2/A.msg")), "msg")
        self.assertEqual(fi.kind_for_path(P("srv/A.srv")), "srv")
        self.assertEqual(fi.kind_for_path(P("srv/A.idl")), "srv")
        self.assertEqual(fi.kind_for_path(P("other/A.idl")), "msg")
        self.assertIsNone(fi.kind_for_path(P("msg/A.txt")))

    def test_label_for_ref_dir(self):
        ref = fi.InterfaceRef("p", "msg", "Q")
        self.assertEqual(fi.label_for(ref, "p", "msg", "msg/fields"), "//msg/fields:Q")
        self.assertEqual(fi.label_for(ref, "p", "msg/fields", "msg/fields"), ":Q")
        self.assertEqual(fi.label_for(fi.InterfaceRef("q", "msg", "Q"), "p", "msg", "msg-ros2"), "@q//msg-ros2:Q")

    def test_cmake_explicit_base_rel_and_keywords(self):
        text = (
            "# rosidl_generate_interfaces(ignored \"msg/X.msg\")\n"
            "set(msgs \"msg/fields/A.msg\" msg-ros2/B.msg)\n"
            "list(APPEND msgs \"srv/C.srv\")\n"
            "rosidl_generate_interfaces(${PROJECT_NAME}\n"
            "  ${msgs}\n"
            "  \"${CMAKE_CURRENT_SOURCE_DIR}/msg_ros2:msg/D.msg\"\n"
            "  DEPENDENCIES std_msgs/msg/E.msg\n"
            ")\n")
        self.assertEqual(fi.parse_cmake_interfaces(text), (
            ["msg/fields/A.msg", "msg-ros2/B.msg", "srv/C.srv", "msg_ros2/msg/D.msg"], False))

    def test_cmake_unresolved_and_absent(self):
        self.assertEqual(fi.parse_cmake_interfaces("project(x)\n"), (None, False))
        self.assertEqual(fi.parse_cmake_interfaces("rosidl_generate_interfaces(p ${NOPE})\n"), ([], True))

    def test_cmake_glob_recurse(self):
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp)
            (pkg / "msg" / "motion").mkdir(parents=True)
            (pkg / "msg" / "A.msg").write_text("")
            (pkg / "msg" / "motion" / "B.msg").write_text("")
            text = ('file(GLOB_RECURSE M RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}" "msg/*.msg")\n'
                    "rosidl_generate_interfaces(p ${M})\n")
            self.assertEqual(fi.parse_cmake_interfaces(text, pkg), (["msg/A.msg", "msg/motion/B.msg"], False))

    def test_discover_nonstandard_dirs_and_templates(self):
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp)
            (pkg / "msg-ros2").mkdir()
            (pkg / "msg").mkdir()
            (pkg / "msg-ros2" / "A.msg").write_text("")
            (pkg / "msg" / "T.msg.in").write_text("")
            (pkg / "msg" / "Ros1Only.msg").write_text("")  # not listed in CMake: ignored
            (pkg / "CMakeLists.txt").write_text("rosidl_generate_interfaces(p msg-ros2/A.msg msg/T.msg)\n")
            d = fi.discover_interfaces(pkg)
            self.assertEqual([(f.bazel_dir, f.name) for f in d.files], [("msg-ros2", "A")])
            self.assertEqual([(t.bazel_dir, t.name) for t in d.templates], [("msg", "T")])
            self.assertEqual(d.catalogue(), {("msg", "A"): "msg-ros2", ("msg", "T"): "msg"})

    def test_discover_foreach_prefixed_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp)
            (pkg / "msg").mkdir()
            (pkg / "msg" / "A.msg").write_text("")
            (pkg / "CMakeLists.txt").write_text(
                'set(MSG_FILES "A.msg" "Gone.msg")\n'
                'foreach(F ${MSG_FILES})\n  list(APPEND T "msg/${F}")\nendforeach()\n'
                "rosidl_generate_interfaces(p ${MSG_FILES})\n")
            d = fi.discover_interfaces(pkg)
            self.assertEqual([(f.bazel_dir, f.name) for f in d.files], [("msg", "A")])
            self.assertEqual(d.warnings, ["CMakeLists.txt lists Gone.msg, which does not exist"])

    def test_template_rules_are_kept(self):
        files = [fi.InterfaceFile("msg", "A", Path("A.msg"))]
        text = ('load("@rosidl_default_generators//:defs.bzl", "ros_message")\n'
                'ros_message(name = "A", src = "A.msg")\nros_message(name = "T", src = ":gen")\n')
        check = fi.check_interface_build("p", "msg", files, {"A": []}, fi.DEFAULT, text, None, ["T"])
        self.assertEqual(check.problems, [])
        check = fi.check_interface_build("p", "msg", files, {"A": [":X"]}, fi.DEFAULT, text, None, ["T"])
        self.assertIsNone(check.fixed_text)
        self.assertIn("templated", check.manual_reason)


if __name__ == "__main__":
    unittest.main()

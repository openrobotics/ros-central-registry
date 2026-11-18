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

from tools.chores import fix_proto_fields as fpf


class TestParseFields(unittest.TestCase):
    def test_msg_with_constants_comments_and_defaults(self):
        msg = (
            "# Header comment\n"
            "uint8 NO_ERROR = 0\n"
            "uint8 LOOKUP_ERROR=1\n"
            "\n"
            "@optional\n"
            "std_msgs/Header header\n"
            "@optional int32 count 42 # trailing comment\n"
            'string label "a=b"\n'
        )
        self.assertEqual(
            fpf.parse_rosidl_sections(msg, ".msg"),
            [("", ["header", "count", "label"])],
        )

    def test_srv_sections(self):
        srv = "int64 a\nint64 b\n---\nint64 sum\n"
        self.assertEqual(
            fpf.parse_rosidl_sections(srv, ".srv"),
            [("Request", ["a", "b"]), ("Response", ["sum"])],
        )

    def test_srv_with_empty_request(self):
        srv = "---\nstring frame_yaml\n"
        self.assertEqual(
            fpf.parse_rosidl_sections(srv, ".srv"),
            [("Request", []), ("Response", ["frame_yaml"])],
        )

    def test_action_sections(self):
        action = (
            "# Goal\nint32 order\n---\n"
            "# Result\nint32[] sequence\n---\n"
            "# Feedback\nint32[] partial_sequence\n"
        )
        self.assertEqual(
            fpf.parse_rosidl_sections(action, ".action"),
            [
                ("Goal", ["order"]),
                ("Result", ["sequence"]),
                ("Feedback", ["partial_sequence"]),
            ],
        )

    def test_idl_single_struct(self):
        idl = (
            "module builtin_interfaces {\n"
            "  module msg {\n"
            '    @verbatim (language="comment", text="Time struct")\n'
            "    struct Time {\n"
            "      @default (value=0)\n"
            "      int32 sec;\n"
            "      sequence<double, 3> values;\n"
            "      uint32 nanosec[2];\n"
            "    };\n"
            "  };\n"
            "};\n"
        )
        self.assertEqual(
            fpf.parse_idl_sections(idl),
            [("", ["sec", "values", "nanosec"])],
        )

    def test_idl_empty_struct_placeholder_omitted(self):
        idl = (
            "module std_msgs {\n"
            "  module msg {\n"
            "    struct Empty {\n"
            "      uint8 structure_needs_at_least_one_member;\n"
            "    };\n"
            "  };\n"
            "};\n"
        )
        self.assertEqual(fpf.parse_idl_sections(idl), [("", [])])

    def test_idl_service_and_action_structs(self):
        srv_idl = (
            "module pkg { module srv {\n"
            "  struct Add_Request { int64 a; int64 b; };\n"
            "  struct Add_Response { int64 sum; };\n"
            "}; };\n"
        )
        self.assertEqual(
            fpf.parse_idl_sections(srv_idl),
            [("Request", ["a", "b"]), ("Response", ["sum"])],
        )
        act_idl = (
            "module pkg { module action {\n"
            "  struct Fib_Goal { int32 order; };\n"
            "  struct Fib_Result { sequence<int32> seq; };\n"
            "  struct Fib_Feedback { sequence<int32> seq; };\n"
            "}; };\n"
        )
        self.assertEqual(
            fpf.parse_idl_sections(act_idl),
            [("Goal", ["order"]), ("Result", ["seq"]), ("Feedback", ["seq"])],
        )


class TestUpdateInterfaceText(unittest.TestCase):
    def test_msg_rendering_and_idempotence(self):
        src = "std_msgs/Header header\nstring format\nuint8[] data\n"
        updated, kind = fpf.update_interface_text(src, ".msg")
        self.assertEqual(kind, fpf.STAT_ADDED)
        expected = (
            "std_msgs/Header header\n"
            "string format\n"
            "uint8[] data\n"
            "\n"
            "# ================================================================================\n"
            "# Protobuf Field Numbers — do not change assigned numbers; append new fields only.\n"
            "# ================================================================================\n"
            "# [proto]\n"
            "#   header = 1\n"
            "#   format = 2\n"
            "#   data = 3\n"
            "# ================================================================================\n"
        )
        self.assertEqual(updated, expected)
        again, kind2 = fpf.update_interface_text(updated, ".msg")
        self.assertIsNone(kind2)
        self.assertEqual(again, expected)

    def test_preserves_existing_numbers_and_appends_new_fields(self):
        existing_msg = (
            "int32 first\n"
            "int32 middle_new\n"
            "int32 second\n"
            "\n"
            "# ================================================================================\n"
            "# Protobuf Field Numbers — do not change assigned numbers; append new fields only.\n"
            "# ================================================================================\n"
            "# [proto]\n"
            "#   first = 1\n"
            "#   second = 5\n"
            "# ================================================================================\n"
        )
        updated, kind = fpf.update_interface_text(existing_msg, ".msg")
        self.assertEqual(kind, fpf.STAT_UPDATED)
        self.assertIn("#   first = 1\n#   second = 5\n#   middle_new = 6\n", updated)

    def test_idl_rendering(self):
        idl = (
            "module builtin_interfaces {\n"
            "  module msg {\n"
            "    struct Time {\n"
            "      int32 sec;\n"
            "      uint32 nanosec;\n"
            "    };\n"
            "  };\n"
            "};\n"
        )
        updated, kind = fpf.update_interface_text(idl, ".idl")
        self.assertEqual(kind, fpf.STAT_ADDED)
        self.assertTrue(
            updated.endswith(
                "// ================================================================================\n"
                "// Protobuf Field Numbers — do not change assigned numbers; append new fields only.\n"
                "// ================================================================================\n"
                "// [proto]\n"
                "//   sec = 1\n"
                "//   nanosec = 2\n"
                "// ================================================================================\n"
            )
        )


class TestEndToEndSweep(unittest.TestCase):
    def test_sweep_updates_vendored_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            vendor_dir = Path(tmp)
            pkg_dir = vendor_dir / "demo_msgs+"
            (pkg_dir / "msg").mkdir(parents=True)
            (pkg_dir / "srv").mkdir(parents=True)
            (pkg_dir / "package.xml").write_text(
                '<package format="3"><name>demo_msgs</name>'
                "<depend>rosidl_default_generators</depend></package>\n"
            )
            msg_file = pkg_dir / "msg" / "Point.msg"
            msg_file.write_text("float64 x\nfloat64 y\n")
            srv_file = pkg_dir / "srv" / "Ask.srv"
            srv_file.write_text("string question\n---\nstring answer\n")

            rc = fpf.main(["--vendor-dir", str(vendor_dir), "--no-progress"])
            self.assertEqual(rc, 0)
            self.assertIn("# [proto]\n#   x = 1\n#   y = 2\n", msg_file.read_text())
            self.assertIn(
                "# [proto:Request]\n#   question = 1\n#\n# [proto:Response]\n#   answer = 1\n",
                srv_file.read_text(),
            )

    def test_main_discovers_bazel_test_and_copy_file_interfaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            vendor_dir = Path(tmp)
            pkg_dir = vendor_dir / "sample_pkg+"
            (pkg_dir / "test" / "msg").mkdir(parents=True)
            (pkg_dir / "ros2").mkdir(parents=True)
            (pkg_dir / "msg").mkdir(parents=True)
            (pkg_dir / "MODULE.bazel").write_text('module(name = "sample_pkg", version = "1.0.0")\n')
            (pkg_dir / "package.xml").write_text(
                "<package format='3'><name>sample_pkg</name></package>\n"
            )
            test_msg = pkg_dir / "test" / "msg" / "String.msg"
            test_msg.write_text("string data\n")
            (pkg_dir / "test" / "msg" / "BUILD.bazel").write_text(
                'ros_interface(name = "String", src = "String.msg")\n'
            )
            copied_msg = pkg_dir / "ros2" / "Color.msg"
            copied_msg.write_text("float64 r\nfloat64 g\n")
            (pkg_dir / "msg" / "BUILD.bazel").write_text(
                'copy_file(name = "_copy", src = "//ros2:Color.msg", out = "Color.msg")\n'
                'ros_message(name = "Color", src = "Color.msg")\n'
            )

            rc = fpf.main(["--vendor-dir", str(vendor_dir), "--no-progress"])
            self.assertEqual(rc, 0)
            self.assertIn("# [proto]\n#   data = 1\n", test_msg.read_text())
            self.assertIn("# [proto]\n#   r = 1\n#   g = 2\n", copied_msg.read_text())


if __name__ == "__main__":
    unittest.main()

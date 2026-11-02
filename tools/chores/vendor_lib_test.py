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

import unittest

from tools.chores import vendor_lib as vl


class TestFormatting(unittest.TestCase):
    def test_progress(self):
        self.assertEqual(vl.format_progress(32, 67, 128), "Currently processing 32 packages (67 done, 128 remain)")
        self.assertEqual(vl.format_progress(1, 0, 0), "Currently processing 1 package (0 done, 0 remain)")


class TestScheduling(unittest.TestCase):
    def test_dependency_levels(self):
        self.assertEqual(vl.dependency_levels({"a": [], "b": ["a"], "c": ["a", "b"]}), [["a"], ["b"], ["c"]])

    def test_dependency_levels_cycle(self):
        levels = vl.dependency_levels({"a": ["b"], "b": ["a"], "c": ["a", "b"]})
        self.assertEqual(levels, [["a"], ["b"], ["c"]])

    def test_run_bfs_order_and_progress(self):
        order, progress = [], []
        graph = {"a": [], "b": ["a"], "c": ["b"], "d": []}
        results = vl.run_bfs(graph, lambda n: n.upper(), 4, lambda n, r: order.append(n),
                             on_progress=lambda *p: progress.append(p))
        self.assertEqual(results, {"a": "A", "b": "B", "c": "C", "d": "D"})
        self.assertLess(order.index("a"), order.index("b"))
        self.assertLess(order.index("b"), order.index("c"))
        self.assertEqual(progress[-1], (0, 4, 0))
        for running, done, remaining in progress:
            self.assertEqual(running + done + remaining, 4)


class TestModuleDeps(unittest.TestCase):
    MODULE = (
        'module(\n    name = "p",\n    version = "1.0.0-1.rcr.0",\n    bazel_compatibility = [">=7.2.1"],\n)\n\n'
        '# BCR dependencies\nbazel_dep(name = "rules_cc", version = "0.2.26")\n\n'
        '# RCR Dependencies\nbazel_dep(name = "ament_cmake", version = "2")\nbazel_dep(name = "std_msgs", version = "5")\n\n'
        '# Setup Python\npython = use_extension("@rules_python//python/extensions:python.bzl", "python")\n'
    )

    def test_parse_module_version(self):
        self.assertEqual(vl.parse_module_version(self.MODULE), "1.0.0-1.rcr.0")
        self.assertIsNone(vl.parse_module_version('bazel_dep(name = "x", version = "1")'))

    def test_add_into_rcr_block_sorted(self):
        out = vl.add_bazel_deps(self.MODULE, {"builtin_interfaces": "2.4.5-1.rcr.1", "std_msgs": "9"})
        block = out.split("# RCR Dependencies\n")[1].split("\n\n")[0].splitlines()
        self.assertEqual(block, [
            'bazel_dep(name = "ament_cmake", version = "2")',
            'bazel_dep(name = "builtin_interfaces", version = "2.4.5-1.rcr.1")',
            'bazel_dep(name = "std_msgs", version = "5")',  # existing pin untouched
        ])
        self.assertIn("# Setup Python", out)
        self.assertEqual(vl.add_bazel_deps(out, {"builtin_interfaces": "x"}), out)

    def test_add_without_rcr_block(self):
        text = 'module(name = "p", version = "1")\n\nbazel_dep(name = "rules_cc", version = "0.2.26")\n'
        out = vl.add_bazel_deps(text, {"std_msgs": "5"})
        self.assertTrue(out.endswith('# RCR Dependencies\nbazel_dep(name = "std_msgs", version = "5")\n'))

    def test_add_package_xml_depends_after_last_depend(self):
        text = (
            '<?xml version="1.0"?>\n<package format="3">\n  <name>p</name>\n'
            "  <buildtool_depend>ament_cmake</buildtool_depend>\n"
            "    <depend>geometry_msgs</depend>\n"
            "  <test_depend>ament_lint_auto</test_depend>\n"
            "  <export><build_type>ament_cmake</build_type></export>\n</package>\n"
        )
        out = vl.add_package_xml_depends(text, ["std_msgs", "builtin_interfaces", "geometry_msgs"])
        self.assertIn(
            "    <depend>geometry_msgs</depend>\n"
            "    <depend>builtin_interfaces</depend>\n"
            "    <depend>std_msgs</depend>\n"
            "  <test_depend>", out)
        # Only additions: every original line survives unchanged.
        self.assertEqual([line for line in out.splitlines() if "builtin_interfaces" not in line
                          and "std_msgs" not in line], text.splitlines())
        self.assertEqual(vl.add_package_xml_depends(out, ["std_msgs"]), out)

    def test_add_package_xml_depends_no_existing_depends(self):
        text = '<package format="3">\n  <name>p</name>\n  <export/>\n</package>\n'
        out = vl.add_package_xml_depends(text, ["std_msgs"])
        self.assertIn("  <name>p</name>\n  <depend>std_msgs</depend>\n  <export/>", out)

    def test_parse_rcr_deps(self):
        self.assertEqual(vl.parse_rcr_deps(self.MODULE), ["ament_cmake", "std_msgs"])
        self.assertIsNone(vl.parse_rcr_deps('bazel_dep(name = "x", version = "1")\n'))
        self.assertEqual(vl.ament_package_labels(["p", "std_msgs", "rosdistro"], "p"),
                         ["@rosdistro//:ament_package", "@std_msgs//:ament_package"])


if __name__ == "__main__":
    unittest.main()

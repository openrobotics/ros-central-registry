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

from tools.chores import fix_dependencies as fd
from tools.chores import vendor_lib as vl

WANT = ["@rosdistro//:ament_package", "@std_msgs//:ament_package"]

HEADER = "# Copyright\n\n"


class TestCheckAmentPackage(unittest.TestCase):
    def test_clean(self):
        text = HEADER + fd.AMENT_LOAD + "\n\n" + vl.render_ament_package(WANT) + "\n"
        self.assertEqual(fd.check_ament_package(text, WANT).problems, [])

    def test_buildifier_repo_shorthand(self):
        want = ["@ament_package//:ament_package", "@rosdistro//:ament_package"]
        text = (HEADER + fd.AMENT_LOAD + '\n\nament_package(\n    name = "ament_package",\n'
                '    package_xml = "package.xml",\n    deps = [\n        "@ament_package",\n'
                '        "@rosdistro//:ament_package",\n    ],\n)\n')
        self.assertEqual(fd.check_ament_package(text, want).problems, [])
        self.assertEqual(fd.canonical_label("@foo"), "@foo//:foo")
        self.assertEqual(fd.canonical_label("@foo//:bar"), "@foo//:bar")

    def test_missing_and_stale_keep_other_deps(self):
        text = (
            HEADER + 'load("@rosdistro//ament:defs.bzl", "ament_package")\n\n'
            "ament_package(\n"
            '    name = "ament_package",\n'
            "    headers = HEADERS,  # keep me\n"
            '    package_xml = "package.xml",\n'
            "    deps = [\n"
            '        ":local",\n'
            '        "@ament_cmake_gtest//:ament_package",\n'
            '        "@rosdistro//:ament_package",\n'
            "    ],\n"
            ")\n"
        )
        check = fd.check_ament_package(text, WANT)
        self.assertEqual([c for c, _ in check.problems], ["missing-deps", "stale-deps"])
        self.assertEqual(dict(check.stats), {fd.STAT_ADDED: 1, fd.STAT_REMOVED: 1})
        new = check.fixed_text
        self.assertIn("# keep me", new)
        self.assertIn('":local"', new)
        self.assertIn('"@std_msgs//:ament_package"', new)
        self.assertNotIn("ament_cmake_gtest", new)
        self.assertEqual(fd.check_ament_package(new, WANT).problems, [])

    def test_no_ament_package_adds_target_and_load_symbol(self):
        text = HEADER + 'load("@rosdistro//ament:defs.bzl", "ament_index")\n\ncc_library(name = "x")\n'
        check = fd.check_ament_package(text, WANT)
        self.assertEqual(check.problems[0][0], "no-ament-package")
        new = check.fixed_text
        self.assertIn('load("@rosdistro//ament:defs.bzl", "ament_index", "ament_package")', new)
        self.assertIn("### PACKAGING", new)
        self.assertEqual(fd.check_ament_package(new, WANT).problems, [])

    def test_no_ament_load_at_all(self):
        text = HEADER + 'cc_library(name = "x")\n'
        new = fd.check_ament_package(text, WANT).fixed_text
        self.assertLess(new.index(fd.AMENT_LOAD), new.index("cc_library("))
        self.assertEqual(fd.check_ament_package(new, WANT).problems, [])

    def test_wrong_name_and_missing_attrs_rerender(self):
        text = HEADER + fd.AMENT_LOAD + '\n\nament_package(name = "pkg")\n'
        check = fd.check_ament_package(text, WANT)
        codes = [c for c, _ in check.problems]
        self.assertIn("wrong-name", codes)
        self.assertIn("no-package-xml", codes)
        self.assertEqual(fd.check_ament_package(check.fixed_text, WANT).problems, [])

    def test_manual_cases(self):
        two = HEADER + 'ament_package(name = "a")\nament_package(name = "b")\n'
        self.assertIsNone(fd.check_ament_package(two, WANT).fixed_text)
        computed = HEADER + 'ament_package(name = "ament_package", package_xml = "package.xml", deps = DEPS)\n'
        check = fd.check_ament_package(computed, WANT)
        self.assertIsNone(check.fixed_text)
        self.assertIn("literal", check.manual_reason)

    def test_missing_root_build(self):
        check = fd.check_ament_package(None, WANT)
        self.assertEqual(check.stats[fd.STAT_ADDED], 2)
        self.assertTrue(check.fixed_text.startswith(vl.COPYRIGHT_HEADER))
        self.assertEqual(fd.check_ament_package(check.fixed_text, WANT).problems, [])


class TestEndToEnd(unittest.TestCase):
    def test_fix_then_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp) / "p+"
            pkg.mkdir()
            (pkg / "package.xml").write_text("<package><name>p</name></package>")
            (pkg / "MODULE.bazel").write_text(
                'module(name = "p", version = "1")\n\n'
                '# BCR dependencies\nbazel_dep(name = "rules_cc", version = "0.2.22")\n\n'
                '# RCR Dependencies\nbazel_dep(name = "rosdistro", version = "x")\n'
                'bazel_dep(name = "std_msgs", version = "5")\n')
            (pkg / "BUILD.bazel").write_text(
                fd.AMENT_LOAD + '\n\nament_package(\n    name = "ament_package",\n    package_xml = "package.xml",\n'
                '    deps = ["@ament_cmake_gtest//:ament_package"],\n)\n')
            packages = vl.discover_packages(Path(tmp))
            first = fd.DependencyAuditor(packages, fix=True, buildifier=None).audit("p")
            self.assertEqual(first.status, "fixed", first.issues)
            self.assertEqual(dict(first.stats), {fd.STAT_ADDED: 2, fd.STAT_REMOVED: 1})
            self.assertEqual(vl.format_package_line("p", first, fd.STAT_KEYS),
                             "✎ fixed p (2 added, 1 removed) [2 RCR deps; rewrote BUILD.bazel]")
            second = fd.DependencyAuditor(packages, fix=False, buildifier=None).audit("p")
            self.assertEqual(second.status, "clean", second.issues)
            self.assertNotIn("rules_cc", (pkg / "BUILD.bazel").read_text())

    def test_parallel_sweep_writes_each_package_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(40):
                pkg = Path(tmp) / f"p{i}+"
                pkg.mkdir()
                (pkg / "package.xml").write_text(f"<package><name>p{i}</name></package>")
                (pkg / "MODULE.bazel").write_text(f'# RCR Dependencies\nbazel_dep(name = "d{i}", version = "1")\n')
                (pkg / "BUILD.bazel").write_text(fd.AMENT_LOAD + '\n\nament_package(name = "ament_package")\n')
            packages = vl.discover_packages(Path(tmp))
            auditor = fd.DependencyAuditor(packages, fix=True, buildifier=None)
            results = vl.run_bfs({p: [] for p in packages}, auditor.audit, 16, lambda n, r: None)
            self.assertEqual({r.status for r in results.values()}, {"fixed"})
            for i in range(40):
                text = (Path(tmp) / f"p{i}+" / "BUILD.bazel").read_text()
                self.assertIn(f'"@d{i}//:ament_package"', text)

    def test_no_rcr_block_is_manual(self):
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp) / "p+"
            pkg.mkdir()
            (pkg / "package.xml").write_text("<package><name>p</name></package>")
            (pkg / "MODULE.bazel").write_text('module(name = "p", version = "1")\n')
            result = fd.DependencyAuditor(vl.discover_packages(Path(tmp)), fix=True, buildifier=None).audit("p")
            self.assertEqual(result.status, "manual")
            self.assertFalse((pkg / "BUILD.bazel").exists())

    def test_missing_root_only_created_on_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp) / "p+"
            pkg.mkdir()
            (pkg / "package.xml").write_text("<package><name>p</name></package>")
            (pkg / "MODULE.bazel").write_text('# RCR Dependencies\nbazel_dep(name = "rosdistro", version = "x")\n')
            packages = vl.discover_packages(Path(tmp))
            skipped = fd.DependencyAuditor(packages, fix=True, buildifier=None).audit("p")
            self.assertEqual(skipped.status, "clean")
            self.assertEqual([i.code for i in skipped.issues], ["unpackaged"])
            self.assertFalse((pkg / "BUILD.bazel").exists())
            created = fd.DependencyAuditor(packages, fix=True, buildifier=None, create_missing_root=True).audit("p")
            self.assertEqual(created.status, "fixed")
            self.assertIn('"@rosdistro//:ament_package"', (pkg / "BUILD.bazel").read_text())

    def test_cycle_and_unpackaged_deps_are_dropped(self):
        # fastrtps_c genuinely test-depends on fastrtps_cpp; fastrtps_cpp only
        # depends on fastrtps_c through a synthetic MODULE dep (not in
        # package.xml), so that's the edge that has to go. Both also depend on
        # `raw`, which has no root BUILD.bazel.
        with tempfile.TemporaryDirectory() as tmp:
            def make(name, deps, xml_deps, root=True):
                pkg = Path(tmp) / f"{name}+"
                pkg.mkdir()
                (pkg / "package.xml").write_text(f"<package><name>{name}</name>{xml_deps}</package>")
                (pkg / "MODULE.bazel").write_text("# RCR Dependencies\n" + "".join(
                    f'bazel_dep(name = "{d}", version = "1")\n' for d in deps))
                if root:
                    (pkg / "BUILD.bazel").write_text(
                        fd.AMENT_LOAD + '\n\nament_package(\n    name = "ament_package",\n'
                        '    package_xml = "package.xml",\n    deps = [\n' + "".join(
                            f'        "@{d}//:ament_package",\n' for d in sorted(deps)) + "    ],\n)\n")
            make("c", ["cpp", "raw", "rosdistro"], "<test_depend>cpp</test_depend><depend>raw</depend>")
            make("cpp", ["c", "raw", "rosdistro"], "<depend>raw</depend>")
            make("raw", ["rosdistro"], "", root=False)
            packages = vl.discover_packages(Path(tmp))
            unpackaged = {"raw"}
            cyclic = fd.plan_package_edges(packages, unpackaged)
            self.assertEqual(cyclic, {"cpp": {"c"}})
            auditor = fd.DependencyAuditor(packages, fix=True, buildifier=None, cyclic=cyclic, unpackaged=unpackaged)
            cpp = auditor.audit("cpp")
            self.assertEqual(cpp.status, "fixed", cpp.issues)
            self.assertEqual(sorted(i.code for i in cpp.issues), ["cycle", "unpackaged-dep"])
            text = (Path(tmp) / "cpp+" / "BUILD.bazel").read_text()
            self.assertNotIn("@c//", text)
            self.assertNotIn("@raw//", text)
            self.assertIn('"@rosdistro//:ament_package"', text)
            c = auditor.audit("c")
            self.assertIn('"@cpp//:ament_package"', (Path(tmp) / "c+" / "BUILD.bazel").read_text())
            self.assertEqual([i.code for i in c.issues], ["unpackaged-dep"])


class TestPlanEdges(unittest.TestCase):
    def test_priorities(self):
        xml = ("<package><name>p</name><test_depend>a</test_depend><depend>b</depend>"
               "<doc_depend>c</doc_depend><test_depend>b</test_depend><exec_depend>a</exec_depend></package>")
        self.assertEqual(fd.dep_priorities(xml), {"a": fd.PRIORITY_RUNTIME, "b": fd.PRIORITY_RUNTIME,
                                                  "c": fd.PRIORITY_TEST})

    def test_acyclic_graph_keeps_everything(self):
        wanted = {"a": {"b", "c", "external"}, "b": {"c"}, "c": set()}
        self.assertEqual(fd.plan_edges(wanted, lambda p, d: 0), {})

    def test_lowest_priority_edge_of_a_cycle_is_dropped(self):
        wanted = {"a": {"b"}, "b": {"c"}, "c": {"a"}}
        prio = {("a", "b"): 0, ("b", "c"): 2, ("c", "a"): 1}
        self.assertEqual(fd.plan_edges(wanted, lambda p, d: prio[(p, d)]), {"b": {"c"}})

    def test_ties_break_deterministically(self):
        wanted = {"a": {"b"}, "b": {"a"}}
        self.assertEqual(fd.plan_edges(wanted, lambda p, d: 0), {"b": {"a"}})


if __name__ == "__main__":
    unittest.main()

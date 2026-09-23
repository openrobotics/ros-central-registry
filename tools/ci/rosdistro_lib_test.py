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

import io
import subprocess
import tarfile
import unittest

from tools.ci import rosdistro_lib


def _make_tarball(files: dict) -> bytes:
    """Build an in-memory .tar.gz from {relative_path: file_content}."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for rel_path, content in files.items():
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name=rel_path)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _package_xml(name: str) -> str:
    return f'<?xml version="1.0"?><package format="2"><name>{name}</name></package>'


def _fake_get_with_bcr(tarball: bytes, bcr_hits=()):
    """
    A requests.get stand-in that answers both kinds of call
    resolve_unreleased_repo_packages makes: the archive download (any URL
    not under bcr.bazel.build) and the per-package BCR collision check
    (bcr_module_exists) -- returning 200 only for names in `bcr_hits`.
    """
    class _TarballResponse:
        content = tarball

        def raise_for_status(self):
            pass

    class _BcrResponse:
        def __init__(self, status_code):
            self.status_code = status_code

    def _get(url, *a, **k):
        if url.startswith("https://bcr.bazel.build/modules/"):
            name = url.split("/modules/", 1)[1].split("/", 1)[0]
            return _BcrResponse(200 if name in bcr_hits else 404)
        return _TarballResponse()

    return _get


class TestListNewTags(unittest.TestCase):

    def _fake_run(self, tag_names):
        class _FakeResult:
            stdout = "\n".join(tag_names) + "\n"

        def _run(*args, **kwargs):
            return _FakeResult()
        return _run

    def test_only_returns_tags_newer_than_latest_bootstrapped(self):
        # lyrical/2026-05-22 predates the already-bootstrapped 2026-06-08
        # and was intentionally never bootstrapped -- must not resurface.
        tags = ["lyrical/2026-05-22", "lyrical/2026-06-08", "lyrical/2026-06-23", "rolling/2026-01-21"]
        original_run = subprocess.run
        rosdistro_lib.subprocess.run = self._fake_run(tags)
        try:
            result = rosdistro_lib.list_new_tags("lyrical", {"lyrical.2026-06-08"})
        finally:
            rosdistro_lib.subprocess.run = original_run
        self.assertEqual(result, ["2026-06-23"])

    def test_no_prior_bootstrap_returns_everything(self):
        tags = ["lyrical/2026-05-22", "lyrical/2026-06-08"]
        original_run = subprocess.run
        rosdistro_lib.subprocess.run = self._fake_run(tags)
        try:
            result = rosdistro_lib.list_new_tags("lyrical", set())
        finally:
            rosdistro_lib.subprocess.run = original_run
        self.assertEqual(result, ["2026-05-22", "2026-06-08"])


class TestComputeDefaultStripPrefix(unittest.TestCase):

    def test_replaces_slashes(self):
        self.assertEqual(
            rosdistro_lib.compute_default_strip_prefix("rcutils-release", "release/lyrical/rcutils/7.1.1-3"),
            "rcutils-release-release-lyrical-rcutils-7.1.1-3",
        )

    def test_ros_module_archive_shape(self):
        self.assertEqual(
            rosdistro_lib.compute_default_strip_prefix("rosdistro", "lyrical/2026-06-08"),
            "rosdistro-lyrical-2026-06-08",
        )


class TestResolvePackages(unittest.TestCase):

    def test_expands_multi_package_repo(self):
        distribution = {
            "repositories": {
                "rclcpp": {
                    "release": {
                        "url": "https://github.com/ros2-gbp/rclcpp-release.git",
                        "version": "32.0.0-1",
                        "packages": ["rclcpp", "rclcpp_action"],
                        "tags": {"release": "release/{package}/{version}"},
                    }
                },
            }
        }
        packages = rosdistro_lib.resolve_packages(distribution, "lyrical", "2026-06-08")
        self.assertIn("rclcpp", packages)
        self.assertIn("rclcpp_action", packages)
        self.assertEqual(packages["rclcpp"].version, "32.0.0-1")
        self.assertEqual(packages["rclcpp"].tag, "release/rclcpp/32.0.0-1")
        self.assertEqual(
            packages["rclcpp"].url,
            "https://github.com/ros2-gbp/rclcpp-release/archive/refs/tags/release/rclcpp/32.0.0-1.tar.gz",
        )

    def test_single_package_repo_defaults_name_to_repo_name(self):
        distribution = {
            "repositories": {
                "rcutils": {
                    "release": {
                        "url": "https://github.com/ros2-gbp/rcutils-release.git",
                        "version": "7.1.1-3",
                        "tags": {"release": "release/{package}/{version}"},
                    }
                },
            }
        }
        packages = rosdistro_lib.resolve_packages(distribution, "lyrical", "2026-06-08")
        self.assertIn("rcutils", packages)
        self.assertEqual(packages["rcutils"].version, "7.1.1-3")

    def test_date_versioned_meta_package_gets_distro_date_version(self):
        distribution = {
            "repositories": {
                "ros_core": {
                    "release": {
                        "url": "https://github.com/ros2-gbp/ros_core-release.git",
                        "version": "1.2.3-1",
                        "tags": {"release": "release/{package}/{version}"},
                    }
                },
            }
        }
        packages = rosdistro_lib.resolve_packages(distribution, "lyrical", "2026-06-08")
        self.assertEqual(packages["ros_core"].version, "lyrical.2026-06-08")

    def test_ignored_packages_are_skipped(self):
        distribution = {
            "repositories": {
                "cyclonedds": {
                    "release": {
                        "url": "https://github.com/ros2-gbp/cyclonedds-release.git",
                        "version": "1.0.0",
                        "tags": {"release": "release/{package}/{version}"},
                    }
                },
            }
        }
        packages = rosdistro_lib.resolve_packages(distribution, "lyrical", "2026-06-08")
        self.assertNotIn("cyclonedds", packages)

    def test_extra_packages_always_included(self):
        packages = rosdistro_lib.resolve_packages({"repositories": {}}, "lyrical", "2026-06-08")
        self.assertIn("rosidl_adapter_proto", packages)
        self.assertIn("rosidl_typesupport_protobuf", packages)

    def test_source_only_repo_without_release_is_skipped(self):
        distribution = {
            "repositories": {
                "some_doc_only_repo": {
                    "doc": {"type": "git", "url": "https://github.com/ros2/foo.git", "version": "lyrical"},
                },
            }
        }
        packages = rosdistro_lib.resolve_packages(distribution, "lyrical", "2026-06-08")
        self.assertNotIn("some_doc_only_repo", packages)

    def test_never_released_repo_falls_back_to_upstream_tag(self):
        # Mirrors aruco_markers in the real lyrical/2026-06-08 distribution.yaml:
        # a 'source:' entry, no 'release:' block at all -- never bloom-released
        # into this distro. The repo produces two packages sharing one archive.
        distribution = {
            "repositories": {
                "aruco_markers": {
                    "source": {
                        "type": "git",
                        "url": "https://github.com/namo-robotics/aruco_markers.git",
                        "version": "rolling",
                    },
                },
            }
        }
        original_run = subprocess.run
        original_get = rosdistro_lib.requests.get

        def _fake_run(args, **kwargs):
            class _Result:
                returncode = 0
                stdout = "upstream/0.0.3\nupstream/0.0.4\nsome-other-tag\n"
            assert args[2] == "repos/namo-robotics/aruco_markers-release/tags"
            return _Result()

        tarball = _make_tarball({
            "aruco_markers-release-upstream-0.0.4/package.xml": _package_xml("aruco_markers"),
            "aruco_markers-release-upstream-0.0.4/aruco_markers_msgs/package.xml":
                _package_xml("aruco_markers_msgs"),
        })

        rosdistro_lib.subprocess.run = _fake_run
        rosdistro_lib.requests.get = _fake_get_with_bcr(tarball)
        try:
            packages = rosdistro_lib.resolve_packages(distribution, "lyrical", "2026-06-08")
        finally:
            rosdistro_lib.subprocess.run = original_run
            rosdistro_lib.requests.get = original_get

        self.assertIn("aruco_markers", packages)
        self.assertIn("aruco_markers_msgs", packages)
        self.assertEqual(packages["aruco_markers"].version, "0.0.4")
        self.assertEqual(packages["aruco_markers"].tag, "upstream/0.0.4")
        self.assertEqual(packages["aruco_markers"].repo_owner, "namo-robotics")
        self.assertEqual(packages["aruco_markers"].repo_name, "aruco_markers-release")
        self.assertEqual(
            packages["aruco_markers"].default_strip_prefix,
            "aruco_markers-release-upstream-0.0.4",
        )
        self.assertEqual(
            packages["aruco_markers_msgs"].default_strip_prefix,
            "aruco_markers-release-upstream-0.0.4/aruco_markers_msgs",
        )
        self.assertEqual(packages["aruco_markers"].package_xml_subdir, "")
        self.assertEqual(
            packages["aruco_markers_msgs"].package_xml_subdir, "aruco_markers_msgs"
        )
        self.assertEqual(
            packages["aruco_markers"].url,
            "https://github.com/namo-robotics/aruco_markers-release/archive/refs/tags/upstream/0.0.4.tar.gz",
        )

    def test_release_missing_version_falls_back_and_honors_package_list(self):
        # Mirrors cob_common: a 'release:' block exists (url + packages),
        # but has no 'version' pin yet, so the normal path can't use it.
        # The archive contains a decoy package not in release.packages --
        # it must be filtered out, not silently included.
        distribution = {
            "repositories": {
                "cob_common": {
                    "release": {
                        "url": "https://github.com/ros2-gbp/cob_common-release.git",
                        "packages": ["cob_actions", "cob_msgs"],
                        "tags": {"release": "release/lyrical/{package}/{version}"},
                    },
                    "source": {
                        "type": "git",
                        "url": "https://github.com/4am-robotics/cob_common.git",
                        "version": "rolling",
                    },
                },
            }
        }

        def _fake_run(args, **kwargs):
            class _Result:
                returncode = 0
                stdout = "upstream/2.8.12\n"
            return _Result()

        tarball = _make_tarball({
            "cob_common-release-upstream-2.8.12/cob_actions/package.xml": _package_xml("cob_actions"),
            "cob_common-release-upstream-2.8.12/cob_msgs/package.xml": _package_xml("cob_msgs"),
            "cob_common-release-upstream-2.8.12/cob_decoy/package.xml": _package_xml("cob_decoy"),
        })

        original_run = subprocess.run
        original_get = rosdistro_lib.requests.get
        rosdistro_lib.subprocess.run = _fake_run
        rosdistro_lib.requests.get = _fake_get_with_bcr(tarball)
        try:
            packages = rosdistro_lib.resolve_packages(distribution, "lyrical", "2026-06-08")
        finally:
            rosdistro_lib.subprocess.run = original_run
            rosdistro_lib.requests.get = original_get

        self.assertIn("cob_actions", packages)
        self.assertIn("cob_msgs", packages)
        self.assertNotIn("cob_decoy", packages)

    def test_package_colliding_with_bcr_module_is_not_recovered(self):
        # Mirrors the real ecal bug: its upstream archive bundles a vendored
        # third-party package.xml declaring <name>protobuf</name>, one
        # directory below the wrapper root -- shallow enough to pass the
        # depth filter, so only the BCR-collision guard catches it.
        distribution = {
            "repositories": {
                "ecal": {
                    "source": {
                        "type": "git",
                        "url": "https://github.com/eclipse-ecal/ecal.git",
                        "version": "master",
                    },
                },
            }
        }

        def _fake_run(args, **kwargs):
            class _Result:
                returncode = 0
                stdout = "upstream/5.12.0\n"
            return _Result()

        tarball = _make_tarball({
            "ecal-release-upstream-5.12.0/package.xml": _package_xml("ecal"),
            "ecal-release-upstream-5.12.0/thirdparty/protobuf/package.xml": _package_xml("protobuf"),
        })

        original_run = subprocess.run
        original_get = rosdistro_lib.requests.get
        rosdistro_lib.subprocess.run = _fake_run
        rosdistro_lib.requests.get = _fake_get_with_bcr(tarball, bcr_hits={"protobuf"})
        try:
            packages = rosdistro_lib.resolve_packages(distribution, "lyrical", "2026-06-08")
        finally:
            rosdistro_lib.subprocess.run = original_run
            rosdistro_lib.requests.get = original_get

        self.assertIn("ecal", packages)
        self.assertNotIn("protobuf", packages)

    def test_package_dropped_from_complete_release_list_is_not_recovered(self):
        # Mirrors ros2_controllers: a fully valid release (url + version +
        # packages) that simply doesn't list effort_controllers any more.
        # This is a maintainer decision, not a data gap -- must NOT trigger
        # the fallback at all (the primary path already handles this repo).
        distribution = {
            "repositories": {
                "ros2_controllers": {
                    "release": {
                        "url": "https://github.com/ros2-gbp/ros2_controllers-release.git",
                        "version": "6.7.0-1",
                        "packages": ["joint_state_broadcaster"],
                        "tags": {"release": "release/{package}/{version}"},
                    },
                },
            }
        }
        original_run = subprocess.run
        rosdistro_lib.subprocess.run = lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("fallback must not run for a fully-resolved release")
        )
        try:
            packages = rosdistro_lib.resolve_packages(distribution, "lyrical", "2026-06-08")
        finally:
            rosdistro_lib.subprocess.run = original_run

        self.assertIn("joint_state_broadcaster", packages)
        self.assertNotIn("effort_controllers", packages)

    def test_no_upstream_tag_found_yields_no_packages(self):
        distribution = {
            "repositories": {
                "some_repo": {
                    "source": {"type": "git", "url": "https://github.com/example/some_repo.git", "version": "rolling"},
                },
            }
        }

        def _fake_run(args, **kwargs):
            class _Result:
                returncode = 1
                stdout = ""
            return _Result()

        original_run = subprocess.run
        rosdistro_lib.subprocess.run = _fake_run
        try:
            packages = rosdistro_lib.resolve_packages(distribution, "lyrical", "2026-06-08")
        finally:
            rosdistro_lib.subprocess.run = original_run

        self.assertNotIn("some_repo", packages)


class TestFindBestUpstreamTag(unittest.TestCase):

    def test_prefers_higher_version_and_tries_alt_owner_on_miss(self):
        original_run = subprocess.run

        def _fake_run(args, **kwargs):
            repo_path = args[2]
            class _Result:
                returncode = 0
                stdout = ""
            if repo_path == "repos/primary-owner/some-release/tags":
                return _Result()  # no tags -- forces the alt-owner probe
            if repo_path == "repos/ros2-gbp/some-release/tags":
                result = _Result()
                result.stdout = "upstream/1.0.0\nupstream/1.2.0\nupstream/1.10.0\nnot-a-match\n"
                return result
            raise AssertionError(f"unexpected repo probed: {repo_path}")

        rosdistro_lib.subprocess.run = _fake_run
        try:
            found = rosdistro_lib._find_best_upstream_tag("primary-owner", "some-release", "ros2-gbp")
        finally:
            rosdistro_lib.subprocess.run = original_run

        # 1.10.0 must win over 1.2.0 numerically, not lexicographically.
        self.assertEqual(found, ("ros2-gbp", "some-release", "upstream/1.10.0"))

    def test_returns_none_when_neither_owner_has_a_match(self):
        original_run = subprocess.run
        rosdistro_lib.subprocess.run = lambda *a, **k: type(
            "R", (), {"returncode": 1, "stdout": ""}
        )()
        try:
            found = rosdistro_lib._find_best_upstream_tag("owner", "repo", "ros2-gbp")
        finally:
            rosdistro_lib.subprocess.run = original_run
        self.assertIsNone(found)


class TestDiscoverPackagesInArchive(unittest.TestCase):

    def test_finds_root_and_one_level_nested_packages(self):
        tarball = _make_tarball({
            "repo-tag/package.xml": _package_xml("repo"),
            "repo-tag/sub/package.xml": _package_xml("sub_pkg"),
            "repo-tag/README.md": "not a package.xml",
        })

        class _FakeResponse:
            content = tarball

            def raise_for_status(self):
                pass

        original_get = rosdistro_lib.requests.get
        rosdistro_lib.requests.get = lambda *a, **k: _FakeResponse()
        try:
            discovered = rosdistro_lib.discover_packages_in_archive("unused")
        finally:
            rosdistro_lib.requests.get = original_get

        self.assertEqual(
            discovered,
            {
                "repo": "repo-tag",
                "sub_pkg": "repo-tag/sub",
            },
        )

    def test_ignores_package_xml_nested_two_or_more_levels_deep(self):
        # Mirrors the real eCAL bug: a vendored third-party dependency's
        # own package.xml, buried well below the wrapper root, must not be
        # treated as a real top-level package of the repo being scanned.
        tarball = _make_tarball({
            "repo-tag/package.xml": _package_xml("repo"),
            "repo-tag/thirdparty/protobuf/php/ext/google/protobuf/package.xml":
                _package_xml("protobuf"),
        })

        class _FakeResponse:
            content = tarball

            def raise_for_status(self):
                pass

        original_get = rosdistro_lib.requests.get
        rosdistro_lib.requests.get = lambda *a, **k: _FakeResponse()
        try:
            discovered = rosdistro_lib.discover_packages_in_archive("unused")
        finally:
            rosdistro_lib.requests.get = original_get

        self.assertEqual(discovered, {"repo": "repo-tag"})


class TestBcrModuleExists(unittest.TestCase):

    def test_true_on_200(self):
        class _Response:
            status_code = 200

        original_get = rosdistro_lib.requests.get
        rosdistro_lib.requests.get = lambda *a, **k: _Response()
        try:
            self.assertTrue(rosdistro_lib.bcr_module_exists("protobuf"))
        finally:
            rosdistro_lib.requests.get = original_get

    def test_false_on_404(self):
        class _Response:
            status_code = 404

        original_get = rosdistro_lib.requests.get
        rosdistro_lib.requests.get = lambda *a, **k: _Response()
        try:
            self.assertFalse(rosdistro_lib.bcr_module_exists("some_ros_only_package"))
        finally:
            rosdistro_lib.requests.get = original_get

    def test_false_on_network_error(self):
        import requests as requests_module

        def _raise(*a, **k):
            raise requests_module.exceptions.ConnectionError("boom")

        original_get = rosdistro_lib.requests.get
        rosdistro_lib.requests.get = _raise
        try:
            self.assertFalse(rosdistro_lib.bcr_module_exists("anything"))
        finally:
            rosdistro_lib.requests.get = original_get


class TestFetchPackageXmlDependencies(unittest.TestCase):

    def test_parses_dependency_tags(self):
        pkg_source = rosdistro_lib.PackageSource(
            version="1.0.0", url="unused", default_strip_prefix="unused",
        )

        # Monkeypatch requests.get to avoid a real network call in this test.
        class _FakeResponse:
            text = (
                '<?xml version="1.0"?>'
                '<package format="2">'
                "<name>foo</name>"
                "<buildtool_depend>ament_cmake</buildtool_depend>"
                "<depend>rclcpp</depend>"
                "<build_depend>rcutils</build_depend>"
                "<exec_depend>rcutils</exec_depend>"
                "<test_depend>ament_lint_auto</test_depend>"
                "</package>"
            )

            def raise_for_status(self):
                pass

        original_get = rosdistro_lib.requests.get
        rosdistro_lib.requests.get = lambda *a, **k: _FakeResponse()
        try:
            deps = rosdistro_lib.fetch_package_xml_dependencies(pkg_source)
        finally:
            rosdistro_lib.requests.get = original_get

        self.assertEqual(deps, {"rclcpp", "rcutils", "ament_lint_auto"})

    def test_uses_package_xml_subdir_when_set(self):
        pkg_source = rosdistro_lib.PackageSource(
            version="1.0.0", url="unused", default_strip_prefix="unused",
            repo_owner="namo-robotics", repo_name="aruco_markers-release",
            tag="upstream/0.0.4", package_xml_subdir="aruco_markers_msgs",
        )

        class _FakeResponse:
            text = '<?xml version="1.0"?><package format="2"><name>aruco_markers_msgs</name><depend>std_msgs</depend></package>'

            def raise_for_status(self):
                pass

        requested_urls = []
        original_get = rosdistro_lib.requests.get

        def _fake_get(url, timeout=None):
            requested_urls.append(url)
            return _FakeResponse()

        rosdistro_lib.requests.get = _fake_get
        try:
            deps = rosdistro_lib.fetch_package_xml_dependencies(pkg_source)
        finally:
            rosdistro_lib.requests.get = original_get

        self.assertEqual(deps, {"std_msgs"})
        self.assertEqual(
            requested_urls,
            [
                "https://raw.githubusercontent.com/namo-robotics/aruco_markers-release/"
                "upstream/0.0.4/aruco_markers_msgs/package.xml"
            ],
        )


if __name__ == "__main__":
    unittest.main()

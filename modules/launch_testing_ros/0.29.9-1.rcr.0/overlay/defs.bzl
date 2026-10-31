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

"""Bazel rules for running ROS launch tests with launch_testing_ros."""

load("@launch_testing//:defs.bzl", "launch_test")

def launch_ros_test(name, src, data = [], deps = [], args = [], **kwargs):
    """Define a Bazel test target for a ROS launch test file.

    Args:
        name: Name of the test target (e.g. "test_example.launch").
        src: Path or label of the launch test file.
        data: Runtime data dependencies (typically :ament_index targets).
        deps: Additional Python library dependencies.
        args: Additional arguments passed to launch_test (e.g. "key:=value").
        **kwargs: Additional keyword arguments forwarded to py_test.
    """
    launch_test(
        name = name,
        src = src,
        data = data,
        deps = list(deps) + [
            Label("@launch_ros//:launch_ros"),
            Label("@launch_testing_ros//:launch_testing_ros"),
        ],
        args = args,
        **kwargs
    )

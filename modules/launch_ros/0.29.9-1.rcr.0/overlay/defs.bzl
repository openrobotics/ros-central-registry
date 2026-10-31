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

"""Bazel rules for running ROS launch files with launch_ros."""

load("@launch//:defs.bzl", "launch_binary")

def launch_ros_binary(name, src, data = [], deps = [], args = [], **kwargs):
    """Define a runnable Bazel target for a ROS launch file.

    Args:
        name: Name of the target (e.g. "example.launch").
        src: Path or label of the launch file (.py, .xml, or .yaml).
        data: Runtime data dependencies (typically :ament_index targets).
        deps: Additional Python library dependencies.
        args: Additional arguments passed to the launch runner.
        **kwargs: Additional keyword arguments forwarded to py_binary.
    """
    launch_binary(
        name = name,
        src = src,
        data = data,
        deps = list(deps) + [Label("@launch_ros//:launch_ros")],
        args = args,
        **kwargs
    )

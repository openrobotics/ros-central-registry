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

"""Entry point for launch_test targets."""

import atexit
import os
import shutil
import sys

import launch.logging
from launch_testing.launch_test import main
from rcr_launch_guard import launch_process_guard


def _cleanup_log_symlinks(log_dir: str) -> None:
    """Remove symlinks in ROS_LOG_DIR so Bazel output validation succeeds."""
    if not os.path.isdir(log_dir):
        return
    for root, dirs, files in os.walk(log_dir):
        for name in dirs + files:
            path = os.path.join(root, name)
            if os.path.islink(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass


def _configure_bazel_environment() -> None:
    """Configure environment variables and arguments for Bazel test execution."""
    stdlib_prefixes = (
        os.path.realpath(sys.prefix),
        os.path.realpath(sys.base_prefix),
    )
    os.environ['PYTHONPATH'] = os.pathsep.join(
        p for p in sys.path
        if p and not os.path.realpath(p).startswith(stdlib_prefixes)
        and '/lib/python' not in p.replace('\\', '/')
    )
    py_bin_dir = os.path.dirname(sys.executable)
    if py_bin_dir:
        os.environ['PATH'] = (
            py_bin_dir + os.pathsep + os.environ.get('PATH', '')
        )

    if not os.environ.get('AMENT_PREFIX_PATH'):
        runfiles_dir = os.environ.get('RUNFILES_DIR')
        test_workspace = os.environ.get('TEST_WORKSPACE')
        if runfiles_dir and test_workspace:
            os.environ['AMENT_PREFIX_PATH'] = os.path.join(
                runfiles_dir, test_workspace
            )
        else:
            os.environ['AMENT_PREFIX_PATH'] = os.getcwd()

    # Mirror launch_main.py: put each underlay prefix's bin/ on PATH so that
    # `$(find-exec ...)` / FindExecutable() resolve executables installed to
    # bin/ (e.g. xacro), the same way a sourced ROS install does.
    ament_bin_dirs = [
        os.path.abspath(os.path.join(prefix, 'bin'))
        for prefix in os.environ.get('AMENT_PREFIX_PATH', '').split(os.pathsep)
        if prefix and os.path.isdir(os.path.join(prefix, 'bin'))
    ]
    if ament_bin_dirs:
        os.environ['PATH'] = (
            os.pathsep.join(ament_bin_dirs)
            + os.pathsep
            + os.environ.get('PATH', '')
        )

    if 'TEST_SRCDIR' in os.environ and shutil.which('ros2') is None:
        bin_dir = os.path.join(
            os.environ.get('TEST_TMPDIR', '/tmp'), 'ros2_bin'
        )
        os.makedirs(bin_dir, exist_ok=True)
        ros2_bin = os.path.join(bin_dir, 'ros2')
        with open(ros2_bin, 'w') as f:
            f.write(
                '#!/bin/sh\n'
                f'exec "{sys.executable}" -c '
                '"import sys; from ros2cli.cli import main; sys.exit(main())" "$@"\n'
            )
        os.chmod(ros2_bin, 0o755)
        os.environ['PATH'] = (
            bin_dir + os.pathsep + os.environ.get('PATH', '')
        )

    launch.logging._renew_latest_log_dir = lambda *, log_dir: True
    base_tmp = (
        os.environ.get('TEST_TMPDIR') or
        os.environ.get('TEST_UNDECLARED_OUTPUTS_DIR')
    )
    if base_tmp and not os.environ.get('ROS_LOG_DIR'):
        log_dir = os.path.join(base_tmp, 'ros_log')
        os.makedirs(log_dir, exist_ok=True)
        os.environ['ROS_LOG_DIR'] = log_dir
        atexit.register(_cleanup_log_symlinks, log_dir)

    xml_output_file = os.environ.get('XML_OUTPUT_FILE')
    if (
        xml_output_file and
        '--junit-xml' not in sys.argv and
        not any(arg.startswith('--junit-xml=') for arg in sys.argv)
    ):
        sys.argv.extend(['--junit-xml', xml_output_file])


if __name__ == '__main__':
    _configure_bazel_environment()
    # Under `bazel test` the guard kills (rather than aborts on) processes a
    # previous, e.g. timed-out, attempt left behind; see rcr_launch_guard.
    with launch_process_guard(target=os.environ.get('TEST_TARGET')):
        main()

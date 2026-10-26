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

"""Entry point for launch_binary targets."""

import argparse
import atexit
from collections import OrderedDict
import os
import sys
from typing import List
from typing import Text
from typing import Tuple

from launch import LaunchDescription
from launch import LaunchService
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
import launch.logging


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


def _parse_launch_arguments(
    launch_arguments: List[Text],
) -> List[Tuple[Text, Text]]:
    """Parse command-line launch arguments in '<name>:=<value>' format."""
    parsed_launch_arguments: OrderedDict[Text, Text] = OrderedDict()
    for argument in launch_arguments:
        count = argument.count(':=')
        if (
            count == 0 or
            argument.startswith(':=') or
            (count == 1 and argument.endswith(':='))
        ):
            raise RuntimeError(
                f"malformed launch argument '{argument}', "
                "expected format '<name>:=<value>'"
            )
        name, value = argument.split(':=', maxsplit=1)
        parsed_launch_arguments[name] = value
    return list(parsed_launch_arguments.items())


def main(argv: List[Text] = sys.argv[1:]) -> int:
    """Run a launch file using LaunchService."""
    parser = argparse.ArgumentParser(
        description='Run a ROS launch file.'
    )
    parser.add_argument(
        'launch_file',
        help='Path to the launch file.',
    )
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        default=False,
        help='Put the launch service in debug mode.',
    )
    parser.add_argument(
        '-n', '--noninteractive',
        action='store_true',
        default=not sys.stdin.isatty(),
        help='Run the launch service non-interactively.',
    )
    parser.add_argument(
        'launch_arguments',
        nargs='*',
        help="Arguments in '<name>:=<value>' format.",
    )
    args = parser.parse_args(argv)

    if not os.path.isfile(args.launch_file):
        parser.error(f"Launch file '{args.launch_file}' does not exist")

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

    ament_bin_dirs = [
        os.path.join(prefix, 'bin')
        for prefix in os.environ.get('AMENT_PREFIX_PATH', '').split(os.pathsep)
        if prefix and os.path.isdir(os.path.join(prefix, 'bin'))
    ]
    if ament_bin_dirs:
        os.environ['PATH'] = (
            os.pathsep.join(ament_bin_dirs)
            + os.pathsep
            + os.environ.get('PATH', '')
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

    parsed_launch_arguments = _parse_launch_arguments(args.launch_arguments)
    launch_description = LaunchDescription([
        IncludeLaunchDescription(
            AnyLaunchDescriptionSource(os.path.abspath(args.launch_file)),
            launch_arguments=parsed_launch_arguments,
        ),
    ])
    launch_service = LaunchService(
        argv=args.launch_arguments,
        noninteractive=args.noninteractive,
        debug=args.debug,
    )
    launch_service.include_launch_description(launch_description)
    return launch_service.run()


if __name__ == '__main__':
    sys.exit(main())

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
"""Bazel equivalent of libmavconn's cmake/Modules/em_expand.cmake.

Usage: em_expand.py OUTPUT TEMPLATE DIALECT [DIALECT ...]
"""

import sys

import em


def main():
    out, template, dialects = sys.argv[1], sys.argv[2], sys.argv[3:]
    em.invoke([
        "-D", "MAVLINK_V20_DIALECTS=%r" % (dialects,),
        "-o", out,
        template,
    ])


if __name__ == "__main__":
    main()

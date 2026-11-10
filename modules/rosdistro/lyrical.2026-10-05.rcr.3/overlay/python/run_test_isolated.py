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

"""Run a test under a ROS_DOMAIN_ID that no other concurrently running test is using.

Intended as a Bazel ``--run_under`` wrapper (see the ``test`` options of the
generated ``.bazelrc``). Bazel's sandboxes on macOS (darwin-sandbox) and on
Linux hosts without user namespaces (processwrapper-sandbox) share the host
loopback interface, so two tests running at the same time on the default
ROS_DOMAIN_ID would discover each other's nodes. Giving every test its own
domain keeps them apart without having to run them one at a time.

The lease protocol is the one used by the ``domain_coordinator`` ROS package
(ament_cmake_ros): a domain ID in 1..100 is considered taken while any process
holds a TCP socket bound to port ``32768 + domain_id``. Re-implementing those
few lines here, rather than depending on ``domain_coordinator``, avoids a
dependency cycle (that package depends on ``rosdistro``) while staying
interoperable with tools that still use it in-process (e.g. ``ros2 test``).

An explicitly set ROS_DOMAIN_ID in the test's environment is left alone.
"""

import os
import random
import socket
import sys

# Keep in sync with domain_coordinator/impl.py.
PORT_BASE = 32768
NUM_DOMAINS = 100


def lease_domain_id():
    """Return (socket, domain_id) with the socket holding the lease for domain_id."""
    start = random.randrange(NUM_DOMAINS)
    for offset in range(NUM_DOMAINS):
        domain_id = (start + offset) % NUM_DOMAINS + 1
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("", PORT_BASE + domain_id))
        except OSError:
            sock.close()
            continue
        return sock, domain_id
    raise RuntimeError("run_test_isolated: no free ROS_DOMAIN_ID in 1..%d" % NUM_DOMAINS)


def main(argv):
    if not argv:
        print("usage: run_test_isolated <command> [args...]", file=sys.stderr)
        return 2
    if "ROS_DOMAIN_ID" not in os.environ:
        sock, domain_id = lease_domain_id()
        # The test process inherits the bound socket and so keeps the lease
        # for exactly as long as it (and anything it spawns) lives.
        sock.set_inheritable(True)
        os.environ["ROS_DOMAIN_ID"] = str(domain_id)
    print("run_test_isolated: ROS_DOMAIN_ID=%s" % os.environ["ROS_DOMAIN_ID"], file=sys.stderr, flush=True)
    os.execvp(argv[0], argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


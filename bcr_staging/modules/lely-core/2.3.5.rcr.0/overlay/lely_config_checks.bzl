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

"""Autoconf-style checks used to generate lely-core's config.h.

Mirrors the probes in upstream configure.ac for the configuration used by
ros2_canopen's lely_core_libraries (`--disable-cython --disable-doc
--disable-tests --disable-static --disable-diag`), evaluated against Bazel's
configured cc_toolchain. Standard C header checks and AC_USE_SYSTEM_EXTENSIONS
come from the macro targets listed in the autoconf_hdr deps.
"""

load("@rules_cc_autoconf//autoconf:checks.bzl", "checks")

LELY_CONFIG_CHECKS = [
    # AC_INIT([Lely core libraries], [2.3.5], [], [lely-core])
    checks.AC_DEFINE("PACKAGE", '"lely-core"'),
    checks.AC_DEFINE("PACKAGE_NAME", '"Lely core libraries"'),
    checks.AC_DEFINE("PACKAGE_TARNAME", '"lely-core"'),
    checks.AC_DEFINE("PACKAGE_VERSION", '"2.3.5"'),
    checks.AC_DEFINE("PACKAGE_STRING", '"Lely core libraries 2.3.5"'),
    checks.AC_DEFINE("PACKAGE_BUGREPORT", '""'),
    checks.AC_DEFINE("PACKAGE_URL", '""'),
    checks.AC_DEFINE("VERSION", '"2.3.5"'),

    # AX_CXX_COMPILE_STDCXX([11], [ext], [mandatory])
    checks.AC_DEFINE("HAVE_CXX11", "1"),

    # LT_INIT: AC_CHECK_HEADERS([dlfcn.h]) and the libtool objdir.
    checks.AC_CHECK_HEADER("dlfcn.h", define = "HAVE_DLFCN_H"),
    checks.AC_DEFINE("LT_OBJDIR", '".libs/"'),

    # AX_PTHREAD: PTHREAD_PRIO_INHERIT availability.
    checks.AC_CHECK_DECL(
        "PTHREAD_PRIO_INHERIT",
        define = "HAVE_PTHREAD_PRIO_INHERIT",
        includes = ["#include <pthread.h>"],
    ),

    # --disable-diag
    checks.AC_DEFINE("LELY_NO_DIAG", "1"),

    # AC_CHECK_HEADER([valgrind/valgrind.h], [AC_DEFINE([LELY_HAVE_VALGRIND])])
    checks.AC_CHECK_HEADER("valgrind/valgrind.h", define = "LELY_HAVE_VALGRIND"),

    # SocketCAN: AC_CHECK_HEADERS([linux/can.h], [AC_DEFINE([LELY_HAVE_SOCKET_CAN])])
    checks.AC_CHECK_HEADER("linux/can.h", define = "HAVE_LINUX_CAN_H"),
    checks.AC_CHECK_HEADER("linux/can.h", name = "lely_have_socket_can", define = "LELY_HAVE_SOCKET_CAN"),
    checks.AC_CHECK_HEADER("linux/can/error.h", define = "HAVE_LINUX_CAN_ERROR_H"),
    checks.AC_CHECK_HEADER("linux/can/netlink.h", define = "HAVE_LINUX_CAN_NETLINK_H"),
    checks.AC_CHECK_HEADER("linux/can/raw.h", define = "HAVE_LINUX_CAN_RAW_H"),
    checks.AC_CHECK_DECL(
        "CAN_RAW_FD_FRAMES",
        define = "HAVE_CAN_RAW_FD_FRAMES",
        includes = ["#include <linux/can/raw.h>"],
    ),
    checks.AC_CHECK_HEADER("linux/rtnetlink.h", define = "HAVE_LINUX_RTNETLINK_H"),
    checks.AC_CHECK_HEADER("bluetooth/bluetooth.h", define = "HAVE_BLUETOOTH_BLUETOOTH_H"),
    checks.AC_CHECK_HEADER("bluetooth/rfcomm.h", define = "HAVE_BLUETOOTH_RFCOMM_H"),
    checks.AC_CHECK_HEADER("ifaddrs.h", define = "HAVE_IFADDRS_H"),
    checks.AC_CHECK_HEADER("sys/epoll.h", define = "HAVE_SYS_EPOLL_H"),
    checks.AC_CHECK_HEADER("sys/ioctl.h", define = "HAVE_SYS_IOCTL_H"),

    # LELY_HAVE_IXXAT / LELY_HAVE_VCI / HAVE_CANTYPE_H are Windows-only probes
    # (IXXAT VCI SDK) and stay undefined on the platforms we build for.
]

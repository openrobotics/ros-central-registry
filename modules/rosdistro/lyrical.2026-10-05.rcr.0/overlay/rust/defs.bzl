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
"""Rust rules and providers for ROS packages.

rules_rs is a redistribution of rules_rust: the actual rules and providers
live in the patched @rules_rust repository that rules_rs provisions via a
module extension (see rosdistro's MODULE.bazel). Only rosdistro brings that
repository into scope; every other module loads what it needs from here, the
same way third-party C++ deps are centralized under @rosdistro//cc.
"""

load("@rules_rs//rs:rust_binary.bzl", _rust_binary = "rust_binary")
load("@rules_rs//rs:rust_library.bzl", _rust_library = "rust_library")
load("@rules_rs//rs:rust_test.bzl", _rust_test = "rust_test")
load("@rules_rust//rust:rust_common.bzl", _CrateInfo = "CrateInfo")

CrateInfo = _CrateInfo

rust_binary = _rust_binary

rust_library = _rust_library

rust_test = _rust_test

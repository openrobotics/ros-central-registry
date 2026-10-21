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

load("@rosdistro//cc:defs.bzl", "collect_transitive_dynamic_deps")
load("@rules_cc//cc:defs.bzl", "cc_library", "cc_shared_library")

def class_loader_plugin(name, dynamic_deps = [], **kwargs):
    cc_library(
        name = "{0}_library".format(name),
        alwayslink = True,
        **kwargs
    )
    collect_transitive_dynamic_deps(
        name = "{0}_transitive_dynamic_deps".format(name),
        dynamic_deps = dynamic_deps,
    )
    cc_shared_library(
        name = name,
        exports_filter = ["{0}_library".format(name)],
        deps = ["{0}_library".format(name)],
        dynamic_deps = ["{0}_transitive_dynamic_deps".format(name)],
    )

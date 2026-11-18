# Copyright 2025 Open Source Robotics Foundation, Inc.
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

RosPyBindingsInfo = provider(
    "Encapsulates Python modules generated for an underlying ROS message.",
    fields = [
        "cc_info",  # CcInfo: static archive of the extension module (+ what it links against)
        "static_library",  # LibraryToLink: static archive of the extension module, or None
        "module_name",  # str: file name of the extension module (<pkg>__<type>__<name>_s__rosidl_typesupport_c.so)
        "module_package",  # str: package path of the interface target (where the module file lives)
        "dep_labels",  # list of Labels: interfaces whose extension modules this one calls into
        "transitive_sources",  # generated .py interface code
        "imports",  # import path for generated code
        "sources",  # generated C sources of this interface's bindings (_foo_s.c, entry point)
    ],
)

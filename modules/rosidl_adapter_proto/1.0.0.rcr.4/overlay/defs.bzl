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

load(
    ":aspects.bzl",
    _rosidl_adapter_proto_aspect = "rosidl_adapter_proto_aspect",
)
load(
    ":tools.bzl",
    _merge_proto_infos = "merge_proto_infos",
)
load(
    ":types.bzl",
    _RosProtoInfo = "RosProtoInfo",
)

# Provider returned by the aspect containing protobuf info.
RosProtoInfo = _RosProtoInfo

# Aspect to collect RosProtoInfo across a graph.
rosidl_adapter_proto_aspect = _rosidl_adapter_proto_aspect

# Reusable tooling for merging ProtoInfos.
merge_proto_infos = _merge_proto_infos

// Copyright 2026 Open Source Robotics Foundation, Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#ifndef RCR_BAZEL_TEST_HELPER_HPP_
#define RCR_BAZEL_TEST_HELPER_HPP_

#ifdef __cplusplus
#include <string>

extern "C" const char * rcr_rlocation(const char * path, const char * source_repo);

namespace rcr_test_helper
{

inline const char * rlocation(const char * path, const char * source_repo = "")
{
  return ::rcr_rlocation(path, source_repo);
}

inline std::string rlocation_str(const char * path, const char * source_repo = "")
{
  return std::string(::rcr_rlocation(path, source_repo));
}

}  // namespace rcr_test_helper

#ifndef RCR_CURRENT_REPOSITORY
#ifdef BAZEL_CURRENT_REPOSITORY
#define RCR_CURRENT_REPOSITORY BAZEL_CURRENT_REPOSITORY
#else
#define RCR_CURRENT_REPOSITORY ""
#endif
#endif

#define RCR_RLOCATION(path) (::rcr_rlocation((path), RCR_CURRENT_REPOSITORY))
#define RCR_RLOCATION_STR(path) (::rcr_test_helper::rlocation_str((path), RCR_CURRENT_REPOSITORY))
#endif  // __cplusplus

#endif  // RCR_BAZEL_TEST_HELPER_HPP_


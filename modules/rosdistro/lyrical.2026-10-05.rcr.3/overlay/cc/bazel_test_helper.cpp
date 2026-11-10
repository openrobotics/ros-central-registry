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

#include "bazel_test_helper.hpp"

#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>

#if defined(_WIN32)
#include <stdlib.h>
#include <windows.h>
#define setenv(name, val, overwrite) _putenv_s(name, val)
#elif defined(__APPLE__)
#include <limits.h>
#include <mach-o/dyld.h>
#include <unistd.h>
#else
#include <limits.h>
#include <unistd.h>
#endif

#include "rules_cc/cc/runfiles/runfiles.h"

namespace
{

using rules_cc::cc::runfiles::Runfiles;

std::string get_executable_path()
{
#if defined(_WIN32)
  char result[MAX_PATH + 1] = {'\0'};
  auto path_len = GetModuleFileNameA(NULL, result, MAX_PATH);
#elif defined(__APPLE__)
  char result[PATH_MAX + 1] = {'\0'};
  uint32_t path_len = PATH_MAX;
  if (_NSGetExecutablePath(result, &path_len) != 0) {
    return "ignore-argv[0]";
  }
  path_len = static_cast<uint32_t>(std::string(result).length());
#else
  char result[PATH_MAX + 1] = {'\0'};
  ssize_t path_len = readlink("/proc/self/exe", result, PATH_MAX);
#endif
  if (path_len > 0) {
    return std::string(result, static_cast<size_t>(path_len));
  }
  return "ignore-argv[0]";
}

int initialize_test_environment()
{
  const char * test_tmpdir = std::getenv("TEST_TMPDIR");
  if (test_tmpdir) {
    setenv("ROS_HOME", test_tmpdir, 1);
    setenv("TMPDIR", test_tmpdir, 1);
    setenv("HOME", test_tmpdir, 1);
  }
  return 0;
}

// Global static initializer to ensure environment setup runs before main()
int dummy = initialize_test_environment();

}  // namespace

extern "C" const char * rcr_rlocation(const char * path, const char * source_repo)
{
  if (path == nullptr || path[0] == '\0') {
    return "";
  }
  const std::string raw_path(path);
  const std::string src_repo(source_repo ? source_repo : "");
  const std::string cache_key = src_repo + "|" + raw_path;

  static std::mutex mutex;
  static std::unordered_map<std::string, std::string> cache;
  static std::unique_ptr<Runfiles> runfiles;
  static bool runfiles_initialized = false;

  std::lock_guard<std::mutex> lock(mutex);
  auto it = cache.find(cache_key);
  if (it != cache.end()) {
    return it->second.c_str();
  }

  if (!runfiles_initialized) {
    runfiles_initialized = true;
    std::string error;
    const char * test_srcdir = std::getenv("TEST_SRCDIR");
    const char * manifest_file = std::getenv("RUNFILES_MANIFEST_FILE");
    if ((test_srcdir && test_srcdir[0] != '\0') || (manifest_file && manifest_file[0] != '\0')) {
      runfiles.reset(Runfiles::CreateForTest(&error));
    }
    if (!runfiles) {
      runfiles.reset(Runfiles::Create(get_executable_path(), &error));
    }
  }

  const bool had_trailing_slash = raw_path.size() > 1 && raw_path.back() == '/';
  std::string norm_path = std::filesystem::path(raw_path).lexically_normal().generic_string();
  while (norm_path.size() > 1 && (norm_path.back() == '/' || norm_path.back() == '.')) {
    if (norm_path.size() >= 2 && norm_path.substr(norm_path.size() - 2) == "/.") {
      norm_path.resize(norm_path.size() - 2);
    } else if (norm_path.back() == '/') {
      norm_path.pop_back();
    } else {
      break;
    }
  }

  std::string resolved;
  if (runfiles) {
    resolved = runfiles->Rlocation(norm_path, src_repo);
    std::error_code ec;
    if (resolved.empty() || !std::filesystem::exists(resolved, ec)) {
      const auto slash = norm_path.find('/');
      if (slash != std::string::npos) {
        const std::string repo = norm_path.substr(0, slash);
        const std::string rest = norm_path.substr(slash);
        for (const std::string & candidate_rloc : {repo + "+" + rest, "_main" + rest}) {
          std::string candidate = runfiles->Rlocation(candidate_rloc, "");
          if (!candidate.empty() && std::filesystem::exists(candidate, ec)) {
            resolved = std::move(candidate);
            break;
          }
        }
      }
    }
  }
  if (resolved.empty()) {
    resolved = norm_path;
  }
  if (had_trailing_slash && !resolved.empty() && resolved.back() != '/') {
    resolved.push_back('/');
  }

  auto [inserted_it, _] = cache.emplace(cache_key, std::move(resolved));
  return inserted_it->second.c_str();
}

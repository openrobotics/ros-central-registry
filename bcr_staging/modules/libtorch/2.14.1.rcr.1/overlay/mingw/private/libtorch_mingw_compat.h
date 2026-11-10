// Force-included (-include) into every source file of @libtorch's libraries
// on Windows, for upstream code that is only built with MSVC on Windows and
// otherwise assumes POSIX:
//
// - c10/util/tempfile.cpp uses _SH_DENYNO and _S_IREAD/_S_IWRITE, which the
//   MSVC headers it includes declare transitively, but MinGW-w64's do not.
// - c10/util/env.cpp only takes its putenv() path under _MSC_VER, so MinGW-w64
//   builds call the POSIX setenv()/unsetenv(), which its C runtime does not
//   declare. Provide them on top of _putenv_s().
// - torch/csrc/jit/frontend/strtod.cpp uses locale_t, newlocale() and
//   strtod_l() outside _MSC_VER: map them to the C runtime's _locale_t,
//   _create_locale() and _strtod_l(), as its _MSC_VER branch does.
// - torch/csrc/jit/codegen/fuser/cpu/temp_file.h uses mkstemps() outside
//   _MSC_VER.
// - aten/src/ATen/cpu/vec/vec128/vec128_uint_aarch64.h (windows_arm64) uses
//   the glibc/BSD `uint` typedef from <sys/types.h>.
#pragma once

#if defined(__MINGW32__) && defined(__cplusplus)
#include <errno.h>
#include <fcntl.h>
#include <io.h>
#include <locale.h>
#include <share.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#include <random>

typedef unsigned int uint;

static inline int setenv(const char* name, const char* value, int overwrite) {
  if (!overwrite && getenv(name) != nullptr) {
    return 0;
  }
  return _putenv_s(name, value);
}

// On Windows an assignment with an empty value removes the variable.
static inline int unsetenv(const char* name) {
  return _putenv_s(name, "");
}

typedef _locale_t locale_t;
#ifndef LC_ALL_MASK
#define LC_ALL_MASK 0
#endif

// Only the "C" locale for all categories is used, so the mask is not needed.
static inline locale_t newlocale(int /*mask*/, const char* name, locale_t /*base*/) {
  return _create_locale(LC_ALL, name);
}

static inline double strtod_l(const char* nptr, char** endptr, locale_t loc) {
  return _strtod_l(nptr, endptr, loc);
}

// Replaces the six X's before the last `suffix_len` characters of `tmpl` with
// random characters, and creates that file exclusively.
static inline int mkstemps(char* tmpl, int suffix_len) {
  static const char kChars[] =
      "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  const size_t length = strlen(tmpl);
  if (suffix_len < 0 || length < static_cast<size_t>(suffix_len) + 6) {
    errno = EINVAL;
    return -1;
  }
  char* x = tmpl + length - suffix_len - 6;
  if (strncmp(x, "XXXXXX", 6) != 0) {
    errno = EINVAL;
    return -1;
  }
  std::random_device device;
  std::uniform_int_distribution<int> pick(0, sizeof(kChars) - 2);
  for (int attempt = 0; attempt < 100; ++attempt) {
    for (int i = 0; i < 6; ++i) {
      x[i] = kChars[pick(device)];
    }
    const int fd = _sopen(
        tmpl, _O_RDWR | _O_CREAT | _O_EXCL | _O_BINARY, _SH_DENYNO,
        _S_IREAD | _S_IWRITE);
    if (fd >= 0 || errno != EEXIST) {
      return fd;
    }
  }
  errno = EEXIST;
  return -1;
}
#endif

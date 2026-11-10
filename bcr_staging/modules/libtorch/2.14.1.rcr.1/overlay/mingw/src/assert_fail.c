// glibc's __assert_fail() for MinGW-w64 targets (see ../include/assert.h).
#include <assert.h>
#include <stdlib.h>

void __assert_fail(
    const char* assertion,
    const char* file,
    unsigned int line,
    const char* function) {
  (void)function;
  _assert(assertion, file, line);
  abort();
}

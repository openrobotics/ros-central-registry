// MinGW-w64's <assert.h>, plus the glibc function __assert_fail(), which
// upstream's CUDA_KERNEL_ASSERT (torch/headeronly/macros/Macros.h) calls on
// every compiler but MSVC, and only declares itself in NDEBUG builds. It is
// defined in ../src/assert_fail.c on top of MinGW-w64's _assert().
//
// Like the C library's <assert.h>, this has no include guard: it may be
// included again with NDEBUG changed.
#include_next <assert.h>

#if defined(__MINGW32__) && !defined(C10_MINGW_ASSERT_FAIL_DECLARED)
#define C10_MINGW_ASSERT_FAIL_DECLARED
#ifdef __cplusplus
extern "C" {
#endif
void __assert_fail(
    const char* assertion,
    const char* file,
    unsigned int line,
    const char* function)
#ifdef __cplusplus
    noexcept
#endif
    __attribute__((__noreturn__));
#ifdef __cplusplus
}
#endif
#endif

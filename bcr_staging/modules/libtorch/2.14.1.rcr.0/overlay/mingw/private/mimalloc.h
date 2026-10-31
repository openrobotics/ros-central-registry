// MinGW-w64 stand-in for the two mimalloc functions that c10's CPU allocator
// calls (c10/core/impl/alloc_cpu.cpp) when USE_MIMALLOC is defined, which
// upstream does on Windows.
//
// Without USE_MIMALLOC, a non-MSVC Windows build would take the POSIX path:
// posix_memalign(), which MinGW-w64 lacks, paired with free(). The BCR
// mimalloc module cannot stand in either: it only exposes mimalloc as a malloc
// override (its static library is private, and its DLL flavor does not link
// with MinGW-w64). So, like upstream's MSVC path, allocate with
// _aligned_malloc() and release with the matching _aligned_free().
#pragma once

#include <malloc.h>
#include <stddef.h>

static inline void* mi_malloc_aligned(size_t size, size_t alignment) {
  return _aligned_malloc(size, alignment);
}

static inline void mi_free(void* p) {
  _aligned_free(p);
}

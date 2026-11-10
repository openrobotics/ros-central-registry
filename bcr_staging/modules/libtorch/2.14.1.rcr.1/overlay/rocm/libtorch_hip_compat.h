// Force-included into the ROCm backend's sources (c10_hip, torch_hip): what
// upstream's ROCm build gets from libstdc++, but @llvm's libc++ does not.
#pragma once

// libc++'s configuration first: with a non-HIP compiler, HIP's
// host_defines.h defines __noinline__ as nothing, which breaks libc++'s
// __has_attribute(__noinline__) in a libc++ header included after it.
#include <cstddef>

#if defined(__HIP__)
// HIP's __device__ memcpy() and memset(), in namespace std too: Clang's HIP
// wrapper includes libc++'s <cstring> (through <algorithm>) before them, so
// std::memcpy() (e.g. in torch/headeronly/util/Half.h) is host-only otherwise.
#include <hip/hip_runtime.h>

#include <cstring>

namespace std {
using ::memcpy;
using ::memset;
}  // namespace std
#endif

// MinGW-w64 ships its Windows SDK headers in lowercase (windows.h), while
// upstream PyTorch includes some of them with MSVC's spelling. On
// case-sensitive filesystems (cross-compiling from Linux or macOS) those
// includes fail, so this shim forwards to the real header. #include_next also
// works on case-insensitive hosts, where this file shadows windows.h itself.
#include_next <windows.h>

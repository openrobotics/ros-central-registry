/*
 * Minimal stand-in for MoltenVK's <MoltenVK/mvk_vulkan.h>, written for this
 * overlay (no MoltenVK code is copied). On macOS, upstream's header
 * (MoltenVK/MoltenVK/API/mvk_vulkan.h) defines VK_USE_PLATFORM_METAL_EXT and
 * VK_USE_PLATFORM_MACOS_MVK and includes <vulkan/vulkan.h>; this does the same.
 *
 * Qt's cocoa QPA plugin includes this header when QT_FEATURE_vulkan is on.
 * MoltenVK itself is not linked: Qt dlopen()s the Vulkan loader at runtime,
 * so all the plugin needs is the Khronos headers with the Apple surface
 * platforms enabled (VK_MVK_macos_surface and VK_EXT_metal_surface).
 */

#ifndef QT_BAZEL_MVK_VULKAN_H
#define QT_BAZEL_MVK_VULKAN_H

#ifndef VK_USE_PLATFORM_MACOS_MVK
#define VK_USE_PLATFORM_MACOS_MVK 1
#endif
#ifndef VK_USE_PLATFORM_METAL_EXT
#define VK_USE_PLATFORM_METAL_EXT 1
#endif

#include <vulkan/vulkan.h>

#endif  // QT_BAZEL_MVK_VULKAN_H

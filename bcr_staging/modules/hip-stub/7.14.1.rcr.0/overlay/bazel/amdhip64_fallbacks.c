// What libamdhip64's shim does without a ROCm installation (see gen_shim.py),
// for the functions where returning hipErrorNoDevice is not enough: they must
// report zero devices, return a valid string, or register device code at
// static initialization without failing.
#include <stddef.h>

#define HIP_SUCCESS 0
#define HIP_ERROR_NO_DEVICE 100

int shim_fallback_hipGetDeviceCount(int* count) {
  if (count) *count = 0;
  return HIP_ERROR_NO_DEVICE;
}

int shim_fallback_hipDriverGetVersion(int* version) {
  if (version) *version = 0;
  return HIP_SUCCESS;
}

int shim_fallback_hipRuntimeGetVersion(int* version) {
  if (version) *version = 0;
  return HIP_ERROR_NO_DEVICE;
}

const char* shim_fallback_hipGetErrorName(int error) {
  return error == HIP_SUCCESS ? "hipSuccess" : "hipErrorNoDevice";
}

const char* shim_fallback_hipGetErrorString(int error) {
  return error == HIP_SUCCESS ? "no error" : "no ROCm-capable device is detected";
}

const char* shim_fallback_hipApiName(unsigned id) {
  (void)id;
  return "unknown";
}

// Device code registration (emitted by Clang into every HIP translation unit
// and run at static initialization): a non-null handle, and no-ops.
static void* shim_fat_binary_handle;

void** shim_fallback___hipRegisterFatBinary(const void* data) {
  (void)data;
  return &shim_fat_binary_handle;
}

void shim_fallback___hipUnregisterFatBinary(void** handle) { (void)handle; }

void shim_fallback___hipRegisterFunction(void) {}

void shim_fallback___hipRegisterVar(void) {}

void shim_fallback___hipRegisterManagedVar(void) {}

void shim_fallback___hipRegisterSurface(void) {}

void shim_fallback___hipRegisterTexture(void) {}

// What libhiprtc's shim does without a ROCm installation (see gen_shim.py),
// for the functions where returning an error code is not enough.

const char* shim_fallback_hiprtcGetErrorString(int result) {
  return result == 0 ? "HIPRTC_SUCCESS" : "HIPRTC_ERROR_INTERNAL_ERROR";
}

int shim_fallback_hiprtcVersion(int* major, int* minor) {
  if (major) *major = 0;
  if (minor) *minor = 0;
  return 11;  // HIPRTC_ERROR_INTERNAL_ERROR
}

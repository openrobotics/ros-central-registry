# Places the CUDA (.nv_fatbin) and HIP (.hip_fatbin) device code sections
# after .bss instead of in the main read-only segment before .text.
#
# By default, ld.lld groups allocatable read-only PROGBITS sections between
# .rodata and .text. With all ATen GPU kernels linked in, .nv_fatbin exceeds
# 2 GiB and pushes .text out of reach of x86_64's signed 32-bit PC-relative
# jump-table relocations (R_X86_64_PC32) in .rodata. Only .nvFatBinSegment
# and .hipFatBinSegment (in .data) reference the fatbin sections, and they
# use 64-bit pointer relocations (R_X86_64_64 / R_AARCH64_ABS64).
SECTIONS {
  .nv_fatbin : { *(.nv_fatbin .nv_fatbin.*) }
  .hip_fatbin : { *(.hip_fatbin .hip_fatbin.*) }
}
INSERT AFTER .bss;

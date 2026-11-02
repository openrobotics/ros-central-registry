/* Entry point of sleef's code generators (mkrename, mkdisp, mkalias) in the
 * Bazel build: `<tool> <output file> [arguments...]` runs the generator's
 * main(), renamed to sleef_tool_main, with its standard output redirected to
 * <output file>. Upstream's CMake build redirects with the shell instead, which
 * would need bash on Windows hosts. */
#include <stdio.h>

int sleef_tool_main(int argc, char **argv);

int main(int argc, char **argv) {
  if (argc < 2) {
    fprintf(stderr, "usage: %s <output file> [arguments...]\n", argv[0]);
    return 2;
  }
  if (freopen(argv[1], "w", stdout) == NULL) {
    perror(argv[1]);
    return 1;
  }
  argv[1] = argv[0];
  return sleef_tool_main(argc - 1, argv + 1);
}

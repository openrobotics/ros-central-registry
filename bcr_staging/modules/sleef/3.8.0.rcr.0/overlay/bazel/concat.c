/* `concat <output file> <input files...>`: concatenates files, like the
 * sleef_concat_files() of upstream's CMake build, without a shell. */
#include <stdio.h>

int main(int argc, char **argv) {
  if (argc < 2) {
    fprintf(stderr, "usage: %s <output file> <input files...>\n", argv[0]);
    return 2;
  }
  FILE *out = fopen(argv[1], "wb");
  if (out == NULL) {
    perror(argv[1]);
    return 1;
  }
  char buffer[65536];
  for (int i = 2; i < argc; ++i) {
    FILE *in = fopen(argv[i], "rb");
    if (in == NULL) {
      perror(argv[i]);
      return 1;
    }
    size_t n;
    while ((n = fread(buffer, 1, sizeof(buffer), in)) > 0) {
      if (fwrite(buffer, 1, n, out) != n) {
        perror(argv[1]);
        return 1;
      }
    }
    fclose(in);
  }
  return fclose(out) == 0 ? 0 : 1;
}

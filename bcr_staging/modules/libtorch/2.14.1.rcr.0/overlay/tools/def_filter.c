// Removes the C++ standard library's symbols from the EXPORTS of a DEF file.
//
// Usage: def_filter <input.def> <output.def>
//
// A DLL's objects also define (as COMDATs) the inline functions, vtables and
// typeinfo of the std:: types they use. Every binary links its own static
// libc++, so exporting those from the DLL makes lld fail with
// "<symbol> was replaced" when a binary both imports one and links libc++'s
// definition. Only entities in namespace std are dropped; functions of the
// DLL that merely take std:: types as arguments are kept.

#include <ctype.h>
#include <stdio.h>
#include <string.h>

static int starts_with(const char* s, const char* prefix) {
  return strncmp(s, prefix, strlen(prefix)) == 0;
}

// Skips an optional number and the following '_' of a thunk's call offset.
static const char* skip_call_offset(const char* s) {
  if (*s == 'n') {
    ++s;
  }
  while (isdigit((unsigned char)*s)) {
    ++s;
  }
  return *s == '_' ? s + 1 : s;
}

// Whether an Itanium-mangled name names an entity in namespace std.
static int is_std_symbol(const char* name) {
  if (!starts_with(name, "_Z")) {
    return 0;
  }
  name += 2;
  // Special names: vtable, VTT, typeinfo, typeinfo name, guard variable.
  if (starts_with(name, "TV") || starts_with(name, "TT") ||
      starts_with(name, "TI") || starts_with(name, "TS") ||
      starts_with(name, "GV")) {
    name += 2;
  } else if (starts_with(name, "Th")) {  // Non-virtual thunk.
    name = skip_call_offset(name + 2);
  } else if (starts_with(name, "Tv")) {  // Virtual thunk.
    name = skip_call_offset(skip_call_offset(name + 2));
  }
  if (*name == 'N') {
    ++name;
    while (*name == 'r' || *name == 'V' || *name == 'K') {  // CV-qualifiers.
      ++name;
    }
  }
  return starts_with(name, "St");
}

int main(int argc, char** argv) {
  if (argc != 3) {
    fprintf(stderr, "usage: %s <input.def> <output.def>\n", argv[0]);
    return 2;
  }
  FILE* in = fopen(argv[1], "rb");
  if (in == NULL) {
    perror(argv[1]);
    return 1;
  }
  FILE* out = fopen(argv[2], "wb");
  if (out == NULL) {
    perror(argv[2]);
    fclose(in);
    return 1;
  }
  char line[16384];
  while (fgets(line, sizeof(line), in) != NULL) {
    const char* symbol = line;
    while (*symbol == ' ' || *symbol == '\t') {
      ++symbol;
    }
    // Export lines are indented; LIBRARY and EXPORTS are not.
    if (symbol != line && is_std_symbol(symbol)) {
      continue;
    }
    fputs(line, out);
  }
  fclose(in);
  return fclose(out) == 0 ? 0 : 1;
}

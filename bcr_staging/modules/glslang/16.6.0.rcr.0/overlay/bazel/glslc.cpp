// A glslc-compatible front end for glslang's standalone compiler.
//
// Tools such as PyTorch's tools/gen_vulkan_spv.py invoke shaderc's `glslc`.
// This translates the subset of glslc's options they use into glslang's
// (StandAlone/StandAlone.cpp, whose main() is compiled as
// glslang_standalone_main) and always compiles GLSL to SPIR-V for Vulkan:
//
//   -fshader-stage=<stage>   ->  -S <stage> (glslc's stage names, e.g.
//                                compute, mapped to glslang's, e.g. comp)
//   --target-env=<env>       ->  --target-env <env>
//   -I<dir>, -I <dir>        ->  -I<dir>
//   -D<macro>[=<value>]      ->  -D<macro>[=<value>]
//   -o <file>                ->  -o <file>
//   -Werror                  ->  (ignored: glslang has no equivalent)
//
// Like glslc, it enables `#include` in all shaders (glslang only allows it
// with #extension GL_GOOGLE_include_directive, which this adds to the
// preamble).
//   <file>                   ->  <file>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

int glslang_standalone_main(int argc, char* argv[]);

namespace {

bool StartsWith(const char* s, const char* prefix) {
  return std::strncmp(s, prefix, std::strlen(prefix)) == 0;
}

// glslc's -fshader-stage names, in glslang's -S spelling.
std::string GlslangStage(const std::string& stage) {
  static const char* const kStages[][2] = {
      {"vertex", "vert"},       {"fragment", "frag"},
      {"tesscontrol", "tesc"},  {"tesseval", "tese"},
      {"geometry", "geom"},     {"compute", "comp"},
      {"task", "task"},         {"mesh", "mesh"},
  };
  for (const auto& [glslc, glslang] : kStages) {
    if (stage == glslc) {
      return glslang;
    }
  }
  return stage;
}

}  // namespace

int main(int argc, char* argv[]) {
  std::vector<std::string> args = {
      argv[0],
      "-V",
      "-P#extension GL_GOOGLE_include_directive : enable\n",
  };
  for (int i = 1; i < argc; ++i) {
    const char* arg = argv[i];
    if (StartsWith(arg, "-fshader-stage=")) {
      args.push_back("-S");
      args.push_back(GlslangStage(arg + std::strlen("-fshader-stage=")));
    } else if (StartsWith(arg, "--target-env=")) {
      args.push_back("--target-env");
      args.push_back(arg + std::strlen("--target-env="));
    } else if (std::strcmp(arg, "-I") == 0 || std::strcmp(arg, "-o") == 0) {
      if (i + 1 >= argc) {
        std::fprintf(stderr, "glslc: missing argument to %s\n", arg);
        return 2;
      }
      if (arg[1] == 'I') {
        args.push_back(std::string("-I") + argv[++i]);
      } else {
        args.push_back("-o");
        args.push_back(argv[++i]);
      }
    } else if (std::strcmp(arg, "-Werror") == 0) {
      continue;
    } else if (StartsWith(arg, "-I") || StartsWith(arg, "-D") || arg[0] != '-') {
      args.push_back(arg);
    } else {
      std::fprintf(stderr, "glslc: unsupported option %s\n", arg);
      return 2;
    }
  }
  std::vector<char*> new_argv;
  for (std::string& a : args) {
    new_argv.push_back(a.data());
  }
  new_argv.push_back(nullptr);
  return glslang_standalone_main(static_cast<int>(args.size()), new_argv.data());
}

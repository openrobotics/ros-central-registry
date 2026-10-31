// Links bitcode files into one bitcode library and gives every external
// definition linkonce_odr linkage: what cmake/OCL.cmake's opencl_bc_lib()
// does with llvm-link and utils/prepare-builtins (its second, internalizing
// llvm-link of the single linked module changes nothing, and opt runs no
// passes).
//
// Usage: link-builtins -o <output.bc> <input.bc or .ll>...
#include <memory>
#include <string>
#include <system_error>
#include <vector>

#include "llvm/Bitcode/BitcodeWriter.h"
#include "llvm/IR/LLVMContext.h"
#include "llvm/IR/Module.h"
#include "llvm/IRReader/IRReader.h"
#include "llvm/Linker/Linker.h"
#include "llvm/Support/CommandLine.h"
#include "llvm/Support/FileSystem.h"
#include "llvm/Support/SourceMgr.h"
#include "llvm/Support/ToolOutputFile.h"
#include "llvm/Support/raw_ostream.h"

using namespace llvm;

static cl::list<std::string> InputFilenames(cl::Positional, cl::OneOrMore,
                                            cl::desc("<input bitcode files>"));
static cl::opt<std::string> OutputFilename("o", cl::Required,
                                           cl::desc("Output filename"),
                                           cl::value_desc("filename"));

int main(int argc, char** argv) {
  cl::ParseCommandLineOptions(argc, argv, "bitcode library linker\n");
  LLVMContext Context;
  auto Composite = std::make_unique<Module>("link-builtins", Context);
  Linker L(*Composite);
  for (const std::string& Filename : InputFilenames) {
    SMDiagnostic Err;
    std::unique_ptr<Module> M = parseIRFile(Filename, Err, Context);
    if (!M) {
      Err.print(argv[0], errs());
      return 1;
    }
    if (L.linkInModule(std::move(M))) {
      errs() << argv[0] << ": failed to link " << Filename << "\n";
      return 1;
    }
  }

  // utils/prepare-builtins: avoids duplicate symbols when device code of
  // several translation units links the library (-fgpu-rdc).
  for (GlobalValue& GV : Composite->global_values()) {
    if (!GV.isDeclaration() && GV.getLinkage() == GlobalValue::ExternalLinkage &&
        !isa<GlobalIFunc>(GV)) {
      GV.setLinkage(GlobalValue::LinkOnceODRLinkage);
    }
  }

  std::error_code EC;
  ToolOutputFile Out(OutputFilename, EC, sys::fs::OF_None);
  if (EC) {
    errs() << argv[0] << ": " << EC.message() << "\n";
    return 1;
  }
  WriteBitcodeToFile(*Composite, Out.os());
  Out.keep();
  return 0;
}

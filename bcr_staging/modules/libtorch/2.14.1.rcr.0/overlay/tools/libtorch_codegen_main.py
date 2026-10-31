"""Runs one of PyTorch's build-time code generators from a Bazel action.

Usage: libtorch_codegen_main.py <module> <source root> <bin root> <outputs file>
           [arguments...]

Runs `python -m <module> [arguments...]` (or `python <module>` if it is a .py
file relative to <source root>) from <source root> (the root of the
PyTorch source tree in the execroot), because upstream's generators resolve
some inputs relative to the current directory (e.g. generate_code.py's
torch/csrc/lazy/ts_backend/ts_native_functions.cpp). Every "{bin}" in the
arguments is replaced with the absolute path of <bin root> (the source root's
counterpart in the bin directory), where the outputs go, and every
"{execroot}" with the absolute path of the execroot (e.g. for tools).

Some generators embed their output directory in what they write (e.g. the lazy
tensor generator's `#include <{output dir}/LazyIr.h>`), so afterwards the
absolute <bin root> prefix is removed from the outputs listed in
<outputs file>, leaving paths relative to the include root.
"""

import os
import runpy
import sys


def main():
    module, source_root, bin_root, outputs_file, *arguments = sys.argv[1:]
    execroot = os.getcwd()
    bin_root = os.path.join(execroot, bin_root)
    with open(outputs_file) as f:
        outputs = [os.path.join(execroot, line.strip()) for line in f if line.strip()]
    arguments = [
        a.replace("{bin}", bin_root).replace("{execroot}", execroot)
        for a in arguments
    ]

    os.chdir(source_root)
    sys.argv = [module] + arguments
    try:
        if module.endswith(".py"):
            runpy.run_path(module, run_name="__main__")
        else:
            runpy.run_module(module, run_name="__main__", alter_sys=True)
    except SystemExit as e:
        if e.code not in (None, 0):
            raise
    os.chdir(execroot)

    prefix = bin_root + "/"
    for output in outputs:
        with open(output, encoding="utf-8") as f:
            content = f.read()
        if prefix in content:
            with open(output, "w", encoding="utf-8") as f:
                f.write(content.replace(prefix, ""))


if __name__ == "__main__":
    main()

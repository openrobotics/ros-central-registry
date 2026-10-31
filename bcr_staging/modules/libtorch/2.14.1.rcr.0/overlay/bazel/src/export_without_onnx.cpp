// The part of upstream's torch/csrc/jit/serialization/export.cpp that does not
// need ONNX: writeArchiveAndTensors(), which TorchScript serialization
// (export_module.cpp) uses. The rest of export.cpp is ONNX export for the
// Python bindings and needs the onnx and protobuf libraries, so @libtorch
// builds this copy of the function instead of the whole file.
//
// Copied verbatim from pytorch/pytorch@v2.14.1; keep it in sync on upgrades.

#include <torch/csrc/jit/serialization/export.h>

#include <caffe2/serialize/inline_container.h>
#include <torch/csrc/jit/serialization/pickle.h>

namespace torch::jit {

void writeArchiveAndTensors(
    const std::string& archive_name,
    const char* data,
    size_t size,
    const std::vector<at::Tensor>& tensors,
    caffe2::serialize::PyTorchStreamWriter& out) {
  std::string prefix = archive_name + "/";
  size_t i = 0;
  for (const auto& td : tensors) {
    WriteableTensorData writable_td = getWriteableTensorData(td);
    std::string fname = prefix + std::to_string(i++);
    out.writeRecord(fname, writable_td.data(), writable_td.sizeInBytes());
  }
  std::string fname = archive_name + ".pkl";
  out.writeRecord(fname, data, size);
}

} // namespace torch::jit

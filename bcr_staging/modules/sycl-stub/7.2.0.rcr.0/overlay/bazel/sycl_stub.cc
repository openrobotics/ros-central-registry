// The parts of libsycl's stub (see //:sycl) that have to work without SYCL
// platforms: enumerating them (there are none), and sycl::exception and its
// error category, whose vtable and type information are data that the
// stub's aborting trampolines cannot provide.
#include <sycl/sycl.hpp>

#include <memory>
#include <string>
#include <system_error>
#include <vector>

namespace sycl {
inline namespace _V1 {

namespace {

class SyclCategory : public std::error_category {
 public:
  const char* name() const noexcept override { return "sycl"; }
  std::string message(int) const override { return "SYCL error"; }
};

}  // namespace

const std::error_category& sycl_category() noexcept {
  static const SyclCategory category;
  return category;
}

std::error_code make_error_code(sycl::errc E) noexcept {
  return {static_cast<int>(E), sycl_category()};
}

exception::exception(std::error_code Ec, std::shared_ptr<context> SharedPtrCtx,
                     const char* WhatArg)
    : MMsg(std::make_shared<detail::string>(WhatArg ? WhatArg : "")),
      MContext(std::move(SharedPtrCtx)),
      MErrC(Ec) {}

exception::~exception() = default;

const std::error_code& exception::code() const noexcept { return MErrC; }

const std::error_category& exception::category() const noexcept {
  return MErrC.category();
}

const char* exception::what() const noexcept {
  return MMsg ? MMsg->c_str() : "";
}

bool exception::has_context() const noexcept { return MContext != nullptr; }

exception_list::size_type exception_list::size() const { return MList.size(); }

exception_list::iterator exception_list::begin() const { return MList.begin(); }

exception_list::iterator exception_list::end() const { return MList.end(); }

std::vector<platform> platform::get_platforms() { return {}; }

std::vector<device> device::get_devices(info::device_type) { return {}; }

}  // namespace _V1
}  // namespace sycl

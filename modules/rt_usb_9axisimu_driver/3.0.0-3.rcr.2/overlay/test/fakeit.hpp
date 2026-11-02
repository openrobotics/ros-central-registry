#ifndef FAKEIT_HPP_
#define FAKEIT_HPP_

#include <functional>
#include <memory>
#include <queue>
#include "rt_usb_9axisimu_driver/rt_usb_9axisimu.hpp"

namespace fakeit {

template <typename T>
class Mock;

template <>
class Mock<rt_usb_9axisimu::SerialPort> {
 public:
  struct State {
    std::queue<std::function<void(const char*)>> setPort_q;
    std::function<void(const char*)> setPort_always = [](const char*) {};

    std::queue<std::function<bool(const char*)>> openPort_q;
    std::function<bool(const char*)> openPort_always = [](const char*) { return true; };

    std::queue<std::function<bool()>> openSerialPort_q;
    std::function<bool()> openSerialPort_always = []() { return true; };

    std::queue<std::function<void()>> closeSerialPort_q;
    std::function<void()> closeSerialPort_always = []() {};

    std::queue<std::function<int(unsigned char*, unsigned int)>> readFromDevice_q;
    std::function<int(unsigned char*, unsigned int)> readFromDevice_always =
        [](unsigned char*, unsigned int) { return 0; };

    std::queue<std::function<int(unsigned char*, unsigned int)>> writeToDevice_q;
    std::function<int(unsigned char*, unsigned int)> writeToDevice_always =
        [](unsigned char*, unsigned int) { return 0; };
  };

  class Impl : public rt_usb_9axisimu::SerialPort {
   public:
    State* s = nullptr;

    void setPort(const char* p) override {
      if (!s->setPort_q.empty()) {
        auto f = s->setPort_q.front();
        s->setPort_q.pop();
        f(p);
        return;
      }
      s->setPort_always(p);
    }

    bool openPort(const char* p) override {
      if (!s->openPort_q.empty()) {
        auto f = s->openPort_q.front();
        s->openPort_q.pop();
        return f(p);
      }
      return s->openPort_always(p);
    }

    bool openSerialPort() override {
      if (!s->openSerialPort_q.empty()) {
        auto f = s->openSerialPort_q.front();
        s->openSerialPort_q.pop();
        return f();
      }
      return s->openSerialPort_always();
    }

    void closeSerialPort() override {
      if (!s->closeSerialPort_q.empty()) {
        auto f = s->closeSerialPort_q.front();
        s->closeSerialPort_q.pop();
        f();
        return;
      }
      s->closeSerialPort_always();
    }

    int readFromDevice(unsigned char* buf, unsigned int len) override {
      if (!s->readFromDevice_q.empty()) {
        auto f = s->readFromDevice_q.front();
        s->readFromDevice_q.pop();
        return f(buf, len);
      }
      return s->readFromDevice_always(buf, len);
    }

    int writeToDevice(unsigned char* buf, unsigned int len) override {
      if (!s->writeToDevice_q.empty()) {
        auto f = s->writeToDevice_q.front();
        s->writeToDevice_q.pop();
        return f(buf, len);
      }
      return s->writeToDevice_always(buf, len);
    }

    static void operator delete(void*) noexcept {}
  };

  std::shared_ptr<State> state_ = std::make_shared<State>();
  Impl impl_;

  Mock() { impl_.s = state_.get(); }
  Mock(const Mock& other) : state_(other.state_) { impl_.s = state_.get(); }
  Mock& operator=(const Mock& other) {
    state_ = other.state_;
    impl_.s = state_.get();
    return *this;
  }

  rt_usb_9axisimu::SerialPort& get() { return impl_; }
};

template <typename R, typename... Args>
struct Stubber {
  std::queue<std::function<R(Args...)>>* q;
  std::function<R(Args...)>* always;

  template <typename V = R>
  void AlwaysReturn(V val) {
    *always = [val](Args...) -> R { return val; };
  }

  void AlwaysReturn() {
    *always = [](Args...) {};
  }

  template <typename V>
  void Return(V v1) {
    q->push([v1](Args...) -> R { return v1; });
  }

  template <typename V1, typename V2>
  void Return(V1 v1, V2 v2) {
    q->push([v1](Args...) -> R { return v1; });
    q->push([v2](Args...) -> R { return v2; });
  }

  template <typename F>
  Stubber& Do(F f) {
    q->push(f);
    return *this;
  }

  template <typename F>
  void AlwaysDo(F f) {
    *always = f;
  }
};

inline Stubber<void, const char*> stub_setPort(Mock<rt_usb_9axisimu::SerialPort>& m) {
  return {&m.state_->setPort_q, &m.state_->setPort_always};
}
inline Stubber<bool, const char*> stub_openPort(Mock<rt_usb_9axisimu::SerialPort>& m) {
  return {&m.state_->openPort_q, &m.state_->openPort_always};
}
inline Stubber<bool> stub_openSerialPort(Mock<rt_usb_9axisimu::SerialPort>& m) {
  return {&m.state_->openSerialPort_q, &m.state_->openSerialPort_always};
}
inline Stubber<void> stub_closeSerialPort(Mock<rt_usb_9axisimu::SerialPort>& m) {
  return {&m.state_->closeSerialPort_q, &m.state_->closeSerialPort_always};
}
inline Stubber<int, unsigned char*, unsigned int> stub_readFromDevice(
    Mock<rt_usb_9axisimu::SerialPort>& m) {
  return {&m.state_->readFromDevice_q, &m.state_->readFromDevice_always};
}
inline Stubber<int, unsigned char*, unsigned int> stub_writeToDevice(
    Mock<rt_usb_9axisimu::SerialPort>& m) {
  return {&m.state_->writeToDevice_q, &m.state_->writeToDevice_always};
}

template <typename S>
S When(S s) {
  return s;
}

}  // namespace fakeit

#define Method(mock, name) ::fakeit::stub_##name(mock)

#endif  // FAKEIT_HPP_

#include <iostream>
#include <thread>
#include <chrono>
#include <filesystem>
#include <gtest/gtest.h>

#if defined(__APPLE__)
#include <mach/mach.h>
#include <mach/thread_act.h>
#endif

#if !defined(_WIN32)
#include <dlfcn.h>
#endif

namespace {

size_t get_current_thread_count() {
#if defined(__APPLE__)
  thread_act_array_t thread_list;
  mach_msg_type_number_t thread_count;
  kern_return_t kr = task_threads(mach_task_self(), &thread_list, &thread_count);
  if (kr == KERN_SUCCESS) {
    for (mach_msg_type_number_t i = 0; i < thread_count; ++i) {
      mach_port_deallocate(mach_task_self(), thread_list[i]);
    }
    vm_deallocate(mach_task_self(), (vm_address_t)thread_list, thread_count * sizeof(thread_act_t));
    return thread_count;
  }
  return 1;
#else
  size_t count = 0;
  try {
    for (const auto & entry : std::filesystem::directory_iterator("/proc/self/task")) {
      (void)entry;
      count++;
    }
  } catch (...) {
    return 1; // Fallback if /proc is not mounted
  }
  return count;
#endif
}

class DDSThreadCleanupListener : public ::testing::EmptyTestEventListener {
public:
  void OnTestProgramStart(const ::testing::UnitTest& /*unit_test*/) override {
    baseline_thread_count_ = get_current_thread_count();
  }

  void OnTestSuiteStart(const ::testing::TestSuite& /*test_suite*/) override {
    suite_baseline_thread_count_ = get_current_thread_count();
  }

  void OnTestStart(const ::testing::TestInfo& /*test_info*/) override {
    // Capture threads spawned in SetUpTestSuite() / SetUpTestCase() so tests
    // that share a suite-level rclcpp context do not wait 2s on every TEST_F.
    suite_baseline_thread_count_ = std::max(suite_baseline_thread_count_, get_current_thread_count());
  }

  void OnTestEnd(const ::testing::TestInfo& test_info) override {
    auto start = std::chrono::steady_clock::now();
    constexpr std::chrono::milliseconds timeout(2000);
    size_t target_threads = std::max(baseline_thread_count_, suite_baseline_thread_count_);
    
    size_t current_threads = get_current_thread_count();
    while (current_threads > target_threads) {
      if (std::chrono::steady_clock::now() - start > timeout) {
        std::cerr << "[ WARNING ] " << test_info.test_suite_name() << "." << test_info.name() 
                  << " timed out waiting for background threads to exit. "
                  << "Baseline: " << target_threads 
                  << ", Current: " << current_threads << "\n";
        break;
      }
      std::this_thread::sleep_for(std::chrono::milliseconds(10));
      current_threads = get_current_thread_count();
    }
  }

  void OnTestProgramEnd(const ::testing::UnitTest& /*unit_test*/) override {
#if !defined(_WIN32)
    struct EmptySharedPtr {
      void* ptr = nullptr;
      void* cntrl = nullptr;
    };
    using ShutdownSharedPtrFn = bool (*)(const EmptySharedPtr&, const std::string&);
    const char* symbols[] = {
        "_ZN6rclcpp8shutdownERKNSt3__110shared_ptrINS_7ContextEEERKNS0_12basic_stringIcNS0_11char_traitsIcEENS0_9allocatorIcEEEE",
        "_ZN6rclcpp8shutdownERKSt10shared_ptrINS_7ContextEERKNSt7__cxx1112basic_stringIcSt11char_traitsIcESaIcEEE",
    };
    ShutdownSharedPtrFn fn = nullptr;
    for (const char* sym : symbols) {
      fn = reinterpret_cast<ShutdownSharedPtrFn>(dlsym(RTLD_DEFAULT, sym));
      if (fn) break;
    }
    if (!fn) {
      for (const char* lib : {"librclcpp.so", "lib/librclcpp.so"}) {
        void* handle = dlopen(lib, RTLD_LAZY | RTLD_NOLOAD);
        if (handle) {
          for (const char* sym : symbols) {
            fn = reinterpret_cast<ShutdownSharedPtrFn>(dlsym(handle, sym));
            if (fn) break;
          }
          dlclose(handle);
          if (fn) break;
        }
      }
    }
    if (fn) {
      try {
        EmptySharedPtr empty;
        fn(empty, "");
      } catch (...) {
      }
    }
#endif
  }

private:
  size_t baseline_thread_count_ = 1;
  size_t suite_baseline_thread_count_ = 1;
};

// Register the listener statically
static struct DDSThreadCleanupListenerRegistrar {
  DDSThreadCleanupListenerRegistrar() {
    auto& listeners = ::testing::UnitTest::GetInstance()->listeners();
    listeners.Append(new DDSThreadCleanupListener);
  }
} g_dds_thread_cleanup_listener_registrar;

} // namespace

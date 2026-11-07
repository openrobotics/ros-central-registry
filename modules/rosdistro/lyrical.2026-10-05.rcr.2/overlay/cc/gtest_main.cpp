// Default test entry point for @rosdistro//cc:googletest.
//
// googletest >= 1.18 marks its own `@googletest//:gtest_main` as
// `alwayslink = True`, which forces its `main()` into every binary that
// (transitively) links it -- even tests that define their own `main()`,
// producing "duplicate symbol: main" link errors. This copy lives in a
// regular (non-alwayslink) static library, so the linker only pulls it in
// when nothing else in the test binary defines `main()`.

#include <gmock/gmock.h>

int main(int argc, char ** argv)
{
  // InitGoogleMock() also initializes Google Test.
  testing::InitGoogleMock(&argc, argv);
  return RUN_ALL_TESTS();
}

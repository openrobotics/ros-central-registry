#include <gtest/gtest.h>
#include <rclcpp/rclcpp.hpp>
#include "generate_parameter_library/test_parameters.hpp"

TEST(TestParameterLibrary, BasicDefaults) {
  auto node = std::make_shared<rclcpp::Node>("test_node");
  auto param_listener = std::make_shared<test_params::ParamListener>(node);
  
  auto params = param_listener->get_params();
  EXPECT_EQ(params.some_int, 42);
  EXPECT_EQ(params.some_string, "hello");
}

int main(int argc, char** argv) {
  testing::InitGoogleTest(&argc, argv);
  rclcpp::init(argc, argv);
  int result = RUN_ALL_TESTS();
  rclcpp::shutdown();
  return result;
}

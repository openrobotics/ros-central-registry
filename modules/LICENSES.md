## Where the license text came from

| Source | Packages | How it's referenced |
|---|---:|---|
| License file in the package's own source archive | 508 | Referenced directly (`"LICENSE"`, or `"//:LICENSE"` from sub-packages) |
| Monorepo root above `strip_prefix` (`rosidl_adapter_proto`, `rosidl_typesupport_protobuf{,_c,_cpp}`) | 4 | Copied into `overlay/` |
| Upstream **source repo root** (release tarball had none) | 1,103 | Copied into `overlay/` |
| **Generic SPDX text** for the license in `package.xml` (no license file anywhere) | 50 | Generated `overlay/LICENSE` |
| **Total updated** | **1,665** | |

When `license()` is declared in a sub-package (e.g. `msg/BUILD.bazel`), the root `BUILD.bazel` also gets `exports_files(["<license file>"])`. This applies to 10 packages.

## Packages that got a generic license (no license file found anywhere)

The upstream repo has no root license file at the release tag (confirmed by listing each repo root), and the tarball has none. These 50 got the canonical SPDX text from `spdx/license-list-data`, placeholders included:

- **BSD-3-Clause** (`package.xml` says "BSD" or "BSD-3-Clause"): angles, camera_calibration_parsers, camera_info_manager, dual_arm_panda_moveit_config, eigen_stl_containers, filters, four_wheel_steering_msgs, geodesy, geographic_info, geographic_msgs, image_transport, image_transport_py, joy_teleop, jsk_common_msgs, jsk_footstep_msgs, jsk_hark_msgs, kobuki_ros_interfaces, laser_proc, libg2o, map_msgs, moveit_resources_panda_moveit_config, moveit_resources_pr2_description, nmea_msgs, nmea_navsat_driver, object_recognition_msgs, octomap_msgs, octomap_server, pcl_conversions, pcl_ros, posedetection_msgs, rqt_action, rqt_msg, rqt_srv, speech_recognition_msgs, teleop_tools_msgs, turtlesim, turtlesim_msgs, ublox_gps, ublox_msgs, ublox_serialization, urg_c, vrpn, wiimote_msgs, wireless_msgs, wireless_watcher
- **MIT**: apriltag_msgs, microstrain_inertial_description
- **Apache-2.0**: jsk_gui_msgs
- **Two licenses, both texts in one file**: rqt_bag_plugins (BSD-3-Clause + HPND), tlsf_cpp (LGPL-2.1-only + Apache-2.0)

## Not updated

- **144 versions have no `license(...)` rule at all**, so there's nothing to add to. They are mostly metapackages and pure-Python or `ament_*` lint packages: ament_clang_format, ament_cmake_clang_format, ament_pclint, ament_pyflakes, auto_apms_ros2behavior, autoware_lanelet2_extension_python, autoware_msgs, bond_core, canopen, canopen_utils, clips_executive, compressed_image_transport, cx_* (14), desktop, desktop_full, diagnostics, dynamixel_workbench, ecl_core, eigen3_cmake_module, examples_rclpy_guard_conditions, examples_rclpy_pointcloud_publisher, executive_smach, ffw, ffw_teleop, geometry2, geometry_tutorials, gps_umd, image_common, image_pipeline, image_transport_plugins, image_view, imu_pipeline, imu_tools, joy_tester, kdl_parser_py, key_teleop, kobuki_core, kortex_driver, lanelet2, lanelet2_python, launch_testing_examples, leo, leo_desktop, leo_robot, leo_simulator, libcamera, linux_isolate_process, lz4_cmake_module, mcap_vendor, metavision_driver, mola, mola_sm_loop_closure, mola_state_estimation, moveit, moveit_planners, moveit_plugins, moveit_resources, moveit_ros, moveit_runtime, mrpt_navigation, nao_button_sim, nodl_python, nodl_to_policy, octomap_mapping, off_highway_sensor_drivers, open_manipulator, open_manipulator_teleop, openeb_vendor, ouxt_common, perception, perception_pcl, phidgets_drivers, picknik_ament_copyright, pybind11_json_vendor, py_trees_ros_viewer, python_cmake_module, qt_gui_core, rmf_charging_schedule, rmf_demos_bridges, ros, ros2_control, ros2_controllers, ros2acceleration, ros2controlcli, ros2launch_security, ros2nodl, ros2trace, ros2trace_analysis, ros_base, ros_gz, rosbag2, rosbag2_examples_py, rosbag2_storage_default_plugins, rosbag2_test_common, rosbag2_to_video, rosbridge_suite, rosidlcpp, rqt_common_plugins, rqt_dotgraph, rqt_gauges, rqt_moveit, rqt_robot_monitor, rqt_runtime_monitor, sdformat_test_files, sick_safevisionary_tests, simulation, smach, soccer_interfaces, swri_cli_tools, swri_roscpp, tango_icons_vendor, teleop_tools, tf2_tools, theora_image_transport, trac_ik, tracetools_image_pipeline, tracetools_read, tracetools_test, turtlebot3_autorace, turtlebot3_simulations, twist_stamper, ublox, ur, urdf_parser_plugin, vision_opencv, vitis_common, yaml_cpp_vendor, yasmin_cli, yasmin_plugins_manager, zstd_cmake_module, zstd_image_transport
- **`rosdistro`** was left alone on purpose. Its only `license()` (in `cc/basalt`) declares Apache-2.0, but the repo's `LICENSE` is BSD-3-Clause.
- **`xacro`** already had `license_text`.

## Things worth a look

> [!WARNING]
> **The repo-root license doesn't always match the package.** For 1,103 packages the file came from the source repo root, which describes the whole repository. In some repos it covers a bundled library or a different license than the one the package declares:
> - **phidgets_\*** (16 packages): the root `LICENSE` describes the bundled *libphidgets22* (LGPL), while the packages declare BSD.
> - **image_pipeline** packages (camera_calibration, depth_image_proc, image_proc, image_publisher, image_rotate, stereo_image_proc): the root is Apache-2.0, the packages declare BSD-3-Clause.
> - **nav2 / opennav** and **mavros**: the root file is a multi-license overview, not a single license text.

**Branch instead of tag (17 packages).** These had no tag matching the release version, so the file was taken from the distro's source branch: ackermann_msgs, avt_vimba_camera, foxglove_bridge, foxglove_msgs, int2dds_ffi_vendor, rmw_int2dds_cpp, jacro, moveit_task_constructor_{capabilities,core,demo,msgs,visualization}, rviz_marker_tools, pcl_msgs, rc_common_msgs, plus ackermann_nlmpc{,_msgs} (self-hosted GitLab at tag `1.0.3`).

**Hand-picked when a package ships several license files.** In each case I picked the file matching `license_kinds`: gtsam uses `LICENSE.BSD` (its `LICENSE` is an overview), eiquadprog uses `COPYING.LESSER`, ros_industrial_cmake_boilerplate uses `LICENSE.Apache-2.0`, ecl_license uses `licenses/COPYING`, live555_vendor uses `LICENSES/LGPL-3.0-or-later.txt`, and cv_bridge/image_geometry use `LICENSE-BSD`. For ecl_command_line, ecl_console and ecl_eigen, the `license/` folder holds bundled third-party texts (tclap, rang, Eigen), so I used the ecl_core repo-root license instead.

**`license_kinds` disagrees with the license text.** I did not change any `license_kinds`; I'm only flagging these:
- **Clear mismatches:**
  - Apache-2.0 declared, text is LGPL/GPL: slam_toolbox, plotjuggler_ros, popf, protobuf_comm, visp, gstreamer_ros_babel_fish, canopen_402_driver, apriltag_mit, video_to_image_msg_publisher, mola_input_ouster
  - BSD declared, text is Apache: controller_manager_msgs, turtle_tf2_py, moveit_resources_panda_description
  - Apache declared, text is BSD: robot_localization, examples_tf2_py, ros2plugin, rviz_ogre_vendor, ur_moveit_config, moveit_resources_prbt_pg70_support, moveit_ros_trajectory_cache, plansys2_pddl_parser
  - Other: tcb_span (BSL-1.0 declared, text is MIT), rosx_introspection (MIT declared, text is LGPL), plotjuggler (MPL-2.0 declared, text is LGPL), libcaer_vendor (BSD-2 declared, text is Apache), jrl_cmakemodules (BSD-2 declared, text is LGPL), wiimote, can_msgs, mola_bridge_ros2, mola_input_euroc_dataset, imu_complementary_filter, rviz_imu_plugin, leo_description, open3d_vendor, ouster_sensor_msgs, webots_ros2_crazyflie, avt_vimba_camera
- **Wrong text picked for the package** (third-party or overview file): phidgets_\* and the image_pipeline packages above.

## Process notes

- Work was done in a dedicated `workspace_license/`. `workspace/` and `workspace_webots/` were not touched.
- On its first run, `create_patch` re-diffed two unrelated cartographer patches (`pose_graph_{2d,3d}.h`) with a different hunk layout. I restored the committed versions and their `source.json` hashes so only license changes remain.
- `buildifier` still flags `modules/rtabmap/0.23.13-1.rcr.0/overlay/REPO.bazel`. That issue was already there before this work and is unrelated.

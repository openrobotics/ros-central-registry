<p align="center">
<img width="256" src="docs/source/rcr_logo.png"/>
<br/>   
<font size="6">ROS Central Registry</font>
<br/>
The <a href="https://bazel.ros.org">ROS Central Registry</a> provides <a href= "https://bazel.build">Bazel</a> modules for <a href="https://ros.org">Robot Operating System (ROS)</a> core packages. This repo provides tooling that automates the release and patching process in response to upstream changes.
</p>

# Releases

## lyrical.2026-06-08.rcr.2
![linting](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/linting.json)
![tooling](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/tooling.json)
![docs build](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/docs_build.json)
![deployment](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/deployment.json)

| Platform | Examples | Build | FastDDS | FastDDS Dynamic | CycloneDDS | Zenoh |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| ubuntu-26.04 | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_8.x_ubuntu-26.04_examples.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_9.x_ubuntu-26.04_examples.json) | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_8.x_ubuntu-26.04_build.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_9.x_ubuntu-26.04_build.json) | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_8.x_ubuntu-26.04_test_rmw_fastrtps_cpp.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_9.x_ubuntu-26.04_test_rmw_fastrtps_cpp.json) | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_8.x_ubuntu-26.04_test_rmw_fastrtps_dynamic_cpp.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_9.x_ubuntu-26.04_test_rmw_fastrtps_dynamic_cpp.json) | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_8.x_ubuntu-26.04_test_rmw_cyclonedds_cpp.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_9.x_ubuntu-26.04_test_rmw_cyclonedds_cpp.json) | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_8.x_ubuntu-26.04_test_rmw_zenoh_cpp.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_9.x_ubuntu-26.04_test_rmw_zenoh_cpp.json) |
| ubuntu-26.04-arm | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_8.x_ubuntu-26.04-arm_examples.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_9.x_ubuntu-26.04-arm_examples.json) | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_8.x_ubuntu-26.04-arm_build.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_9.x_ubuntu-26.04-arm_build.json) | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_8.x_ubuntu-26.04-arm_test_rmw_fastrtps_cpp.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_9.x_ubuntu-26.04-arm_test_rmw_fastrtps_cpp.json) | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_8.x_ubuntu-26.04-arm_test_rmw_fastrtps_dynamic_cpp.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_9.x_ubuntu-26.04-arm_test_rmw_fastrtps_dynamic_cpp.json) | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_8.x_ubuntu-26.04-arm_test_rmw_cyclonedds_cpp.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_9.x_ubuntu-26.04-arm_test_rmw_cyclonedds_cpp.json) | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_8.x_ubuntu-26.04-arm_test_rmw_zenoh_cpp.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_9.x_ubuntu-26.04-arm_test_rmw_zenoh_cpp.json) |
| macos-26-intel | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_8.x_macos-26-intel_examples.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_9.x_macos-26-intel_examples.json) | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_8.x_macos-26-intel_build.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_9.x_macos-26-intel_build.json) | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_8.x_macos-26-intel_test_rmw_fastrtps_cpp.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_9.x_macos-26-intel_test_rmw_fastrtps_cpp.json) | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_8.x_macos-26-intel_test_rmw_fastrtps_dynamic_cpp.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_9.x_macos-26-intel_test_rmw_fastrtps_dynamic_cpp.json) | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_8.x_macos-26-intel_test_rmw_cyclonedds_cpp.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_9.x_macos-26-intel_test_rmw_cyclonedds_cpp.json) | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_8.x_macos-26-intel_test_rmw_zenoh_cpp.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_9.x_macos-26-intel_test_rmw_zenoh_cpp.json) |
| macos-26 | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_8.x_macos-26_examples.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_9.x_macos-26_examples.json) | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_8.x_macos-26_build.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_9.x_macos-26_build.json) | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_8.x_macos-26_test_rmw_fastrtps_cpp.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_9.x_macos-26_test_rmw_fastrtps_cpp.json) | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_8.x_macos-26_test_rmw_fastrtps_dynamic_cpp.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_9.x_macos-26_test_rmw_fastrtps_dynamic_cpp.json) | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_8.x_macos-26_test_rmw_cyclonedds_cpp.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_9.x_macos-26_test_rmw_cyclonedds_cpp.json) | ![8.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_8.x_macos-26_test_rmw_zenoh_cpp.json) ![9.x](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/asymingt/f796805a77e0f05cc837b18e60142773/raw/lyrical.2026-06-08.rcr.2_perception_9.x_macos-26_test_rmw_zenoh_cpp.json) |

# Prerequisites

The RCR builds **everything from source** using a hermetic LLVM/clang toolchain and a hermetic Python interpreter that Bazel downloads automatically. As a result you do **not** need a system C/C++ compiler or an existing ROS installation.

## Ubuntu 26.04 (amd64 or arm64)

Make sure you have git, Python3, and zip compression tools installed:

```
sudo apt-get update && sudo apt-get install -y git unzip zip
```

Then download bazelisk and put it on your path:

```bash
mkdir -p ~/.local/bin
curl -Lo ~/.local/bin/bazel \
  https://github.com/bazelbuild/bazelisk/releases/latest/download/bazelisk-linux-$(dpkg --print-architecture)
chmod +x  ~/.local/bin/bazel
```

## MacOS Tahoe (amd64 or arm64)

Install the system SDK frameworks and linker:

```
xcode-select --install
```

Install Homebrew and then the necessary tools:

```bash
brew install bazelisk git
```

# Verify your setup

Check that the commands below print versions.

```bash
bazel --version
git --version
```

# Quick demo

```python
git clone https://github.com/openrobotics/ros-central-registry.git
```

Switch to the examples folder, which is a Bazel workspace showing some simple examples:

```
cd ros-central-registry/examples
```

Now you can run an example C++ publisher and subscriber that communicate a custom message:

```
bazel run //:example_ros_publisher_cc    # in one terminal   
bazel run //:example_ros_subscriber_cc   # in another terminal
```

We currently support C, C++ and Python client nodes, as well as the generation of ROS messages, services and actions from message definitions. To see more examples, use the `query` verb in conjunction with a recursive wildcard expansion `...` relative to the root of the examples folder `//` to list all targets:

```
bazel query //...
```

Please refer to [examples/README.md](examples/README.md) for more information.

# Building and testing the full perception release

To build and test an entire ROS variant (for example `perception`), generate a workspace
from the repository root and run Bazel inside it:

```bash
# From the root of the repository, generate the workspace/ folder for a release.
bazel run //tools/ci:setup_workspace -- --release=lyrical.2026-06-08.rcr.2

# Switch to the generated workspace.
cd workspace

# Build all packages in the perception variant.
bazel build --config perception

# Test all packages in the perception variant.
bazel test --config perception
```

The `setup_workspace` target resolves every package in the requested release, writes a
`MODULE.bazel`, a `.bazelrc`, and `ros-<variant>.txt` target lists into `workspace/`. The
available variants are `core`, `base`, `desktop`, `desktop_full`, `perception` and
`simulation`; select one with the matching `--config` flag. The first build compiles the
whole distribution from source and can take a long time on a cold cache; subsequent builds
reuse the local and remote caches.

Right now we support everything up to perception. Beyond perception, the other variants (desktop, simulation and desktop_full) are incomplete. The biggest issue is that packages (rviz, gazebo, etc) depend on OpenGL, which requires headers to be supplied from the host, breaking hermeticity.

# Usage instructions

When this line is added to a `.bazelrc` file it instructs Bazel to look for modules first in the RCR, and then in the BCR.

```bazel
common --registry=https://bazel.ros.org --registry=https://bcr.bazel.build
```

When the following lines are added to the `MODULE.bazel` file, Bazel will load the `core` ROS variant, which contains a minimum set of ROS packages required to build any ROS project. The `std_msgs` and `rclcpp` packages are among these.

```bazel
bazel_dep(name = "ros_core", version = "lyrical.2026-06-08.rcr.2")
bazel_dep(name = "rclcpp", version = "0.0.0")    # resolves version 32.0.0-1.rcr.1 
bazel_dep(name = "std_msgs", version = "0.0.0")  # resolves version 5.9.2-3.rcr.1 
```

The example above loads the RCR patch release #1 of the `lyrical/2026-06-08` upstream ROS release branch. Bazel [does not](https://github.com/bazelbuild/bazel/issues/28881) transitively export these packages to be visible to the current workspace, so if you need to use a package like `@rclcpp` you must depend on it explicitly by name using `0.0.0` as a boilerplate version. Bazel will use the [Minimal Version Selection (MVS)](https://bazel.build/external/module#version-selection) algorithm to choose the right version. Since any version dominates `0.0.0`, it will by default pick the version loaded transitively via the `ros_core` load in the line above. This allows one to load ROS modules / packages from a variant without knowing specific versions.


Once you have loaded a ROS release, you can use any of the packages from that release. Below is an example of building a simple C++ publisher node that publishes `std_msgs/string` messages. You can see a very similar functional example in [examples/BUILD.bazel](examples/BUILD.bazel) using a custom message.

```python
load("@rules_cc//cc:defs.bzl", "cc_binary")

cc_binary(
    name = "my_simple_string_publisher",
    srcs = ["my_simple_string_publisher.cc"],
    deps = [
        "@std_msgs//:cc",
        "@rclcpp//:rclcpp_library",
    ],
)
```

# Architectural overview

## Module organization

Software modules are divided into two categories: 
- __Third-party modules__: these are upstream, general software packages that are external to ROS and therefore they do not have a `package.xml` file. They live in the [Bazel Central Registry (BCR)](https://registry.bazel.build) and are useful to more than just the ROS ecosystem. Examples include `zlib`, `fastdds`, `ogre`, etc.
- __ROS modules__ - these correspond to individual ROS packages (not repositories), and they have a distinct `package.xml` file. Examples of these include `rclcpp`, `rclcpp_action`, `launch_ros`, etc. These modules live in the [ROS Central Registry (RCR)](https://github.com/openrobotics/ros-central-registry) and are maintained by this GitHub project in response to upstream releases.

This block diagram below shows how RCR releases are organized. A workspace will always have at least two `--registry` entries: one for the BCR (shaded in green) and another for the RCR (shaded in blue). You can think of the RCR as an augmentation to the BCR, and so RCR modules can depend on BCR modules, but not vice versa.

![RCR Architecture](docs/images/architecture.png)

BCR dependencies can be divided into __build tools__ (e.g. `rules_cc`, `llvm`) and __libraries__ (e.g. `zlib`, `openssl`). One of our key design choices is to proxy all libraries through a single `rosdistro` module. What this means in practice is that a RCR package that needs `zlib` will depend on `@rosdistro//cc:zlib`, and not `@zlib`.

We have chosen to do this for a couple of reasons:

1. **It's the norm in ROS** - Traditionally, ROS packages don't specify a version when declaring dependencies in `package.xml` files. Rather, they specify package keys and rely on `rosdep` to resolve the correct OS-specific package name and version for the key. This is to handle the case where one Linux distro uses `libusb-dev` and another uses `libusb1.0-dev`, and the fact that operating systems are continually rolling out updated package versions. This approach greatly simplifies dependency pinning for RCR packages. 
2. **It's easier to manage and automate** - Having a single `MODULE.bazel` file in `rosdistro` for all third-party dependencies is considerably easier than ensuring that two packages don't pull in a common dependency with different version requirements. For example, if `rclcpp` requires `zlib@1.2.13` and `libopenssl` requires `zlib@1.2.16` Bazel's MVS algorithm would pick the highest of the two which may not be compatible with `rclcpp`. Our centralized approach guards against this by ensuring all packages use a consistent release-specific version.
3. **It standardizes the Python environment** - We mandate that ROS packages use the pip extension offered by the `rosdistro` module to ensure that a consistent set of versions are delivered across all RCR packages. If we didn't do this, multiple packages could end up pulling in different versions of the same Python package via different mechanisms, and the one that is ultimately used is simply the first one listed on the `PYTHONPATH` constructed by Bazel.
4. **It allows us to declare shared libraries for third-party dependencies** - One of the goals of the RCR is to enable a developer to stitch together build artifacts into something that resembles a traditional ROS underlay. In order to do this we have to produce shared libraries. Doing this for third-party dependencies requires that a `cc_shared_library` is created for each library. This is not very difficult, but it is boilerplate code that we can add in the `rosdistro` module to keep the entire dependency chain organized.

## Runtime data

In ROS, runtime data is accessed through the `ament_index`, which is essentially a file structure relative to the root of your underlay (e.g., `/opt/ros/lyrical`) that allows packages to share files with each other. In this paradigm a single shared index -- specified by the `AMENT_PREFIX_PATH` environment variable -- is shared at runtime with targets across all packages so that they can resolve libraries, executables, plugins, and other assets from all packages.

Conversely, in Bazel each target gets its own isolated directory of files, which is populated based on the transitive accumulation of `data` dependencies. For efficiency reasons the directory is a forest of symlinks to the original files. This model for data access preserves hermeticity by making explicit what is accessible by any target. Unlike `ament_index`, it also avoids the case where stale files persist in the index over time, since the runfile tree is rebuilt for each target.

Our project unifies the two approaches by treating the runfile directory as the `ament_index`. To do this we wrap all data, libraries, plugins, etc with a rule `ament_index(...)` before passing them to a target. This rule prepares the runfile symlinks to mimic the ament_index. We then set the `AMENT_PREFIX_PATH` to the runfile directory when a `bazel run ...` or `bazel test ...` is run. Outside of a Bazel context the `AMENT_PREFIX_PATH` will be respected.

At the end of a `MODULE.bazel` file for a package you will see an `ament_package` call. Behaviorally, this does the same thing as `ament_index`, but it also provides a few more rules `:pkg` and `:tar` that help with serializing executables, libraries, Python modules and data into a layer for containerization.

```python
load("@rules_cc//cc:defs.bzl", "cc_binary")
load("@rosdistro//ament:defs.bzl", "ament_index", "ament_package")

ament_index(
    name = "ament_index",
    package_xml = "package.xml",
    data = glob(["config/**"]),¬
    deps = ["@foo//:ament_package"]
)

cc_binary(
    name = "bar",
    srcs = ["bar.cc"],
    data = [":ament_index"],
    deps = ["@ament_index_cpp"],
)

ament_package(
    name = "ament_package",
    package_xml = "package.xml",
    executables = [":my_node"],
    deps = ["@foo//:ament_package"]
)
```

## Shared libraries

In Bazel create C/C++ executables and tests targets with `cc_binary` and `cc_test`, which respectively link statically and dynamically by default. This behavior can be overridden with `linkstatic = True | False` or `linkshared = True | False`. However, this mechanism governs how linking is carried out within Bazel's library management system. This is designed for internal use, and obfuscates the library names. To create reusable shared libraries we have to use the `cc_shared_library` rule, which comes with its own challenges.

The `cc_shared_library` constructs its own shadow dependency chain over the `cc_library` dependency chain, and its purpose is to instruct the linker how to strip out and link symbols. A consequence of this design choice is that every shared library needs both a `cc_library` rule (representing the primary link chain) and a `cc_shared_library` rule (for the shared library augmentation). Therefore, if we have some library `bar` that declares a shared library `bar` that transitively depends on a shared library `foo` from module `foo`, we have to take care to link correctly in the following way:

```python
load("@rosdistro//ament:defs.bzl", "ament_package")
load("@rosdistro//cc:defs.bzl", "collect_transitive_dynamic_deps", "ros_local_defines")
load("@rules_cc//cc:defs.bzl", "cc_library", "cc_shared_library", "cc_test")

HEADERS = glob(["include/**/*.hpp"])

DEPENDENCIES = {"@foo//:foo": "@foo//:foo_library"}

cc_library(
    name = "bar_library",
    srcs = glob(["src/**/*.cpp"]),
    hdrs = glob(["src/**/*.hpp"]),
    includes = ["include"],
    deps = DEPENDENCIES.values() + [
      "@std_msgs//:cc"                  # See notes below
    ],
)

cc_shared_library(
    name = "bar",
    dynamic_deps = DEPENDENCIES.keys(),
    exports_filter = [":bar_library"],
    deps = [":bar_library"],
)

collect_transitive_dynamic_deps(
    name = "transitive_dynamic_deps",
    dynamic_deps = [":bar"],
)

cc_test(
    name = "baz",
    srcs = ["test/baz.cpp"],
    dynamic_deps = [":transitive_dynamic_deps"],
    deps = DEPENDENCIES.values() + [
        ":foo",
        "@googletest//:gtest",
        "@googletest//:gtest_main",
        "@test_msgs//:cc",              # See notes below
    ],
)

ament_package(
    name = "ament_package",
    package_xml = "package.xml",
    headers = HEADERS,
    libraries = [":bar"],
    deps = ["@foo//:ament_package"]
)
```

Some important notes about the code above:

1. The message packages have `:cc` targets that supply both compilation information (via a `CcInfo`) and shared library files (via `DefaultInfo`) so they can be just listed in the `deps` directly; you do not have to import special targets for the message language bindings.
2. The `collect_transitive_dynamic_deps` rule is needed because `dynamic_deps` does not work transitively. So, in order for `baz` to link correctly to `foo` through `bar`, we need to collect all of the shared libraries from `bar` and all of its `dynamic_deps`, and then pass them to `baz`. You only need to do this for `cc_test` or `cc_binary` rules.

## Message generation

One of our objectives is to provide the ability to compile small, portable C and C++ nodes as single ROS nodes. Achieving this requires that we make a few key changes to how messages and their corresponding language bindings are defined, and how the RMW middleware layer is configured. 

1. Message dependency chains are declared at the message-level, not the package-level. Broadly speaking, if `sensor_msgs/msg/CompressedImage` relies on `std_msgs/msg/Header`, then the `@sensor_msgs//msg:CompressedImage` Bazel target must have a `deps` entry for `@std_msgs//msg:Header`. This enables binaries to compile-in only the symbols for messages they use, and not entire packages.
2. At runtime the type adapter calls `dlopen` to load the typesupport shared library for the active middleware when it needs to transform serialized bytes on the wire to the language. We have modified this type adapter to first look for the symbols on the active binary, in case they were compiled statically into the binary.
3. By default, when the `--@rosdistro//:rmw=...` flag is set, it configures the RMW implementation to a specific single middleware. The `RMW_IMPLEMENTATION` environment variable should not be used. This allows a ROS node that depends on `rclcpp`, which in turn depends on `rmw_implementation` transitively through `rcl`, to avoid having to dynamically open a shared library for its RMW implementation.

## Static compilation

If you run `bazel run //:example_ros_publisher_cc --dynamic_mode=off --@rosdistro//:rmw=rmw_cyclonedds_cpp` in the examples folder you will get a single portable executable with all required symbols statically linked into the executable. These flags must always be used together, as both the typesupports and the middleware / dependencies must both be either statically or dynamically linked, but never mixed.

For a simple rmw_zenoh_cpp publisher this will result in a 170M binary. With the following compiler optimizations, you can drop this to around 47M:

```
$ bazel build //:example_ros_publisher_cc --dynamic_mode=off --@rosdistro//:rmw=rmw_zenoh_cpp -c opt \
    --copt=-Os --copt=-fdata-sections  --copt=-ffunction-sections --copt=-fno-asynchronous-unwind-tables \
        --linkopt=-Wl,--gc-sections --linkopt=-s  --strip=always
$ du -hs bazel-bin/example_ros_publisher_cc
47M     bazel-bin/example_ros_publisher_cc
```

For a simple rmw_fastrtps_cpp publisher this drops even further to 30M:

```
$ bazel build //:example_ros_publisher_cc --dynamic_mode=off --@rosdistro//:rmw=rmw_fastrtps_cpp -c opt \
    --copt=-Os --copt=-fdata-sections  --copt=-ffunction-sections --copt=-fno-asynchronous-unwind-tables \
        --linkopt=-Wl,--gc-sections --linkopt=-s  --strip=always
$ du -hs bazel-bin/example_ros_publisher_cc
30M     bazel-bin/example_ros_publisher_cc
```

For a simple rmw_cyclonedds_cpp publisher this drops even further to 8.8M:

```
$ bazel build //:example_ros_publisher_cc --dynamic_mode=off --@rosdistro//:rmw=rmw_cyclonedds_cpp -c opt \
    --copt=-Os --copt=-fdata-sections  --copt=-ffunction-sections --copt=-fno-asynchronous-unwind-tables \
        --linkopt=-Wl,--gc-sections --linkopt=-s  --strip=always
$ du -hs bazel-bin/example_ros_publisher_cc
8.8M     bazel-bin/example_ros_publisher_cc
```

# Remote caching

For every build action (e.g., compiling a C++ file or running a code generator), Bazel computes a unique hash based on its inputs (source files, dependency headers, compiler options, environment variables, and tools). If the output was already generated for the same inputs, Bazel can just reuse the cached output instead of recomputing it. 

The RCR is configured by default to use a hermetic clang toolchain provided by the [llvm](https://github.com/hermeticbuild/hermetic-llvm) module. Provided two machines share an architecture (e.g., aarch64 or x86_64), they will produce the same hash for the same inputs. So your code will build identically on any two machines.

Bazel can be configured to use a remote cache. What this does is allow multiple machines to share a common build and test cache. So, put simply, if somebody has built a particular target, and then you build that same target, your machine can just pull the build outputs from the remote cache instead of having to recompute them. This can provide substantial speedups for a fresh checkout.

The RCR continuous integration workflow uses a remote cache offered by Intrinsic at https://storage.googleapis.com/intrinsic-opensource-buildcache. Every commit to the main branch is built by our continuous integration system for both x86_64 and aarch64 and the outputs are pushed to this shared cache. As a result, ROS modules will build very quickly after a fresh checkout.

# Agentic workflows

Repository maintainers can use two automated GitHub Actions workflows powered by the Gemini CLI:

1. **Issue implementation (`gemini-implement` label)**
   - Add the `gemini-implement` label to an issue.
   - The workflow creates an implementation branch, applies changes following the repository skills in `.agent/skills/`, and opens a pull request for review.

2. **Interactive assistance (`@gemini-bot` mention)**
   - Mention `@gemini-bot` in an issue, pull request comment, or pull request review.
   - The workflow responds to questions, investigates build/test failures, or pushes follow-up commits to address review feedback.

*Note: Execution is restricted to repository maintainers (`OWNER`, `MEMBER`, or `COLLABORATOR`) and requires the `GEMINI_API_KEY` repository secret.*

# Contributing

If you would like to contribute code or tooling updates to this project, please refer to [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines, licensing details, and commit signing requirements. 
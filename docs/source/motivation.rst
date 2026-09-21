Motivation
==========

`Bazel <https://bazel.build>`__ is an open-source build tool that originated within Google. It supports many different programming languages, and its goal is to build large projects with efficiency and reliability.

By enforcing the compilation of all code **from source** within a strict `sandbox <https://bazel.build/docs/sandboxing>`__ environment, Bazel eliminates the classic ``"it works on my machine"`` issues caused by operating system and dependency discrepancies between code on different machines, e.g. engineering, CI, and production.

This cohesive paradigm replaces the fragile, environment-dependent workspace model with a rigorous dependency graph, unlocking advanced capabilities like `remote caching <https://bazel.build/remote/caching>`__ and `remote execution <https://bazel.build/remote/rbe>`__ to drastically **accelerate build times** while ensuring that tests and binaries are **reproducible**.

Traditionally, Bazel has been used in large monorepos, but with the introduction of `Bazel modules <https://bazel.build/external/module>`__ it has become considerably easier to use Bazel in smaller, more distributed projects. Many popular projects already have corresponding Bazel modules hosted in the `Bazel Central Registry (BCR) <https://registry.bazel.build>`__. The existence of this mechanism makes Bazel an appealing supplementary build system for ROS.

The `ROS Central Registry (RCR) <https://github.com/openrobotics/ros-central-registry>`__ is similar to the BCR, acting as a central registry for hosting Bazel build modules for ROS packages. Adding support for an existing or new ROS package is as simple as following our :ref:`developer_guide` and opening up a pull request to this repository.
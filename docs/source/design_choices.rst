Design choices
==============

This page is targeted at those who are interested in learning more about the key design decisions that the team made when developing the ROS Central Registry.

Versioning
----------

Let's say we are creating a new release for the ``kilted/2026-01-22`` release tag. In this release the ``rclcpp`` package moved from ``29.5.5-1`` to ``29.5.6-1``. Bootstrapping will result in a new Bazel module for ``rclcpp`` with the version ``kilted.29.5.6-1``. Assuming we have to fix some build errors as a result of the code change, the released version will be ``kilted.29.5.6-1.rcr.1``, with ``.rcr.1`` signalling that a patch was needed, and this will be tagged in the first release of package ``rosdistro`` with version ``kilted.2026-01-22.rcr.1``.

.. code-block:: shell

    multiple_version_override(
        module_name = "sensor_msgs",
        versions = [
            "jazzy.29.5.6-1.rcr.1",
            "kilted.29.5.6-1.rcr.1",
        ],
    )

Weekly patch rollup
~~~~~~~~~~~~~~~~~~~

Patches to individual packages land continuously through the week rather than as one big release cut. The workflow is split into a developer-facing step, run locally as many times as needed, and a weekly rollup, run once by CI.

During the week, a developer fixes one package at a time:

.. code-block:: shell

    bazel run //tools/ci:setup_workspace -- --release=lyrical.2026-06-08.rcr.2
    bazel run //tools/ci:vendor_modules -- rclcpp
    # ... edit workspace/vendor/rclcpp+/ in place ...
    bazel run //tools/ci:create_patch -- rclcpp

``create_patch`` diffs the edit against raw upstream (not the currently-patched version -- every ``.rcr.N`` of a package's patches/overlay describe a transformation relative to the *same* raw upstream archive, not an incremental delta from ``.rcr.(N-1)``) and creates a single new module version, e.g. ``rclcpp@32.0.0-1.rcr.1`` -> ``rclcpp@32.0.0-1.rcr.2``. This becomes the developer's PR -- it never touches any other package.

"Immutable" here means immutable once it's reached a shared branch (checked locally via git, against ``main`` by default) -- a version that only exists on the developer's own branch is freely amendable in place instead, so iterating on the same not-yet-merged patch doesn't mint a new ``.rcr.N`` per edit. See the ``create-patch`` and ``rebase-module`` skills.

Because per-package patches land independently and asynchronously, ``setup_workspace`` always resolves every package to its true latest published version, loudly, via ``single_version_override``:

.. code-block:: shell

    OVERRIDE: rclcpp pinned at 32.0.0-1.rcr.1 by release lyrical.2026-06-08.rcr.1,
              but a newer patch 32.0.0-1.rcr.2 already exists -- overriding workspace to use it.

This is what keeps two developers patching the same package in the same week from colliding on the same next version number: whichever workspace is set up second sees the first developer's already-merged patch as the new "latest" and increments from there, rather than recomputing the same version the first developer already claimed.

Once a week, ``//tools/ci:rollup_patches`` aggregates whatever leaf patches landed: for every package with a newer published version than what the current ``ros`` release references, it transitively bumps every package that depends on it -- purely a ``bazel_dep`` pin update, no content change -- so ``rclcpp_action@...rcr.1`` becomes ``rclcpp_action@...rcr.2`` simply because ``rclcpp`` moved. It then regenerates the top-level ``ros`` module to reference the new versions, runs the result through the full CI matrix, and auto-merges on success (otherwise the PR is assigned for manual review). See ``.github/workflows/weekly_rollup.yml``.

Interfaces
----------
The ROS Central Registry adopts many of the aspects of `rules_ros2 <https://github.com/mvukov/rules_ros2>`__ with a few key differences. The most obvious one is that interface dependencies are declared at the message level, not the package level. As an example, consider adding the following new message ``ExampleMessage.msg`` that depends on two common interfaces, ``sensor_msgs/CompressedImage`` and ``std_msgs/String``.

.. code-block:: python

    std_msgs/String message
    sensor_msgs/CompressedImage back_left
    sensor_msgs/CompressedImage back_right
    sensor_msgs/CompressedImage front_left
    sensor_msgs/CompressedImage front_right

When you create a Bazel target for this interface, you must declare the dependencies at the message level, and not the package level. This allows the IDL generators -- which convert this language-neutral interface description into language-specific code -- to generate exactly what is needed for the target, without any extra code that is not used. This makes for faster builds and smaller build products.

.. code-block:: python

    load("@ros//:rules.bzl", "ros_interface")

    ros_interface(
        name = "ExampleMessage",
        src = "ExampleMessage.msg",
        deps = [
            "@sensor_msgs//msg:CompressedImage",
            "@std_msgs//msg:String",
        ],
    )

Other differences are that we have -- as best as possible -- copied the rule semantics from protocol buffers (for example ``cc_ros_library`` is the C++ bindings for ROS interfaces in the same way ``cc_proto_library`` is the C++ bindings for protocol buffer messages) and used bare language rules (``cc_binary`` instead of ``ros_cc_binary``) to avoid any opaqueness in our design.

.. code-block:: python

    load("@rosidl_generator_cpp//:rules.bzl", "cc_ros_library")
    load("@rules_cc//cc:defs.bzl", "cc_binary")

    cc_ros_library(
        name = "example_ros_cc_msgs",
        deps = [
            "//msg:ExampleMessage",
        ],
    )

    cc_binary(
        name = "example_ros_publisher_cc",
        srcs = ["ros/example_ros_publisher.cc"],
        deps = [
            "@rclcpp",
            ":example_ros_cc_msgs"
        ],
    )

Shared libraries
----------------

Before the ``cc_shared_library`` rule was introduced, shared libraries had to be built using ``cc_binary`` with the ``linkshared = True`` attribute. This was not ideal because it meant that the shared library would be built as a binary, which is not what we want. It also meant that we had to manually link the shared library to the binary, rather than letting Bazel manage that dependency for us.

Runtime data
------------

One of the key differences between a CMake-based build and a Bazel-based build for ROS is how runtime data is handled. In a CMake build, runtime data is typically installed to a fixed location (for example to the ``install`` folder in a ROS workspace) with an ``INSTALL`` function. When you source ``install/setup.bash``, it automatically adds the ``install`` folder to your ``AMENT_PREFIX_PATH`` environment variable. Each client library then relies on a language-specific ``ament_index`` package to provide something like a ``get_package_share_directory(package_name)`` function to access data.

The issue with the CMake approach is that unrelated packages (not just dependencies and the current package) can install data into the same directory. This can cause conflicts and couples the behavior of the node to an execution context (i.e. not hermetic), which can in turn cause nondeterministic failures.

Bazel resolves this problem using ``runfiles``. What this looks like in practice is that whenever a target is built, every data dependency it needs is listed in its ``data`` attribute. This ``data`` attribute is then used to create a ``runfiles`` tree, which is essentially a set of symbolic links to the underlying data files. This makes the build hermetic and prevents conflicts between unrelated packages.

To avoid having to change all the code in ROS to understand Bazel runfiles, we have modified the ``ament_index`` package for each language to treat the root of the runfiles folder as the prefix path if the ``AMENT_PREFIX_PATH`` environment variable is unset. In a hypothetical ``example_project``, we encapsulate data with a ``ros_data`` rule, which serves to recreate the ament index folder layout within the runfiles tree of a specific binary. 

.. code-block:: python

    load("@ros//:rules.bzl", "ros_data")
    load("@rules_cc//cc:defs.bzl", "cc_library")

    cc_library(
        name = "util_library",
        hdrs = ["include/example_project/util.hh"],
        srcs = ["src/util.cc"],
        includes = ["include"],
    )

    ros_data(
        name = "data",
        data = [
            "config/default.yaml",
            ":util_library",
            "@gtsam//:gtsam",
        ],
    )

    cc_binary(
        name = "example_ros_publisher_cc",
        srcs = ["ros/example_ros_publisher.cc"],
        data = [
            ":data",
            "@ament_index_cpp"
        ],
    )

When you run ``bazel run //:example_ros_publisher_cc``, the ``example_ros_publisher_cc.runfiles`` directory is created, which organizes the libraries and binaries into a common ``lib`` folder, and the headers and shared data into ``include`` and ``share`` folders respectively, organized by package.

::

    example_project/
    └── bazel-bin/
        ├── example_ros_publisher_cc
        └─── example_ros_publisher_cc.runfiles/
            ├── include/
            │   └── example_project/ 
            │       └── util.hh
            ├── lib/
            │   ├── libutil_library.so
            │   └── gtsam
            └── share/
                └── example_project/
                    └── config/
                        └── default.yaml


This illustrates the principle. In practice, the rule is more complex because it also has to traverse the dependency chain to bring in files for the transitive dependencies of the includes.


Python modules
--------------

The standard way to handle Python dependencies in Bazel is to use the ``pip.bzl`` extension from `rules_python <https://github.com/bazelbuild/rules_python>`__ to parse a ``requirements_lock.txt`` file and download, compile and expose Python modules as Bazel targets. This is done using the ``pip_install`` rule. In practice, this involves adding something like this from within a ``MODULE.bazel`` file:

.. code-block:: python

    bazel_dep(name = "rules_python", version = "2.2.0")

    ...

    pip = use_extension("@rules_python//python/extensions:pip.bzl", "pip")
    pip.parse(
        hub_name = "pip_deps",
        python_version = "3.12",
        requirements_lock = "//:requirements.txt",
    )
    use_repo(pip, "pip_deps")

Then, from any build file you can access the Python modules as if they were regular Bazel targets.

.. code-block:: python

    load("@rules_python//python:defs.bzl", "py_binary")
    load("@pip_deps//:requirements.bzl", "requirement")

    py_binary(
        name = "baz",
        srcs = ["baz.py"],
        main = "baz.py",
        deps = [
            requirement("numpy"),
        ],
    )

Relying on modules having their own ``requirements_lock.txt`` is antithetical to the ROS philosophy of having a single source of truth for operating system and Python dependencies.

More importantly, it is a recipe for disaster because it means that different Bazel modules can import different versions of the same Python module. At runtime, both Python module versions will be available in the runfile tree of any target that depends on both Bazel modules. The version that is ultimately selected is the one which appears last in the ``PYTHONPATH`` environment variable. This can cause conflicts and nondeterministic failures, and should be avoided.

To fix this issue, we have centralized the Python dependency management in the ``rosdistro`` Bazel module. This means that each ROS release has its own global ``requirements_lock.txt`` file, which is used to download, compile and expose Python modules as Bazel targets for the entire ROS package ecosystem at the time of release. It then provides this simple extension:

.. code-block:: python
   :caption: rosdistro/bazel/python/extensions.bzl

    load("@rules_python//python/extensions:pip.bzl", "pip")

    def _pip_ros_impl(ctx):
        # This is a 'no-op' logic-wise, but it allows Bazel to see
        # the repos that this extension 'claims' to provide.
        pass

    # This extension essentially acts as a bridge
    pip_ros = module_extension(implementation = _pip_ros_impl)


Now that this extension is available, we can modify any ROS package to reference a specific ``rosdistro`` release and use the "pass-through" module extension to access the pip deps:

.. code-block:: python
   :caption: MODULE.bazel

    bazel_dep(name = "rosdistro", version = "rolling/2026-01-26")

    pip_ros = use_extension("@rosdistro//bazel/python:extensions.bzl", "pip_ros")
    use_repo(pip_ros, "pip_ros")

This makes usage similar to how it would look if a module-specific pip repository was being used:

.. code-block:: python
   :caption: BUILD.bazel

    load("@rules_python//python:defs.bzl", "py_binary") 
    load("@pip_ros//:requirements.bzl", "requirement")

    py_binary(
        name = "baz",
        srcs = ["baz.py"],
        main = "baz.py",
        deps = [
            requirement("numpy"),
        ],
    )
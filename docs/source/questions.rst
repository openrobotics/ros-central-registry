FAQs
====

Why not use a module extension?
+++++++++++++++++++++++++++++++
If you've been working with Bazel for a while, you might have come across the ``pip`` or ``crates`` extensions in ``rules_python`` or ``rules_rust`` respectively. You might wonder why we don't support a usage pattern that offers something like the following for convenience:

.. code-block:: python
   :caption: MODULE.bazel

   bazel_dep(name = "rosdistro", version = "rolling.2026-02-19.rcr.1")

   ...

   load("@rosdistro//bazel:ros.bzl", "ros")
   ros.load("sensor_msgs")
   ros.load("rclcpp")
   use_repo(ros, "ros")


Unfortunately, this is not possible because of the order in which Bazel phases its execution. In the first resolution phase the ``MODULE.bazel`` file is parsed and dependencies are resolved. In the second extension phase the module extensions are loaded and executed. In summary, we wouldn't be able to distribute ROS packages as Bazel modules, and therefore we'd lose the dependency and versioning benefits. Instead, we'd have to resort to the older ``http_archive`` or ``git_repository`` rules.

How do I get a package into the registry?
+++++++++++++++++++++++++++++++++++++++++++++

We only support packages that are present in the upstream ``rosdistro`` repository. If you'd like to see a package in the registry, please open an issue against the `rosdistro <https://github.com/ros/rosdistro>`__ repository to request its inclusion.

If your package was recently added to ``rosdistro``, then you will need to wait for the next release to bootstrap the module. Once it has been bootstrapped, you can follow the "patching" instructions in the `developer guide <developer_guide.html>`__ to create a local development environment in which to iterate on your module. Once you have a module, you can open a pull request against the RCR. After it merges, you should be able to use the module in your own projects. The next weekly distribution rollup will then automatically pick up your patch and include it in the next release, without you needing to do anything further.

How do I update your documentation?
+++++++++++++++++++++++++++++++++++

You can check out the RCR repo and run the following command to preview the documentation locally:

.. code-block:: shell 

   bazel run //docs:preview

This will build the documentation and serve it locally on port 8000. You can then open `http://localhost:8000 <http://localhost:8000>`__ in your browser to view the documentation. It will update automatically as you make changes to the documentation source files in the ``docs`` directory of the repository. Once you are satisfied with your changes, you can open a pull request against the RCR.


How do I deploy build products to a robot?
++++++++++++++++++++++++++++++++++++++++++

Right now we don't have a solid answer for this. Since we build everything from source using a hermetic toolchain, we should in principle be able to cross-compile for different architectures.

However, packaging remains an open problem. Currently, we think that a (yet to be written) ``ros_underlay`` rule might be the right answer to this problem. This rule would collect binaries, libraries, and data files from the workspace into a tarball whose file structure resembles a ROS underlay.  One could then write an application-specific rule that takes this tarball and deploys it to a robot. 

.. code-block:: python 

   ros_underlay(
      name = "my_underlay",
      executables = ["@example//:foo_node"],
      libraries = ["@example//:bar_component"],
      data = ["@example//:baz_data"],
   )

If you have any ideas or suggestions about how we might improve this workflow, please reach out to us.

How do I use LibTorch or CUDA?
++++++++++++++++++++++++++++++

LibTorch (PyTorch's C++ library, 2.14.1) is built from source with the same hermetic Clang/libc++ toolchain as everything else, rather than downloaded as the prebuilt archive that upstream's ``libtorch_vendor`` fetches. ROS packages link it through ``@rosdistro//cc:torch`` (also aliased as ``@libtorch_vendor//:torch``), a single shared ``libtorch.so``.

The default build is **CPU-only**: ``torch_conversions`` and its tests build and run everywhere, while the CUDA packages (``cuda_buffer``, ``cuda_buffer_backend``) are skipped as incompatible. Opt into CUDA on Linux with ``--config=cuda``:

.. code-block:: shell

   bazel build --config=cuda @cuda_buffer_backend//... @torch_conversions//...

This compiles CUDA with Clang (not ``nvcc``) against a hash-pinned CUDA 12.8.1 redistribution downloaded by Bazel, so no CUDA installation, GPU or driver is needed to *build*. Binaries load ``libcuda.so.1`` from the host's NVIDIA driver at run time. Device code targets Hopper (``sm_90``) plus ``sm_90`` PTX by default; build for your own GPU by overriding the architecture list in your ``user.bazelrc``:

.. code-block:: shell

   build:cuda --@rules_cuda//cuda:archs=sm_89

Tests that move data through GPU memory (``test_cuda_buffer`` and the ``cuda_image_*`` launch tests) are tagged ``manual`` and ``requires-gpu``; run them explicitly on a machine with an NVIDIA GPU.

Some differences from upstream's prebuilt LibTorch are worth knowing about: there is no MKL/LAPACK (CPU ``linalg`` operations raise at run time) and no cuDNN or FlashAttention. The MPS (Apple), Vulkan, ROCm and Intel XPU backends are present but switched off; see the comments at the top of the staged ``libtorch`` module's ``overlay/BUILD.bazel`` for the flags that enable them.

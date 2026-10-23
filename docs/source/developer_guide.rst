.. _developer_guide:

Developer guide
===============

Overview
++++++++

ROS is a federated ecosystem of packages, with no central authority controlling the versioning or release of individual packages. However, the ROS Team maintains several **distributions** of ROS packages that are tied to specific operating systems. And, periodically they release updated package version collections for a distribution, which is called a **release**.

Releases are made via the `rosdistro <https://github.com/ros/rosdistro>`__ repository. The open source community opens pull requests against this repository to update package versions. Every month or so a ROS maintainer picks a specific and well-tested commit in this repository to tag with a release version. For example the `kilted/2025-12-12 <https://github.com/ros/rosdistro/tree/kilted/2025-12-12>`__ tag is a release of the **kilted** distribution on 2025-12-12.

The ROS Central Registry lags behind rosdistro releases, because developers introduce breaking changes, and we will occasionally need to patch upstream source code to make the collection of packages build and pass tests in Bazel.

The rough process that we follow is:
    (1) Automatically bootstrap a new distro release as a copy of the previous one, as soon as upstream ``rosdistro`` tags it.
    (2) Fix, one package at a time, any generated modules that have build or test failures.
    (3) Automatically roll up whatever per-package patches landed that week into a new distribution release.
    (4) Repeat step (2) for any bugs identified after a release -- patches merge continuously and independently, rather than as part of a coordinated release cut.

Bootstrapping
+++++++++++++

Bootstrapping a new distro release is fully automated: you should never need to run it yourself. Every night, ``.github/workflows/nightly_bootstrap.yml`` scans ``rosdistro`` for any tag newer than what's already bootstrapped in this registry and, for each one, runs:

.. code-block:: shell

   bazel run //tools/ci:bootstrap_release -- --distro rolling

Under the hood this reads ``distribution.yaml`` and each package's ``package.xml`` directly from the tag (no ``rosdep``/``rosinstall_generator``) to resolve every package's upstream version, source archive, and dependencies. It then creates a new Bazel module version in ``modules/`` for every package whose upstream version changed since the last bootstrap; packages that didn't change are left referencing whatever version they're already at. It does this using these rules:
    1. If a package version has not changed, it does nothing.
    2. If a package already exists in the registry, it copies the ``source.json``, patches, and overlays from its previous version, updating only the upstream archive URL and integrity hash to the new version.
    3. If a package has never existed in the registry before, it creates a ``0.0.0`` placeholder stub with no dependencies -- a resolvable module with nothing else in it, ready to be fleshed out the first time someone actually needs to patch it.

Each newly-bootstrapped package is migrated straight to a ``.rcr.0`` patch version, so, for example, ``rosdistro``'s Python/``ament``/``cc`` build-rule overlay survives every new distro date without anyone re-patching it by hand.

So, continuing with our example, bootstrapping the new ``rolling`` tag will look at the ``rclcpp`` package and see that it has moved from version ``30.1.3-1`` to ``30.1.4-1``. After applying the rules above, the folder layout will look something like this:

::

    ros-central-registry/
    ├── ...
    └── modules/
        ├── ...
        ├── rclcpp/
        │   ├── ...
        │   ├── 30.1.3-1.rcr.2/                # previously-patched version
        │   │   ├── overlay/
        │   │   │   └── BUILD.bazel
        │   │   ├── patches/
        │   │   │   └── 0001-fix-build-error.patch
        │   │   ├── MODULE.bazel
        │   │   └── source.json
        │   ├── 30.1.4-1.rcr.0/                # newly-bootstrapped version, carrying
        │   │   ├── overlay/                   # forward the same patches/overlay
        │   │   │   └── BUILD.bazel
        │   │   ├── patches/
        │   │   │   └── 0001-fix-build-error.patch
        │   │   ├── MODULE.bazel
        │   │   └── source.json
        │   └── metadata.json
        └── ros/
            ├── ...
            └── rolling.2026-01-21/            # the new umbrella release module
                └── MODULE.bazel

If a freshly-bootstrapped package doesn't actually build or pass its tests, that's a normal bug -- patch it the same way as any other package, per the next section.

Patching
++++++++

Firstly, generate a throwaway Bazel workspace for the release you want to patch:

.. code-block:: text

   bazel run //tools/ci:setup_workspace -- --release=lyrical.2026-10-05.rcr.0

This creates a ``workspace/`` directory (gitignored, safe to regenerate at any time) with a ``MODULE.bazel`` that pins every package in the release, plus a ``.bazelrc`` already configured with ``--vendor_dir=vendor``.

Next, change into that workspace and vendor the module(s) you want to patch. This follows each module's ``source.json`` to download the upstream source code, apply any existing patches, and generate the vendor directory.

.. code-block:: text

   cd workspace
   bazel run //tools/ci:vendor_modules -- rclcpp

This creates a vendor directory with a copy of the upstream source code, existing patches, and overlays already applied.

::

    ros-central-registry/
        └── workspace/
            ├── vendor/
            │   ├── ...
            │   └── rclcpp+/                # This is where you make your changes.
            ├── .bazelrc
            └── MODULE.bazel

Because ``--vendor_dir=vendor`` is already set in ``.bazelrc``, you can build and test directly:

.. code-block:: text

   bazel build @rclcpp//...
   bazel test  @rclcpp//...

You can now iterate on the source code under ``vendor/rclcpp+/`` -- patching source files, adding or editing ``BUILD.bazel`` files -- until you get the result you want.

Once you're happy with the fix, roll it up into a new module version:

.. code-block:: text

   cd ..
   bazel run //tools/ci:create_patch -- rclcpp

This diffs your edits against raw upstream (not the currently-published version -- every ``.rcr.N`` of a package describes a transformation relative to the same raw upstream archive, not an incremental delta from ``.rcr.(N-1)``), and writes the result as a single new module version, e.g. ``rclcpp@32.0.0-1.rcr.1`` -> ``rclcpp@32.0.0-1.rcr.2``.

If you've vendored and edited more than one package and aren't sure which ones you actually changed, omit the module name -- ``create_patch`` will auto-detect every vendored package with real local edits and ask for one confirmation before rolling all of them up:

.. code-block:: text

   bazel run //tools/ci:create_patch

::

    ros-central-registry/
    └── modules/
        ├── ...
        └── rclcpp/
            ├── ...
            ├── 32.0.0-1.rcr.1/                 # original version
            │   ├── overlay/
            │   │   └── BUILD.bazel
            │   ├── patches/
            │   │   └── 0001-fix-build-error.patch
            │   ├── MODULE.bazel
            │   └── source.json
            ├── 32.0.0-1.rcr.2/                 # new patch version
            │   ├── overlay/
            │   │   ├── tests/
            │   │   │   └── BUILD.bazel         # new tests added by you
            │   │   └── BUILD.bazel             # new build files added by you
            │   ├── patches/
            │   │   ├── 0001-fix-build-error.patch
            │   │   └── 0002-additional-fix.patch # new fix to source code
            │   ├── MODULE.bazel
            │   └── source.json                 # updated patches, overlays and hashes
            └── metadata.json                   # updated to list the new version

You are now in a position to open a PR against the ROS Central Registry containing exactly the new module version directory (e.g. ``modules/rclcpp/32.0.0-1.rcr.2/``) and the corresponding update to ``modules/rclcpp/metadata.json``. Never touch an existing version directory or any other package's files -- CI enforces this and will reject the PR otherwise. Your patch will be picked up automatically by the next weekly distribution rollup; there's no separate step to "release" it yourself.

Interfaces
++++++++++

ROS interface files (``.msg``, ``.srv``, ``.action``) are declared with the ``ros_interface`` Bazel rule in a ``BUILD.bazel`` file. Unlike most other Bazel targets, the ``BUILD.bazel`` declaring a ``ros_interface`` must live in the *same directory* as the interface file it references (i.e. inside the package's ``msg``, ``srv``, or ``action`` folder, not one level up) -- the underlying IDL codegen tooling reconstructs the interface's path relative to that ``BUILD.bazel``'s own directory, so moving it breaks the build. See the ``action_msgs`` module for a working example.

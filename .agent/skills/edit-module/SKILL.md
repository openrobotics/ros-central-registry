---
name: edit-module
description: Add, fix, or patch Bazel modules in the ROS Central Registry. Describes the end-to-end setup-vendor-edit-patch workflow, overlay rules (including ros_interface files), licensing rules, dependency constraints, and MODULE.bazel validation rules.
---

Editing, fixing, or patching Bazel modules in the ROS Central Registry (RCR) follows a structured setup, vendor, edit, and patch pipeline. You must always use the automated tools (`setup_workspace`, `vendor_modules`, and `create_patch`) rather than manually creating or editing files under `modules/` directly.

## The Workflow

### 1. Set Up a Throwaway Workspace
Generate a local, gitignored Bazel workspace for the targeted release (e.g. `lyrical.2026-06-08.rcr.2`).
```shell
bazel run //tools/ci:setup_workspace -- --release=<release-name>
```
For more details, see the `setup-workspace` skill.

### 2. Vendor the Module
Check out the package's real upstream source with all existing patches/overlays already applied into `workspace/vendor/<module-name>+/`.
```shell
cd workspace
bazel run //tools/ci:vendor_modules -- <module-name>
```
> [!NOTE]
> You might need to vendor additional dependencies (other ROS packages) required by your target module if they aren't fully implemented or are only partially implemented yet. You can vendor multiple packages at the same time:
> ```shell
> bazel run //tools/ci:vendor_modules -- package_a package_b
> ```
For more details, see the `vendor-module` skill.

### 3. Make Edits and Test
Modify files, write new files, or configure build files inside `workspace/vendor/<module-name>+/`. Test your changes directly using Bazel:
```shell
bazel build @<module-name>//...
bazel test @<module-name>//...
```

### 4. Create the Patch
Roll up all your edits relative to raw upstream into a new module version directory under `modules/<package>/<new-version>/`:
```shell
cd ..
bazel run //tools/ci:create_patch -- <module-name>
```
If the current version has already reached `main`, this increments the `.rcr.N` patch version (e.g. `1.0.0-1.rcr.1` -> `1.0.0-1.rcr.2`); if the version only exists on your branch, it amends that version in place instead (so re-running this after more edits to a not-yet-merged patch doesn't mint another version). Either way it updates `metadata.json` to include the version and auto-generates:
- `source.json` (with updated patch/overlay integrity hashes)
- `overlay/` (for brand-new files like `BUILD.bazel`)
- `patches/` (diffs of files modified in place)

If you touched multiple packages, running `bazel run //tools/ci:create_patch` with no arguments will roll up all changed modules at once.

> [!NOTE]
> While a PR can contain changes/additions for more than one module, large PRs affecting multiple unrelated modules are discouraged. Prefer submitting smaller, focused PRs per module (or per closely-related set of modules) to make reviews and CI runs more manageable.

### 5. Recovering From a Stale Workspace
If `create_patch` refuses because `modules/<package>/<version>/` changed on disk since you vendored it (e.g. a `git pull` brought in a concurrent edit), or you otherwise need to re-baseline against the current `modules/` state without losing uncommitted edits, see the `rebase-module` skill instead of re-running `setup-workspace`/`vendor-module` by hand.

---

## Writing `BUILD.bazel` Overlays

When creating or modifying a package's `BUILD.bazel` file, keep the following guidelines in mind:

### 1. Declaring Licensing
Every newly authored or hand-edited `BUILD.bazel` file should declare the package's license using `rules_license`. Ensure the license matches the package's actual upstream license (defined in its `package.xml` `<license>` tag or LICENSE file).
```python
load("@rules_license//rules:license.bzl", "license")

package(
    default_applicable_licenses = [":license"],
    default_visibility = ["//visibility:public"],
)

license(
    name = "license",
    license_kinds = [
        "@rules_license//licenses/spdx:BSD-3-Clause", # Match package.xml
    ],
)
```

### 2. ROS Interface Files (`.msg`, `.srv`, `.action`)
ROS interface files must be declared using the `ros_interface` Bazel rule.
> [!IMPORTANT]
> The `BUILD.bazel` declaring `ros_interface` must live in the **same directory** as the interface files (e.g. inside the package's `msg/`, `srv/`, or `action/` directory, rather than the root directory). The codegen tooling reconstructs paths relative to the build file's folder, so placing the `BUILD.bazel` file higher up will break the build.

To generate the code bindings and ament_index for these interfaces, check the package dependencies (usually in `package.xml` or `MODULE.bazel`):
- If the package depends on `rosidl_core_generators`, load and call `core_generators`.
- If the package depends on `rosidl_default_generators`, load and call `default_generators`.

These macros are declared in the package's root `BUILD.bazel` file, referencing the complete list of interfaces:
```python
load("@rosidl_default_generators//:defs.bzl", "default_generators")

default_generators(
    package_xml = "package.xml",
    deps = [
        "//msg:GoalInfo",
        "//msg:GoalStatus",
        "//srv:CancelGoal",
    ],
)
```
This automatically sets up all language targets (C++, Python, etc.) and an `ament_index` for the package.

Finally, declare an `ament_package` target bundling this package by listing upstream `ament_package` targets of all dependencies:
```python
load("@rosdistro//ament:defs.bzl", "ament_package")

ament_package(
    name = "ament_package",
    package_xml = "package.xml",
    deps = [
        ":ament_index",
        # List other package dependencies' ament_package targets here...
    ],
)
```

For reference implementations, inspect the `action_msgs` or `actuator_msgs` modules.

### 3. C/C++ Libraries and Shared Libraries
For package stability, mock testing, and minimizing the runfile footprint, RCR requires C or C++ libraries to expose both:
- A static target: `cc_library` named `:<name>_library` (containing sources/headers/defines).
- A dynamic shared library target: `cc_shared_library` named `:<name>` (exporting/wrapping the static target).

```python
cc_library(
    name = "my_lib_library",
    srcs = glob(["src/**/*.cpp"]),
    hdrs = glob(["include/**/*.hpp"]),
    includes = ["include"],
    deps = [
        "@rclcpp//:rclcpp_library",
    ],
)

cc_shared_library(
    name = "my_lib",
    dynamic_deps = [
        "@rclcpp//:rclcpp",
    ],
    exports_filter = [":my_lib_library"],
    deps = [":my_lib_library"],
)
```

#### Transitive Dynamic Dependency Collection
To ensure binaries (e.g. `cc_binary`) and tests (e.g. `cc_test`) are linked correctly, you must call `collect_transitive_dynamic_deps` right before defining the binary/test targets.
- Load the helper macro:
  ```python
  load("@rosdistro//cc:defs.bzl", "collect_transitive_dynamic_deps")
  ```
- Declare the dependency map and call `collect_transitive_dynamic_deps`:
  ```python
  # Map dynamic targets (keys) to their static library targets (values)
  TEST_DEPENDENCIES = {
      ":my_lib": ":my_lib_library",
      "@rclcpp//:rclcpp": "@rclcpp//:rclcpp_library",
  }

  collect_transitive_dynamic_deps(
      name = "transitive_dynamic_deps",
      dynamic_deps = TEST_DEPENDENCIES.keys(),
      visibility = ["//visibility:private"],
  )
  ```
- Pass `transitive_dynamic_deps` as `dynamic_deps` and use the static libraries under `deps`:
  ```python
  cc_test(
      name = "my_test",
      srcs = ["test/my_test.cpp"],
      dynamic_deps = [":transitive_dynamic_deps"],
      deps = TEST_DEPENDENCIES.values() + [
          "@rosdistro//cc:googletest",
      ],
  )
  ```

For reference implementations, inspect the `rosbag2_cpp` or `filters` modules.

### 4. Writing Test Targets and Upstream Parity

When porting tests to Bazel (`cc_test`, `py_pytest`):
- **Maintain Upstream Test Parity (Never Hallucinate Tests)**: Do not invent or hallucinate synthetic test files (e.g. writing custom `test_utest.cpp` or `test_utest.py`) if they are not in the upstream package. We preserve and package upstream code; we do not expand test suites arbitrarily.
- **Port All Non-Integration Unit Tests**: Port all unit tests defined in upstream `CMakeLists.txt`. Only omit integration tests that require external hardware, running robot simulators, or non-hermetic external network connections.
- **No Hardcoded Environment Overrides**: Do NOT set `env = {"AMENT_PREFIX_PATH": ".", "LD_LIBRARY_PATH": "./lib"}` in test targets. These are configured globally in `.bazelrc`.
- **Multi-RMW & Platform Safety**:
  - **CycloneDDS discovery loops**: When tests poll for publisher/subscriber matching (e.g. `while (sub_->get_publisher_count() == 0)`), always call `executor_->spin_some()` inside the loop so CycloneDDS processes discovery events.
  - **Zenoh shutdown safety**: Never leave active ROS 2 publishers/subscriptions inside static or global singletons that destruct during program exit after `rclcpp::shutdown()`. Provide an explicit cleanup hook (e.g. `clearAllRegistries()`) in `TearDownTestSuite()` before `rclcpp::shutdown()` to avoid Zenoh Tokio runtime teardown panics.
  - **Standard C++ Portability**: Use portable C++ headers (e.g. `<cstdio>` and `<cstdlib>` instead of GNU-specific `<error.h>`).

---

## ROS Package Packaging with Ament (Ament Index & Ament Package)

Understand the distinct separation of responsibilities between `ament_index` and `ament_package`:
- `ament_index` prepares datasets and metadata for targets **inside** this package.
- `ament_package` bundles exported artifacts for **downstream** consumers (mirroring `cmake install`).

```python
load("@rosdistro//ament:defs.bzl", "ament_index", "ament_package")
```

### 1. The `ament_index` Rule
The `ament_index` target aggregates the package XML, libraries, plugins, URDF/Xacro models, configs, meshes, and transitively links the `ament_index` of all dependencies:
```python
ament_index(
    name = "ament_index",
    export_name = "package_name",
    data = glob([
        "config/**",
        "launch/**",
        "urdf/**",
    ]),
    libraries = [":package_name"], # libraries/plugins exported by this package
    package_xml = "package.xml",
    # Optional list of plugin XML configurations:
    plugins = ["plugin.xml"],
    deps = [
        # List the :ament_index target of every bazel_dep dependency
        "@dependency_a//:ament_index",
        "@dependency_b//:ament_index",
    ],
)
```

### 2. Passing to Targets (Data Dependency)
Feed `:ament_index` into the `data` attribute of any executables or test targets in the current package. This ensures the libraries, executables, and registered files appear correctly in the runfiles directory at runtime (which serves as the local `AMENT_PREFIX_PATH`):
```python
cc_test(
    name = "my_test",
    srcs = ["test.cpp"],
    data = [":ament_index"],
    deps = [...],
)
```

### 3. The `ament_package` Rule
At the end of the `BUILD.bazel` file, declare the `ament_package` rule **exactly once**. It acts as the final bundling rule for downstream consumers, depending on `:ament_index` and the `:ament_package` target of all dependencies:
```python
ament_package(
    name = "ament_package",
    headers = HEADERS,
    libraries = [":package_name"],
    package_xml = "package.xml",
    deps = [
        ":ament_index", # transitively pulls in all upstream dependencies' ament_package targets
    ],
)
```
> [!IMPORTANT]
> Internal targets within the package (such as tests or helper binaries) must **never** depend on `:ament_package`. They should depend on `:ament_index` (via `data`) or on direct library targets.


---

## Managing Dependencies

### 1. Non-ROS / Third-Party (BCR) Dependencies
Never declare new `bazel_dep` entries in a package's own `MODULE.bazel`. Instead:
1. Add the `bazel_dep` (and any module extensions/repository rules) to the `rosdistro` module's `MODULE.bazel`.
2. Wrap and expose the dependency in `modules/rosdistro/<version>/overlay/cc/BUILD.bazel` (e.g. wrapping it as a target like `@rosdistro//cc:<target>`).
3. Make the package depend on `@rosdistro//cc:<target>`.

This ensures all packages in a given distro release resolve to the exact same version of third-party dependencies.

### 2. Python Dependencies
Add Python packages to `rosdistro`'s `requirements.in`, then run `bazel run //:requirements.update` to update the locks. Do not edit `requirements.txt` or `requirements_windows.txt` by hand.

---

## MODULE.bazel Validation Rules

CI enforces that existing version directories are immutable once merged to `main`.
- **Allowed MODULE.bazel Edits**: The only acceptable modification to an existing `MODULE.bazel` file is the `version` argument being incremented by exactly one patch suffix (e.g., `1.0.0-1.rcr.1` to `1.0.0-1.rcr.2`). Any other change will fail validation.
- **`rosdistro` Exception**: The `rosdistro` module is exempt from this version-bump-only rule and allows general modifications to its `MODULE.bazel` (e.g., adding BCR dependencies).

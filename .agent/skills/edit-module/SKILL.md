---
name: edit-module
description: Add, fix, or patch Bazel modules in the ROS Central Registry. Describes the end-to-end setup-vendor-edit-patch workflow, core build-file principles (no canonical @@ repo references, explicit file lists over globs, minimal transitive deps, launch targets depending on the nodes they launch, cross-platform target naming without shared_lib_name or platform suffixes), overlay rules (including ros_interface files), licensing rules, dependency constraints, and MODULE.bazel validation rules.
---

Editing, fixing, or patching Bazel modules in the ROS Central Registry (RCR) follows a structured setup, vendor, edit, and patch pipeline. You must always use the automated tools (`setup_workspace`, `vendor_modules`, and `create_patch`) rather than manually creating or editing files under `modules/` directly.

## The Workflow

### 1. Set Up a Throwaway Workspace
Generate a local, gitignored Bazel workspace for the targeted release (e.g. `lyrical.2026-10-05.rcr.0`).
```shell
bazel run //tools/ci:setup_workspace -- --release=lyrical.2026-10-05.rcr.0
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

### 5. Commit (Signed Off) and Open the PR
Every commit you make must be signed off for the [Developer Certificate of Origin](https://developercertificate.org/). Always commit with `-s` so it gets a `Signed-off-by:` trailer matching the commit author's email:
```shell
git commit -s -m "<module>: <what changed>"
```
> [!IMPORTANT]
> This applies to **every** commit on the branch, including fixups and amends (`git commit -s --amend --no-edit`), not just the last one. A PR can't merge while any of its commits lacks a matching sign-off. If earlier commits are missing it, fix them with `git rebase --signoff <oldest-offending-sha>^`, and ask the user before force-pushing.

Before pushing, run the local lint and module checks and write the PR description from the repository's PR template. See the `setup-pull-request` skill for the exact commands and template rules.

### 6. Recovering From a Stale Workspace
If `create_patch` refuses because `modules/<package>/<version>/` changed on disk since you vendored it (e.g. a `git pull` brought in a concurrent edit), or you otherwise need to re-baseline against the current `modules/` state without losing uncommitted edits, see the `rebase-module` skill instead of re-running `setup-workspace`/`vendor-module` by hand.

---

## Core Principles for Build Files

These five rules apply to every `BUILD.bazel`, `.bzl`, and `MODULE.bazel` you author or edit — overlays, patches, and staged BCR modules alike. They take precedence over any example elsewhere in this skill or in existing modules that predate them.

### 1. Never use canonical (`@@`) repository references

Always reference other repositories by their **apparent** name (`@freeimage//:__subpackages__`), never by their canonical name (`@@freeimage+//:__subpackages__`, `@@//:...`, `@@rules_python++pip+pip_ros`).

> [!CAUTION]
> Canonical names are an internal Bazel implementation detail (the `+`/`++` suffixes are generated by bzlmod and can change between Bazel versions or module-graph shapes). They silently bypass the module's declared dependencies, so they hide missing `bazel_dep`s and can break without warning. `@@//` is especially dangerous: it means the **root** module, not the current one, so inside any module it matches none of that module's own targets.

If a repository isn't visible under an apparent name, that means it isn't a direct dependency — fix that properly by adding the `bazel_dep` (to `rosdistro`'s `MODULE.bazel` for packages; to the staged module's own `MODULE.bazel` under `bcr_staging/`) rather than reaching around it with `@@`.

There are a small number of genuinely legitimate uses — e.g. Starlark that rebuilds a label from a resolved `Label.repo_name` (which is always canonical), or string-normalizing code that merely *detects* an `@@` prefix. **You must get explicit sign-off from the human before introducing any new `@@` reference**, even in those cases. Explain why the apparent name cannot work and where the reference lives, and wait for approval; do not add it first and mention it afterwards.

### 2. Prefer exhaustive file lists over globs

List source, header, data, and test files explicitly instead of using `glob(...)`:

```python
# Preferred
cc_library(
    name = "my_lib_library",
    srcs = [
        "src/bar.cpp",
        "src/foo.cpp",
    ],
    hdrs = [
        "include/my_lib/bar.hpp",
        "include/my_lib/foo.hpp",
    ],
)

# Avoid
cc_library(
    name = "my_lib_library",
    srcs = glob(["src/**/*.cpp"]),
    hdrs = glob(["include/**/*.hpp"]),
)
```

Explicit lists make the review diff show exactly what each target compiles or ships, stop stray files (editor backups, `__pycache__`, generated outputs, runtime-written files) from silently entering a target, and make it obvious when upstream adds, removes, or renames a file in a new release. Only fall back to a glob when an explicit list is genuinely impractical (for example, thousands of mesh or texture assets in a model directory), and keep it as narrow as possible.

### 3. Each target declares its minimum viable set of dependencies

Every target should list only the dependencies **it directly uses** — no more. Lean on transitivity for everything else:

- A library's `deps` carry its own transitive libraries; consumers must not repeat them.
- An executable carries its own runtime metadata via `data = [":ament_index"]` (see the Ament section below), so anything that runs it gets that data for free.
- Do not "pad" a target with extra deps or data just to make something work. If something downstream is missing at runtime, the fix belongs on the target that actually needs it, so every consumer benefits.

The goal is that each target is self-sufficient: depending on it is enough to use it, and its `deps`/`data` lists stay short, accurate, and reviewable.

### 4. Launch targets depend on the nodes they launch

`launch_ros_binary`, `launch_binary`, and `launch_ros_test` need special handling. You must **parse the launch file itself** — Python (`.launch.py`), XML (`.launch.xml`), or YAML (`.launch.yaml`) — to work out what it starts, then depend on exactly those things:

| What the launch file references | Put this in `deps` |
|---|---|
| A node, e.g. `Node(package='ros_gz_bridge', executable='parameter_bridge')` / `<node pkg="..." exec="...">` | The executable target, e.g. `@ros_gz_bridge//:parameter_bridge` |
| Another launch file, e.g. `IncludeLaunchDescription(... 'ros_gz_sim' ... 'gz_sim.launch.py')` / `<include file="$(find-pkg-share ...)/...">` | That launch target, e.g. `@ros_gz_sim//launch:gz_sim_launch` |
| A composable node loaded into a container | The `rclcpp_components_register_node` target (or the container plus the component's library) |
| A command-line tool, e.g. `ExecuteProcess(cmd=['xacro', ...])` | The tool's target, e.g. `@xacro` |
| Python helpers imported by the launch file, e.g. `get_package_share_directory` | The library, e.g. `@ament_index_python` |

Each node target carries its own runtime data transitively (it already has `data = [":ament_index"]`), so the launch target must **not** also list the node's `@<pkg>//:ament_index`. `data` is reserved for the current package's own non-executable share content (params, maps, worlds, URDF, RViz configs), usually just `"//:ament_index"`:

```python
launch_ros_binary(
    name = "spawn_tb3_launch",
    src = "spawn_tb3.launch.py",
    data = [
        "//:ament_index",
    ],
    deps = [
        "@ament_index_python",
        "@ros_gz_bridge//:parameter_bridge",
        "@ros_gz_sim//:create",
        "@xacro",
    ],
)
```

This keeps both `data` and `deps` small, and means fixing a node's runtime dependencies once fixes every launch file that starts it.

> [!IMPORTANT]
> Verify launch targets by actually running them (`bazel run @<pkg>//launch:<target>`) and reading the log for `process has died`, tracebacks, `package not found`, or missing-library errors. A launch target that builds can still fail at runtime if a node or included launch file is missing from `deps`.

### 5. Cross-platform target naming: never use `shared_lib_name` or platform-specific target names

All `BUILD.bazel` files must be platform-agnostic across Linux (`x86_64`, `aarch64`), macOS (`darwin_arm64`), and Windows:

- **Do NOT set `shared_lib_name` on `cc_shared_library`**: Hardcoding `shared_lib_name = "libfoo.so"` or `shared_lib_name = "pkg/_foo.so"` forces a Linux `.so` filename and breaks on macOS (`.dylib`) and Windows (`.dll`). Omit `shared_lib_name` completely and let `cc_shared_library` use its built-in toolchain logic to name the shared library artifact appropriately for the target platform (`lib<name>.so`, `lib<name>.dylib`, or `<name>.dll`).
- **Never bake platform, architecture, or Python ABI triples into target names**: Target names must never contain suffixes like `.cpython-314-x86_64-linux-gnu`, `x86_64-unknown-linux-gnu`, or `_solib_k8`. For example, name targets `"state_machine_library"` and `"state_machine"`, never `"state_machine.cpython-314-x86_64-linux-gnu_library"` or `"state_machine.cpython-314-x86_64-linux-gnu"`.
- **Never hardcode architecture-specific solib rpaths**: Do not add `-Wl,-rpath,$ORIGIN/../_solib_k8/...` in `user_link_flags`; Bazel and `ament_index` manage runtime library paths across platforms automatically.

---

## Writing `BUILD.bazel` Overlays

When creating or modifying a package's `BUILD.bazel` file, keep the following guidelines in mind:

### 1. Copyright Header and Licensing
Every newly authored or hand-edited `BUILD.bazel` or `.bzl` file must begin with the `# Copyright ...` header comment block at the very top of the file (starting on line 1), **before** any `load(...)` statements:
> [!IMPORTANT]
> Never place or insert a `load(...)` statement before the `# Copyright` header comment block. Placing `load()` above the copyright comment prevents `buildifier` from consolidating `load()` statements and causes `ament_copyright` linter tests to fail.

After the copyright header and `load()` statements, declare the package's license using `rules_license`. Ensure the license matches the package's actual upstream license (defined in its `package.xml` `<license>` tag or LICENSE file).
```python
# Copyright 2026 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
    srcs = [
        "src/my_lib.cpp",
    ],
    hdrs = [
        "include/my_lib/my_lib.hpp",
    ],
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

> [!WARNING]
> Do **not** set `shared_lib_name` on `cc_shared_library` (e.g. `shared_lib_name = "libmy_lib.so"`), and do **not** include platform/ABI triples (such as `.cpython-314-x86_64-linux-gnu`) in `name`. `cc_shared_library` automatically names the output `lib<name>.so` on Linux, `lib<name>.dylib` on macOS, and `<name>.dll` on Windows based on `name`.

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
    data = [
        "config/params.yaml",
        "urdf/robot.urdf.xacro",
    ],
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

Node executables (`cc_binary`, `py_binary`, `qt_cc_binary`, `rclcpp_components_register_node`) must carry `data = [":ament_index"]` themselves, so that anything that runs them — launch files in this or other packages — gets the node's runtime data transitively (see Core Principle 4). Because `ament_index` would otherwise depend on the executable that depends on it, list such executables in `ament_package(executables = ...)` for downstream export, **not** in `ament_index(executables = ...)`:
```python
cc_binary(
    name = "parameter_bridge",
    srcs = ["src/parameter_bridge.cpp"],
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
Never declare new `bazel_dep` entries in a package's own `MODULE.bazel`. (Staged BCR modules under `bcr_staging/modules/` are the exception: they declare their own `bazel_dep`s like any BCR module.) Instead:
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

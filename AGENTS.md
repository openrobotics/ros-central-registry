# AGENTS.md

Guidance for coding agents working in this repository. Read this before making
changes under `bcr_staging/`, `modules/`, `tools/ci/`, or `.github/workflows/`.

## What this project is

The ROS Central Registry (RCR) publishes [ROS](https://ros.org) core packages
as [Bazel](https://bazel.build) modules (`modules/<package>/<version>/`), so
they can be consumed with `bazel_dep()` like any other Bazel Central Registry
module. Everything is built from source with a hermetic toolchain — no system
ROS install, no `rosdep`. This repo does not author ROS packages; it tracks
and packages what already exists upstream in
[`ros/rosdistro`](https://github.com/ros/rosdistro).

## Four things you must not forget

1. **Scope is upstream `rosdistro` only.** We only package what's already in
   the upstream `rosdistro` repository. Never hand-author a brand-new
   package's module directory because someone asked for a package that isn't
   there yet — the answer is "request it in `rosdistro` upstream, then wait
   for the next bootstrap." See `docs/source/questions.rst`.

2. **Bootstrapping a new distro release is fully automated.** `.github/workflows/nightly_bootstrap.yml`
   runs nightly, finds any `rosdistro` tag newer than what's already
   bootstrapped, and runs `bazel run //tools/ci:bootstrap_release` for it,
   committing straight to `main`. You should never need to hand-run this
   yourself, and should never hand-craft what it produces (bare module
   versions per changed package, `0.0.0` stubs for brand-new packages). If a
   freshly-bootstrapped package doesn't build, that's a normal bug — fix it
   with the patching workflow below, same as any other package.

3. **Distribution rollups are automated and happen weekly.** `.github/workflows/weekly_rollup.yml`
   runs every Sunday 11pm PDT, aggregates whatever per-package patches merged
   that week, bumps the top-level `ros` module to reference them, runs full
   CI, and auto-merges on green. Individual package patches (see the
   patching workflow) merge independently through the week; nobody manually
   cuts a distribution release.

4. **Bazel modules are immutable once merged to `main`.** A version directory
   under `modules/<package>/<version>/` is never edited, renamed, or deleted
   after merge — CI enforces this (`tools/ci/check_pr_modules.py`: any diff
   under `modules/` that isn't a brand-new version directory, an append-only
   edit to `metadata.json`, or a version-bump-only modification to `MODULE.bazel`,
   fails). The only exception is the `rosdistro` module, which permits any edits
   to its `MODULE.bazel` files. Fixing a bug in a package means creating a
   **new** version directory (e.g. `rclcpp@32.0.0-1.rcr.1` ->
   `rclcpp@32.0.0-1.rcr.2`), never editing the old one in place.

## How to fix a bug in a package

Don't hand-edit files under `modules/`. Use the setup → vendor → edit/test →
patch pipeline — see the skills in `.agent/skills/`:

- `.agent/skills/setup-workspace/` — generate a throwaway Bazel workspace for
  a release.
- `.agent/skills/vendor-module/` — check out one or more packages' real
  sources into that workspace for in-place editing, and iterate with
  `bazel build`/`bazel test`.
- `.agent/skills/create-patch/` — roll your edits up into new module
  version(s), either for one named package or auto-detected across
  everything you touched. A version that only exists on your current
  branch (not yet on `main`) is amended in place rather than incremented,
  so iterating on the same not-yet-merged patch no longer mints a new
  `.rcr.N` directory per run.
- `.agent/skills/rebase-module/` — recover from a stale workspace (e.g. a
  `git pull`/rebase brought in a concurrent change to a not-yet-published
  version) without losing your own uncommitted edits.
- `.agent/skills/release-automation/` — what's automated (bootstrap, rollup)
  and what you should never try to do by hand.

**Re-running `vendor-module` on a package you've already vendored discards
any uncommitted edits to it**, even extensive ones — it re-fetches from
whatever's currently published under `modules/` (plus overlay/patches),
which does not include edits you haven't rolled into a `create-patch` output
yet. This bites hardest when you're iterating on a dependency (e.g.
`rosdistro`) and a downstream package in the *same* workspace, since
re-running `setup-workspace`/`vendor-module` to pick up the dependency's new
patch version silently wipes out any not-yet-patched work on the downstream
package too. If you have uncommitted edits worth keeping, use
`.agent/skills/rebase-module/` instead of re-running `setup-workspace`/
`vendor-module` directly — it preserves your edits, re-baselines against the
current `modules/` state, and reapplies them on top.

## Adding a new third-party (BCR) dependency

Never add a new `bazel_dep` to a package's own `MODULE.bazel` (e.g. because
its `CMakeLists.txt` needs something not already declared there, such as a
prebuilt SDK upstream fetches via CMake `FetchContent`). Only `rosdistro`'s
`MODULE.bazel` gains new BCR deps.

Before adding anything, check whether it's already there: grep
`rosdistro`'s `overlay/cc/BUILD.bazel` for a same-named target under
`@rosdistro//cc:`. A lot of common third-party libraries (`curl`, `eigen`,
`spdlog`, `opencv`, PCL, OpenSSL via `boringssl`, ...) are already wired up
because some other package needed them first — don't assume a dependency is
missing just because the package you're working on doesn't declare it
itself. When you do need to add a genuinely new one, double check you have
the exact right BCR module before wiring it in: similarly-named modules can
be unrelated projects (e.g. the BCR module named `zip` is Info-ZIP's
`zip`/`unzip` CLI tool, not `libzip`, the C API library most C++ code
actually links against — read the module's own `overlay/BUILD.bazel` on
[bazel-central-registry](https://github.com/bazelbuild/bazel-central-registry/tree/main/modules)
to confirm what it actually provides before assuming a name match is right).

Add the `bazel_dep` (and any module extension/repository rule needed to
fetch it, e.g. a platform-specific prebuilt release archive) to
`rosdistro`'s `MODULE.bazel`, then expose it as a
`cc_library`/`cc_shared_library` target in `rosdistro`'s `overlay/cc/BUILD.bazel`
(see the `mcap`/`zstd`/`fastdds` targets there for the pattern of wrapping an
upstream BCR target, and `bazel_test_helper`/`googletest` for small
from-source helper libraries). Packages that need the dependency then depend
on `@rosdistro//cc:<target>` rather than declaring the BCR dep themselves.

This forces every package in a given distro release to pin to the exact same
version of any transitive (non-ROS) dependency, instead of letting individual
packages drift to their own versions.

**You cannot locally build/test against a newly-added `rosdistro` `bazel_dep`
by editing the vendored copy alone.** `setup-workspace` resolves the module
graph from what's actually published under `modules/` at the time it runs —
editing `workspace/vendor/rosdistro+/MODULE.bazel` changes source content but
not what Bazel resolved as `rosdistro`'s dependencies, so the new dep won't
exist in the graph and any target referencing it fails with "no repository
visible as '@<dep>'". The working sequence is: vendor `rosdistro` and make
your edits (`MODULE.bazel` + `overlay/cc/BUILD.bazel`) as usual, then run the
`create-patch` skill on `rosdistro` *before* trying to build against the new
dep — this materializes an (uncommitted) `modules/rosdistro/<version>/`
that `setup-workspace`'s override mechanism picks up automatically on its
next run (same mechanism that lets two people patch the same package in one
week without colliding). Re-run `setup-workspace`, re-vendor, and only then
does the new dependency actually resolve. If you need further edits after
that, repeat the loop — re-run `create-patch -- rosdistro` again rather than
hand-editing the version directory it already produced. As long as that
version hasn't reached `main` yet, `create-patch` amends it in place each
time (see the `create-patch` skill), so there's no stale intermediate
directory to clean up before opening the PR.

A package that needs a dependency you just added to `rosdistro` won't
actually build with its own `bazel_dep(name = "rosdistro", ...)` pin
unchanged — `create-patch` doesn't bump that pin for you (bumping
dependents when a dependency moves is the weekly rollup's job, not an
individual patch's), so the package genuinely can't build standalone until
either the rollup runs or you note the ordering dependency explicitly for
the reviewer (this `rosdistro` patch has to merge and roll up before, or
alongside, the package's own patch).

When a package bundles or vendors a third-party SDK as embedded source (e.g.
`find_package(SomeSDK REQUIRED)` pointing at a subdirectory shipped inside
the package's own archive), don't assume the SDK's own top-level
`CMakeLists.txt` defaults tell you what's actually needed — check how the
*consuming* package's `CMakeLists.txt` configures that subdirectory first
(look for `option(...)` overrides or cache variables set immediately before
its `add_subdirectory()`/`find_package()` call). A big, scary-looking
transitive dependency is often disabled entirely by the consuming package
and doesn't need to be wired up at all.

Don't trust a `CMakeLists.txt`'s declared include paths (or other
target-configuration details) at face value when translating them to
Bazel — verify against the actual `#include` statements in source instead.
CMake/autotools builds can silently tolerate a wrong or stale include path
because a system-installed copy of the same library papers over it in
upstream's own CI, which Bazel's hermetic, no-system-headers builds won't
do. If a declared include path doesn't match what the source files actually
`#include`, trust the source.

The same centralization applies to Python dependencies: add the package to
`rosdistro`'s `requirements.in`, then regenerate both locks rather
than hand-editing them — `bazel run //:requirements.update` for
`requirements.txt` (see its own header comment).

## Repository layout

- `modules/<package>/<version>/` — one Bazel module version per package
  version. Contains `MODULE.bazel`, `source.json` (upstream archive +
  integrity hash), and optionally `patches/` (unified diffs against raw
  upstream) and `overlay/` (brand-new files, typically `BUILD.bazel`s).
- `modules/ros/<release>/` — the top-level umbrella module for one dated
  distro release (e.g. `lyrical.2026-06-08.rcr.2`), pinning every package's
  resolved version.
- `tools/ci/` — the Python tooling that drives everything above:
  `bootstrap_release.py`, `rollup_patches.py`, `setup_workspace.py`,
  `vendor_modules.py`, `create_patch.py`, `check_pr_modules.py`,
  `rosdistro_lib.py`/`bzlmod_lib.py` (shared helpers). Each has a `_test.py`
  sibling and a matching `py_test` target in `tools/ci/BUILD.bazel` — read
  the tests before changing behavior, and add to them when you change or add
  behavior.
- `workspace/` — generated by `setup_workspace`/`vendor_modules`; gitignored,
  never hand-edited or committed to.
- `docs/source/` — Sphinx docs (`design_choices.rst` has the full versioning
  scheme rationale; `questions.rst` is the FAQ).
- `examples/` — a separate, runnable Bazel workspace demonstrating usage.

## Working in `tools/ci/`

- Python scripts here are structured as `<name>.py` (thin `main()`/CLI) +
  `<name>_test.py` (unit tests against the pure helper functions) +
  `BUILD.bazel` `py_library`/`py_binary`/`py_test` triple. Follow that split
  for new tooling rather than putting logic only reachable through `main()`.
- Run tests with `bazel test //tools/ci/...` (or `bazel test //...` across the workspace).
  Never run `pytest` directly on the host system — test targets (including `py_test`
  targets that invoke pytest under the hood) are hermetically managed and executed by Bazel.
- `sys.exit`/`parser.error` belong in `main()` only; helper functions should
  raise exceptions so they stay unit-testable without subprocess/`SystemExit`
  gymnastics.

## Testing

Always run tests using Bazel:
- **CI tooling unit tests**: `bazel test //tools/ci/...`
- **Full workspace tests**: `bazel test //...`
- **Vendored module tests**: `bazel test @<module-name>//...` (inside `workspace/`)

Never invoke `pytest`, `unittest`, or `ctest` directly on the host system. Bazel handles all test runners, dependencies, and environment setup hermetically.

### Upstream Test Parity and Test Scope
- **Match upstream test coverage; do not hallucinate tests**: Never author, invent, or hallucinate new test files (e.g. creating synthetic `test_utest.cpp` or `test_utest.py`) if they do not exist in the upstream package. We preserve and package upstream code, we do not expand test suites arbitrarily.
- **Port all real upstream unit tests**: Ensure all non-integration unit tests defined in upstream's `CMakeLists.txt` or test folders are ported to Bazel test targets (`cc_test`, `py_pytest`). Only omit integration tests that require external hardware, live robot simulators, or non-hermetic external network environments.
- **Verify interface completeness**: When packaging message, service, or action packages, check all `.msg`, `.srv`, and `.action` files against the upstream tag/archive to ensure every single interface is declared in `deps` of `default_generators` or `core_generators`.
- **No hardcoded environment variables in test targets**: Do NOT hardcode `env = {"AMENT_PREFIX_PATH": ".", "LD_LIBRARY_PATH": "./lib"}` in `cc_test` or `py_test` targets. `AMENT_PREFIX_PATH` and library paths are configured globally in `.bazelrc`.

### Cross-Platform and Multi-RMW Compatibility
- **Portable C++**: Write clean, standard C++ without GNU-specific headers (e.g. avoid `<error.h>`, use `<cstdio>`/`fprintf` and `<cstdlib>`/`exit`). Never hardcode host/target CPU architectures (e.g. x86_64 prebuilt packages) into module dependencies.
- **CycloneDDS discovery wait loops**: When tests poll for publisher/subscriber discovery in a `while` loop (e.g. `while (sub_->get_publisher_count() == 0)`), always spin the node executor (e.g. `executor_->spin_some()`) on each iteration. Unlike FastDDS which performs discovery asynchronously in background threads, CycloneDDS requires the node executor to spin to process discovery events.
- **Zenoh shutdown safety & static singletons**: Never allow active ROS 2 publishers, subscriptions, or nodes to remain in static/global variables that destruct during program exit after `rclcpp::shutdown()`. Under Zenoh (`rmw_zenoh_cpp`), destroying publishers after the Tokio runtime/Thread Local Storage is torn down triggers a process-abort panic. Provide explicit cleanup hooks (e.g. `clearAllRegistries()` in test `TearDownTestSuite()`) before `rclcpp::shutdown()`.
- **Avoid unthrottled tight loops querying RMW graph state**: Avoid tight loops invoking dynamic graph queries like `get_subscription_count()` thousands of times in a row, which cause extreme test slowdowns and timeouts under non-dynamic RMWs.

## Packaging Conventions: `ament_index` vs `ament_package`

Understand the distinct roles of `ament_index` and `ament_package`:
- **`ament_index` (Data dependency for internal targets)**: Aggregates package metadata, configuration files, URDF/Xacro models, launch files, plugins, and libraries for ingestion by test targets and binary targets in the *current* package (passed via `data = [":ament_index"]`).
- **`ament_package` (Downstream export bundling)**: Declared *exactly once* at the bottom of the root `BUILD.bazel` to bundle all exported headers, libraries, executables, and dependencies for *downstream* consumers (mirroring CMake `install()`). Targets within the package must NOT depend on `:ament_package`.

## Module Integrity and Cleanliness

- **No reject or conflict artifacts**: Never leave `.rej`, `.orig`, or temporary conflict files in vendored module trees or commit them to `modules/`. Clean them up before creating patches.
- **Authoritative integrity hashes**: Never hand-edit SHA-256 integrity hashes in `source.json`. Let `create_patch` generate them, and verify with `bazel run //tools/ci:check_pr_modules`.

## Linting

CI (`.github/workflows/_check_for_linting_errors.yml`) fails a PR on either
of these, so check both before considering a change done:

- **Every `BUILD.bazel`/`.bzl` file in the repo must pass buildifier**:
  `buildifier -mode check -r .` from the repo root. If it's not on your
  `PATH`, grab the same version CI uses:
  `curl -L https://github.com/bazelbuild/buildtools/releases/download/v8.5.1/buildifier-linux-amd64 -o buildifier && chmod +x buildifier`.
  Use `buildifier -mode fix -r .` to auto-fix formatting issues.
- **Every Python file under `tools/`, `examples/`, and `docs/` must pass
  ruff**: `ruff check tools examples docs` from the repo root. CI pins
  `ruff==0.15.22` (`astral-sh/ruff-action`) — install the same version
  (`pipx install ruff==0.15.22` or `pip install ruff==0.15.22`) so local
  results match CI exactly; a newer ruff can flag (or miss) different things.
  There's no `ruff.toml`/`pyproject.toml` in this repo, so it runs with
  ruff's defaults.

## Licensing

`rules_license` is already a default `bazel_dep` on every module (see
`BCR_DEPS` in `tools/ci/bootstrap_release.py`), so it never needs adding —
but any `BUILD.bazel` you newly author or hand-edit (typically `overlay/`
files added via `create_patch`, or a package's own `msg`/`srv`/`action`
`BUILD.bazel`) should declare the package's license with it, matching this
existing pattern (e.g. `modules/rosidl_parser/*/overlay/BUILD.bazel`):

```python
load("@rules_license//rules:license.bzl", "license")

package(
    default_applicable_licenses = [":license"],
    default_visibility = ["//visibility:public"],
)

license(
    name = "license",
    license_kinds = [
        "@rules_license//licenses/spdx:Apache-2.0",
    ],
)
```

Match `license_kinds` to the package's actual upstream license (its
`package.xml`'s `<license>` tag) rather than defaulting to Apache-2.0 --
`BSD-3-Clause` shows up frequently too. This isn't retrofitted across every
existing overlay file (many predate the convention), so don't feel obligated
to add it to files you're not otherwise touching -- just include it in any
new or edited one.


---
name: release-automation
description: Explains what's fully automated in this repo (bootstrapping new rosdistro releases, weekly distribution rollups) and what is explicitly out of scope (packages not present in upstream rosdistro). Use this whenever a task asks you to add a new distro release, cut/bump a distribution version, or add a package that isn't already bootstrapped — the answer to all three is almost always "that's automated, don't do it by hand" or "that's out of scope, file it upstream."
---

Two of the biggest-looking tasks in this repo are things you should almost
never do by hand. Read this before attempting either.

## Bootstrapping a new distro release — automated, nightly

`.github/workflows/nightly_bootstrap.yml` runs every night at 08:00 UTC. It
scans `ros/rosdistro` for any tag newer than what's already bootstrapped here
and, for each one, runs:

```shell
bazel run //tools/ci:bootstrap_release -- --distro <distro>
```

This reads `distribution.yaml` and every package's `package.xml` straight
from the upstream tag (no `rosdep`/`rosinstall_generator`), creates a bare
(unpatched) module version for every package whose upstream version changed,
a `0.0.0` stub for any package that's brand-new to the registry, and migrates
each to `.rcr.0` while carrying forward existing patches/overlay from its
previous version. Packages whose upstream version is *unchanged* are pinned
to their existing `.rcr.N` — unless that version's `MODULE.bazel` boilerplate
(the canned BCR `bazel_dep` block and module-extension trailer in
`bootstrap_release.py`) has since changed, in which case a `.rcr.N+1` copy
with a re-rendered `MODULE.bazel` is minted so every version the release pins
declares the same third-party deps/extensions as a fresh one. It commits
straight to `main` — there's no PR gate, since this is purely additive
scaffolding nothing published yet depends on.

The same re-rendering is available on demand for versions that only exist
on your branch (so they can be edited in place rather than re-minted):
`bazel run //tools/chores:sync_module_boilerplate -- --dry-run`.

**You should not run `bootstrap_release` yourself** unless a human has
specifically asked you to backfill/re-check a particular distro
(`workflow_dispatch` with a `distro` input covers that). If a
freshly-bootstrapped package fails to build, that's just a normal bug in that
package — fix it with the `setup-workspace` → `vendor-module` →
`create-patch` pipeline, the same as any other patch.

## Distribution rollups — automated, weekly

`.github/workflows/weekly_rollup.yml` runs every Sunday 11pm PDT (06:00 UTC
Monday). It finds every package with a newer published version than what the
current `ros` release references (i.e. everything `create-patch` landed that
week), transitively bumps every package that depends on one of them (a pure
version-pin bump, no content change), regenerates the top-level `ros` module,
runs the full CI matrix on a bot branch, and auto-merges on green (or opens a
PR for manual follow-up on failure).

**You should not manually bump the `ros` module's pinned versions or cut a
new `.rcr.N` distribution release.** Land your fix as an ordinary
single-package patch (`create-patch` skill) and let the weekly rollup pick it
up. If nothing was patched that week, the rollup is simply a no-op.

## Package scope — upstream `rosdistro` only

This registry only packages what's already present in the upstream
[`ros/rosdistro`](https://github.com/ros/rosdistro) repository. If asked to
"add package X" and X isn't already bootstrapped under `modules/X/`:

- Don't hand-author a new `modules/<name>/` directory from scratch.
- The correct next step is requesting inclusion in `rosdistro` upstream, then
  waiting for the next nightly bootstrap to pick it up automatically.

See `docs/source/questions.rst` for the canonical statement of this, and
`docs/source/design_choices.rst` for the full versioning-scheme rationale
behind both automated workflows.

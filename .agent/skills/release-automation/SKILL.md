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

### Running a rollup by hand (only when a human explicitly asks)

If a human asks you to cut the next `.rcr.N` release manually, do it with the
same tool the workflow uses, never by hand-editing `modules/ros/`:

```shell
# 1. Preview, then write. --release is the <distro>.<date> row, NOT the full
#    .rcr.N version -- the script picks the next free .rcr.N itself.
bazel run //tools/ci:rollup_patches -- --release=lyrical.2026-10-05 --dry-run
bazel run //tools/ci:rollup_patches -- --release=lyrical.2026-10-05
```

The last line of output is `Rolled up to ros version <NEW>.` It mints a new
version directory for `ros` and every variant (`ros_core`, `ros_base`,
`perception`, `simulation`, `desktop`, `desktop_full`), plus pure
version-pin-bump directories for any package that transitively depends on
something patched that week, and appends to each one's `metadata.json`.
Verify the result the same way CI will (`setup-pull-request` skill has the
full `check_pr_modules` invocation; buildifier the touched dirs).

#### Post-rollup: point everything at the new release

`rollup_patches` only touches `modules/`. The rest of the repo still names
the *previous* release and must be moved forward in the same branch/PR, or
CI keeps testing the old release and users keep getting it by default. With
`OLD`/`NEW` as the previous and new full versions (`<distro>.<date>.rcr.N`
-> `<distro>.<date>.rcr.N+1`):

1. **CI workflows** -- every `_check_distribution_*.yml` and
   `_check_cuda_compiles.yml` under `.github/workflows/` has a
   `matrix.ros:` list entry naming the release under test. Replace `OLD`
   with `NEW` so this branch's CI exercises the release it just created.
2. **README build-status matrix** -- the `## <release>` heading under
   `# Releases` and every shields.io badge in the table beneath it embed the
   release in the gist filename (`.../raw/<release>_<bazel>_<os>_<job>.json`).
   Replace the previous release with the new one (don't add a second
   section -- the front page shows only the current release).
3. **Docs and markdown** -- `README.md`, `CONTRIBUTING.md`,
   `docs/source/*.rst`, and the sibling skills under `.agent/skills/` all
   quote `--release=OLD` / `bazel_dep(..., version = "OLD")` snippets. Move
   them all to `NEW` so users get the latest release by default.
4. **`examples/MODULE.bazel`** -- the `bazel_dep(name = "perception", ...)`
   pin is what the examples CI job (and anyone copying the example) builds
   against; bump it too.

In practice this is one mechanical substitution. Scope it to tracked files
and leave `modules/`, `bcr_staging/` (immutable module content) and
`tools/ci/*_test.py` (fixtures use fixed historical versions on purpose)
alone. This skill file is deliberately written with placeholders so the
substitution doesn't rewrite it:

```shell
OLD=<distro>.<date>.rcr.N      # e.g. the heading currently in README.md
NEW=<distro>.<date>.rcr.N+1    # the "Rolled up to ros version" output
git ls-files | grep -v '^modules/\|^bcr_staging/\|_test\.py$' \
  | xargs grep -l -I "$OLD" | xargs sed -i "s/$OLD/$NEW/g"
# Nothing outside modules/, bcr_staging/ and tests should still name OLD:
git ls-files | grep -v '^modules/\|^bcr_staging/\|_test\.py$' | xargs grep -n -I "$OLD"
```

**Watch out for `rosdistro`.** The `rosdistro` module's own version uses the
same `<distro>.<date>.rcr.N` shape as the `ros` release but its `N`
increments independently (it's patched like any other package), so a
`bazel_dep(name = "rosdistro", version = ...)` pin -- `examples/MODULE.bazel`
has one -- can coincidentally equal `OLD` and get rewritten to a `rosdistro`
version that doesn't exist. After the substitution, `git diff` the touched
files and revert any `rosdistro` pin the `sed` changed (or exclude that line
up front). A `ros`/variant release pin and a `rosdistro` pin are different
things even when the strings match.

Then re-run `buildifier -mode check -r .` (the `examples/MODULE.bazel` edit)
and commit everything -- `modules/`, `.github/workflows/`, docs, examples --
together, signed off (`setup-pull-request` skill). Note the
`weekly_rollup.yml` `workflow_dispatch` default is the `<distro>.<date>` row,
not a `.rcr.N`, so it only needs updating when a new *dated* release is
bootstrapped, not after a patch rollup.

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

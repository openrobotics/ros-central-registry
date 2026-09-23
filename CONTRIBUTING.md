## Ownership

Any contribution that you make to this repository will be under the Apache 2 License, as dictated by that [license](http://www.apache.org/licenses/LICENSE-2.0.html):

~~~
5. Submission of Contributions. Unless You explicitly state otherwise,
   any Contribution intentionally submitted for inclusion in the Work
   by You to the Licensor shall be under the terms and conditions of
   this License, without any additional terms or conditions.
   Notwithstanding the above, nothing herein shall supersede or modify
   the terms of any separate license agreement you may have executed
   with Licensor regarding such Contributions.
~~~

Contributors must sign-off each commit by adding a `Signed-off-by: ...` line to commit messages to certify that they have the right to submit the code they are contributing to the project according to the [Developer Certificate of Origin (DCO)](https://developercertificate.org/).

## Adding a new distribution (automated)

Upstream (`ros/rosdistro`) tags a new dated release for each distro roughly every 2-3 weeks (e.g. `lyrical/2026-06-23`). You don't need to do anything for this: `.github/workflows/nightly_bootstrap.yml` runs nightly, scans for any tag newer than what's already bootstrapped here, and for each one runs `bazel run //tools/ci:bootstrap_release -- --distro <distro>`, which:

- Reads `distribution.yaml` and each package's `package.xml` directly from the tag (no `rosdep`/`rosdistro`/`rosinstall_generator` — see `docs/source/design_choices.rst`), to resolve every package's upstream version, source archive, and dependencies.
- Creates a bare (unpatched) module version for every package whose upstream version actually changed since the last bootstrap; packages that didn't change are left referencing whatever version they're already at.
- Creates a `0.0.0` placeholder version for any package that's never existed in the registry before (a resolvable stub with no dependencies — see `tools/ci/bootstrap_release.py`'s `render_stub_module_dot_bazel`).
- Migrates each newly-bootstrapped package straight to a `.rcr.0`, carrying forward whatever patches/overlay applied to its previous version (so, for example, `rosdistro`'s Python/`ament`/`cc` build-rule overlay survives every new distro date without anyone re-patching it).

The workflow commits directly to `main` once `tools/ci/check_pr_modules.py`'s append-only guardrail passes — there's no PR gate here, since this is purely additive scaffolding that nothing currently-published references yet (unlike the weekly rollup below, which changes the active `ros` release pointer and does need full-CI gating). If a freshly-bootstrapped package doesn't actually build, that's a normal bug — patch it the same way as any other, per the next section.

To scan a distro other than the default list (`lyrical`) once, or re-run manually, use `workflow_dispatch` with a `distro` input; to make a distro part of the permanent nightly scan, add it to the `matrix.distro` fallback list in `nightly_bootstrap.yml`.

## Patching individual packages (manual)

If you need to fix a bug in a single RCR package, use this workflow rather than hand-editing files under `modules/`:

```shell
bazel run //tools/ci:setup_workspace -- --release=lyrical.2026-06-08.rcr.2
bazel run //tools/ci:vendor_modules -- rclcpp
# cd workspace
# ... edit vendor/rclcpp+/ in place ...
# ... then verify bazel test @rclcpp//... works
# ... and when you're ready to submit a patch ...
# cd ..
#
bazel run //tools/ci:create_patch -- rclcpp
```

`create_patch` creates a single new module version (e.g. `rclcpp@32.0.0-1.rcr.1` -> `rclcpp@32.0.0-1.rcr.2`) under `modules/rclcpp/`. That new directory plus the updated `metadata.json` is your entire PR — don't touch any other package's files, and don't modify or delete existing version directories (CI enforces this).

Run `bazel run //tools/ci:setup_workspace` again before patching if some time has passed since you first set up the workspace — it always resolves every package to its latest published version (printing an `OVERRIDE:` line whenever it does), so you never compute a patch version that collides with someone else's concurrent PR to the same package.

## Distribution patch releases (automated)

Patches to individual packages merge independently through the week — nobody needs to coordinate a release. Every Sunday 11pm PDT, `.github/workflows/weekly_rollup.yml` runs `bazel run //tools/ci:rollup_patches -- --release=<distro>.<date>`, which:

- Finds every package with a newer published version than what the current `ros` release references (i.e. every `create_patch` PR merged since the last rollup).
- Transitively bumps every package that depends on one of them — purely a `bazel_dep` pin update, no content change — so e.g. `rclcpp_action@...rcr.1` becomes `rclcpp_action@...rcr.2` simply because `rclcpp` moved. Nothing needs to be re-patched just because a dependency moved.
- Regenerates the top-level `ros` module to reference the new versions, and bumps the hardcoded `ros:` matrix entry in the three `_check_distribution_*.yml` workflows so the existing CI matrix actually exercises the new release.
- Runs the result through the full CI suite on a bot-created branch (reusing `ci.yaml`'s whole job graph). If everything passes, it squash-merges automatically; if anything fails, it opens a PR and assigns it to `@asymingt` for manual follow-up.

If nothing was patched that week, the workflow is a no-op — it doesn't cut an empty release. See `docs/source/design_choices.rst` (Versioning) for the full picture, including how the two automated workflows above interact with each other.

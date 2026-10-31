---
name: setup-pull-request
description: Prepare and open a pull request against the ROS Central Registry correctly. Covers signing off every commit (DCO), running the same lint, tooling, and module checks CI runs before pushing, and filling in the repository's PR template in full. Use this whenever you're about to commit, push, or open/update a PR, or when CI fails on a "Check modules", "Lint", or sign-off check.
---

Use this skill after you've finished the actual change (usually via the
`setup-workspace` → `vendor-module` → `create-patch` pipeline in
`edit-module`). It covers the three things PRs most often get wrong:

1. Commits that aren't signed off.
2. Pushing without running the cheap local checks that CI runs first. Every
   expensive CI job (distribution builds, tests) waits on those checks, so
   one lint error or module violation hides every real build/test result.
3. A PR description that ignores or only partly fills in the template.

## 1. Every commit must be signed off

Every commit on the branch, not just the last one, needs a
`Signed-off-by:` trailer certifying the
[Developer Certificate of Origin](https://developercertificate.org/) (see
`CONTRIBUTING.md`). The trailer's email must match the commit's **author**
email.

Always commit with `-s`:

```shell
git commit -s -m "rclcpp: fix ... in 32.0.0-1.rcr.2"
git commit -s --amend --no-edit   # amending keeps/adds the sign-off
```

> [!IMPORTANT]
> Never add a sign-off on someone else's behalf, and never change a commit's
> author to make a sign-off "match". If a commit authored by someone else
> isn't signed off, ask them, or the user, to fix it.

### Checking the branch

List every commit since `main` whose message has no sign-off matching its
author:

```shell
git fetch origin main
git log --format="%h %ae" origin/main..HEAD | while read -r h e; do
  git log -1 --format=%B "$h" | grep "^Signed-off-by:" | grep -q "<$e>" \
    || echo "MISSING SIGN-OFF: $(git log -1 --format='%h %an <%ae> :: %s' "$h")"
done
```

No output means every commit is fine.

### Fixing missing sign-offs

Rebase from the parent of the **oldest** offending commit, not from `main`.
That rewrites the fewest commits. `--signoff` adds the trailer only where it
isn't already the last one, so commits that are already signed off don't get
duplicates.

```shell
git branch backup/pre-signoff HEAD            # safety net
git rebase --signoff <oldest-offending-sha>^
git diff backup/pre-signoff HEAD --quiet && echo "trees identical"
```

Re-run the check above, then push with
`git push --force-with-lease`. **Ask the user before force-pushing** a
branch that's already on the remote, because it rewrites shared history.

## 2. Run the basic checks locally before pushing

Run these from the repo root. They're fast (seconds to a couple of minutes)
and match the CI gates in `.github/workflows/`.

### Lint (`_check_for_linting_errors.yml`)

```shell
buildifier -mode check -r .          # every BUILD.bazel / .bzl / MODULE.bazel
ruff check tools examples docs       # every Python file CI lints
```

- Use the versions CI pins, `buildifier` **v8.5.1** and `ruff` **0.15.22**
  (`pipx install ruff==0.15.22`). Other versions flag different things.
- Auto-fix formatting with `buildifier -mode fix -r .`, then re-check.
- Every `BUILD.bazel`/`.bzl`/`MODULE.bazel` keeps its `# Copyright` header on
  line 1, above any `load()` (see `AGENTS.md`).

### Tooling tests (`_check_tooling.yml`)

Run these whenever you touch `tools/`, the root `BUILD.bazel`/`MODULE.bazel`,
or `docs/`:

```shell
bazel test //tools/ci/...     # or `bazel test //...` to match CI exactly
```

Never call `pytest`/`unittest` directly. Bazel runs them hermetically.

### Module checks (`_check_bazel_modules.yml`)

CI runs `check_pr_modules` once per registry directory against the PR's diff
from `main`. It enforces immutability: no edits to published versions, no
orphaned or unlisted patch/overlay files, correct `source.json` integrity
hashes, append-only `metadata.json`. Reproduce it exactly. **Commit first**,
because the diff is taken from `origin/main...HEAD`.

```shell
git fetch origin main
git diff --no-renames --name-status origin/main...HEAD > /tmp/diff_status.txt

rm -rf /tmp/old_metadata && mkdir -p /tmp/old_metadata
for d in modules bcr_staging/modules; do
  git diff --no-renames --diff-filter=M --name-only origin/main...HEAD \
    | grep -E "^$d/[^/]*/metadata.json$|^$d/[^/]*/[^/]*/MODULE.bazel$" \
    | while read -r f; do
        mkdir -p "/tmp/old_metadata/$(dirname "$f")"
        git show "origin/main:$f" > "/tmp/old_metadata/$f" || true
      done
done

bazel run //tools/ci:check_pr_modules -- \
    --diff-status /tmp/diff_status.txt --old-metadata-dir /tmp/old_metadata \
    --directory modules
bazel run //tools/ci:check_pr_modules -- \
    --diff-status /tmp/diff_status.txt --old-metadata-dir /tmp/old_metadata \
    --directory bcr_staging/modules --skip-dependency-consistency
```

Add `--permit-module-deletion` to the `modules` run **only** if the PR carries
the `permit module deletion` label. CI adds that flag only for labeled PRs.

If it reports violations:

- **Integrity mismatch / patch file missing from `source.json`**: never
  hand-edit hashes or `source.json`. Re-run
  `bazel run //tools/ci:create_patch -- <module>` (see `create-patch`). A
  `patches/` file that isn't listed in `source.json` usually means a later
  `create_patch` run started from a stale vendored tree and silently dropped
  an earlier fix. Restore the fix rather than deleting the file.
- **Edits to a published version**: make a new `.rcr.N` version instead
  (see `AGENTS.md` rule 4).
- **No `.rej`/`.orig` files**: delete them before committing.

### Tests for what you changed

CI's build and test matrix is expensive, but you should still build and test
the packages you touched, inside `workspace/`:

```shell
bazel build @<module>//...
bazel test @<module>//...
```

For launch targets, actually `bazel run` them and read the log (see
`edit-module` core principle 4).

## 3. Follow the PR template exactly

Every PR description **must** use `.github/PULL_REQUEST_TEMPLATE.md`, with
every section present and filled in. Don't delete sections, leave
placeholders, or replace the template with a free-form summary. Opening the
PR with `gh` doesn't apply the template automatically. Write the body from it
explicitly:

```shell
cp .github/PULL_REQUEST_TEMPLATE.md /tmp/pr_body.md
$EDITOR /tmp/pr_body.md           # fill in every section
gh pr create --base main --title "<module>: <what changed>" --body-file /tmp/pr_body.md
```

Section by section:

- **Summary**: what the PR changes and why. Name every module/version it
  adds (e.g. `rclcpp@32.0.0-1.rcr.2`) and call out any ordering dependency,
  e.g. a package patch that needs a `rosdistro` patch to merge and roll up
  first (see `AGENTS.md`).
- **Acknowledgements**: the three checkboxes (Contributing Guidelines, Code
  of Conduct, OSRF Generative AI policy) are attestations by the **human**
  submitting the PR. Leave them unchecked for the user to tick. Don't tick
  them on the user's behalf.
- **Generative AI disclosure**: required. If you're an agent writing any
  part of the change, the answer is **Yes**. Say which tool/model and which
  parts it produced (code, tests, commit messages, PR description).
- **Related issue(s)**: `Fixes #NNN` if there is one, otherwise state
  explicitly that there's no tracked issue. Don't leave `- Fixes:` empty.
- **Additional information**: exactly which local checks and tests you ran
  (and on which OS/arch), anything you couldn't verify (e.g. Linux-only
  failures checked only on macOS), and any follow-ups.

## Checklist before pushing or opening the PR

- [ ] Every commit on `origin/main..HEAD` is signed off by its author.
- [ ] `buildifier -mode check -r .` and `ruff check tools examples docs` are clean.
- [ ] `bazel test //tools/ci/...` passes (if `tools/`/`docs/`/root files changed).
- [ ] `check_pr_modules` passes for both `modules` and `bcr_staging/modules`.
- [ ] Changed packages build and test in `workspace/`; no `.rej`/`.orig` files.
- [ ] The PR body is the full template, with every section filled in and the
      acknowledgement boxes left for the human.
- [ ] Got the user's OK before any force-push.


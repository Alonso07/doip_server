# Dependency PR Review and Auto-Merge

Review **all** open dependency-update PRs on `alonso07/doip_server` in a single session.
Run the test suite, and squash-merge every PR that passes. Keep going until no more
mergeable PRs remain in this run.

## Steps

### 1. Collect all open dependency PRs

Call `mcp__github__list_pull_requests` (state=`open`) on repo `alonso07/doip_server`.

Build a **work queue** of PRs whose title matches any of these patterns (case-insensitive):
- starts with `chore(deps`
- starts with `chore: bump`
- starts with `ci(`
- contains `bump … from … to`
- has label `dependencies` or `github_actions`

If the queue is empty, print "No open dependency PRs found." and stop.

### 2. Main loop — repeat until the queue is empty

Pick the next PR from the queue and execute steps 2a–2g.
**Do not stop between PRs.** Continue until every PR has been processed.

#### 2a. Fetch PR details

Call `mcp__github__pull_request_read` with the PR number.
Record: head SHA, branch name, mergeable state, draft status.

Skip immediately (mark `skipped — draft`) if the PR is a draft.

#### 2b. Classify CI status

Call `mcp__github__get_commit` on the head SHA and inspect check-run conclusions:

| Classification | Condition |
|----------------|-----------|
| `all_passed`   | Every check is `success` or `skipped` |
| `pending`      | At least one check is `queued` or `in_progress` |
| `failed`       | At least one check is `failure` or `cancelled` |
| `no_checks`    | No check runs registered yet |

#### 2c. `pending` → skip

Record `CI pending — skipped`. Move to next PR.

#### 2d. `failed` → skip

Record which checks failed. Record `CI failed — skipped`. Move to next PR.

#### 2e. `all_passed` or `no_checks` → run local tests

```bash
poetry install --no-interaction --no-root
poetry run pytest tests/ -v --tb=short -q 2>&1 | tail -40
```

- Exit code **0** → proceed to 2f (merge).
- Non-zero → post a comment on the PR:

  > `[auto-merge] Skipped: local test suite failed. See workflow logs.`

  Record `local tests failed — skipped`. Move to next PR.

#### 2f. Merge

Call `mcp__github__merge_pull_request`:
- `repo`: `alonso07/doip_server`
- `pull_number`: PR number
- `merge_method`: `"squash"`
- `commit_title`: PR title (verbatim)
- `commit_message`: `"Auto-merged: all CI checks passed and local tests verified."`

On success → record `merged ✓`.

On conflict or error → post a comment:

  > `[auto-merge] Merge failed: <error message>.`

  Record `merge conflict — skipped`. Move to next PR.

#### 2g. After each merge — refresh the queue

Re-call `mcp__github__list_pull_requests` (state=`open`) and rebuild the queue
with the same filter. This picks up any PRs that Dependabot rebased onto the
freshly-merged commit. Continue the loop with the refreshed queue.

### 3. Final summary

After the queue is exhausted, print:

```
========================================
  Dependency PR Auto-Merge — Summary
========================================
PR    | Title                                | Action
------|--------------------------------------|----------------------
#32   | chore(deps): bump X 1.0→1.1          | merged ✓
#34   | chore(deps-dev): bump Y 2.0→2.1      | merged ✓
#36   | chore(deps): bump Z 3.0→4.0          | CI failed — skipped
#38   | ci(deps): bump actions/checkout v5→v6 | CI pending — skipped
========================================
Merged: 2   Skipped: 2   Total: 4
```

## Safety rules

- **Never** merge a PR with `pending` or `failed` CI checks.
- **Never** merge a PR when local tests exit non-zero.
- **Never** force-push, close, or delete any PR branch.
- If `mergeable` is `"conflicting"` in step 2a, skip immediately — record `conflict — skipped`.
- The squash merge keeps main history linear and clean.

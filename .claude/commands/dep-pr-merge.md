# Dependency PR Review and Auto-Merge

Review all open dependency-update PRs on `alonso07/doip_server`, run the test suite
against each one, and merge any PR whose CI checks have fully passed.

## Steps

### 1. List open dependency PRs

Use `mcp__github__list_pull_requests` (state=open) on repo `alonso07/doip_server`.
Keep only PRs whose title matches one of these patterns (case-insensitive):
- starts with `chore(deps`
- starts with `chore: bump`
- starts with `ci(`
- contains `bump … from … to`
- label `dependencies` or `github_actions`

If no matching PRs are found, report "No open dependency PRs found." and stop.

### 2. For each dependency PR (process one at a time)

#### 2a. Fetch PR details

Call `mcp__github__pull_request_read` with the PR number to get the head SHA,
branch name, and merge status.

#### 2b. Check CI status

Use `mcp__github__search_pull_requests` or `mcp__github__get_commit` on the head SHA
to determine check-run conclusions. Classify the PR as one of:

| State | Meaning |
|-------|---------|
| **all_passed** | Every required check is `success` or `skipped` |
| **pending** | At least one check is still `queued` or `in_progress` |
| **failed** | At least one check is `failure` or `cancelled` |
| **no_checks** | No CI checks have been registered yet |

#### 2c. If state is `pending`

Report the PR as still running and skip it (do NOT merge).

#### 2d. If state is `failed`

Report which checks failed and skip (do NOT merge).

#### 2e. If state is `all_passed`

Run the local test suite to double-check before merging:

```bash
cd /home/user/doip_server
poetry install --no-interaction --no-root
poetry run pytest tests/ -v --tb=short -q 2>&1 | tail -30
```

- If **tests pass** (exit code 0): proceed to merge (step 2f).
- If **tests fail**: report the failures, add a comment on the PR explaining
  why auto-merge was skipped, and do NOT merge.

#### 2f. Merge the PR

Call `mcp__github__merge_pull_request` with:
- `repo`: `alonso07/doip_server`
- `pull_number`: the PR number
- `merge_method`: `"squash"`
- `commit_title`: the PR title
- `commit_message`: `"Auto-merged after all CI checks passed and local tests verified."`

After merging, report: `✓ PR #<N> merged: <title>`

#### 2g. If state is `no_checks`

Run the local test suite (same commands as 2e).

- If **tests pass**: merge (step 2f) and note that CI had not yet run.
- If **tests fail**: skip and report the failures.

### 3. Summary

After processing all dependency PRs, print a table:

```
PR   | Title                          | Action
-----|--------------------------------|------------------
#32  | chore(deps): bump X from 1→2   | merged ✓
#34  | chore(deps): bump Y from 3→4   | CI pending — skipped
#36  | chore(deps): bump Z from 5→6   | tests failed — skipped
```

## Notes

- Never merge a PR that has any failed or pending CI check **and** failing local tests.
- Never force-push or close a PR that you did not merge.
- If `mcp__github__merge_pull_request` returns a conflict error, report it and skip.
- The squash merge method keeps the main branch history clean.

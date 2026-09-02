---
name: speckit-ship
description: Use when the user wants to finalize an implementation, run /speckit.ship, commit changes and raise pull requests for affected repos, update Jira child stories with PR links, or complete PDLC post-implement governance (Phase 8D through Checkpoint 5).
---

# speckit-ship

Post-implementation phase — commit changes, raise pull requests, and update Jira child stories for a completed feature.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Finalise a completed implementation by executing PDLC post-implement governance:
- Update `workflow-state.md` to mark Phase 8C complete.
- Add implementation comments to Jira child stories (Phase 8D).
- Present CHECKPOINT 4 and await user confirmation before any PR.
- Commit, push, and raise pull requests for all affected repos (Phase 9).
- Update Jira child stories with PR links.
- Close out at CHECKPOINT 5.

Run this skill **after** `speckit.implement` has produced its `## Implementation Complete` report.

## HARD STOP Rules

**Rule 1 — Never exit silently.** You MUST produce at minimum one message explaining what happened before stopping.

**Rule 2 — STORY_ID is required.** Scan `$ARGUMENTS` for a token matching `STORY_ID=<value>`. If not found, stop with:

```text
## Ship Agent — HARD STOP: Missing STORY_ID

Provide STORY_ID as the first token, e.g.:
  /speckit.ship STORY_ID=SCRUM-43
```

**Rule 3 — Never create a PR before CHECKPOINT 4 is confirmed by the user.** If the user has not explicitly typed "yes" at the CHECKPOINT 4 gate, do not proceed to Phase 9.

**Rule 4 — Never merge PRs.** Creation and re-use only.

**Rule 5 — Allowed GitHub hosts only.** Never create PRs against non-GitHub remotes. Allowed hosts: `github.com` and `github.ibm.com` only (default-deny all others).

## Entry Validation

1. Resolve `FEATURE_DIR = <repo-root>/specs/<STORY_ID>`.
2. Read `specs/<STORY_ID>/workflow-state.md`.
3. Check that `Phase 8C: Implement` is either marked `[x]` in Completed Phases **or** that `impl-queue.md` (if present) has all entries ticked `[x]`. If neither condition is met, warn:

   ```text
   ## Ship Agent — Warning: Implementation May Be Incomplete

   workflow-state.md does not show Phase 8C as complete.
   This may mean speckit.implement has not finished, or workflow-state.md was not updated.

   Type **yes** to proceed anyway, or **no** to abort and run /speckit.implement first.
   ```

   Wait for user confirmation before continuing.

---

## PDLC Orchestration — Post-Implement

> This section executes only when STORY_ID has been resolved and Entry Validation has passed.

After the implementation is complete and the completion report has been output, execute these PDLC governance steps.

**State Update — Phase 8C complete:**
In `specs/<STORY_ID>/workflow-state.md`, set `CURRENT_STAGE` to `CHECKPOINT_4_PENDING` and mark `[x] Phase 8C: Implement`.

### Phase 8D — Post-Implementation Jira Story Updates

For every affected sibling repo (all repos excluding the pdlc repo), update the child Jira story with the tasks completed for that repo.

> **Formatting rule**: When calling any Jira MCP tool, always pass body text with actual line breaks — never use `\n` escape sequences.

1. Read `specs/<STORY_ID>/tasks.md` and group all completed tasks (`[x]`) by their target repo.

2. For each repo that has at least one completed task:
   a. Collect the list of completed task descriptions for that repo.
   b. Collect the list of files added or modified in that repo during Phase 8C.
   c. Build a structured Jira comment (substitute all placeholders, use real newlines):

      ```
      Implementation complete for repo `<REPO>`:

      Completed tasks:
      - <task description 1>
      - <task description 2>
      ...

      Files modified/created:
      - <file path 1>
      - <file path 2>
      ...

      Validation:
      - Unit tests: PASSED
      - Compile check: PASSED
      ```

   d. Add the comment to the child Jira story (from `Child Stories` in `workflow-state.md`) using the Jira MCP tool.
   e. Transition the child Jira story to `In Progress` (or the nearest equivalent status) using the Jira MCP tool.

3. If a Jira comment or transition call fails, log `FAILED: <reason>` and continue. Do not block the workflow.

4. Display a summary table:

   | Repo | Child Story | Tasks Completed | Jira Comment Added | Status Transition |
   |------|-------------|-----------------|-------------------|------------------|
   | `<repo>` | `<key>` | `<n>` | `YES` / `NO (error)` | `UPDATED` / `FAILED` |

**State Update — Phase 8D complete:**
In `specs/<STORY_ID>/workflow-state.md`, mark `[x] Phase 8D: Jira Stories Updated`.

### CHECKPOINT 4 — Validation Complete

Present:
- `tasks.md` with all tasks checked off.
- A summary of every file added or modified, grouped by repo.
- Confirmation that validation passed: unit tests, compilation checks, and linting all successful.
- Phase 8D Jira update summary: per-repo child story comment and status transition results.
- Per-repo git status snapshot for changed repos (staged, unstaged, untracked).

Ask the user:
> "Validation phase complete. Unit tests, compilation, and code quality checks have passed. Child Jira stories have been updated with completed task details (Phase 8D).
> Here is a summary of all changes made.
> Type **yes** to proceed to commit and pull request creation, or describe any changes you want made first."

Do not create any PR until the user confirms.

**State Update — CHECKPOINT 4 confirmed:**
In `specs/<STORY_ID>/workflow-state.md`, set `CURRENT_STAGE` to `PHASE_9_PENDING` and mark `[x] CHECKPOINT 4: Validation Complete`.

### Phase 9 — Raise Pull Requests

Finalize validated changes by committing and creating pull requests for each affected repo. Read `specs/<STORY_ID>/workflow-state.md` and load the `Child Stories` mapping before proceeding.

#### Guardrails

- Never create a PR before validation has completed and CHECKPOINT 4 is confirmed.
- Never create duplicate PRs for the same repo/branch pair — always check for an existing open PR first.
- Never create PRs against non-GitHub remotes. Allowed hosts: `github.com` and `github.ibm.com` only (default-deny all others).
- Never switch branches in the orchestrator repo.
- Never merge PRs — creation only.
- Do not use shell tools. Use MCP git tools for all git operations and GitHub MCP tools for all PR operations.

#### Branch name rules

- **Orchestrator repo** (pdlc repo - the current one): branch is exactly `<STORY_ID>`. Only stage files within `specs/<STORY_ID>/` — never stage files outside `specs/`.
- **Sibling repos**: branch is exactly the repo's **child story key** from `workflow-state.md > Child Stories` (e.g. `DPDE-14`), not the parent story key.

#### Per-repo steps (repeat for every affected repo)

For each repo in the affected repos list:

1. **Pre-checks** — confirm in order:
   - Path is a git repository.
   - Current branch matches the expected branch name.
   - `origin` remote URL host is `github.com` or `github.ibm.com`. If not, mark `BLOCKED` and skip PR creation for this repo.
   - Validation summary is available from CHECKPOINT 4. If missing, mark `BLOCKED`.
   - GitHub MCP tools are available.

2. **Finalize git state**:
   - Inspect working tree: staged, unstaged, untracked files.
   - Stage only the appropriate scope:
     - Orchestrator repo: `git add specs/<STORY_ID>/` only.
     - Sibling repos: stage all changed files in the repo root.
   - If uncommitted changes exist, create a commit:
     - Sibling repo commit message: `<CHILD_STORY_KEY>: <story title>`
     - Orchestrator repo commit message: `<STORY_ID>: <story title>`
   - Ensure the working tree is clean before PR operations.

3. **Push branch**:
   - Push the expected branch to `origin`, setting upstream tracking if missing.

4. **Detect existing PR**:
   - Use GitHub MCP tools to list open PRs with head `<expected-branch-name>` and base `main`.
   - If one exists, reuse it and record `ALREADY_EXISTS`.

5. **Create PR** (only when no open PR exists):
   - Title:
     - Sibling repos: `<CHILD_STORY_KEY>: <story title>`
     - Orchestrator repo: `<STORY_ID>: <story title>`
   - Body (use real newlines):
     ```
     ## Summary
     <repo-specific summary of implemented changes>

     ## Validation
     - Unit tests: <PASSED / FAILED / SKIPPED>
     - Compile/lint: <PASSED / FAILED / SKIPPED>

     ## Traceability
     - Parent story: <STORY_ID>
     - Child story: <CHILD_STORY_KEY> (sibling repos only)
     - Spec artifacts: specs/<STORY_ID>/spec.md, specs/<STORY_ID>/plan.md, specs/<STORY_ID>/tasks.md
     - Commit: <commit hash> — <commit message>
     ```
   - Use GitHub MCP tools to create the PR.

6. **Check PR review state** after creation or reuse:
   - **`CHANGES_REQUESTED`**: Fetch all review comments. Present them and ask: "The PR has reviewer comments requiring changes. Would you like me to apply the suggested changes? (yes / no / apply-specific: \<comment numbers\>)"
     - **yes**: apply all suggestions, commit `<STORY_ID>: address review comments`, push, re-evaluate.
     - **apply-specific**: apply only the identified comments, commit, push, re-evaluate.
     - **no**: mark `BLOCKED — CHANGES_REQUESTED`, provide remediation steps.
   - **`APPROVED`**: continue normally.
   - **`REVIEW_REQUIRED` / no reviews yet**: report `PENDING_REVIEW`, surface PR URL. Do not block.

7. If pre-checks, commit, or push fail for a repo: record the failure, continue evaluating remaining repos, and report all blockers at the end.

#### Per-repo report table

After all repos are processed, display:

| Repo | Branch | Commit | PR Result | PR URL |
|------|--------|--------|-----------|--------|
| `<repo>` | `<branch>` | `CREATED` / `SKIPPED_NO_CHANGES` / `BLOCKED` | `CREATED` / `ALREADY_EXISTS` / `BLOCKED` | `<url or —>` |

#### Post-PR Jira Updates

After all PRs have been created or confirmed, for each affected sibling repo:

1. Transition the child Jira story to `In Review` using the Jira MCP tool.
2. Add a comment to the child Jira story (use real newlines):

   ```
   Pull request raised for `<REPO>`.

   PR: <PR_URL>
   Branch: <child-story-key>
   Parent story: <STORY_ID>
   ```

3. If a Jira transition or comment call fails, log the failure and continue.

Display a per-repo Jira update summary:

| Repo | Child Story | Jira Status | Comment Added |
|------|-------------|-------------|---------------|
| `<repo>` | `<key>` | `UPDATED` / `SKIPPED (no PR)` / `FAILED` | `YES` / `NO` |

### CHECKPOINT 5 — PRs Created and Jira Updated

Present:
- Per-repo PR status (`CREATED`, `ALREADY_EXISTS`, `BLOCKED`).
- PR links for all created/reused PRs.
- Per-repo Jira child story update summary (status transition + comment result).
- Any blockers with exact remediation needed.

Ask the user:
> "Pull request phase complete. Child Jira stories have been updated with PR links.
> Type **yes** to confirm the workflow is complete, or describe any PR or Jira updates you want first."

**State Update — CHECKPOINT 5 confirmed:**
In `specs/<STORY_ID>/workflow-state.md`, set `CURRENT_STAGE` to `COMPLETE`, mark `[x] Phase 9: Raise PRs` and `[x] CHECKPOINT 5: PRs Created`, and record all created/reused PR links under `Key Data > Implementation PRs`. Update `Last Updated` to today's date.

**Invoke observe-workflow**: After the state update, unconditionally invoke the `observe-workflow` skill with the following four arguments resolved in this order:
- ARG1 (`db_path`): read `settings.yaml` → `observe.db_path`
- ARG2 (`first_message`): the **first user message sent in the current chat session** (the literal text of the first `user` role turn in this conversation — this is what the query script matches against in the database)
- ARG3 (`project_id`): read `settings.yaml` → `observe.project_id`
- ARG4 (`jira_id`): the active Jira story ID (already resolved from `$ARGUMENTS`)

**Invoke observe-workflow-reconcile**: Immediately after `observe-workflow` completes (regardless of whether it succeeded or produced an N/A stub), invoke the `observe-workflow-reconcile` skill with:
- ARG1 (`jira_id`): the active Jira story ID (already resolved from `$ARGUMENTS`)

`db_path` and `project_id` are read by the skill itself from `settings.yaml` — do not pass them as arguments.

This reconciliation pass performs a broad LIKE search across the Bob DB for all tasks mentioning the JIRA story ID, infers the workflow phase for each row, patches any N/A stubs in `specs/<STORY_ID>/observe-workflow.md`, and appends any previously unrecorded phases as new entries.

> **Workflow complete.** All phases from specification through pull request creation have been executed. The story `<STORY_ID>` is ready for code review.

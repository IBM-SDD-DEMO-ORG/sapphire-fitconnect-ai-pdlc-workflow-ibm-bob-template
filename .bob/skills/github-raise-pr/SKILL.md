---
name: github-raise-pr
description: Use when the user wants to create governed GitHub pull requests for validated story branches across affected repos, run /github.raise-pr, commit changes, push branches, or detect and handle existing PRs across multiple repos with PR review state handling.
---

# github-raise-pr

Create governed GitHub pull requests for validated story branches across affected repos.

## User Input

```text
$ARGUMENTS
```

Use any provided input first. If key fields are missing, infer safely from available artifacts and report assumptions. Run in "Advanced" mode.

## Purpose

Finalize validated repo changes by creating required commits and then creating or reusing pull requests in a repeatable, governed way.

## Guardrails

- Never create a PR before validation has completed and the user has approved proceeding.
- Never create duplicate PRs for the same repo/branch pair.
- Never create PRs against non-GitHub remotes. Allowed hosts: github.com and github.ibm.com only.
- Never switch branches in the orchestrator repo.
- Never merge PRs; creation only.
- Do not use shell tools in this workflow.
- Use MCP filesystem tools for all file operations and MCP git tools for all git operations.

## Required Inputs Per Repo

- Story ID (for example: SAP-1234) — parent story key, used for the orchestrator repo branch and PR traceability
- Per-repo branch name — for sibling repos, this is the **child story key** (e.g., `SCRUM-11`) from `workflow-state.md > Child Stories`; for the orchestrator repo, this is the parent story key
- Repo path
- Story title
- Validation summary (unit tests, compile/lint outcomes)
- Target base branch (default: main)

## Workflow

1. Collect target repos from user input. If not provided, infer from `specs/<STORY_ID>/tasks.md` and include only repos with code changes in this run.
2. For each repo, run these checks in order:
   - Confirm the path is a git repository.
   - Determine the expected branch name for this repo: use the child story key (from the caller-provided per-repo branch mapping) for sibling repos; use the parent story ID for the orchestrator repo.
   - Confirm current branch is exactly the expected branch name for this repo.
   - Confirm `origin` remote URL host is explicitly allowlisted: `github.com` or `github.ibm.com` only (default-deny all other hosts).
   - Confirm validation summary is provided or inferable from workspace artifacts; if missing, mark `BLOCKED`.
   - Confirm GitHub MCP tools are available for PR operations.
3. For each repo, finalize post-validation git state:
   - Inspect working tree status (staged, unstaged, untracked).
   - If uncommitted changes exist, stage changes for that repo only.
   - Create at least one non-empty commit when changes are present.
   - Commit message format: `<STORY_ID>: <story title>` (or equivalent repo-specific scope).
   - Do not amend commits unless explicitly requested.
   - Ensure working tree is clean (`git status --porcelain` empty) before PR operations.
4. Push branch if needed using MCP git tooling:
   - Push the repo's expected branch (child story key for sibling repos; parent story ID for orchestrator repo) to `origin` and set upstream tracking when missing.
5. Detect existing PR before creating a new one:
   - Use GitHub MCP tools to list open PRs by head `<expected-branch-name>` (child story key or parent story ID as appropriate) and base `<base>`.
   - If one exists, reuse it and report `ALREADY_EXISTS`.
6. Create PR when no open PR exists:
   - Title format: `<CHILD_STORY_KEY>: <story title>` for sibling repos; `<STORY_ID>: <story title>` for the orchestrator repo
   - Body includes:
     - Summary of implemented changes (repo specific)
     - Validation evidence: unit tests and compile/lint status
     - Story traceability: reference to parent story `<STORY_ID>`, child story key (for sibling repos), and `specs/<STORY_ID>/` artifacts used
     - Commit evidence: commit hash and commit message created in this phase when applicable
   - Use GitHub MCP tools to create the PR.
7. Return a concise per-repo report with:
   - Repo
   - Branch
   - Base branch
   - Commit result (`CREATED`, `SKIPPED_NO_CHANGES`, or `BLOCKED`)
   - PR result (`CREATED`, `ALREADY_EXISTS`, or `BLOCKED`)
   - PR URL (if available)
   - Any blockers and remediation steps

## PR Review State Handling

After a PR is created or found to already exist, check its current review state using GitHub MCP tools before returning the final report.

### `CHANGES_REQUESTED` (rejection)

If any reviewer has submitted a `CHANGES_REQUESTED` review on the PR:

1. Fetch all review comments from the PR using GitHub MCP tools.
2. Surface each comment in the output: reviewer login, file path (if applicable), line (if applicable), and comment body.
3. **Ask the user**: "The PR has reviewer comments requiring changes. Would you like me to apply the changes suggested in these comments? (yes / no / apply-specific: <comment numbers>)"
   - Wait for the user's explicit response before proceeding.
   - If **yes**: attempt to apply all suggested changes to the affected files in the working branch, commit with message `<STORY_ID>: address review comments`, push to origin, and re-evaluate the PR review state.
   - If **apply-specific**: apply only the comments identified by the user-supplied numbers, commit, push, and re-evaluate.
   - If **no**: skip auto-apply, mark the PR result as `BLOCKED — CHANGES_REQUESTED`, and return remediation steps (see below) so the user can act manually.
4. Do NOT proceed with any further phases for this repo until the review state is resolved.
5. If the user declined auto-apply, return remediation steps:
   - Address each reviewer comment in the working branch.
   - Push the updated commits to the same branch.
   - Re-run this skill to re-evaluate the PR state.

### `APPROVED`

If at least one approval exists and no `CHANGES_REQUESTED` review is outstanding, continue normally.

### `REVIEW_REQUIRED` / no reviews yet

If the PR is open but has no reviews, report `PENDING_REVIEW` and surface the PR URL so the caller can share it with approvers. Do not block; allow the caller to decide whether to wait.

## Failure Handling

If any repo fails pre-checks, commit finalization, push checks, or has an active `CHANGES_REQUESTED` review, do not proceed with PR approval gate invocation for that repo. Continue evaluating remaining repos and report all blockers clearly at the end.

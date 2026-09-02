---
name: pdlc-pr-approval-gate
description: Use when the user wants to check PR approval status for a spec, plan, or tasks artifact, run /pdlc.pr-approval-gate, or verify that a GitHub PR has been approved by the required role configured in settings.yaml. Returns PASS or FAIL with remediation steps.
---

# pdlc-pr-approval-gate

Generic PR approval gate for spec, plan, and tasks artifacts. Reads required approver role from settings.yaml.

## User Input

```text
$ARGUMENTS
```

Expected argument format (space-separated or key=value):
- `STORY_ID=<key>` — Jira story key (e.g. SCRUM-10)
- `ARTIFACT=spec|plan|tasks` — which artifact is being gated
- `SKIP_APPROVAL_GATES=true|false` — optional test-mode bypass toggle

If arguments are absent, infer `STORY_ID` from the current git branch or active `specs/` folder. Infer `ARTIFACT` from which phase triggered the hook (default: `plan`).

## Objective

Return `PASS` only if the GitHub PR for the `<STORY_ID>` branch has an approval from the required role for the given artifact type (as configured in `settings.yaml`). Otherwise return `FAIL` with remediation steps.

If `SKIP_APPROVAL_GATES=true` is explicitly provided, treat this as test mode and return `PASS` without PR approval checks.

## Steps

0. Parse `SKIP_APPROVAL_GATES` from arguments.
   - If `SKIP_APPROVAL_GATES=true`, return immediate test bypass result in the required output shape:

```text
HOOK_RESULT: PASS
HOOK_NAME: PR Approval Gate — <ARTIFACT>
STORY_ID: <story id>
ARTIFACT: <spec|plan|tasks>
APPROVER_ROLE: TEST_BYPASS
APPROVER_IDENTITY: TEST_BYPASS
PR: TEST_BYPASS
APPROVED_BY: TEST_BYPASS
MERGED_AT: TEST_BYPASS
APPROVAL_AT: TEST_BYPASS
DETAILS: TEST_BYPASS enabled via SKIP_APPROVAL_GATES=true
REMEDIATION: Disable SKIP_APPROVAL_GATES to enforce normal approval gate checks
```

   - If absent or false, continue with normal gate evaluation.

1. Resolve `STORY_ID` and `ARTIFACT` from arguments or by inference.

2. Read `settings.yaml` from the workspace root and resolve:
   - `approver_role` = `pdlc.approvals.<ARTIFACT>.approver_role`
   - `require_merge` = `pdlc.approvals.<ARTIFACT>.require_merge`
   - GitHub identity = `pdlc.roles.<approver_role>.github_team` and/or `pdlc.roles.<approver_role>.github_users`
   - If `settings.yaml` is absent or the key is missing, use defaults:
     - `spec`  → role `product_owner`, require_merge `true`
     - `plan`  → role `fde`, require_merge `false`
     - `tasks` → role `fde`, require_merge `false`
   - Note any fallback used in output.

3. Find the PR associated with head branch `<STORY_ID>` to `main`:
   - For `ARTIFACT=spec`: find the specification PR (may be merged; look at both open and recently merged PRs).
   - For `ARTIFACT=plan` or `tasks`: find the open (or most recently closed) design PR.

4. Inspect PR review state before validating gate conditions:
   - Use GitHub MCP tools to fetch all reviews on the PR.
   - If any reviewer has submitted a `CHANGES_REQUESTED` review, set `HOOK_RESULT` to `FAIL`, set `DETAILS` to `CHANGES_REQUESTED — reviewer <login>: <comment body>` for each such review, and set `REMEDIATION` to "Address the reviewer's requested changes on branch `<STORY_ID>`, push the updated commits, then re-run this gate." Return immediately — do not proceed with further approval checks.
   - Otherwise, continue:
   - At least one approval exists on the PR from the resolved `approver_role` team/users.
   - If `require_merge: true`, PR state must also be `MERGED`.
   - Required status checks are passing (or not required by repo policy).

5. Output result in this exact shape:

```text
HOOK_RESULT: PASS|FAIL
HOOK_NAME: PR Approval Gate — <ARTIFACT>
STORY_ID: <story id>
ARTIFACT: <spec|plan|tasks>
APPROVER_ROLE: <role name from settings>
APPROVER_IDENTITY: <github_team or user list>
PR: <url or NONE>
APPROVED_BY: <reviewer login(s) or NONE>
MERGED_AT: <timestamp or NONE — only relevant when require_merge: true>
APPROVAL_AT: <timestamp or NONE>
DETAILS: <short reason>
REMEDIATION: <next action if FAIL, e.g. "Request review from <approver_identity> on <PR_URL>">
```

## Result Rules

- `PASS`: required approval from configured role present; merged if `require_merge: true`.
- `FAIL`: any required condition missing.

Do not start or resume implementation work in this command; only report gate status.

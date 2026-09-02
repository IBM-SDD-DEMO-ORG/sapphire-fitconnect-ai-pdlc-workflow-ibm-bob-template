---
name: speckit-impl-queue
description: Use when the user wants to generate an implementation queue, run /speckit.impl-queue, or create an ordered list of speckit.implement invocations (one per repo/phase bucket) for a feature story before beginning implementation.
---

# speckit-impl-queue

Generate the implementation queue for a feature story — an ordered list of speckit.implement invocations (one per repo/phase bucket) covering all remaining tasks.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Generate `impl-queue.md` for the given story: an ordered list of `speckit.implement` invocations, one per repo/phase bucket, that exhausts all remaining `[ ]` tasks. **Does not implement any code.**

Use this skill when you want to break a large implementation into individually invocable, trackable chunks before starting work. Each queue entry maps to exactly one `speckit.implement STORY_ID=<id> REPO=<repo> PHASE=<phase>` call.

## HARD STOP Rules

**Rule 1 — Never exit silently.** You MUST produce at minimum one message explaining what happened before stopping. An empty return is a protocol violation.

**Rule 2 — STORY_ID is required.** Scan `$ARGUMENTS` for a token matching `STORY_ID=<value>` or a bare Jira-style story ID (e.g. `DPDE-224`, matching `[A-Z]+-\d+`). Normalise a bare ID to `STORY_ID=<value>` in working memory. If neither form is found, stop immediately with:

```text
## Queue Generator — HARD STOP: Missing STORY_ID

Provide STORY_ID as the first token, e.g.:
  /speckit.impl-queue STORY_ID=SCRUM-43
```

## PDLC Entry Gates

> **Activation**: Only when `$ARGUMENTS` contains `STORY_ID=<value>` or a bare Jira-style story ID. Skip if no story ID is present or if `SKIP_APPROVAL_GATES=true` (log `TEST_BYPASS active: Phase 8A/8B gates skipped`).

**Gate 1 — CHECKPOINT 3: Ready for Implementation**

Read `specs/<STORY_ID>/workflow-state.md` and check that `CHECKPOINT 3: Ready for Implementation` is marked `[x]` under Completed Phases.

If not marked, present the checkpoint confirmation prompt:

> "CHECKPOINT 3: Ready for Implementation has not been recorded as confirmed.
> Plan has been approved (Phase 4B), tasks have been analyzed (Phase 7B), approved (Phase 7D), and child Jira stories updated with planned tasks (Phase 7E).
> Type **yes** to confirm and proceed to queue generation, or **no** to abort and return to `/speckit.analyze` first."

If the user confirms (**yes**):
- Mark `[x] CHECKPOINT 3: Ready for Implementation` and set `CURRENT_STAGE` to `PHASE_8A_PENDING` in `workflow-state.md`.
- Continue to Gate 2.

If the user declines (**no**): stop with the message "Run `/speckit.analyze STORY_ID=<STORY_ID>` to complete CHECKPOINT 3 first."

**Gate 2 — Phase 8A: Implementation Entry Gates**

Check that `Phase 8A: Implementation Entry Gates` is marked `[x]` under Completed Phases.

If not marked, verify via GitHub MCP that the tasks PR has the required approval:

1. Read `settings.yaml` and resolve:
   - `tasks_approver_role` = `pdlc.approvals.tasks.approver_role` (default: `fde`)
   - `tasks_require_merge` = `pdlc.approvals.tasks.require_merge` (default: `true`)
   - GitHub team/users = `pdlc.roles.<tasks_approver_role>.github_team` / `.github_users`

2. Check `Key Data > Tasks PR` in `workflow-state.md`.
   - If absent, block: "No tasks PR found. Run `/speckit.analyze STORY_ID=<STORY_ID>` to commit tasks, raise the tasks PR, and obtain approval first."

3. Use GitHub MCP tools to find the tasks PR from head `<STORY_ID>` to `main` (open or merged).

4. Fetch all reviews:
   - If any reviewer submitted `CHANGES_REQUESTED`: surface reviewer login and comment. Block.
   - Otherwise verify: at least one approval from `tasks_approver_role` exists; if `tasks_require_merge: true`, PR must be `MERGED`.

5. If not met: display PR review status and block. Do not generate the queue.

**State Update — Phase 8A passed:**
In `specs/<STORY_ID>/workflow-state.md`, mark `[x] Phase 8A: Implementation Entry Gates` (if not already marked).

---

## Steps

1. **Resolve `FEATURE_DIR`**: Extract `<value>` from the `STORY_ID=<value>` token in `$ARGUMENTS`. Set `FEATURE_DIR = <repo-root>/specs/<value>`. Validate that `FEATURE_DIR` exists as a directory and contains `tasks.md`. If not, stop with a clear error:

   ```text
   ## Queue Generator — HARD STOP: FEATURE_DIR Invalid

   FEATURE_DIR: <path>
   Reason: <directory not found | tasks.md missing>
   Resolution: Run /speckit.tasks STORY_ID=<STORY_ID> to generate tasks first.
   ```

2. **Read `tasks.md`** from `FEATURE_DIR`.

3. **Construct the repo queue**: Collect the ordered list of unique `target repo` values across all tasks, by first appearance and cross-repo dependencies. A repo whose tasks are depended upon by another repo must appear first.

4. **Collect phases per repo**: For each repo in the queue, collect the distinct phase names that contain at least one `[ ]` task for that repo, in phase order (Setup → Tests → Core → Integration → Polish).

5. **Write `FEATURE_DIR/impl-queue.md`**:

   ```markdown
   # Implementation Queue — <STORY_ID>

   Generated: <today's date>

   > Each entry is one `speckit.implement` invocation. Entries are processed in order.
   > Tick `[x]` only when the corresponding invocation produces a `## Phase Complete` report.

   ## Queue

   - [ ] repo-1 / Phase 1: Setup — Kafka Topics & Avro Schema Contracts
   - [ ] repo-1 / Phase 2: Foundational — DB Migrations, Enums, JPA Entities, Repositories
   - [ ] repo-2 / Phase 2: Foundational — DB Migrations, Enums, JPA Entities, Repositories
   - [ ] repo-1 / Phase 3: ...
   ...

   ## Invocation Template

   For each entry above, invoke:
   ```
   /speckit.implement STORY_ID=<STORY_ID> REPO=<repo-name> PHASE=<exact phase label>
   ```
   ```

   Phase labels must be copied verbatim from the phase headers in `tasks.md` so the implement agent can match them with an exact string comparison.

**State Update (when STORY_ID was provided):**
In `specs/<STORY_ID>/workflow-state.md`, mark `[x] Phase 8B: Generate Implementation Queue`.

6. **Output**:

   ```text
   ## Queue Generated — <STORY_ID>

   Queue written to: specs/<STORY_ID>/impl-queue.md
   Total invocations: <N>

   | # | Repo | Phase |
   |---|------|-------|
   | 1 | <repo> | <phase> |
   | 2 | <repo> | <phase> |
   ...

   Run each entry in order:
     /speckit.implement STORY_ID=<STORY_ID> REPO=<repo-name> PHASE=<exact phase label>

   Or skip the queue and run all at once:
     /speckit.implement STORY_ID=<STORY_ID>

   When all implementations are done, raise PRs with:
     /speckit.ship STORY_ID=<STORY_ID>
   ```

7. **Invoke observe-workflow**: After outputting the queue summary, unconditionally invoke the `observe-workflow` skill with the following four arguments resolved in this order:
   - ARG1 (`db_path`): read `settings.yaml` → `observe.db_path`
   - ARG2 (`first_message`): construct the literal string `/speckit-impl-queue STORY_ID=<JIRA-ID>` where `<JIRA-ID>` is replaced with the active Jira story ID (e.g. `/speckit-impl-queue DPDE-224`). If no match is found with `STORY_ID=`, also try `/speckit-impl-queue <JIRA-ID>`. Do **NOT** use the raw user message text, do **NOT** use just the Jira ID alone — always pass the full `/speckit-impl-queue <JIRA-ID>` string as ARG2.
   - ARG3 (`project_id`): read `settings.yaml` → `observe.project_id`
   - ARG4 (`jira_id`): the active Jira story ID (already resolved from `$ARGUMENTS`)

8. **Stop.** Do not implement any code.

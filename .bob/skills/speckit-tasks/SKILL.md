---
name: speckit-tasks
description: Use when the user wants to generate an actionable tasks.md, run /speckit.tasks, break a plan into dependency-ordered implementation tasks, or proceed through PDLC tasks PR submission and approval gate. Requires plan.md to be available.
---

# speckit-tasks

Generate an actionable, dependency-ordered tasks.md for the feature based on available design artifacts.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). Run in "Advanced" mode.

## Pre-Execution Checks

**Check for extension hooks (before tasks generation)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_tasks` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    
    Wait for the result of the hook command before proceeding to the Outline.
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

---

## PDLC Orchestration — Pre-Tasks

> **Activation**: This section executes when `$ARGUMENTS` contains a `STORY_ID=<value>` token **or** a bare Jira-style story ID (e.g. `DPDE-224`, matching `[A-Z]+-\d+`). Extract the story ID from either form. If neither is detected, skip this section and proceed directly to the Outline.

### Settings Load

Read `settings.yaml` from the workspace root and resolve session variables (submitter_role, plan_approver_role, tasks_approver_role, GitHub team/users). Use defaults if any key is absent.

### Phase 6A: Tasks Entry Gates (mandatory)

Before generating tasks, verify the plan PR is approved and merged.

> **Test bypass**: If `SKIP_APPROVAL_GATES=true` is in `$ARGUMENTS`, skip all gate checks below, log `TEST_BYPASS active: Phase 6A plan gate skipped`, and proceed to Skill Auto-Detection.

1. Verify Phase 4B is complete: a plan PR exists for branch `<STORY_ID>`. Check `Key Data > Plan PR` in `specs/<STORY_ID>/workflow-state.md`.
   - If absent, block: "No plan PR found. Run `/speckit.plan STORY_ID=<STORY_ID>` to generate the plan and raise the plan PR first."

2. Read `settings.yaml` and resolve:
   - `plan_approver_role` = `pdlc.approvals.plan.approver_role` (default: `fde`)
   - `plan_require_merge` = `pdlc.approvals.plan.require_merge` (default: `true`)
   - GitHub team/users = `pdlc.roles.<plan_approver_role>.github_team` / `.github_users`

3. Use GitHub MCP tools to find the plan PR from head `<STORY_ID>` to `main` (look at both open and merged PRs).

4. Fetch all reviews on the PR:
   - If any reviewer submitted `CHANGES_REQUESTED`: surface each reviewer login and comment. Block with: "Plan PR has changes requested. Resolve the reviewer's feedback via `/speckit.plan`, then re-run `/speckit.tasks`."
   - Otherwise verify: at least one approval from the resolved `plan_approver_role` team/users exists.
   - If `plan_require_merge: true`, verify PR state is `MERGED`.

5. If gate conditions are not met: display current PR review status and block. Do not proceed to task generation until gate passes.

**State Update — Phase 6A Entry Gates passed:**
In `specs/<STORY_ID>/workflow-state.md`, mark `[x] Phase 6A: Tasks Entry Gates` under Completed Phases.

### Skill Auto-Detection

Scan `$ARGUMENTS`, `specs/<STORY_ID>/spec.md`, and `specs/<STORY_ID>/plan.md` to detect the tech stack and load relevant skills using `read_file`. Print evidence block:

```text
## Skills Loaded

- Detected technologies: <comma-separated list or "none">
- Skills loaded: <paths or "none">
```

Load parent skill routers from `.bob/skills` for any detected technology (Java → `.bob/skills/java/SKILL.md`, GraphQL → `.bob/skills/graphql/SKILL.md`, React → `.bob/skills/react/SKILL.md`). Apply guidance throughout task generation.

---

## Outline

1. **Setup**: Run `.specify/scripts/powershell/check-prerequisites.ps1 -Json` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load design documents**: Read from FEATURE_DIR:
   - **Required**: plan.md (tech stack, libraries, structure), spec.md (user stories with priorities)
   - **Optional**: data-model.md (entities), contracts/ (interface contracts), research.md (decisions), quickstart.md (test scenarios)
   - Note: Not all projects have all documents. Generate tasks based on what's available.
   - **Platform and codebase context**: Read `AGENTS.md` from the workspace root. Extract the repo registry and per-repo conventions for every repo identified as affected in plan.md.

     **For each affected repo, check if CodeGraph is available**:
     
     **CodeGraph Detection**:
     - Check if `../<repo-name>/.codegraph/` directory exists
     - If exists: Repository is indexed by CodeGraph
     - If not exists: Fall back to manual file reading

     **IF CodeGraph Available**:
     1. **First**, check if `codegraph_explore` MCP tool is available in your tool list
     2. **If MCP tool available**: Use `codegraph_explore` with natural language query
     3. **If MCP tool NOT available**: Try shell command `codegraph explore "<query>"`
     4. **If shell command fails**: Fall back to manual file reading (see below)
     5. **Always report** which method succeeded in the task generation summary
     
     Query examples for task-level details:
     * "Show all classes and methods in <module-name>"
     * "Find test patterns and naming conventions"
     * "Show existing <entity> model fields and their relationships"
     * "Show all methods in <ClassName>"
     
     Extract from results: file paths, class names, method signatures, test patterns, existing vs new files

     **IF CodeGraph NOT Available**:
     - Fall back to manual exploration (current approach)
     - Explore each affected sibling repository at `../<repo-name>/` to confirm which files already exist versus which need to be created
     - Do NOT read build outputs (`target/`, `dist/`, `node_modules/`)

     Ensure every task description references the correct absolute file path and existing class/method names rather than invented placeholders.

3. **Execute task generation workflow**:
   - Load plan.md and extract tech stack, libraries, project structure
   - Load spec.md and extract user stories with their priorities (P1, P2, P3, etc.)
   - If data-model.md exists: Extract entities and map to user stories
   - If contracts/ exists: Map interface contracts to user stories
   - If research.md exists: Extract decisions for setup tasks
   - Generate tasks organized by user story (see Task Generation Rules below)
   - Generate dependency graph showing user story completion order
   - Create parallel execution examples per user story
   - Validate task completeness (each user story has all needed tasks, independently testable)

4. **Generate tasks.md**: Use `.specify/templates/tasks-template.md` as structure, fill with:
   - Correct feature name from plan.md
   - Phase 1: Setup tasks (project initialization)
   - Phase 2: Foundational tasks (blocking prerequisites for all user stories)
   - Phase 3+: One phase per user story (in priority order from spec.md)
   - Each phase includes: story goal, independent test criteria, tests (if requested), implementation tasks
   - Final Phase: Polish & cross-cutting concerns
   - All tasks must follow the strict checklist format (see Task Generation Rules below)
   - Clear file paths for each task
   - Dependencies section showing story completion order
   - Parallel execution examples per story
   - Implementation strategy section (MVP first, incremental delivery)

5. **Report**: Output path to generated tasks.md and summary:
   - Total task count
   - Task count per user story
   - Parallel opportunities identified
   - Independent test criteria for each story
   - Suggested MVP scope (typically just User Story 1)
   - Format validation: Confirm ALL tasks follow the checklist format

Context for task generation: $ARGUMENTS

The tasks.md should be immediately executable - each task must be specific enough that an LLM can complete it without additional context.

## Task Generation Rules

**CRITICAL**: Tasks MUST be organized by user story to enable independent implementation and testing.

**Tests are OPTIONAL**: Only generate test tasks if explicitly requested in the feature specification or if user requests TDD approach.

### Checklist Format (REQUIRED)

Every task MUST strictly follow this format:

```text
- [ ] [TaskID] [P?] [Story?] Description with file path
```

**Format Components**:

1. **Checkbox**: ALWAYS start with `- [ ]` (markdown checkbox)
2. **Task ID**: Sequential number (T001, T002, T003...) in execution order
3. **[P] marker**: Include ONLY if task is parallelizable (different files, no dependencies on incomplete tasks)
4. **[Story] label**: REQUIRED for user story phase tasks only
   - Format: [US1], [US2], [US3], etc. (maps to user stories from spec.md)
   - Setup phase: NO story label
   - Foundational phase: NO story label  
   - User Story phases: MUST have story label
   - Polish phase: NO story label
5. **Description**: Clear action with exact file path

**Examples**:

- ✅ CORRECT: `- [ ] T001 Create project structure per implementation plan`
- ✅ CORRECT: `- [ ] T005 [P] Implement authentication middleware in src/middleware/auth.py`
- ✅ CORRECT: `- [ ] T012 [P] [US1] Create User model in src/models/user.py`
- ✅ CORRECT: `- [ ] T014 [US1] Implement UserService in src/services/user_service.py`
- ❌ WRONG: `- [ ] Create User model` (missing ID and Story label)
- ❌ WRONG: `T001 [US1] Create model` (missing checkbox)
- ❌ WRONG: `- [ ] [US1] Create User model` (missing Task ID)
- ❌ WRONG: `- [ ] T001 [US1] Create model` (missing file path)

### Task Organization

1. **From User Stories (spec.md)** - PRIMARY ORGANIZATION:
   - Each user story (P1, P2, P3...) gets its own phase
   - Map all related components to their story:
     - Models needed for that story
     - Services needed for that story
     - Interfaces/UI needed for that story
     - If tests requested: Tests specific to that story
   - Mark story dependencies (most stories should be independent)

2. **From Contracts**:
   - Map each interface contract → to the user story it serves
   - If tests requested: Each interface contract → contract test task [P] before implementation in that story's phase

3. **From Data Model**:
   - Map each entity to the user story(ies) that need it
   - If entity serves multiple stories: Put in earliest story or Setup phase
   - Relationships → service layer tasks in appropriate story phase

4. **From Setup/Infrastructure**:
   - Shared infrastructure → Setup phase (Phase 1)
   - Foundational/blocking tasks → Foundational phase (Phase 2)
   - Story-specific setup → within that story's phase

### Phase Structure

- **Phase 1**: Setup (project initialization)
- **Phase 2**: Foundational (blocking prerequisites - MUST complete before user stories)
- **Phase 3+**: User Stories in priority order (P1, P2, P3...)
  - Within each story: Tests (if requested) → Models → Services → Endpoints → Integration
  - Each phase should be a complete, independently testable increment
- **Final Phase**: Polish & Cross-Cutting Concerns

---

## PDLC Orchestration — Post-Tasks

> **Activation**: This section executes only when `$ARGUMENTS` contained a `STORY_ID=<value>` token or a bare Jira story ID and the PDLC Pre-Tasks section ran above.

After `tasks.md` has been generated (Outline steps 1–6 complete), execute these PDLC governance steps.

**State Update — Phase 6B complete:**
In `specs/<STORY_ID>/workflow-state.md`, set `CURRENT_STAGE` to `CHECKPOINT_2B_PENDING` and mark `[x] Phase 6B: Tasks`.

### CHECKPOINT 2B — Submitter Tasks Review Before PR Submission

Present:
- Total task count and breakdown per user story (P1 → Pn).
- Summary of parallel execution groups (`[P]` markers).
- Task-to-repo mapping (which tasks target which repos).
- Resolved `submitter_role` and `tasks_approver_role` with its GitHub team/users.

Ask the user:
> "`<submitter_role>` checkpoint: please review the generated tasks. Does everything look correct?
> Type **yes** to proceed to artifact analysis and PR submission, or describe the corrections needed."

**Correction loop** — repeat until submitter approves:
1. If the user requests corrections, apply them to `tasks.md` as instructed (re-ordering, adding, removing, or rephrasing tasks).
2. After applying corrections, present a brief summary of what changed.
3. Ask: "Are there any more corrections needed, or do the tasks look good to proceed?"
4. If more corrections requested, return to step 1. When user confirms, exit the loop.

Do not proceed to analysis or commit/push any PR until the submitter has explicitly confirmed.

**State Update — CHECKPOINT 2B approved:**
In `specs/<STORY_ID>/workflow-state.md`, set `CURRENT_STAGE` to `PHASE_7_PENDING` and mark `[x] CHECKPOINT 2B: Submitter Tasks Review`.

> **Next step**: Run `/speckit.analyze STORY_ID=<STORY_ID>` to perform cross-artifact consistency analysis, commit tasks for review, and trigger the tasks approval gate.

---

## Completion — Observability (always runs)

After all preceding steps are complete (Outline + PDLC Post-Tasks if activated), run these two steps unconditionally regardless of whether a STORY_ID was present.

6. **Invoke observe-workflow**: Unconditionally invoke the `observe-workflow` skill with the following four arguments resolved in this order:
   - ARG1 (`db_path`): read `settings.yaml` → `observe.db_path`
   - ARG2 (`first_message`): construct the literal string `/speckit-tasks STORY_ID=<JIRA-ID>` where `<JIRA-ID>` is replaced with the active Jira story ID (e.g. `/speckit-tasks DPDE-224`). If no match is found with `STORY_ID=`, also try `/speckit-tasks <JIRA-ID>`. Do **NOT** use the raw user message text, do **NOT** use just the Jira ID alone — always pass the full `/speckit-tasks <JIRA-ID>` string as ARG2.
   - ARG3 (`project_id`): read `settings.yaml` → `observe.project_id`
   - ARG4 (`jira_id`): the active Jira story ID (from `$ARGUMENTS` or `specs/*/workflow-state.md` `Story ID:`)

7. **Check for extension hooks**: After observe-workflow completes, check `.specify/extensions.yml` for `hooks.after_tasks` entries and process them per the hook rules above. Skip any hook with `command: observe-workflow` — it has already been invoked in step 6.

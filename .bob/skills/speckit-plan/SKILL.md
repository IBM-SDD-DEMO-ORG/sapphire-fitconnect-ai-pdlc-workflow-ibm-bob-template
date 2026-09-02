---
name: speckit-plan
description: Use when the user wants to execute the implementation planning workflow, run /speckit-plan, generate design artifacts (research.md, data-model.md, contracts, quickstart.md), or proceed through PDLC plan approval gate and create Jira child stories.
---

# speckit-plan

Execute the implementation planning workflow using the plan template to generate design artifacts.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). Run in "Advanced" mode.

## Pre-Execution Checks

**Check for extension hooks (before planning)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_plan` key
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

## PDLC Orchestration — Pre-Plan

> **Activation**: This section executes when `$ARGUMENTS` contains a `STORY_ID=<value>` token **or** a bare Jira-style story ID (e.g. `DPDE-224`, matching `[A-Z]+-\d+`). Extract the story ID from either form. If neither is detected, skip this section and proceed directly to the Outline.

### Settings Load

Read `settings.yaml` from the workspace root and resolve the same session variables as in `speckit-specify` (submitter_role, spec_approver_role with require_merge, plan_approver_role, tasks_approver_role, and their GitHub team/users). Use defaults if any key is absent.

### Phase 3C: Plan Entry Gates (mandatory)

Before proceeding to planning, verify that the spec approval gate is satisfied.

> **Test bypass**: If `SKIP_APPROVAL_GATES=true` is in `$ARGUMENTS`, skip all gate checks below, log `TEST_BYPASS active: Phase 3C spec gate skipped`, and proceed to Skill Auto-Detection.

1. Verify Phase 3A is complete: a spec PR exists for branch `<STORY_ID>`. Check `Key Data > Spec PR` in `specs/<STORY_ID>/workflow-state.md`.
   - If absent, block: "No spec PR found. Run `/speckit-specify STORY_ID=<STORY_ID>` or `/speckit-clarify STORY_ID=<STORY_ID>` to raise the spec PR first."

2. Read `settings.yaml` and resolve:
   - `spec_approver_role` = `pdlc.approvals.spec.approver_role` (default: `product_owner`)
   - `spec_require_merge` = `pdlc.approvals.spec.require_merge` (default: `true`)
   - GitHub team/users = `pdlc.roles.<spec_approver_role>.github_team` / `.github_users`

3. Use GitHub MCP tools to find the spec PR from head `<STORY_ID>` to `main` (look at both open and merged PRs).

4. Fetch all reviews on the PR:
   - If any reviewer submitted `CHANGES_REQUESTED`: surface each reviewer login and comment. Block with: "Spec PR has changes requested. Resolve the reviewer's feedback via `/speckit-clarify` or `/speckit-specify`, then re-run `/speckit-plan`."
   - Otherwise verify: at least one approval from the resolved `spec_approver_role` team/users exists.
   - If `spec_require_merge: true`, verify PR state is `MERGED`.

5. If gate conditions are not met: display current PR review status and block. Do not proceed to planning until gate passes.

**State Update — Phase 3C Entry Gates passed:**
In `specs/<STORY_ID>/workflow-state.md`, mark `[x] Phase 3C: Plan Entry Gates` and set `CURRENT_STAGE` to `PHASE_4_PENDING`.

### Skill Auto-Detection

Before proceeding to the Outline, scan `$ARGUMENTS` and any existing `specs/<STORY_ID>/spec.md` to detect the tech stack and load all relevant skills using `read_file`.

Print an evidence block:

```text
## Skills Loaded

- Detected technologies: <comma-separated list or "none">
- Skills loaded:
  - <path 1>
```

**Load the parent skill router** for each detected technology (skills located at `.bob/skills` relative to repo root):

| Detected technology | Parent skill router to load |
|---|---|
| Java, Spring Boot, Maven, Gradle | `.bob/skills/java/SKILL.md` |
| GraphQL schema, SDL, resolvers | `.bob/skills/graphql/SKILL.md` |
| React, JSX, hooks, components | `.bob/skills/react/SKILL.md` |

Apply all loaded skill guidance throughout the plan. If no technology match is found, skip.

---

## Outline

1. **Setup**: Run `.specify/scripts/powershell/setup-plan.ps1 -Json` from repo root and parse JSON for FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load context**:

   a. Read FEATURE_SPEC and `.specify/runtime/effective-constitution.md`. Load IMPL_PLAN template (already copied). If the runtime effective constitution file is missing, stop and instruct the user to run `/constitution.resolve` first.

   b. **Load platform and codebase context** — read `AGENTS.md` from the workspace root. Extract the full repo registry (name, description, tech stack, conventions). Based on FEATURE_SPEC content (user stories, described functionality, referenced entities), identify the affected repos.

   c. For each affected repo, check if CodeGraph is available and use it to understand existing code before designing:

      **CodeGraph Detection**:
      - Check if `../<repo-name>/.codegraph/` directory exists
      - If exists: Repository is indexed by CodeGraph
      - If not exists: Fall back to manual file reading

      **IF CodeGraph Available**:
      1. **First**, check if `codegraph_explore` MCP tool is available in your tool list
      2. **If MCP tool available**: Use `codegraph_explore` with natural language query
      3. **If MCP tool NOT available**: Try shell command `codegraph explore "<query>"`
      4. **If shell command fails**: Fall back to manual file reading (see below)
      5. **Always report** which method succeeded in the Codebase Snapshot
      
      Query examples for architectural understanding:
      * "Show the architecture of <feature-domain> including controllers, services, and data models"
      * "Find all methods that handle <entity-name> and their call paths"
      * "Show existing endpoint patterns and their implementations"
      * "Show the call flow from <endpoint> to database"
      
      Extract from results: method signatures, endpoint paths, field names, call relationships, patterns to extend
      
      Note: CodeGraph provides verbatim source with line numbers plus call paths, including dynamic dispatch

      **IF CodeGraph NOT Available**:
      - Fall back to manual exploration (current approach):
        * **Java/Spring Boot**: read existing controller, service, repository, and entity/DTO files
        * **Python/FastAPI**: read existing route modules, Pydantic model files, and `main.py`/`app.py`
        * **TypeScript/React**: read existing feature component directories, hooks, and relevant Apollo queries/mutations
        * **All repos**: read `README.md` if present
      - Do NOT read build outputs (`target/`, `dist/`, `.next/`), `node_modules/`, or generated files

   d. Output a **Codebase Snapshot** block:
      ```
      ## Codebase Snapshot
      Affected repos: <list>
      
      Exploration method per repo:
      - <repo-1>: CodeGraph (indexed) | Manual file reading (no index)
      - <repo-2>: CodeGraph (indexed) | Manual file reading (no index)
      
      Key existing code observed:
      - <repo>: <existing endpoints/methods, entity names, notable patterns>
      ...
      ```
      Reference this snapshot throughout plan generation to ensure technical decisions build on existing patterns, correct file paths and class names are used, and new fields/endpoints follow established naming conventions.

3. **Execute plan workflow**: Follow the structure in IMPL_PLAN template to:
   - Fill Technical Context (mark unknowns as "NEEDS CLARIFICATION")
   - Fill Constitution Check section from constitution
   - Evaluate gates (ERROR if violations unjustified)
   - Phase 0: Generate research.md (resolve all NEEDS CLARIFICATION)
   - Phase 1: Generate data-model.md, contracts/, quickstart.md
   - Phase 1: Update agent context by running the agent script
   - Re-evaluate Constitution Check post-design

4. **Stop and report**: Command ends after Phase 2 planning. Report branch, IMPL_PLAN path, and generated artifacts.

## Phases

### Phase 0: Outline & Research

1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:

   ```text
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

### Phase 1: Design & Contracts

**Prerequisites:** `research.md` complete

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Define interface contracts** (if project has external interfaces) → `/contracts/`:
   - Identify what interfaces the project exposes to users or other systems
   - Document the contract format appropriate for the project type
   - Skip if project is purely internal (build scripts, one-off tools, etc.)

3. **Agent context update**:
   - Run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType bob`
   - These scripts detect which AI agent is in use
   - Update the appropriate agent-specific context file
   - Add only new technology from current plan
   - Preserve manual additions between markers

**Output**: data-model.md, /contracts/*, quickstart.md, agent-specific file

## Key rules

- Use absolute paths
- ERROR on gate failures or unresolved clarifications

---

## PDLC Orchestration — Post-Plan

> **Activation**: This section executes only when `$ARGUMENTS` contained a `STORY_ID=<value>` token or a bare Jira story ID and the PDLC Pre-Plan section ran above.

After the plan artifacts have been generated (Outline complete), execute these PDLC governance steps.

**State Update — Phase 4 complete:**
In `specs/<STORY_ID>/workflow-state.md`, set `CURRENT_STAGE` to `CHECKPOINT_2A_PENDING` and mark `[x] Phase 4: Plan`.

### CHECKPOINT 2A — Submitter Plan Review Before PR Submission

Present:
- A structured summary of `specs/<STORY_ID>/plan.md`: key architecture decisions, technical context summary, data model overview, and affected repos.
- List of all additional plan artifacts produced (`research.md`, `data-model.md`, `contracts/`, `quickstart.md`).
- Resolved `submitter_role` and `plan_approver_role` with its GitHub team/users.

Ask the user:
> "`<submitter_role>` checkpoint: please review the plan. Does everything look correct?
> Type **yes** to commit and raise the design PR, or describe the corrections needed."

**Correction loop** — repeat until submitter approves:
1. If the user requests corrections, apply them to the relevant plan artifacts as instructed.
2. After applying corrections, present a brief summary of what changed.
3. Ask: "Are there any more corrections needed, or does the plan look good to proceed?"
4. If more corrections requested, return to step 1. When user confirms (types **yes** or equivalent), exit the loop.

Do not commit, push, or raise any PR until the submitter has explicitly confirmed.

**State Update — CHECKPOINT 2A approved:**
In `specs/<STORY_ID>/workflow-state.md`, set `CURRENT_STAGE` to `PHASE_4B_PENDING` and mark `[x] CHECKPOINT 2A: Submitter Plan Review`.

### Phase 4B — Plan Approval Gate

**Test bypass**: If `SKIP_APPROVAL_GATES=true` is in `$ARGUMENTS`, still commit and push plan artifacts and create/reuse the design PR, then skip reviewer wait. Present warning: `TEST_BYPASS active: Phase 4B approval gate skipped`. Set `Key Data > Plan Approval` to `TEST_BYPASS` and continue to Phase 5.

1. Commit plan artifacts to the `<STORY_ID>` branch:
   - Stage all new or modified files under `specs/<STORY_ID>/` produced by the plan phase (`plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`).
   - Hard rule: only stage files within `specs/<STORY_ID>/`. Do not stage files outside `specs/`.
   - Commit message: `<STORY_ID>: add plan artifacts for review`
   - Push to `origin/<STORY_ID>`.

2. Identify or raise the design review PR:
   - Use GitHub MCP tools to check for an open PR from head `<STORY_ID>` to `main`.
   - If none exists, raise one with title: `<STORY_ID>: <story title> — design artifacts`
   - If one exists, reuse it. Record the PR URL under `Key Data > Plan PR` in `workflow-state.md`.

**State Update — Plan PR Raised:**
In `specs/<STORY_ID>/workflow-state.md`, mark `[x] Phase 4A: Plan PR Raised`.

3. Request review from the resolved `plan_approver_role` team/users on the PR.

4. Present to the user:
   > "Plan artifacts have been committed and pushed. Awaiting `<plan_approver_role>` approval on the design PR: `<PR_URL>`
   > Type **yes** once the plan has been approved, or describe any issues."

5. On user confirmation, verify via GitHub MCP:
   - Fetch all reviews on the PR. If any reviewer submitted `CHANGES_REQUESTED`, surface each comment and block.
   - Otherwise verify: at least one approval from `plan_approver_role` team/users exists.
   - If `plan_require_merge: true`, verify the PR is also merged.
   - If not met: display current PR review status and prompt again.

**Hard stop**: Do not proceed to Phase 5 until the plan PR has the required approval from `<plan_approver_role>`, unless `SKIP_APPROVAL_GATES=true`.

**State Update — Phase 4B complete:**
In `specs/<STORY_ID>/workflow-state.md`, set `CURRENT_STAGE` to `PHASE_5_PENDING`, mark `[x] Phase 4B: Plan Approved`, and record the plan approver identity and approval timestamp (or `TEST_BYPASS`) under `Key Data > Plan Approval`.

### Phase 5 — Create Child Jira Stories

Run immediately after Phase 4B. Creates one Jira child story per affected repo and links each to the parent story.

> **Formatting rule**: When calling any Jira MCP tool, always pass body text with actual line breaks — never use `\n` escape sequences in string literals.

1. Read the `Affected Repos` list from `specs/<STORY_ID>/workflow-state.md`.

2. For each affected repo, create a Jira story using the Jira MCP tool:
   - **Summary**: `[<REPO>] <parent story title>`
   - **Description** (substitute all placeholders, use real newline characters):

     ```
     Child story for parent: <STORY_ID> — <parent story title>

     Scope: Implementation work in the `<REPO>` repository.

     Spec artifacts:
     - Spec:  specs/<STORY_ID>/spec.md
     - Plan:  specs/<STORY_ID>/plan.md
     - Tasks: specs/<STORY_ID>/tasks.md
     ```

   - **Issue type**: Story (same project as the parent story)

3. Collect the newly created story key for each repo (e.g., `SCRUM-11`).

4. For each newly created child story, create an issue link to the parent story using `jira_create_issue_link`:
   - `inward_issue_key`: `<child-story-key>`
   - `outward_issue_key`: `<STORY_ID>`
   - `link_type`: `"Relates to"` (prefer `"is subtask of"` or `"Epic-Story Link"` if the project supports them)
   - If the link call fails, log `LINK_FAILED: <child-key> → <STORY_ID>: <reason>` and continue.

5. Record all child story keys in `specs/<STORY_ID>/workflow-state.md` under `## Child Stories`:
   ```
   <repo-1>: <child-key-1>
   <repo-2>: <child-key-2>
   ```

6. Display a summary table:

   | Repo | Child Story Key | Parent Link |
   |------|----------------|-------------|
   | `<repo>` | `<key>` | `LINKED` / `LINK_FAILED` |

**State Update — Phase 5 complete:**
In `specs/<STORY_ID>/workflow-state.md`, set `CURRENT_STAGE` to `PHASE_6_PENDING` and mark `[x] Phase 5: Child Stories Created`.

> **Next step**: Run `/speckit-tasks STORY_ID=<STORY_ID>` to generate the dependency-ordered task list.

---

## Completion — Observability (always runs)

After all preceding steps are complete (Outline + PDLC Post-Plan if activated), run these two steps unconditionally regardless of whether a STORY_ID was present.

5. **Invoke observe-workflow**: Unconditionally invoke the `observe-workflow` skill with the following four arguments resolved in this order:
   - ARG1 (`db_path`): read `settings.yaml` → `observe.db_path`
   - ARG2 (`first_message`): construct the literal string `/speckit-plan STORY_ID=<JIRA-ID>` where `<JIRA-ID>` is replaced with the active Jira story ID (e.g. `/speckit-plan DPDE-224`). If no match is found with `STORY_ID=`, also try `/speckit-plan <JIRA-ID>`. Do **NOT** use the raw user message text, do **NOT** use just the Jira ID alone — always pass the full `/speckit-plan <JIRA-ID>` string as ARG2.
   - ARG3 (`project_id`): read `settings.yaml` → `observe.project_id`
   - ARG4 (`jira_id`): the active Jira story ID (already in working memory from Phase 0)

6. **Check for extension hooks**: After observe-workflow completes, check `.specify/extensions.yml` for `hooks.after_plan` entries and process them per the hook rules above. Skip any hook with `command: observe-workflow` — it has already been invoked in step 5.

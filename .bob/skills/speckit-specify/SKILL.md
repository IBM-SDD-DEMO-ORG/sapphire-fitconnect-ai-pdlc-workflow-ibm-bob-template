---
name: speckit-specify
description: Use when the user wants to create or update a feature specification from a natural language description, run /speckit-specify, or start the PDLC specification workflow for a story. Handles spec writing, constitution checks, PDLC orchestration, and Jira story fetch.
---

# speckit-specify

Create or update the feature specification from a natural language feature description.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). Run in "Advanced" mode.

## Pre-Execution Checks

**Check for extension hooks (before specification)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_specify` key
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

## PDLC Orchestration — Pre-Specify

> **Activation**: This section executes when `$ARGUMENTS` contains a `STORY_ID=<value>` token **or** when `$ARGUMENTS` is a bare Jira-style story ID (e.g. `DPDE-224`, matching pattern `[A-Z]+-\d+`). In either form, extract the story ID and treat it as `STORY_ID`. If neither form is detected, skip this entire section and proceed directly to the Outline.

### Settings Load

Read `settings.yaml` from the workspace root. Resolve and hold in working memory:

| Session variable | Source path in `settings.yaml` | Default |
|---|---|---|
| `submitter_role` | `pdlc.submitter_role` | `fde` |
| `spec_approver_role` | `pdlc.approvals.spec.approver_role` | `product_owner` |
| `spec_require_merge` | `pdlc.approvals.spec.require_merge` | `true` |
| `plan_approver_role` | `pdlc.approvals.plan.approver_role` | `fde` |
| `tasks_approver_role` | `pdlc.approvals.tasks.approver_role` | `fde` |

For each resolved role, look up its GitHub identity under `pdlc.roles.<role_name>`:
- `github_team` — org/team-slug; preferred for PR review requests and approval checks.
- `github_users` — list of individual usernames; used when team is unset.

If `settings.yaml` is missing or a key is absent, use the default value. Report any missing role identity (empty team and users) as a warning but do not block.

### Phase 0 — Resume Detection

Scan the `specs/` directory for any subdirectory containing a `workflow-state.md` file.

**If one or more state files are found:**
1. Read each `workflow-state.md` and collect: Story ID, Story Title, Last Updated, Current Stage.
2. Display the list to the user:
   > "Found in-progress workflow(s):"
   > - `<STORY_ID>` — <title> — stage: `<CURRENT_STAGE>` (last updated: <date>)
   >
   > "Type the story ID to **resume**, **new** to start fresh, or **skip** to proceed directly with the current input arguments."
3. On **resume**: load that `workflow-state.md`, set it as the active state for this session, and proceed from the stored `CURRENT_STAGE`. If `CURRENT_STAGE` indicates Phases 3–9 are already started, present the stored stage to the user and ask which phase to re-run or continue from.
4. On **new** or **skip**: proceed to Phase 1 as a fresh workflow.

**If no state files are found:** proceed directly to Phase 1.

### Phase 1 — Verify Effective Constitution

Use `read_file` to read `.specify/runtime/effective-constitution.md`.

- **If the file loads and contains content**: proceed. All later phases MUST use it as the single source of policy truth.
- **If the read fails or the file is empty**: stop immediately and display:
  > "`.specify/runtime/effective-constitution.md` is missing. Run `/speckit-constitution` to create or update the local constitution (which will automatically regenerate the effective constitution), or run `/constitution.resolve` directly if the local constitution already exists."

  Do not continue until the file is present.

> **Note**: Do **not** use `glob` or `list_files` to check for this file — those tools cannot reliably traverse hidden directories (dot-prefixed paths) on Windows. Always use `read_file` directly.

### Phase 2 — Fetch & Confirm Story

If `$ARGUMENTS` resolves to only a story ID (either `STORY_ID=<value>` or a bare `[A-Z]+-\d+` with no additional feature description text), fetch the Jira story automatically:

1. Use the Jira MCP tool to fetch story `<STORY_ID>`.
2. Display a clean summary:
   - **Title**:
   - **Description**:
   - **Acceptance Criteria**: (numbered list)
   - **Affected Repos**: (inferred from the Task Routing table in `AGENTS.md`; list every repo and the routing reason for each)
   - **Story Points**:
3. For each affected repo, read its `AGENTS.md` from one folder above the workspace root (e.g., `../<repo-name>/AGENTS.md`). Record any repo-specific boundaries and constraints relevant to this story.
4. Compose the feature description string for the Outline from the fetched story data:
   - Feature ID / Branch Name: `<STORY_ID>` (the Jira story number exactly)
   - Headline: the Jira story title.
   - Body: the full Jira description followed by the numbered acceptance criteria.
   - Constraint line: "Affected repos: `<repo-1>`, `<repo-2>`, …"
   - Boundary notes: one line per repo summarising repo-specific constraints.

If `$ARGUMENTS` contains both a story ID and additional feature description text, skip the Jira fetch and use the provided description as-is.

### CHECKPOINT 1 — Confirm Story

Ask the user:
> "Is this story and the affected-repo list correct?
> Type **yes** to proceed to specification, or describe any corrections."

Do not continue until the user confirms.

**State: Create or update `specs/<STORY_ID>/workflow-state.md`** with the following content (substitute real values). If the file already exists (resume), update `CURRENT_STAGE` and the Completed Phases checklist only; do not overwrite stored Key Data or Story Summary.

```markdown
# Workflow State

## Story
- Story ID: <STORY_ID>
- Story Title: <title>
- Started: <today's date>
- Last Updated: <today's date>

## CURRENT_STAGE
PHASE_3_PENDING

## Completed Phases
- [x] Phase 1: Constitution Verified
- [x] Phase 2: Story Fetched
- [x] CHECKPOINT 1: Story Confirmed
- [ ] Phase 3: Specification Created
- [ ] CHECKPOINT 2: Submitter Review
- [ ] Phase 3A: Spec PR Raised
- [ ] Phase 3B: Spec PR Approved
- [ ] Phase 3C: Plan Entry Gates
- [ ] Phase 4: Plan
- [ ] CHECKPOINT 2A: Submitter Plan Review
- [ ] Phase 4A: Plan PR Raised
- [ ] Phase 4B: Plan Approved
- [ ] Phase 5: Child Stories Created
- [ ] Phase 6A: Tasks Entry Gates
- [ ] Phase 6B: Tasks
- [ ] CHECKPOINT 2B: Submitter Tasks Review
- [ ] Phase 7A: Analysis Entry Gates
- [ ] Phase 7B: Analyze
- [ ] Phase 7C: Tasks PR Raised
- [ ] Phase 7D: Tasks PR Approved
- [ ] Phase 7E: Jira Stories Updated with Tasks
- [ ] CHECKPOINT 3: Ready for Implementation
- [ ] Phase 8A: Implementation Entry Gates
- [ ] Phase 8B: Generate Implementation Queue
- [ ] Phase 8C: Implement
- [ ] Phase 8D: Jira Stories Updated
- [ ] CHECKPOINT 4: Validation Complete
- [ ] Phase 9: Raise PRs
- [ ] CHECKPOINT 5: PRs Created

## Key Data
- Spec PR: (not yet raised)
- Spec Approval (`<spec_approver_role>`): (pending)
- Plan PR: (not yet raised)
- Plan Approval (`<plan_approver_role>`): (pending)
- Tasks PR: (not yet raised)
- Tasks Approval (`<tasks_approver_role>`): (pending)
- Implementation PRs: (pending)

## Child Stories
(populated in Phase 5 — one `<repo>: <child-key>` per affected repo)

## Affected Repos
<comma-separated list of affected repo names>

## Story Summary
<one-paragraph summary of the story, including title, key acceptance criteria, and affected repos>
```

---

## Outline

The text the user typed after `/speckit-specify` in the triggering message **is** the feature description. Assume you always have it available in this conversation even if `$ARGUMENTS` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that feature description, do this:

1. **Determine the branch naming mode**:
   - If the feature description explicitly provides a branch name or feature ID in the form of a Jira story number such as `SAP-1234`, use that value exactly as the branch name.
   - Otherwise, generate a concise short name (2-4 words) for the branch:
     - Analyze the feature description and extract the most meaningful keywords
     - Create a 2-4 word short name that captures the essence of the feature
     - Use action-noun format when possible (e.g., `add-user-auth`, `fix-payment-bug`)
     - Preserve technical terms and acronyms (OAuth2, API, JWT, etc.)
     - Keep it concise but descriptive enough to understand the feature at a glance
     - Examples:
       - `I want to add user authentication` → `user-auth`
       - `Implement OAuth2 integration for the API` → `oauth2-api-integration`
       - `Create a dashboard for analytics` → `analytics-dashboard`
       - `Fix payment processing timeout bug` → `fix-payment-timeout`

2. **Create the feature branch** by running the script once with `-Json`:

   - If an explicit Jira story number or branch name is provided, pass it with `-BranchName` and do not generate or append a numeric prefix or slug suffix.
   - Otherwise, pass `-ShortName` and do NOT pass `-Number` so the script auto-detects the next globally available number across all branches and spec directories.

   Examples:
   - PowerShell with explicit Jira branch: `.specify/scripts/powershell/create-new-feature.ps1 -Json -BranchName "SAP-1234" "Feature ID: SAP-1234\nHeadline: Add user authentication"`
   - PowerShell with generated short name: `.specify/scripts/powershell/create-new-feature.ps1 -Json -ShortName "user-auth" "Add user authentication"`

   **IMPORTANT**:
   - When a Jira story number is explicitly provided, preserve it exactly as the branch name
   - Do NOT pass `-Number` unless the user explicitly requests manual numbering
   - Always include the JSON flag (`--json` for Bash, `-Json` for PowerShell) so the output can be parsed reliably
   - You must only ever run this script once per feature
   - The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for
   - The JSON output will contain BRANCH_NAME and SPEC_FILE paths
   - For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot")

3. Load `.specify/templates/spec-template.md` to understand required sections.

4. Follow this execution flow:

    **Pre-step — Load platform and codebase context** (runs before everything else in step 4):

    a. Read `AGENTS.md` from the workspace root. This is the single source of truth for the platform's service architecture, repo registry, tech conventions, and cross-cutting rules. Extract and hold in working memory:
       - The full repo registry: name, description, tech stack, and conventions for every repo.
       - Candidate affected repos: based on the feature description, identify which repos are most likely touched. Match feature domain keywords (e.g., "user profile" → `user-service`; "recommendations" → `recommendation-engine`; "chat / coach" → `wellness-coach`).

    b. For each candidate affected repo, check if CodeGraph is available and use it to understand what already exists before writing requirements:

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
       
       Query examples based on feature domain:
       * "Show me all REST endpoints for user management"
       * "Find authentication and authorization implementations"
       * "Show data models related to <feature-domain>"
       * "Find all controllers and their endpoint paths"
       
       Extract from results: endpoint paths, method signatures, entity/DTO field names, response shapes
       
       Note: CodeGraph returns line-numbered source code plus call paths between symbols

       **IF CodeGraph NOT Available**:
       - Fall back to manual file reading (current approach):
         * **Java/Spring Boot repos**: read 1–2 existing controller files, a representative service class, and entity/DTO record classes
         * **Python/FastAPI repos**: read `main.py` or `app.py` and 1–2 route modules
         * **TypeScript/React repos**: read 1–2 feature component files and a representative Apollo query/mutation
         * **All repos**: read `README.md` if present for high-level context
       - Do NOT read build outputs (`target/`, `dist/`, `.next/`), `node_modules/`, or generated files

    c. Output a **Codebase Snapshot** block before proceeding:
       ```
       ## Codebase Snapshot
       Affected repos (candidates): <list>
       
       Exploration method per repo:
       - <repo-1>: CodeGraph (indexed) | Manual file reading (no index)
       - <repo-2>: CodeGraph (indexed) | Manual file reading (no index)
       
       Key existing artifacts observed:
       - <repo>: <what was found — e.g., "UserController: GET /users/{id}, UserRecord DTO, no wellness-summary field yet">
       ...
       
       Conventions to follow:
       - <e.g., "user-service: record DTOs, constructor injection, Spring layering enforced">
       ```
       Use this snapshot throughout spec generation to ensure requirements do not duplicate existing functionality, reference correct entity/endpoint names, and respect repo boundaries.

    0. **Load the effective constitution**: Read `.specify/runtime/effective-constitution.md` in full before doing anything else. Extract and hold in working memory all numeric thresholds, mandated libraries, and governance rules (e.g., Python coverage = 80%, Java coverage = 80%, TypeScript coverage = 70%, CI stage boundaries, auth requirements). If the file does not exist, warn the user and continue. These values MUST be used as concrete literals in requirements and success criteria — never deferred back to "the workspace constitution" with the value unspecified.

    1. Parse user description from Input
       If empty: ERROR "No feature description provided"
    2. Extract key concepts from description
       Identify: actors, actions, data, constraints
    3. For unclear aspects:
       - Make informed guesses based on context and industry standards
       - Only mark with [NEEDS CLARIFICATION: specific question] if:
         - The choice significantly impacts feature scope or user experience
         - Multiple reasonable interpretations exist with different implications
         - No reasonable default exists
       - **LIMIT: Maximum 3 [NEEDS CLARIFICATION] markers total**
       - Prioritize clarifications by impact: scope > security/privacy > user experience > technical details
    4. Fill User Scenarios & Testing section
       If no clear user flow: ERROR "Cannot determine user scenarios"
    5. Generate Functional Requirements
       Each requirement must be testable
       Use reasonable defaults for unspecified details (document assumptions in Assumptions section)
    6. Define Success Criteria
       Create measurable, technology-agnostic outcomes
       Include both quantitative metrics (time, performance, volume) and qualitative measures (user satisfaction, task completion)
       Each criterion must be verifiable without implementation details
    7. Identify Key Entities (if data involved)
    8. Return: SUCCESS (spec ready for planning)

**Spec Artifact Quality Standards** (apply throughout all steps above):

The spec must match the quality level of the product reference artifacts. Concretely, every User Story section must contain all four of the following sub-sections — no exceptions:

```
### User Story N - <Brief Title> (Priority: P<n>)

<One-paragraph narrative describing the user's goal and context>

**Why this priority**: <Explain the business/user value and why this story is ranked at this priority relative to sibling stories. Be specific, not generic.>

**Independent Test**: <Describe how this story can be tested end-to-end independently of the others, including the specific verification steps. No hand-waving.>

**Acceptance Scenarios**:
1. **Given** <precondition>, **When** <action>, **Then** <expected outcome>.
...(include all happy-path, empty-state, error-state, and loading-state scenarios)
```

Additional required sections:
- `## Assumptions` — list every dependency, data-format, or scope assumption that shapes the spec (not just the obvious ones). One bullet per assumption. Each assumption must be specific enough to be validated later.
- `### Edge Cases` — bullet list of negative / boundary / concurrent scenarios that could affect correctness.

Do not write vague adjectives ("robust", "seamless", "intuitive") without attaching a measurable criterion. Do not write acceptance scenarios without GWT structure.

5. Write the specification to SPEC_FILE using the template structure, replacing placeholders with concrete details derived from the feature description (arguments) while preserving section order and headings.

6. **Specification Quality Validation**: After writing the initial spec, validate it against quality criteria:

   a. **Create Spec Quality Checklist**: Generate a checklist file at `FEATURE_DIR/checklists/requirements.md` using the checklist template structure with these validation items.

   b. **Run Validation Check**: Review the spec against each checklist item.

   c. **Handle Validation Results**:

      - **If all items pass**: Mark checklist complete and proceed to step 7

      - **If items fail (excluding [NEEDS CLARIFICATION])**:
        1. List the failing items and specific issues
        2. Update the spec to address each issue
        3. Re-run validation until all items pass (max 3 iterations)
        4. If still failing after 3 iterations, document remaining issues in checklist notes and warn user

      - **If [NEEDS CLARIFICATION] markers remain**:
        1. Extract all [NEEDS CLARIFICATION: ...] markers from the spec
        2. **LIMIT CHECK**: If more than 3 markers exist, keep only the 3 most critical (by scope/security/UX impact) and make informed guesses for the rest
        3. For each clarification needed (max 3), present options to user
        4. Wait for user to respond, then update spec with answers and re-run validation

   d. **Update Checklist**: After each validation iteration, update the checklist file with current pass/fail status

7. Report completion with branch name, spec file path, checklist results, and readiness for the next phase (`/speckit-clarify` or `/speckit-plan`).

**NOTE:** The script creates and checks out the new branch and initializes the spec file before writing.

## Quick Guidelines

- Focus on **WHAT** users need and **WHY**.
- Avoid HOW to implement (no tech stack, APIs, code structure).
- Written for business stakeholders, not developers.
- DO NOT create any checklists that are embedded in the spec. That will be a separate command.

### Section Requirements

- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### Success Criteria Guidelines

Success criteria must be:

1. **Measurable**: Include specific metrics (time, percentage, count, rate)
2. **Technology-agnostic**: No mention of frameworks, languages, databases, or tools
3. **User-focused**: Describe outcomes from user/business perspective, not system internals
4. **Verifiable**: Can be tested/validated without knowing implementation details

---

## PDLC Orchestration — Post-Specify

> **Activation**: This section executes only when `$ARGUMENTS` contained a `STORY_ID=<value>` token or a bare Jira story ID and the PDLC Pre-Specify section ran above. If no story ID was present, skip this section entirely.

After the specification has been written and validated (Outline steps 1–8 complete), execute these PDLC governance steps.

### Commit Spec to Branch

1. Use MCP git tools to stage all new or modified files under `specs/<STORY_ID>/` produced by the Outline (spec.md, checklists/).
   - **Hard rule**: Only stage files within `specs/<STORY_ID>/`. Use `git add specs/<STORY_ID>/` — do not stage files outside `specs/`.
2. Create a commit with message: `<STORY_ID>: add specification`
3. Push to `origin/<STORY_ID>`.

Do NOT create a pull request at this stage. The spec PR is raised after `/speckit-clarify` runs and the submitter confirms the spec is ready for approver review.

**State Update — Phase 3 complete:**
In `specs/<STORY_ID>/workflow-state.md`, set `CURRENT_STAGE` to `CLARIFY_PENDING` and mark `[x] Phase 3: Specification Created`. Update `Last Updated` to today's date.

> **Next step**: Run `/speckit-clarify STORY_ID=<STORY_ID>` to refine the spec with targeted clarification questions, then raise the specification PR for `<spec_approver_role>` approval.

---

## Completion — Observability (always runs)

After all preceding steps are complete (Outline + PDLC Post-Specify if activated), run these two steps unconditionally regardless of whether a STORY_ID was present.

8. **Invoke observe-workflow**: Unconditionally invoke the `observe-workflow` skill with the following four arguments resolved in this order:
   - ARG1 (`db_path`): read `settings.yaml` → `observe.db_path`
   - ARG2 (`first_message`): the **first user message sent in the current chat session** - that will be `/speckit-specify STORY_ID=<JIRA-ID>` - send `/speckit-specify STORY_ID=<JIRA-ID>` string as is. If it finds no matches, try with `/speckit-specify <JIRA-ID>`
   - ARG3 (`project_id`): read `settings.yaml` → `observe.project_id`
   - ARG4 (`jira_id`): the active Jira story ID (already in working memory from Phase 0)

9. **Check for extension hooks**: After observe-workflow completes, check `.specify/extensions.yml` for `hooks.after_specify` entries and process them per the hook rules above. Skip any hook with `command: observe-workflow` — it has already been invoked in step 8.

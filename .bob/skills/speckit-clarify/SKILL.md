---
name: speckit-clarify
description: Use when the user wants to clarify a feature spec, run /speckit-clarify, identify underspecified areas in a specification, ask targeted clarification questions, or encode answers back into spec.md. Also handles PDLC spec PR raising and approval gate.
---

# speckit-clarify

Identify underspecified areas in the current feature spec by asking up to 5 highly targeted clarification questions and encoding answers back into the spec.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). Run in "Advanced" mode.

## Outline

Goal: Detect and reduce ambiguity or missing decision points in the active feature specification and record the clarifications directly in the spec file.

Note: This clarification workflow is expected to run (and be completed) BEFORE invoking `/speckit-plan`. If the user explicitly states they are skipping clarification (e.g., exploratory spike), you may proceed, but must warn that downstream rework risk increases.

Execution steps:

1. Run `.specify/scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly` from repo root **once** (combined `--json --paths-only` mode / `-Json -PathsOnly`). Parse minimal JSON payload fields:
   - `FEATURE_DIR`
   - `FEATURE_SPEC`
   - (Optionally capture `IMPL_PLAN`, `TASKS` for future chained flows.)
   - If JSON parsing fails, abort and instruct user to re-run `/speckit-specify` or verify feature branch environment.
   - For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. Load the current spec file. Perform a structured ambiguity & coverage scan using this taxonomy. For each category, mark status: Clear / Partial / Missing. Produce an internal coverage map used for prioritization (do not output raw map unless no questions will be asked).

   Functional Scope & Behavior:
   - Core user goals & success criteria
   - Explicit out-of-scope declarations
   - User roles / personas differentiation

   Domain & Data Model:
   - Entities, attributes, relationships
   - Identity & uniqueness rules
   - Lifecycle/state transitions
   - Data volume / scale assumptions

   Interaction & UX Flow:
   - Critical user journeys / sequences
   - Error/empty/loading states
   - Accessibility or localization notes

   Non-Functional Quality Attributes:
   - Performance (latency, throughput targets)
   - Scalability (horizontal/vertical, limits)
   - Reliability & availability (uptime, recovery expectations)
   - Observability (logging, metrics, tracing signals)
   - Security & privacy (authN/Z, data protection, threat assumptions)
   - Compliance / regulatory constraints (if any)

   Integration & External Dependencies:
   - External services/APIs and failure modes
   - Data import/export formats
   - Protocol/versioning assumptions

   Edge Cases & Failure Handling:
   - Negative scenarios
   - Rate limiting / throttling
   - Conflict resolution (e.g., concurrent edits)

   Constraints & Tradeoffs:
   - Technical constraints (language, storage, hosting)
   - Explicit tradeoffs or rejected alternatives

   Terminology & Consistency:
   - Canonical glossary terms
   - Avoided synonyms / deprecated terms

   Completion Signals:
   - Acceptance criteria testability
   - Measurable Definition of Done style indicators

   Misc / Placeholders:
   - TODO markers / unresolved decisions
   - Ambiguous adjectives ("robust", "intuitive") lacking quantification

   For each category with Partial or Missing status, add a candidate question opportunity unless:
   - Clarification would not materially change implementation or validation strategy
   - Information is better deferred to planning phase (note internally)

3. Generate (internally) a prioritized queue of candidate clarification questions (maximum 5). Do NOT output them all at once. Apply these constraints:
    - Maximum of 5 total questions across the whole session.
    - Each question must be answerable with EITHER:
       - A short multiple‑choice selection (2–5 distinct, mutually exclusive options), OR
       - A one-word / short‑phrase answer (explicitly constrain: "Answer in <=5 words").
    - Only include questions whose answers materially impact architecture, data modeling, task decomposition, test design, UX behavior, operational readiness, or compliance validation.
    - Ensure category coverage balance: attempt to cover the highest impact unresolved categories first; avoid asking two low-impact questions when a single high-impact area (e.g., security posture) is unresolved.
    - Exclude questions already answered, trivial stylistic preferences, or plan-level execution details (unless blocking correctness).
    - Favor clarifications that reduce downstream rework risk or prevent misaligned acceptance tests.
    - If more than 5 categories remain unresolved, select the top 5 by (Impact * Uncertainty) heuristic.

4. Sequential questioning loop (interactive):
    - Present EXACTLY ONE question at a time.
    - For multiple‑choice questions:
       - **Analyze all options** and determine the **most suitable option** based on:
          - Best practices for the project type
          - Common patterns in similar implementations
          - Risk reduction (security, performance, maintainability)
          - Alignment with any explicit project goals or constraints visible in the spec
       - Present your **recommended option prominently** at the top with clear reasoning (1-2 sentences explaining why this is the best choice).
       - Format as: `**Recommended:** Option [X] - <reasoning>`
       - Then render all options as a Markdown table:

       | Option | Description |
       |--------|-------------|
       | A | <Option A description> |
       | B | <Option B description> |
       | C | <Option C description> (add D/E as needed up to 5) |
       | Short | Provide a different short answer (<=5 words) (Include only if free-form alternative is appropriate) |

       - After the table, add: `You can reply with the option letter (e.g., "A"), accept the recommendation by saying "yes" or "recommended", or provide your own short answer.`
    - For short‑answer style (no meaningful discrete options):
       - Provide your **suggested answer** based on best practices and context.
       - Format as: `**Suggested:** <your proposed answer> - <brief reasoning>`
       - Then output: `Format: Short answer (<=5 words). You can accept the suggestion by saying "yes" or "suggested", or provide your own answer.`
    - After the user answers:
       - If the user replies with "yes", "recommended", or "suggested", use your previously stated recommendation/suggestion as the answer.
       - Otherwise, validate the answer maps to one option or fits the <=5 word constraint.
       - If ambiguous, ask for a quick disambiguation (count still belongs to same question; do not advance).
       - Once satisfactory, record it in working memory (do not yet write to disk) and move to the next queued question.
    - Stop asking further questions when:
       - All critical ambiguities resolved early (remaining queued items become unnecessary), OR
       - User signals completion ("done", "good", "no more"), OR
       - You reach 5 asked questions.
    - Never reveal future queued questions in advance.
    - If no valid questions exist at start, immediately report no critical ambiguities.

5. Integration after EACH accepted answer (incremental update approach):
    - Maintain in-memory representation of the spec (loaded once at start) plus the raw file contents.
    - For the first integrated answer in this session:
       - Ensure a `## Clarifications` section exists (create it just after the highest-level contextual/overview section per the spec template if missing).
       - Under it, create (if not present) a `### Session YYYY-MM-DD` subheading for today.
    - Append a bullet line immediately after acceptance: `- Q: <question> → A: <final answer>`.
    - Then immediately apply the clarification to the most appropriate section(s):
       - Functional ambiguity → Update or add a bullet in Functional Requirements.
       - User interaction / actor distinction → Update User Stories or Actors subsection (if present) with clarified role, constraint, or scenario.
       - Data shape / entities → Update Data Model (add fields, types, relationships) preserving ordering; note added constraints succinctly.
       - Non-functional constraint → Add/modify measurable criteria in Non-Functional / Quality Attributes section (convert vague adjective to metric or explicit target).
       - Edge case / negative flow → Add a new bullet under Edge Cases / Error Handling (or create such subsection if template provides placeholder for it).
       - Terminology conflict → Normalize term across spec; retain original only if necessary by adding `(formerly referred to as "X")` once.
    - If the clarification invalidates an earlier ambiguous statement, replace that statement instead of duplicating; leave no obsolete contradictory text.
    - Save the spec file AFTER each integration to minimize risk of context loss (atomic overwrite).
    - Preserve formatting: do not reorder unrelated sections; keep heading hierarchy intact.
    - Keep each inserted clarification minimal and testable (avoid narrative drift).

6. Validation (performed after EACH write plus final pass):
   - Clarifications session contains exactly one bullet per accepted answer (no duplicates).
   - Total asked (accepted) questions ≤ 5.
   - Updated sections contain no lingering vague placeholders the new answer was meant to resolve.
   - No contradictory earlier statement remains (scan for now-invalid alternative choices removed).
   - Markdown structure valid; only allowed new headings: `## Clarifications`, `### Session YYYY-MM-DD`.
   - Terminology consistency: same canonical term used across all updated sections.

7. Write the updated spec back to `FEATURE_SPEC`.

8. Report completion (after questioning loop ends or early termination):
   - Number of questions asked & answered.
   - Path to updated spec.
   - Sections touched (list names).
   - Coverage summary table listing each taxonomy category with Status: Resolved (was Partial/Missing and addressed), Deferred (exceeds question quota or better suited for planning), Clear (already sufficient), Outstanding (still Partial/Missing but low impact).
   - If any Outstanding or Deferred remain, recommend whether to proceed to `/speckit-plan` or run `/speckit-clarify` again later post-plan.
   - Suggested next command.

Behavior rules:

- If no meaningful ambiguities found (or all potential questions would be low-impact), respond: "No critical ambiguities detected worth formal clarification." and suggest proceeding.
- If spec file missing, instruct user to run `/speckit-specify` first (do not create a new spec here).
- Never exceed 5 total asked questions (clarification retries for a single question do not count as new questions).
- Avoid speculative tech stack questions unless the absence blocks functional clarity.
- Respect user early termination signals ("stop", "done", "proceed").
- If no questions asked due to full coverage, output a compact coverage summary (all categories Clear) then suggest advancing.
- If quota reached with unresolved high-impact categories remaining, explicitly flag them under Deferred with rationale.

Context for prioritization: $ARGUMENTS

---

## PDLC Orchestration — Post-Clarify

> **Activation**: This section executes only when `$ARGUMENTS` contains a `STORY_ID=<value>` token or a bare Jira-style story ID (e.g. `DPDE-224`, matching `[A-Z]+-\d+`). Extract the story ID from either form. If no story ID is present, skip this section.

After the clarification loop is complete and all answers are written to `spec.md`, execute these PDLC governance steps.

**State Update — Clarify complete:**
In `specs/<STORY_ID>/workflow-state.md`, update `Last Updated` to today's date.

### CHECKPOINT 2 — Submitter Review Before Spec PR Submission

Read `settings.yaml` from the workspace root and resolve `submitter_role`, `spec_approver_role`, and the GitHub team/users for that role (same logic as in `speckit-specify`).

Present:
- Path to `specs/<STORY_ID>/spec.md`
- A bullet list of every user story captured (title and priority label)
- Summary of clarifications added in this session
- Resolved `submitter_role` and `spec_approver_role` with its GitHub team/users

Ask the user:
> "`<submitter_role>` checkpoint: the spec has been updated with clarification answers. Does it look correct for `<spec_approver_role>` review submission?
> Type **yes** to commit and raise the specification PR, or describe corrections to make."

Do not continue until the user confirms.

**State Update — CHECKPOINT 2 confirmed:**
In `specs/<STORY_ID>/workflow-state.md`, set `CURRENT_STAGE` to `PHASE_3A_PENDING` and mark `[x] CHECKPOINT 2: Submitter Review`.

### Phase 3A — Commit Clarification Updates and Raise/Update Spec PR

1. Use MCP git tools to stage all new or modified files under `specs/<STORY_ID>/`.
   - **Hard rule**: only stage files within `specs/<STORY_ID>/`. Use `git add specs/<STORY_ID>/` — do not stage files outside `specs/`.
2. If a spec PR was previously raised (check `Key Data > Spec PR` in `workflow-state.md`), use commit message: `<STORY_ID>: update spec with clarification answers`. Otherwise use: `<STORY_ID>: add specification`.
3. Push to `origin/<STORY_ID>`.
4. Use GitHub MCP tools to find the open PR from head `<STORY_ID>` to `main`:
   - If none exists, create one with title: `<STORY_ID>: <story title> — specification`
   - If one exists, reuse it. Note: pushing new commits may have dismissed prior approvals.
5. Request review from the resolved `spec_approver_role` team/users on the PR.
6. Present PR link and current status to the user.

**State Update — Phase 3A complete:**
In `specs/<STORY_ID>/workflow-state.md`, set `CURRENT_STAGE` to `PHASE_3B_PENDING`, mark `[x] Phase 3A: Spec PR Raised`, and record the PR link under `Key Data > Spec PR`.

### Phase 3B — Spec PR Approved

> **Test bypass**: If `SKIP_APPROVAL_GATES=true` is in `$ARGUMENTS`, still present the PR link, skip reviewer wait, present warning `TEST_BYPASS active: Phase 3B spec PR approval skipped`, set `Key Data > Spec Approval` to `TEST_BYPASS`, and proceed to the next step.

1. Read `settings.yaml` and resolve:
   - `spec_approver_role` = `pdlc.approvals.spec.approver_role` (default: `product_owner`)
   - `spec_require_merge` = `pdlc.approvals.spec.require_merge` (default: `true`)
   - GitHub team/users = `pdlc.roles.<spec_approver_role>.github_team` / `.github_users`

2. Find the spec PR from head `<STORY_ID>` to `main` via GitHub MCP tools (look at both open and recently merged PRs).
   - If no PR found: present error and route back to Phase 3A.

3. Fetch all reviews on the PR. If any reviewer has submitted `CHANGES_REQUESTED`:
   - Surface each reviewer login and their comment body.
   - Block: "The spec PR has changes requested. Please address the reviewer's feedback, push updates, and re-run `/speckit-clarify STORY_ID=<STORY_ID>`."
   - Do not proceed until the `CHANGES_REQUESTED` is resolved.

4. Verify approval conditions:
   - At least one approval from the resolved `spec_approver_role` team/users exists on the PR.
   - If `spec_require_merge: true`, PR state must also be `MERGED`.

5. Present current status to the user:
   > "Spec approval gate: Required approver is `<spec_approver_role>` (`<github_team or github_users>`).
   > Type **yes** once the spec PR has been approved (and merged if required), or describe any issues."

6. On user confirmation, re-verify via GitHub MCP that conditions in step 4 are actually met. If not met, show current PR review status and prompt again. Do not accept chat-only confirmation as a bypass.

**Hard stop**: Do not proceed to planning until conditions pass, unless `SKIP_APPROVAL_GATES=true`.

**State Update — Phase 3B PASS:**
In `specs/<STORY_ID>/workflow-state.md`, set `CURRENT_STAGE` to `PHASE_3C_PENDING`, mark `[x] Phase 3B: Spec PR Approved`, and record the spec approver identity and approval timestamp (or `TEST_BYPASS`) under `Key Data > Spec Approval`.

> **Next step**: Run `/speckit-plan STORY_ID=<STORY_ID>` to generate the implementation plan.

---

## Completion — Observability (always runs)

After all preceding steps are complete (Outline + PDLC Post-Clarify if activated), run these two steps unconditionally regardless of whether a STORY_ID was present.

9. **Invoke observe-workflow**: Unconditionally invoke the `observe-workflow` skill with the following four arguments resolved in this order:
   - ARG1 (`db_path`): read `settings.yaml` → `observe.db_path`
   - ARG2 (`first_message`): the **first user message sent in the current chat session** - that will be `/speckit-clarify STORY_ID=<JIRA-ID>` - send `/speckit-clarify STORY_ID=<JIRA-ID>` string as is. If it finds no matches, try with `/speckit-clarify <JIRA-ID>`
   - ARG3 (`project_id`): read `settings.yaml` → `observe.project_id`
   - ARG4 (`jira_id`): the active Jira story ID (from `$ARGUMENTS` or `specs/*/workflow-state.md` `Story ID:`)

10. **Check for extension hooks**: After observe-workflow completes, check `.specify/extensions.yml` for `hooks.after_clarify` entries and process them per the standard hook rules. Skip any hook with `command: observe-workflow` — it has already been invoked in step 9.

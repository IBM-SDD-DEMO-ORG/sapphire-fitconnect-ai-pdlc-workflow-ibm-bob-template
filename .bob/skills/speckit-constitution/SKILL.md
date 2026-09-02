---
name: speckit-constitution
description: Use when the user wants to create or update the project constitution, run /speckit.constitution, fill constitution template placeholders, or propagate constitution changes to dependent templates. Manages only the local project constitution at .specify/memory/constitution.md.
---

# speckit-constitution

Create or update the project constitution from interactive or provided principle inputs, ensuring all dependent templates stay in sync.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

You are updating the project constitution at `.specify/memory/constitution.md`. This file is a TEMPLATE containing placeholder tokens in square brackets (e.g. `[PROJECT_NAME]`, `[PRINCIPLE_1_NAME]`). Your job is to (a) collect/derive concrete values, (b) fill the template precisely, and (c) propagate any amendments across dependent artifacts.

**CRITICAL CONSTRAINT**: You MUST ONLY edit `.specify/memory/constitution.md` (the LOCAL project constitution). You are ABSOLUTELY FORBIDDEN from modifying any other constitution files, including:
- `org-constitution/constitution.md` (global constitution)
- `.specify/runtime/effective-constitution.md` (generated file)
- Any other constitution files in the workspace
- Do NOT read any other files in this repo for context, only the template, ARGUMENTS should be used

**Violation of this constraint is a critical error that breaks the separation between organization-wide and project-specific governance.**

**Note**: If `.specify/memory/constitution.md` does not exist yet, it should have been initialized from `.specify/templates/constitution-template.md` during project setup. If it's missing, copy the template first.

Follow this execution flow:

1. Load the existing constitution at `.specify/memory/constitution.md`.
   - Identify every placeholder token of the form `[ALL_CAPS_IDENTIFIER]`.
   **IMPORTANT**: The user might require less or more principles than the ones used in the template. If a number is specified, respect that - follow the general template. You will update the doc accordingly.

2. Collect/derive values for placeholders:
   - If user input (conversation) supplies a value, use it.
   - Otherwise infer from existing repo context (README, docs, prior constitution versions if embedded).
   - For governance dates: `RATIFICATION_DATE` is the original adoption date (if unknown ask or mark TODO), `LAST_AMENDED_DATE` is today if changes are made, otherwise keep previous.
   - `CONSTITUTION_VERSION` must increment according to semantic versioning rules:
     - MAJOR: Backward incompatible governance/principle removals or redefinitions.
     - MINOR: New principle/section added or materially expanded guidance.
     - PATCH: Clarifications, wording, typo fixes, non-semantic refinements.
   - If version bump type ambiguous, propose reasoning before finalizing.

3. Draft the updated constitution content:
   - Replace every placeholder with concrete text (no bracketed tokens left except intentionally retained template slots that the project has chosen not to define yet—explicitly justify any left).
   - Preserve heading hierarchy and comments can be removed once replaced unless they still add clarifying guidance.
   - Ensure each Principle section: succinct name line, paragraph (or bullet list) capturing non‑negotiable rules, explicit rationale if not obvious.
   - Ensure Governance section lists amendment procedure, versioning policy, and compliance review expectations.

4. Consistency propagation checklist (convert prior checklist into active validations):
   - Read `.specify/templates/plan-template.md` and ensure any "Constitution Check" or rules align with updated principles.
   - Read `.specify/templates/spec-template.md` for scope/requirements alignment—update if constitution adds/removes mandatory sections or constraints.
   - Read `.specify/templates/tasks-template.md` and ensure task categorization reflects new or removed principle-driven task types (e.g., observability, versioning, testing discipline).
   - Read each command file in `.specify/templates/commands/*.md` (including this one) to verify no outdated references (agent-specific names like CLAUDE only) remain when generic guidance is required.
   - Read any runtime guidance docs (e.g., `README.md`, `docs/quickstart.md`, or agent-specific guidance files if present). Update references to principles changed.

5. Produce a Sync Impact Report (prepend as an HTML comment at top of the constitution file after update):
   - Version change: old → new
   - List of modified principles (old title → new title if renamed)
   - Added sections
   - Removed sections
   - Templates requiring updates (✅ updated / ⚠ pending) with file paths
   - Follow-up TODOs if any placeholders intentionally deferred.

6. Validation before final output:
   - No remaining unexplained bracket tokens.
   - Version line matches report.
   - Dates ISO format YYYY-MM-DD.
   - Principles are declarative, testable, and free of vague language ("should" → replace with MUST/SHOULD rationale where appropriate).

7. **VALIDATION CHECKPOINT - File Path Verification**:
   - Before writing ANY file, verify the target path is EXACTLY `.specify/memory/constitution.md`
   - If the path is anything else (e.g., `org-constitution/constitution.md`), STOP immediately and report an error
   - This is a MANDATORY safety check that MUST NOT be skipped

8. Write the completed constitution back to `.specify/memory/constitution.md` (overwrite).

Formatting & Style Requirements:

- Use Markdown headings exactly as in the template (do not demote/promote levels).
- Wrap long rationale lines to keep readability (<100 chars ideally) but do not hard enforce with awkward breaks.
- Keep a single blank line between sections.
- Avoid trailing whitespace.

If the user supplies partial updates (e.g., only one principle revision), still perform validation and version decision steps.

If critical info missing (e.g., ratification date truly unknown), insert `TODO(<FIELD_NAME>): explanation` and include in the Sync Impact Report under deferred items.

Do not create a new template; always operate on the existing `.specify/memory/constitution.md` file.

---

## Safety Guardrails

**BEFORE making ANY file modifications, you MUST:**

1. **Verify Target File**: Confirm you are editing `.specify/memory/constitution.md` and ONLY this file
2. **Check File Existence**: If the file doesn't exist, copy from `.specify/templates/constitution-template.md` first
3. **Reject Invalid Paths**: If asked to edit any other constitution file, refuse and explain the proper workflow
4. **Document Reasoning**: If the local constitution is in template form, explain that you're filling it in (not bypassing it)

**FORBIDDEN ACTIONS:**
- ❌ Editing `org-constitution/constitution.md` (global constitution)
- ❌ Editing `.specify/runtime/effective-constitution.md` (generated file)
- ❌ Reasoning that "the global is more practical" or "the effective uses the global"
- ❌ Bypassing the local constitution because it's in template form

**CORRECT WORKFLOW:**
1. Update `.specify/memory/constitution.md` (local project constitution)
2. Suggest running `/constitution.resolve` to regenerate effective constitution
3. The effective constitution will merge global + local automatically

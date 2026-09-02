---
name: constitution-pathlint
description: Use when the user wants to enforce constitution path guardrails, run /constitution.pathlint, or validate that agent specs under .github/agents/ reference only the runtime effective constitution and not the local source constitution.
---

# constitution-pathlint

Enforce constitution path guardrails so downstream agents use runtime effective constitution only.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Validate constitution path usage across agent specs to prevent drift back to local source policy in downstream phases.

## Guardrail Rules

1. Runtime enforcement path for downstream agents:
- `.specify/runtime/effective-constitution.md`

2. Source constitution path (restricted use):
- `.specify/memory/constitution.md`

3. Allowed exceptions that may reference source constitution directly:
- `constitution.resolve.agent.md`
- `speckit.constitution.agent.md`
- `pdlc-workflow.agent.md` (workflow orchestration and policy documentation)

4. All other agent files under `.github/agents/*.md` MUST NOT reference `.specify/memory/constitution.md`.

## Execution Steps

1. List all files matching `.github/agents/*.md`.
2. Scan each file for:
- `.specify/memory/constitution.md`
- `.specify/runtime/effective-constitution.md`
3. For each non-exception file containing `.specify/memory/constitution.md`:
- Record a violation with file path and line context.
4. Report status:
- `PASS` when no violations found.
- `BLOCKED` when one or more violations are found.

## Output Contract

Return a concise Markdown report with:
- Status (`PASS` or `BLOCKED`)
- Violations table (file, offending reference, recommended replacement)
- Exception files observed
- Suggested remediation text:
  - Replace `.specify/memory/constitution.md` with `.specify/runtime/effective-constitution.md` in violating files.

If status is `BLOCKED`, instruct the caller to stop workflow progression until violations are resolved.

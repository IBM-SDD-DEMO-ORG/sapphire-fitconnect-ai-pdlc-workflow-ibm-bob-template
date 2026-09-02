---
name: observe-workflow-reconcile
description: >
  Reconciles observe-workflow.md after all speckit phases are complete for a story.
  Queries the Bob SQLite DB with a LIKE search on the JIRA story ID to find all
  task rows, infers the workflow phase for each row from its first_message, and
  fills in any N/A stubs left by earlier observe-workflow invocations that fired
  while a task was still in-flight. Invoked automatically by speckit-ship after
  CHECKPOINT 5 is confirmed.
metadata:
  argument-hint: "<jira_id>"
---

# observe-workflow-reconcile

Reconcile all observability stubs in `specs/<JIRA_ID>/observe-workflow.md` by
performing a broad LIKE query against the Bob SQLite DB and reasoning about which
phase each returned row represents.

## Purpose

The per-phase `observe-workflow` hook often fires before the Bob DB has committed
the completed task record, producing `N/A` stubs. This skill runs **once, at the
end of `speckit-ship`**, finds every task row in the DB whose `first_message`
mentions the JIRA story ID, and patches each stub with the real metrics. It never
overwrites an entry that already has numeric token data.

## Arguments

| # | Name | Description |
|---|---|---|
| ARG1 | `jira_id` | The Jira story ID (e.g. `DPDE-225`). Resolved from `$ARGUMENTS` by the caller. |

`db_path` and `project_id` are always read from `settings.yaml`
(`observe.db_path` and `observe.project_id`). They are **not** passed as
arguments.

## Steps

### Step 1 — Resolve configuration

Read `settings.yaml` and extract:
- `db_path` = `observe.db_path`
- `project_id` = `observe.project_id`

If either is missing or still a placeholder, stop with:

```text
## Reconcile — HARD STOP: Missing observe config

settings.yaml is missing `observe.db_path` or `observe.project_id`.
Add both keys and re-run /speckit.ship STORY_ID=<jira_id>.
```

### Step 2 — Run the broad query script

Execute:

```
python .specify/scripts/python/query_tasks_by_jira.py "<db_path>" "<jira_id>" "<project_id>"
```

- On success, the script prints the path to `.specify/tmp/bob_tasks_<jira_id>.json`
  on stdout and exits with code 0.
- If the command exits with a non-zero code or stderr contains `"error"`, output:

  ```text
  ## Reconcile — Query Failed

  Reason: <stderr content>
  No observability records were updated.
  ```

  Then stop — do not modify `observe-workflow.md`.

### Step 3 — Read the query output

Use `read_file` to read the JSON array at the path printed in Step 2.

Each element in the array has:
- `task_id`
- `first_message`
- `created_at`
- `costs` (object or null)

If the array is empty, output:

```text
## Reconcile — No Rows Found

No DB rows matched JIRA ID '<jira_id>'. Nothing to reconcile.
```

Then stop.

### Step 4 — Infer the workflow phase for each row

For each row, examine `first_message` using these matching rules (apply in order,
first match wins). The agent performs this reasoning — no script is involved.

| first_message pattern | Inferred phase |
|---|---|
| contains `/speckit-specify` or `speckit.specify` | `speckit-specify` |
| contains `/speckit-clarify` or `speckit.clarify` | `speckit-clarify` |
| contains `/speckit-plan` or `speckit.plan` | `speckit-plan` |
| contains `/speckit-checklist` or `speckit.checklist` | `speckit-checklist` |
| contains `/speckit-tasks` or `speckit.tasks` | `speckit-tasks` |
| contains `/speckit-analyze` or `speckit.analyze` | `speckit-analyze` |
| contains `/speckit-impl-queue` or `speckit.impl-queue` | `speckit-impl-queue` |
| contains `/speckit-implement` or `speckit.implement` AND `REPO=` AND `PHASE=` | `speckit-implement / <REPO value> / <PHASE value>` extracted verbatim |
| contains `/speckit-implement` or `speckit.implement` AND `REPO=` (no PHASE) | `speckit-implement / <REPO value>` |
| contains `/speckit-implement` or `speckit.implement` (no REPO) | `speckit-implement` |
| contains `/speckit-ship` or `speckit.ship` | `speckit-ship` |
| none of the above | `unknown — <first_message truncated to 80 chars>` |

Build a working list: `[ { task_id, first_message, created_at, costs, inferred_phase }, … ]`

### Step 5 — Read existing observe-workflow.md

Read `specs/<jira_id>/observe-workflow.md`.

If the file does not exist, output a warning and stop — this skill should only run
after at least one observe-workflow record has been written:

```text
## Reconcile — observe-workflow.md Not Found

Expected: specs/<jira_id>/observe-workflow.md
Run /speckit.ship STORY_ID=<jira_id> to generate it first.
```

Parse the existing file to identify **stub entries** — sections that contain:
```
| Input tokens | N/A |
```
A stub is any `## Observation — …` block whose Token Usage table has `N/A` for
`Input tokens`.

For each stub, extract the workflow phase name from its `- **Workflow phase**:`
line (or from its heading if no phase line is present).

### Step 6 — Match DB rows to stubs

For each stub identified in Step 5:
1. Look for a DB row (from Step 4) whose `inferred_phase` matches the stub's
   workflow phase. Match is case-insensitive; ignore surrounding whitespace.
2. If a match is found AND `costs` is non-null in that DB row, mark the pair as
   **RECONCILABLE**.
3. If no match is found, or costs is null, mark as **UNRESOLVABLE** — leave the
   stub unchanged.

If there are DB rows with no matching stub (i.e. a phase ran but was never
recorded at all), treat them as **NEW** entries to append.

### Step 7 — Patch stubs and append new entries

For each **RECONCILABLE** pair, replace the stub block in `observe-workflow.md`
with a fully populated observation block. Use `search_and_replace` targeting the
exact stub heading line.

Populate the block using the same template as `observe-workflow`:

```markdown
## Observation — <task_id> — <created_at as ISO date>

### Task
- **Task ID**: `<task_id>`
- **Jira Story**: <jira_id>
- **Workflow phase**: <inferred_phase>

### Token Usage
| Metric | Value |
|---|---|
| Input tokens | <input> |
| Output tokens | <output> |
| Cache read | <cacheRead> |
| Cache write | <cacheWrite> |
| Cache hit rate | <cache_hit_%>% |
| Context tokens (reported) | <contextTokens> |
| **Total cost (USD)** | **$<cost>** |

### Context Window Breakdown
| Section | Tokens | % of computed total |
|---|---|---|
| MCP tool definitions | <mcpToolDefinitions> | <pct>% |
| Skills | <skills> | <pct>% |
| Tool system prompts | <toolSystemPrompts> | <pct>% |
| Tool definitions | <toolDefinitions> | <pct>% |
| Project rules | <projectRules> | <pct>% |
| Static sections | <staticSections> | <pct>% |
| Custom instructions | <customInstructions> | <pct>% |
| Base rules | <baseRules> | <pct>% |
| Environment | <environment> | <pct>% |
| Role definition | <roleDefinition> | <pct>% |
| **Total (computed)** | **<total>** | 100% |

### Loaded Skills
| Skill | Tokens |
|---|---|
<one row per entry in costs.contextWindowBreakdown.loadedSkills>

### Observations
- Cache hit rate: <cache_hit_%>% — <"high efficiency" if ≥ 80%, "moderate" if 40–79%, "low — consider cache warm-up" if < 40%>
- Largest context consumer: <section with highest token count> (<tokens> tokens, <pct>%)
- Output/input ratio: <round(output/input*100,2)>% — <"generation-heavy" if > 1%, "analysis/read-heavy" if ≤ 1%>

---
```

Derivation rules:
- **Cache hit %** = `round(cacheRead / input * 100, 1)` — set `0` if `input` is 0
- `<pct>` = `round(token_count / total * 100, 1)`
- Use `N/A` for any field absent or null in `costs`
- Context Window Breakdown fields map from `costs.contextWindowBreakdown.breakdown.*`
- `loadedSkills` rows come from `costs.contextWindowBreakdown.loadedSkills` array
- MCP Servers section is **omitted** in reconciled entries (no `messages` array is
  fetched by this script — only `costs` is available)

For each **NEW** DB row (no matching stub), append a full observation block to the
end of `observe-workflow.md` using `insert_content` at line 0.

For each **UNRESOLVABLE** stub, leave it unchanged and note it in the summary.

### Step 8 — Delete the temporary file

After all writes in Step 7 succeed, delete the temporary JSON file:

```
execute_command: Remove-Item -Force "<path printed by Step 2>"
```

If deletion fails, log a warning and continue.

### Step 9 — Output the reconciliation summary

Print:

```text
## Reconcile Complete — <jira_id>

| Phase | Task ID | Action |
|---|---|---|
| <inferred_phase> | <task_id> | PATCHED stub / APPENDED new / UNRESOLVABLE (no costs) / UNRESOLVABLE (no match) |
| … | … | … |

Total DB rows found: <N>
Stubs patched: <N>
New entries appended: <N>
Unresolvable stubs remaining: <N>
```

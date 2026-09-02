---
name: observe-workflow
description: Use when a speckit skill (specify, clarify, plan, implement) completes a task and needs to record token usage, cost, and context metrics for observability. Also invoked directly via /observe-workflow. Records results as observe-workflow.md alongside workflow-state.md in the story directory.
metadata:
  argument-hint: "<db_path> <first_message> <project_id> <jira_id>"
---

# observe-workflow

Query the Bob SQLite database for a completed task and write a structured observability record to `specs/<JIRA_ID>/observe-workflow.md`, parallel to `workflow-state.md`.

## Arguments

| # | Name | Description |
|---|---|---|
| ARG1 | `db_path` | Absolute path to the Bob SQLite DB (e.g. `C:/Users/<name>/.bob/db/bob.db`) |
| ARG2 | `first_message` | The `first_message` value to match in the `tasks` table |
| ARG3 | `project_id` | The `project_id` value to match in the `tasks` table |
| ARG4 | `jira_id` | The Jira story ID (e.g. `DPDE-223`), used to locate the output directory |

## Invocation modes

**Hook invocation** (automatic, triggered at the end of speckit skills via `after_specify`, `after_clarify`, `after_plan`, `after_implement`):
- The calling speckit skill resolves and supplies all four arguments before invoking this skill.
- ARG1 and ARG3 are read by the calling skill from `settings.yaml` (`observe.db_path` and `observe.project_id`).
- ARG2 is the first user message of the current task (already in context for the calling skill).
- ARG4 is the Jira story ID held in the calling skill's working memory (loaded from `workflow-state.md`).

**Direct invocation** (`/observe-workflow ARG1 ARG2 ARG3 ARG4`):
- All four arguments must be supplied explicitly. If any are missing, use `ask_followup_question`.

## Steps

### Step 1 — Resolve arguments

**If invoked as a hook**: all four arguments are already supplied by the calling speckit skill. Proceed directly.

**If invoked directly**: use the supplied arguments as-is. For any that are still missing:
1. ARG1 (`db_path`) and ARG3 (`project_id`) — read `settings.yaml` and extract `observe.db_path` and `observe.project_id`. If absent or still placeholder values, ask via `ask_followup_question`.
2. ARG2 (`first_message`) — ask via `ask_followup_question` if not supplied.
3. ARG4 (`jira_id`) — scan `specs/` for a `workflow-state.md` and extract `Story ID:`. If not found, ask via `ask_followup_question`.

Do not proceed until all four values are resolved.

### Step 2 — Run the query script

Execute:

```
python .specify/scripts/python/query_task.py "<ARG1>" "<ARG2>" "<ARG3>"
```

- On success, the script prints the path to `.specify/tmp/bob_task_<task_id>.json` on stdout.
- If the command exits with a non-zero code or stderr contains an error JSON, report the error and stop.

### Step 3 — Read the output file

Use `read_file` to read the JSON file at the path printed in Step 2. Extract the following fields:

- `task_id`
- `costs.input`
- `costs.output`
- `costs.cacheRead`
- `costs.cacheWrite`
- `costs.cost`
- `costs.contextTokens`
- `costs.contextWindowBreakdown.total`
- `costs.contextWindowBreakdown.breakdown` (all sub-fields)
- `costs.contextWindowBreakdown.loadedSkills` (array of `{name, tokens}`)

Also derive:
- **Cache hit %** = `round(cacheRead / input * 100, 1)` (set to `0` if input is 0)
- **MCP servers** = parse the `availableTools` array from the first `user` message; group by the `mcp__<server>__` prefix and count tools per server

### Step 4 — Determine the output path

The output file is:

```
specs/<ARG4>/observe-workflow.md
```

If the directory `specs/<ARG4>/` does not exist, stop and report an error — do not create it (the speckit workflow is responsible for directory setup).

If `observe-workflow.md` already exists, **append** a new dated entry to it rather than overwriting.

### Step 5 — Write the observability record

Use `write_file` (new file) or `insert_content` (append) to write the following Markdown block. Fill every placeholder from the data extracted in Step 3.

```markdown
## Observation — <task_id> — <ISO timestamp>

### Task
- **Task ID**: `<task_id>`
- **Jira Story**: <ARG4>

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
<one row per entry in loadedSkills>

### MCP Servers
| Server | Tool count |
|---|---|
<one row per mcp__<server>__ prefix group>

### Observations
- Cache hit rate: <cache_hit_%>% — <"high efficiency" if ≥ 80%, "moderate" if 40–79%, "low — consider cache warm-up" if < 40%>
- Largest context consumer: <name of the section with the highest token count> (<tokens> tokens, <pct>%)
- Output/input ratio: <round(output/input*100,2)>% — <"generation-heavy" if > 1%, "analysis/read-heavy" if ≤ 1%>
<if any mcp server appears twice (e.g. github and github_local_mcp both present): "- ⚠️ Duplicate MCP coverage detected: <list> — consider removing one to reduce context overhead">

---
```

Compute every `<pct>` value as `round(token_count / total * 100, 1)`. Use `N/A` for any field that is null or absent in the JSON.

### Step 6 — Delete the temporary file

After the observability record has been successfully written in Step 5, delete the temporary JSON file that was read in Step 3:

```
execute_command: Remove-Item -Force "<path printed by Step 2>"
```

If the file does not exist or the delete fails, log a warning but do **not** fail the skill — the record has already been written.

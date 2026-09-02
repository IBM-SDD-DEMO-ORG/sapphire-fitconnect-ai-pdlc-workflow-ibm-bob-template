---
name: constitution-resolve
description: Use when the user wants to resolve or regenerate the runtime effective constitution, run /constitution.resolve, merge global and local constitutions with local precedence, or update .specify/runtime/effective-constitution.md. Required before spec/plan/implement workflows when the effective constitution is missing.
---

# constitution-resolve

Resolve runtime effective constitution artifacts by loading global and local constitutions with defined precedence.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Build runtime policy artifacts from two constitution sources with local precedence:

1. **Global constitution** (optional) — may come from a local sibling repo directory, an explicit file path, or a remote location fetched via connector. If absent, the effective constitution contains the local constitution only.
2. **Local constitution** (optional) — `.specify/memory/constitution.md`. If absent, the effective constitution contains the global constitution only.

Local policy has higher precedence than global policy.

## Operating Constraints

- Use filesystem tools for local file operations.
- Use configured MCP tools for remote fetches (see MCP Provider Routing Table in Step 1a for tool mapping).
- Do not call shell commands.
- Do not modify either source constitution.
- This command is a preflight and must run before downstream planning/implementation.
- Keep `constitution.pathlint` behavior unchanged.

## Global Constitution Source Modes

The global constitution source is configurable. Three modes are supported. The **mode is always driven by `settings.yaml`** (or the built-in default); `$ARGUMENTS` may only supply values required by the active mode — not switch it.

| Mode | Required `$ARGUMENTS` | Example value | Resolution |
|---|---|---|---|
| **Local path** | _(none required)_ | — | Reads `path` from `settings.yaml`. |
| **External (MCP)** | `context_id` _(prompted if absent)_ | `ctx_abc123` | Fetch via configured MCP provider (see step 1a). |
| **None / skip** | _(none)_ | — | No global constitution. Effective constitution = local only. |

## Execution Steps

1. **Determine paths and source mode**

   Resolve the active mode using this precedence order (first match wins):

   1. **`settings.yaml`** (project root) — read `constitution.global_source.mode`. If the file is missing, fall through.
   2. **Built-in default** — `mode: local`, `path: ../org-policy-files/engineering`.

   **Mode-argument validation** — once the active mode is resolved, check `$ARGUMENTS` for conflicts:
   - If `$ARGUMENTS` contains `context_id` but mode is **not** `external` → stop with error.
   - If `$ARGUMENTS` contains `global_path` but mode is **not** `local` → stop with error.
   - If `$ARGUMENTS` contains `global_skip` but mode is **not** `none` → stop with error.

   **Step 1a — For `mode: external` (MCP-based global constitution):**

   - Read `constitution.global_source.connection-types` from `settings.yaml`.
   - Validate: `connection-types.MCP` must be present. If missing, stop with error.
   - Validate: `connection-types.MCP.provider` must equal `context-studio`. If different or missing, stop with error.
   - **MCP Provider Routing Table**:
     ```
     provider → MCP tool to invoke
     context-studio → context-broker-hybrid-query
     ```
   - **Require context_id**: Check `$ARGUMENTS` for `context_id`. If absent, **ask the user**: "Please provide the context ID for context-studio (format: `context_id: <id>`)." Wait for the user's response before proceeding.

   Resolved modes:
   - `mode: local` + `path` → set mode = **local**
   - `mode: external` + validated MCP provider + `context_id` → set mode = **external**, provider = **context-studio**
   - `mode: none` → set mode = **none** (`global_found = false` immediately)

   Fixed output paths (not configurable unless overridden in `$ARGUMENTS`):
   - Global snapshot: `.specify/runtime/global-constitution.md`
   - Effective output: `.specify/runtime/effective-constitution.md`
   - Report output: `.specify/runtime/effective-constitution-report.md`
   - Local constitution path: `.specify/memory/constitution.md` (or `local_path` from `$ARGUMENTS`).

2. **Resolve and validate inputs**

   **Local constitution (optional):**
   - Check whether `.specify/memory/constitution.md` exists.
   - If missing → set `local_found = false`. Do **not** error; proceed. The effective constitution will be global-only (or empty if global is also absent — see blocking rule below).
   - If present → set `local_found = true`.
   - **Blocking rule**: if both `local_found = false` AND global resolution will yield `global_found = false` (mode is `none`, or local path does not exist), stop with a clear error: "Neither local nor global constitution is available — nothing to resolve."

   **Global constitution (optional — behaviour by mode):**
   - **Mode: local** — Treat the path as a directory. Find the first existing file in order:
     1. `constitution.md`
     2. `engineering-constitution.md`
     3. `global-constitution.md`
     - If the path is a direct file (not a directory), use it as-is.
     - If the directory/file does not exist → set `global_found = false`. Do **not** error; proceed with local-only mode.
     - **On success (file found)**: Read the file content and copy it verbatim to `.specify/runtime/global-constitution.md`. Set `global_found = true`.
   - **Mode: external** — Call the `context-broker-hybrid-query` MCP tool with the `context_id` payload to fetch the global constitution. On success → set `global_found = true`, store constructed content, copy to `.specify/runtime/global-constitution.md`. On failure → hard stop.
   - Record which source was used in the report (step 9).

3. **Ensure runtime directory exists**
   - Create `.specify/runtime/` if missing.

4. **Global file snapshot**
   - Already handled in Step 2: files are copied to `.specify/runtime/global-constitution.md` during resolution.
   - If `global_found = false`, no global file is written.

5. **Read source files**
   - If `local_found = true`: read the complete text of `.specify/memory/constitution.md`.
     - **Detect if local constitution is a template**: scan the content for unfilled placeholder markers matching the pattern `[WORD]` or `[WORD_WORD_...]`. If any such markers are found, set `local_is_template = true`; otherwise `local_is_template = false`.
   - If `local_found = false`: set `local_is_template = false` (no local content to inspect).

6. **Compose effective constitution**

   Determine the composition case using `global_found`, `local_found`, and `local_is_template`:

   **Case A — `global_found = true` AND `local_found = true` AND `local_is_template = false` (global + real local):**
   - First run step 7 (conflict analysis), then write this file.
   - Structure: HTML comment header + "Resolved Rules" conflict table + PART 1 (global) + PART 2 (local, authoritative).

   **Case B — `global_found = true` AND (`local_found = false` OR `local_is_template = true`) (global-only):**
   - Skip step 7.
   - If `local_found = false`: HTML comment header noting local constitution is absent.
   - If `local_is_template = true`: HTML comment header noting local is an unfilled template.
   - Structure: header + full global content only.

   **Case C — `global_found = false` AND `local_found = true` (local-only, regardless of template status):**
   - Skip steps 7 and conflict analysis. Structure: HTML comment header + full local content only.

   In all cases: do **not** add inline annotations or conflict markers inside the constitution body.

7. **Identify conflicts (analysis pass — read-only, Case A only)**
   - Skip entirely if `global_found = false` or `local_found = false` or `local_is_template = true`.
   - Review both parts and identify every section or rule where local and global directly conflict.
   - Collect each conflict: global rule (with section reference), local rule (with section reference), resolution (local wins).
   - Do **not** modify either source file.
   - **This step MUST complete before writing step 6** — the Resolved Rules table is populated from the output here.

8. **Write effective constitution**
   - Using the output of step 7 (if applicable), write `.specify/runtime/effective-constitution.md` per the template in step 6.
   - Case A: populate the Resolved Rules table (one row per conflict; omit the table entirely if no conflicts were found).
   - Case B: write the global-only template.
   - Case C: write the local-only template.

9. **Write resolution report**
   - Write `.specify/runtime/effective-constitution-report.md` with:
     - **Timestamp** (ISO 8601 UTC)
     - **Global source mode**: local path / external (with provider name and context_id if applicable) / none
     - **Local source**: `.specify/memory/constitution.md`
     - **local_found**: true / false (with note if false)
     - **global_found**: true / false (with reason if false)
     - **Precedence rule applied**
     - **Status**: `PASS` or `BLOCKED`
     - **Override Callouts** section (only when `global_found = true`)
     - **Blocking errors** (both sources absent, missing context_id, MCP validation failure, MCP fetch failure)

10. **Output summary**
    - Return artifact paths and readiness state.

11. **Invoke observe-workflow**: After outputting the summary, unconditionally invoke the `observe-workflow` skill with the following four arguments resolved in this order:
    - ARG1 (`db_path`): read `settings.yaml` → `observe.db_path`
    - ARG2 (`first_message`): the **first user message sent in the current chat session** (the literal text of the first `user` role turn in this conversation — this is what the query script matches against in the database)
    - ARG3 (`project_id`): read `settings.yaml` → `observe.project_id`
    - ARG4 (`jira_id`): the active Jira story ID (from `$ARGUMENTS` if present; otherwise pass an empty string)

## Output Contract

On success, always produce:
- `.specify/runtime/effective-constitution.md` — either two-part concat (with Resolved Rules table) or local-only, depending on `global_found`.
- `.specify/runtime/effective-constitution-report.md` — source mode, conflict callouts, status.
- `.specify/runtime/global-constitution.md` — only when `global_found = true`.

On failure, do not produce partial artifacts unless the report clearly explains why status is `BLOCKED`.

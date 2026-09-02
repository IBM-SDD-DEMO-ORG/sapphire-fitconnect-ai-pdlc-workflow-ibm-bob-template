# Constitution Resolution Report

## Metadata

| Field | Value |
|-------|-------|
| **Timestamp** | 2025-07-17T00:00:00Z |
| **Status** | PASS |

## Sources

| Field | Value |
|-------|-------|
| **Global source mode** | external (provider: context-studio MCP) |
| **Global found** | false — user elected to skip global fetch; no `context_id` supplied |
| **Local source** | `.specify/memory/constitution.md` |
| **Local found** | true |
| **Local is template** | false |

## Resolution

| Field | Value |
|-------|-------|
| **Composition case** | C — Local-only |
| **Precedence rule** | Local constitution only; no global content present to merge |
| **Conflict analysis** | Skipped (global not available) |
| **Override callouts** | N/A (global not available) |

## Output Artifacts

| Artifact | Path | Written |
|----------|------|---------|
| Effective constitution | `.specify/runtime/effective-constitution.md` | ✅ |
| Global snapshot | `.specify/runtime/global-constitution.md` | ❌ (global not fetched) |
| This report | `.specify/runtime/effective-constitution-report.md` | ✅ |

## Blocking Errors

None.

## Notes

- The global constitution source is configured as `mode: external` with provider `context-studio`
  in `settings.yaml`. To include a global constitution in a future run, re-invoke
  `/constitution.resolve` and supply a `context_id` value when prompted.
- `TODO(RATIFICATION_DATE)` remains deferred in the local constitution. Update
  `.specify/memory/constitution.md` line 158 with the formal ratification date and
  re-run `/constitution.resolve`.

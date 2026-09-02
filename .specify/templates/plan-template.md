# Implementation Plan: [FEATURE]

**Branch**: `[branch-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[branch-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]  
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Gate | Principle | Status |
|---|------|-----------|--------|
| 1 | All public functions/methods/classes have docstrings or Javadoc (intent, not implementation) | I. Code Quality | [ ] |
| 2 | No magic numbers or strings — named constants or enums used | I. Code Quality | [ ] |
| 3 | Cyclomatic complexity ≤ 10 per function/method confirmed via static analysis | I. Code Quality | [ ] |
| 4 | No commented-out code committed; feature flags or deletion used instead | I. Code Quality | [ ] |
| 5 | Stack-specific rules applied (Spring layering / PEP 8 + ruff / strict TS / BFF DataLoader) | I. Code Quality | [ ] |
| 6 | Coverage gates planned: Java 80%/100% domain, Python 80%, TS/React 70%, BFF resolvers 100% | II. Testing Standards | [ ] |
| 7 | Contract tests planned for all GraphQL schema changes and Kafka event schema changes | II. Testing Standards | [ ] |
| 8 | Test pyramid respected: unit (mocked I/O), integration (Docker Compose, pre-merge only, not validation), E2E | II. Testing Standards | [ ] |
| 9 | All data-fetching components handle loading skeleton / error boundary / empty state | III. UX Consistency | [ ] |
| 10 | Auth path is exclusively Keycloak OIDC/PKCE; no bypass routes in any environment | III. UX Consistency | [ ] |
| 11 | URL state is source of truth for filters, pagination, and selections | III. UX Consistency | [ ] |
| 12 | Apollo cache policies explicit; no implicit cache-first for mutable health data; cache TTL ≥ 30 s per session | I. Code Quality | [ ] |
| 13 | All services emit structured JSON logs (Logback+logstash / structlog / pino) with trace_id and span_id fields | IV. Observability | [ ] |
| 14 | OTEL metrics exported to Collector: request count, duration histogram, error rate, in-flight counter; custom business metrics added | IV. Observability | [ ] |
| 15 | Distributed traces emitted via OTEL SDK; W3C traceparent propagation used; DB, HTTP, and Kafka operations instrumented as child spans | IV. Observability | [ ] |
| 16 | OTEL_EXPORTER_OTLP_ENDPOINT, OTEL_SERVICE_NAME, and OTEL_DEPLOYMENT_ENVIRONMENT set in every container; no direct backend export from services | IV. Observability | [ ] |
| 17 | *(LangGraph only)* Graph state typed as `TypedDict` with `Annotated` reducers; graph compiled once at startup; nodes are single-responsibility `async`; persistent checkpointer used in production; tool schemas use Pydantic v2 `BaseModel`; trace output enabled in non-local environments | I. Code Quality | [ ] |

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

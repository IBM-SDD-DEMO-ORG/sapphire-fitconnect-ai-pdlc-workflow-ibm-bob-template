<!--
EFFECTIVE CONSTITUTION
======================
Composition case: C — Local-only (global constitution not available)

Global source mode : external (context-studio MCP)
Global found       : false — user elected to skip global fetch (no context_id provided)
Local source       : .specify/memory/constitution.md
Local found        : true
Local is template  : false
Precedence rule    : local-only; no global content present to merge

No global constitution was fetched. This effective constitution contains the
local project constitution only. To include a global constitution, re-run
/constitution.resolve and supply a valid context_id for context-studio.

Generated          : 2025-07-17
-->

# AI PDLC Workflow Sidekick Constitution

## Core Principles

### I. Governed PDLC Workflow

Every feature MUST progress through the full PDLC lifecycle in strict sequence:
Specify → Clarify → Plan → Tasks → Implement → Ship.

- Each phase MUST produce a versioned artifact committed to the sidekick repo.
- No phase may begin until the preceding phase artifact exists and has passed its
  designated approval gate.
- Skipping or short-circuiting any phase is a governance violation that MUST be
  surfaced and remediated before delivery.

**Rationale**: Brownfield teams face hidden coupling across services. Enforcing the
full lifecycle ensures impact is understood before code is written.

### II. Role-Based Approval Gates

Each lifecycle gate MUST be approved by the designated role as configured in
`settings.yaml` → `pdlc.approvals`.

- A submitter MUST NOT self-approve their own gate; the approver MUST be a
  different identity.
- Spec gate MUST be approved by `product_owner` before planning begins.
- Plan and tasks gates MUST be approved by `fde` before implementation begins.
- GitHub PR approval is the ONLY valid approval signal; chat or verbal
  confirmation is NOT sufficient.
- `require_merge: true` gates MUST be fully merged before the next phase starts.

**Rationale**: Separating submitter and approver roles prevents unreviewed work
from entering downstream phases and provides an auditable compliance record.

### III. Spec-Before-Code (NON-NEGOTIABLE)

No implementation work may begin on any repository until all of the following
artifacts exist and have passed their gates:

1. `specs/<story>/spec.md` — approved by product owner.
2. `specs/<story>/plan.md` + supporting design artifacts — approved by FDE.
3. `specs/<story>/tasks.md` — approved by FDE.

- Implementation branches MUST be created from an approved tasks artifact.
- Hotfixes to production are exempt from planning gates but MUST produce a
  retrospective spec entry within 48 hours of deployment.

**Rationale**: Premature coding in brownfield systems creates unreviewed coupling.
Forcing design-first prevents costly late-stage rework.

### IV. Cross-Repo Traceability

Every change MUST be traceable from JIRA story → spec → plan → tasks → PR.

- Each task in `tasks.md` MUST reference its parent user story.
- Pull requests MUST reference the JIRA story ID and the tasks artifact.
- JIRA child stories MUST be created per affected repository during the plan phase
  and updated with PR links during the ship phase.
- Orphaned PRs (no JIRA link, no spec reference) MUST NOT be merged.

**Rationale**: Multi-repo brownfield changes frequently lose traceability. Explicit
linking from story to PR enables impact analysis, rollback scoping, and audits.

### V. Observability & Auditability

All services modified by a feature MUST satisfy the following before ship:

- Structured JSON logs emitted with `trace_id` and `span_id` fields (Logback /
  structlog / pino or equivalent).
- OTEL metrics exported: request count, duration histogram, error rate.
- Distributed traces emitted via OTEL SDK with W3C traceparent propagation.
- `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME`, and
  `OTEL_DEPLOYMENT_ENVIRONMENT` MUST be set in every container.
- Workflow observability: Bob task metrics recorded via `observe-workflow` skill
  with `db_path` and `project_id` configured in `settings.yaml`.

**Rationale**: Without structured observability, brownfield incidents are
undiagnosable. Tracing must span service boundaries to be useful.

## API Compatibility & Contracts

- All API changes MUST include a backward-compatibility assessment documented in
  the plan artifact.
- Breaking changes (schema removal, field rename, behaviour change) MUST be
  versioned and accompanied by a migration plan before the plan gate is approved.
- GraphQL schema changes and Kafka event schema changes MUST include contract
  tests that are written and verified failing before implementation begins.
- Internal service contracts (REST, GraphQL, events) MUST be captured under
  `specs/<story>/contracts/` as part of the plan phase.

## Development Workflow & Quality Gates

- Coverage gates MUST be met before a PR can be merged:
  Java 80% overall / 100% domain layer; Python 80%; TypeScript/React 70%;
  BFF resolvers 100%.
- The test pyramid MUST be respected: unit tests (mocked I/O) → integration tests
  (Docker Compose, pre-merge only) → E2E.
- All public functions, methods, and classes MUST have docstrings or Javadoc
  capturing intent (not implementation).
- No magic numbers or strings — named constants or enums MUST be used.
- No commented-out code may be committed; feature flags or deletion MUST be used.
- Cyclomatic complexity MUST be ≤ 10 per function/method (verified via static
  analysis).

## Governance

This constitution supersedes all other local practices and guidelines for this
sidekick workspace. It is complemented by the organization-wide global
constitution resolved into `.specify/runtime/effective-constitution.md`.

- Amendments MUST be proposed as a PR against `.specify/memory/constitution.md`
  and reviewed by at least one FDE and one Product Owner.
- The version MUST be incremented per semantic versioning:
  MAJOR for governance/principle removals or redefinitions;
  MINOR for new principles or materially expanded guidance;
  PATCH for clarifications, wording, or typo fixes.
- Compliance review MUST occur at the plan gate: the Constitution Check table in
  `plan-template.md` is the canonical compliance checklist.
- After any amendment, `/constitution.resolve` MUST be re-run to regenerate
  `.specify/runtime/effective-constitution.md`.
- All PRs and reviews MUST verify compliance with this constitution before
  approval is granted.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): original adoption date unknown — set when team formally adopts | **Last Amended**: 2025-07-17

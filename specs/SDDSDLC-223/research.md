# Research: SDDSDLC-223 — Body Temperature Metric Ingestion, Storage, and Reporting

**Branch**: `SDDSDLC-223` | **Date**: 2025-07-17

---

## Decision Log

### D-001: Time-Series Storage Pattern for New Metric Type

**Decision**: Extend the existing metrics datastore table/collection by adding `body_temperature` as a new metric type discriminator value, reusing the existing `(user_id, metric_type, timestamp)` composite index pattern.

**Rationale**: The platform already stores blood pressure, SpO2, and activity data. Adding temperature as a new `metric_type` enum value is the lowest-risk path — it reuses existing schema, indexes, retention policies, and rollup infrastructure. A separate table would require new migrations, new rollup jobs, and duplicate retention logic.

**Alternatives considered**:
- Separate `body_temperature` table: rejected — unnecessary schema proliferation, duplicates rollup and retention infrastructure.
- Key-value store per metric: rejected — too loose for typed health data; breaks existing analytics query patterns.

---

### D-002: Idempotency Key for Duplicate Detection

**Decision**: Use a composite natural key `(user_id, device_source, timestamp, value)` for duplicate detection at ingestion time. No separate idempotency token field required.

**Rationale**: The spec (FR-005a) mandates idempotent ingestion. The natural key is sufficient because temperature readings from the same device at the same timestamp with the same value are definitionally identical. Introducing a client-generated idempotency token adds complexity for device manufacturers and is not required by the Jira story.

**Alternatives considered**:
- Client-generated `idempotency_key` header: deferred — adds device-side complexity; natural key sufficient for this story.
- Database unique constraint only: chosen as the primary mechanism; service layer converts constraint violation to a success response.

---

### D-003: Unit Storage and Display Conversion

**Decision**: Store values as submitted (preserving original unit). Client-side °C↔°F conversion only. Backend always returns `{ value, unit }` as stored.

**Rationale**: Clarification Q1 confirmed view-only toggle. Storing in a canonical unit (e.g. always Kelvin or always Celsius) would require lossy conversion for Fahrenheit devices and conflict with FR-002 ("submitted unit MUST be preserved"). Client-side conversion is trivial and keeps the API contract simple.

**Alternatives considered**:
- Canonical storage in Celsius: rejected — would lose precision for °F inputs and conflicts with FR-002.
- Backend unit-preference query param: rejected — Clarification Q1 explicitly rejected this (Option C).

---

### D-004: Rollup Pre-Computation Strategy

**Decision**: Extend the existing scheduled rollup job to process `body_temperature` records using the same aggregation pipeline as other metric types (daily → weekly → monthly, computing min/max/average per user per period).

**Rationale**: The spec (FR-012) requires consistency with existing rollup strategy. Building a separate rollup path would be a maintenance burden and violates the simplicity principle. The existing job can accept `body_temperature` as a new metric_type input with no structural change to the aggregation logic.

**Alternatives considered**:
- On-demand aggregation (no pre-compute): rejected — SC-003 requires trend data within 1 second for 365-day datasets; on-demand aggregation at this volume would exceed the latency target.
- Separate rollup service: rejected — no new scheduling infrastructure per FR-012 assumption.

---

### D-005: Batch Ingestion Error Response Shape

**Decision**: Use a partial-success response envelope for batch submissions: HTTP 207 Multi-Status with per-record `{ index, status, error? }` entries.

**Rationale**: FR-005 requires per-record independent processing and itemised success/failure. HTTP 207 is the standard for batch operations with mixed outcomes. This avoids ambiguity of HTTP 200 with embedded errors.

**Alternatives considered**:
- HTTP 200 with embedded errors array: viable but HTTP 207 is semantically cleaner for partial success.
- Fail-all-or-nothing (HTTP 400 on any invalid): rejected — FR-005 explicitly requires valid records to be stored even when others are invalid.

---

### D-006: Frontend Chart Component Approach

**Decision**: Implement the temperature chart as a new metric-specific chart component reusing the existing chart library already used for blood pressure / SpO2 trend charts. The component receives `{ records: TemperatureRecord[], unit: 'C' | 'F' }` props and handles client-side °C↔°F toggle internally.

**Rationale**: Reusing the existing charting library preserves visual consistency and avoids a new dependency. The component follows the same data-in/display-out pattern already established for other metrics.

**Alternatives considered**:
- Generic parameterised metric chart component: ideal long-term but out of scope for this story — would require refactoring existing metric charts; deferred.

---

### D-007: Future Timestamp Tolerance Window

**Decision**: Reject timestamps more than 5 minutes ahead of server UTC time (HTTP 422). Accept up to 5 minutes for device clock drift.

**Rationale**: Clarification Q3 confirmed this. 5 minutes is a standard tolerance used in OAuth token validation and health-data APIs (e.g. Apple HealthKit, Google Fit). It prevents chart corruption while tolerating typical consumer-device clock drift (usually < 60 seconds).

---

### D-008: Physiological Range Configuration

**Decision**: Store validation range bounds (min/max) as service-level configuration (environment variable or config file), defaulting to 25–45 °C (77–113 °F). The service reads this at startup; no per-request or per-user override.

**Rationale**: FR-003 requires a configurable range. Per-user overrides (e.g. for patients with chronic fever) are not mentioned in the story and would require a settings model — deferred. Service-level config is the simplest implementation that satisfies the requirement.

---

## Outstanding Items (deferred to planning/implementation)

- Exact tech stack for `sapphire-fitconnect-health-service` (Java/Spring Boot or Python/FastAPI) — must be confirmed by reading the repo when available. Plan uses neutral terminology; implementation tasks will specify exact file paths and framework conventions.
- DST boundary handling for rollup periods — implementation detail; the existing rollup job's DST handling applies.
- Exact GraphQL vs REST API shape — depends on how existing metric endpoints are structured; contract files will define both options; implementation team resolves on first code read.

# Implementation Plan: SDDSDLC-223 — Body Temperature Metric Ingestion, Storage, and Reporting

**Branch**: `SDDSDLC-223` | **Date**: 2025-07-17 | **Spec**: [specs/SDDSDLC-223/spec.md](specs/SDDSDLC-223/spec.md)
**Input**: Feature specification from `specs/SDDSDLC-223/spec.md`

---

## Summary

Add body temperature as a first-class health metric to the FitConnect platform. The work spans three repositories:

- **`sapphire-charting-api`** (backend REST): new `bodytemperature` TimescaleDB table, `BODY_TEMPERATURE` enum entry, REST ingestion + trend endpoints following the existing `/api/v1/metrics/{metric}/readings` pattern.
- **`sapphire-bff-api`** (GraphQL BFF): new `bodyTemperatureReadings` query, `bodyTemperatureTrends` query, and `addBodyTemperatureReading` mutation added to `typeDefs.js` + resolvers.
- **`Sapphire`** (frontend): new `BodyTemperatureChart` component in `client/src/components/charts/` following the `HeartRateChart` pattern, new GraphQL queries in `client/src/graphql/health.ts`, dashboard integration in `client/src/pages/dashboard.tsx`.

All design decisions are documented in [`specs/SDDSDLC-223/research.md`](specs/SDDSDLC-223/research.md).

---

## Technical Context

**Language/Version**:
- `sapphire-charting-api`: Java 17, Spring Boot 3.2.2
- `sapphire-bff-api`: Node.js, Apollo Server (GraphQL)
- `Sapphire`: TypeScript 5.6, React 18.3, Vite 5.4

**Primary Dependencies**:
- `sapphire-charting-api`: Spring Boot 3.2.2, Lombok, Jackson, Springdoc OpenAPI 3, TimescaleDB (PostgreSQL 12+)
- `sapphire-bff-api`: Apollo Server, graphql-tag
- `Sapphire`: Apollo Client, Recharts, `@/components/ui/select` (Shadcn), Keycloak OIDC (oidc-client-ts)

**Storage**: TimescaleDB (PostgreSQL + TimescaleDB extension) — new `bodytemperature` hypertable following the same schema as existing metric tables (e.g. `heartrate`, `bloodpressure`)

**Testing**:
- `sapphire-charting-api`: JUnit 5, Maven Surefire; coverage gate 80%
- `sapphire-bff-api`: Jest (assumed, standard Apollo Server testing)
- `Sapphire`: Vitest + Playwright (e2e); coverage gate TypeScript 70%

**Target Platform**: Linux container (charting-api, bff-api); Browser SPA (Sapphire)

**Project Type**: REST service + GraphQL BFF + React SPA

**Performance Goals**: Ingestion ≤ 2 s p95; trend query ≤ 1 s for 365 days of data (SC-001, SC-003); chart renders ≤ 2 s (SC-004)

**Constraints**: Backward-compatible schema and API (FR-008); no new datastore infrastructure; reuse existing TimescaleDB hypertable pattern; BFF follows existing Apollo resolver pattern

**Scale/Scope**: Up to 12 temperature readings per user per day; 2-year dataset horizon

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Gate | Principle | Status |
|---|------|-----------|--------|
| 1 | All public functions/methods/classes have docstrings or Javadoc | I. Code Quality | ✅ Planned — Java: Javadoc on controller/service/repository; TS: JSDoc on components |
| 2 | No magic numbers or strings — named constants or enums used | I. Code Quality | ✅ Planned — `MetricType.BODY_TEMPERATURE` enum; `IngestionSource` enum; `TemperatureUnit` enum |
| 3 | Cyclomatic complexity ≤ 10 per function/method | I. Code Quality | ✅ Planned — validation, ingestion, rollup split into single-responsibility methods |
| 4 | No commented-out code committed | I. Code Quality | ✅ Planned |
| 5 | Stack-specific rules: Spring layering; strict TS | I. Code Quality | ✅ Planned — Controller → Service → Repository layering; strict TypeScript in Sapphire |
| 6 | Coverage gates: Java 80%, TS/React 70% | II. Testing Standards | ✅ Planned — targets in Technical Context above |
| 7 | Contract tests for REST API schema changes | II. Testing Standards | ✅ Planned — OpenAPI contract in `contracts/` |
| 8 | Test pyramid: unit → integration → E2E | II. Testing Standards | ✅ Planned — unit (mocked I/O), integration (TimescaleDB test container), E2E (quickstart.md) |
| 9 | Data-fetching components handle loading / error / empty state | III. UX Consistency | ✅ Planned — `BodyTemperatureChart` must handle `data=[]` empty state and loading skeleton |
| 10 | Auth path exclusively Keycloak OIDC/PKCE | III. UX Consistency | ✅ Existing — charting-api has JWT auth; Sapphire uses oidc-client-ts + PKCE; no new auth flow |
| 11 | URL state is source of truth for filters and selections | III. UX Consistency | ✅ Planned — chart range selection URL-driven (consistent with existing charts) |
| 12 | Apollo cache policies explicit; no implicit cache-first for mutable health data | I. Code Quality | ✅ Planned — temperature readings are mutable; cache-and-network or no-cache policy required |
| 13 | Structured JSON logs with trace_id and span_id | IV. Observability | ✅ Required — SC-007; charting-api uses Logback (Spring); extend with MDC trace fields |
| 14 | OTEL metrics: request count, duration histogram, error rate | IV. Observability | ✅ Required — SC-007 |
| 15 | Distributed traces via OTEL SDK; W3C traceparent; DB and HTTP spans | IV. Observability | ✅ Planned — instrument new ingestion and trend endpoints; DB queries as child spans |
| 16 | OTEL env vars in every container | IV. Observability | ✅ Existing containers — verify charting-api Dockerfile has `OTEL_*` vars |
| 17 | LangGraph: N/A | I. Code Quality | N/A |

**No violations requiring justification.**

---

## Project Structure

### Documentation (this feature)

```text
specs/SDDSDLC-223/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── body-temperature-rest-api.yaml    ← OpenAPI 3.1 (charting-api)
│   └── body-temperature-graphql.graphql  ← GraphQL SDL extension (bff-api)
└── tasks.md  ← generated by /speckit-tasks
```

### Source Code — `sapphire-charting-api` (Java / Spring Boot)

```text
src/main/java/com/health/charting/
├── enums/
│   └── MetricType.java                       ← ADD: BODY_TEMPERATURE("bodytemperature")
├── controller/
│   └── TemperatureController.java            ← NEW: POST /api/v1/metrics/body-temperature
│                                                      GET  /api/v1/metrics/body-temperature/trends
│                                                      POST /api/v1/metrics/body-temperature/batch
├── service/
│   ├── TemperatureIngestionService.java      ← NEW: validation + idempotent storage
│   └── TemperatureTrendService.java          ← NEW: trend aggregation (extends rollup pattern)
├── repository/
│   └── TemperatureRepository.java            ← NEW: TimescaleDB queries on bodytemperature table
├── dto/
│   ├── request/
│   │   ├── TemperatureRecordRequest.java     ← NEW: single ingestion DTO
│   │   └── TemperatureBatchRequest.java      ← NEW: batch ingestion DTO
│   └── response/
│       ├── TemperatureRecordResponse.java    ← NEW: single record response (extends MetricReadingDto pattern)
│       ├── TemperatureBatchResponse.java     ← NEW: HTTP 207 batch response
│       └── TemperatureTrendResponse.java     ← NEW: trend data response
└── config/
    └── TemperatureRangeConfig.java           ← NEW: @ConfigurationProperties for TEMP_MIN/MAX_CELSIUS

src/main/resources/
└── db/migration/
    └── V{next}__add_body_temperature_table.sql  ← NEW: TimescaleDB hypertable + indexes

src/test/java/com/health/charting/
├── controller/TemperatureControllerTest.java
├── service/TemperatureIngestionServiceTest.java
└── integration/TemperatureIngestionIntegrationTest.java
```

### Source Code — `sapphire-bff-api` (Node.js / Apollo Server)

```text
src/
├── schema/
│   └── typeDefs.js          ← ADD: BodyTemperatureReading type, queries, mutation
├── resolvers/
│   └── temperatureResolvers.js  ← NEW: bodyTemperatureReadings, bodyTemperatureTrends, addBodyTemperatureReading
└── datasources/
    └── TemperatureDataSource.js  ← NEW: REST client calling charting-api temperature endpoints
```

### Source Code — `Sapphire` (React / TypeScript)

```text
client/src/
├── components/
│   └── charts/
│       └── body-temperature-chart.tsx   ← NEW: follows heart-rate-chart.tsx pattern
│                                              Recharts LineChart, Select for range (Today/Week/Month),
│                                              °C/°F toggle (client-side conversion)
├── graphql/
│   └── health.ts                        ← ADD: GET_BODY_TEMPERATURE_READINGS, GET_BODY_TEMPERATURE_TRENDS
└── pages/
    └── dashboard.tsx                    ← ADD: BodyTemperatureChart import + useQuery hook
```

**Structure Decision**: Three-repo pattern — REST backend (charting-api) → GraphQL BFF (bff-api) → React SPA (Sapphire). Temperature follows the exact same data flow as existing metrics (HeartRate, BloodPressure).

---

## Architecture Decisions

### AD-001: Separate `bodytemperature` TimescaleDB hypertable
Following the existing pattern (`heartrate`, `bloodpressure`, `glucose` etc. each have their own table), body temperature gets its own `bodytemperature` hypertable. A shared discriminator table was rejected — it doesn't match the codebase pattern and `MetricType.tableName` maps directly to a table name.

### AD-002: `BODY_TEMPERATURE("bodytemperature")` added to `MetricType` enum
The existing `MetricType` enum in `com.health.charting.enums.MetricType` is extended with `BODY_TEMPERATURE("bodytemperature")`. The `fromTableName()` factory method handles resolution automatically.

### AD-003: Extend existing `MetricReadingController`/`MetricReadingService` pattern
New `TemperatureController` follows the exact pattern of `MetricReadingController` — `@GetMapping("/{metric}/readings")` pattern, pagination headers (`X-Page-Number`, `X-Total-Elements` etc.), `MetricReadingDto` response shape with `values: Map<String, Number>`.

### AD-004: HTTP 207 for batch partial success
Batch ingestion returns HTTP 207 Multi-Status with per-record `{ index, status, error? }`.

### AD-005: Natural deduplication key `(user_id, device_source, timestamp, value)`
Composite unique constraint for idempotency. Service converts DB constraint violation to HTTP 200.

### AD-006: Client-side °C↔°F toggle in `BodyTemperatureChart`
Backend returns `{ value, unit }` as stored. React component (following `HeartRateChart` pattern with `useState`) manages toggle state locally.

### AD-007: BFF adds `bodyTemperatureReadings` + `addBodyTemperatureReading` to GraphQL schema
`typeDefs.js` extended. New `TemperatureDataSource` calls charting-api REST endpoints, consistent with existing REST datasource pattern in `sapphire-bff-api`.

### AD-008: Physiological range from Spring `@ConfigurationProperties`
`TEMP_MIN_CELSIUS` / `TEMP_MAX_CELSIUS` environment variables bound via `TemperatureRangeConfig` `@ConfigurationProperties` bean.

---

## Backward Compatibility Assessment

| Change | Repo | Impact | Assessment |
|---|---|---|---|
| `BODY_TEMPERATURE` added to `MetricType` enum | charting-api | Additive | ✅ `fromTableName()` factory unaffected; no switch exhaustiveness issues in Java |
| New `bodytemperature` TimescaleDB table | charting-api | Additive | ✅ No existing tables modified |
| New REST endpoints (ingestion, batch, trends) | charting-api | Additive | ✅ No existing endpoint modified |
| New GraphQL types + queries + mutation | bff-api | Additive | ✅ No existing type or resolver modified |
| New chart component + GraphQL query | Sapphire | Additive | ✅ No existing component modified |
| Dashboard gains BodyTemperatureChart | Sapphire | Additive | ✅ Existing hooks and queries unchanged |

**No breaking changes.**

---

## Complexity Tracking

No constitution violations requiring justification.

---

## Phase 0 Output

- [x] `research.md` — 8 decisions documented, updated with actual codebase patterns

## Phase 1 Output

- [x] `data-model.md` — updated with real schema (TimescaleDB hypertable, Java DTOs, GraphQL types)
- [x] `contracts/body-temperature-rest-api.yaml` — OpenAPI 3.1 for charting-api
- [x] `contracts/body-temperature-graphql.graphql` — GraphQL SDL extension for bff-api
- [x] `quickstart.md` — 11-step end-to-end validation guide

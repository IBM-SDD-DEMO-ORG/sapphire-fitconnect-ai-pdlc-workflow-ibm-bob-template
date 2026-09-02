# Tasks: SDDSDLC-223 — Body Temperature Metric Ingestion, Storage, and Reporting

**Branch**: `SDDSDLC-223` | **Date**: 2025-07-17
**Plan**: [specs/SDDSDLC-223/plan.md](specs/SDDSDLC-223/plan.md)
**Spec**: [specs/SDDSDLC-223/spec.md](specs/SDDSDLC-223/spec.md)

---

## Summary

| Metric | Value |
|---|---|
| Total tasks | 43 |
| Phase 1 — Setup | 2 tasks |
| Phase 2 — Foundational | 5 tasks (added T002a: GraphQL SDL contract test) |
| Phase 3 — US1: Ingest & Store (P1) | 15 tasks |
| Phase 4 — US2: Trends & Chart (P2) | 14 tasks (added T023a BFF tests, T018 split, T029/T030 clarified) |
| Phase 5 — US3: Export & Dashboard (P3) | 5 tasks |
| Phase 6 — Polish & Cross-Cutting | 3 tasks (added T031b BFF OTEL) |
| Parallel tasks `[P]` | 21 |

**Affected Repos**:
- `sapphire-charting-api` — Java 17 / Spring Boot 3.2.2 / TimescaleDB
- `sapphire-bff-api` — Node.js / Apollo Server / GraphQL
- `Sapphire` — TypeScript 5.6 / React 18.3 / Recharts

---

## Dependencies

```
Phase 1 (Setup)
  └─► Phase 2 (Foundational: DB migration + enum)
        └─► Phase 3 (US1: Ingestion API — charting-api)
              ├─► Phase 4 (US2: Trends API — charting-api)
              │     ├─► Phase 4 (US2: BFF GraphQL layer)
              │     │     └─► Phase 4 (US2: Sapphire chart component)
              └─► Phase 5 (US3: Export & Dashboard inclusion)
Phase 6 (Polish) runs after all story phases complete
```

---

## Phase 1 — Setup

*Project and branch initialisation across all three repos.*

- [ ] T001 Create feature branch `SDDSDLC-223` in `sapphire-charting-api` (C:\Users\HimanshuKhatri\Downloads\Local-Repos\Bob-SDD-v1.1\sapphire-charting-api)
- [ ] T002 [P] Create feature branch `SDDSDLC-223` in `sapphire-bff-api` (C:\Users\HimanshuKhatri\Downloads\Local-Repos\Bob-SDD-v1.1\sapphire-bff-api) and `Sapphire` (C:\Users\HimanshuKhatri\Downloads\Local-Repos\Bob-SDD-v1.1\Sapphire)

---

## Phase 2 — Foundational

*Blocking prerequisites that all user stories depend on. Must complete before Phase 3.*

- [ ] T002a [P] Write a failing GraphQL SDL contract test in `sapphire-bff-api/src/schema/__tests__/bodyTemperatureSchema.test.js` BEFORE implementing T021 (constitution requirement: contract tests verified failing before implementation begins):
  - Import the updated `typeDefs.js` once T021 is applied; until then use the SDL from `specs/SDDSDLC-223/contracts/body-temperature-graphql.graphql` directly
  - Assert `bodyTemperatureReadings` query exists in schema
  - Assert `bodyTemperatureTrends` query exists in schema
  - Assert `addBodyTemperatureReading` mutation exists in schema
  - Assert `BodyTemperatureReading` type has fields: `id`, `userId`, `value`, `unit`, `timestamp`
  - Run `npx jest bodyTemperatureSchema` to confirm tests fail (schema not yet extended) — record FAIL output as evidence
- [ ] T003 Add `BODY_TEMPERATURE("bodytemperature")` to `MetricType` enum in `sapphire-charting-api/src/main/java/com/health/charting/enums/MetricType.java` — follow the existing enum pattern; the `tableName` value must exactly match the hypertable name created in T004
- [ ] T004 [P] Create Flyway migration `sapphire-charting-api/src/main/resources/db/migration/V{next}__add_body_temperature_table.sql`:
  ```sql
  CREATE TABLE IF NOT EXISTS bodytemperature (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(1) NOT NULL CHECK (unit IN ('C','F')),
    timestamp TIMESTAMPTZ NOT NULL,
    device_source VARCHAR(255),
    ingestion_source VARCHAR(20) NOT NULL CHECK (ingestion_source IN ('device','api','manual')),
    measurement_method VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT bodytemperature_pkey PRIMARY KEY (id),
    CONSTRAINT bodytemperature_dedup UNIQUE (user_id, device_source, timestamp, value)
  );
  SELECT create_hypertable('bodytemperature', 'timestamp', if_not_exists => TRUE);
  CREATE INDEX IF NOT EXISTS idx_bodytemperature_user_ts ON bodytemperature (user_id, timestamp DESC);
  CREATE INDEX IF NOT EXISTS idx_bodytemperature_user_device_ts ON bodytemperature (user_id, device_source, timestamp DESC);
  ```
- [ ] T005 [P] Create `TemperatureRangeConfig` @ConfigurationProperties bean in `sapphire-charting-api/src/main/java/com/health/charting/config/TemperatureRangeConfig.java` — binds `TEMP_MIN_CELSIUS` (default 25.0) and `TEMP_MAX_CELSIUS` (default 45.0) env vars; annotate with `@Configuration` and `@ConfigurationProperties(prefix = "temperature.range")`
- [ ] T006 [P] Create DTOs in `sapphire-charting-api/src/main/java/com/health/charting/dto/`:
  - `request/TemperatureRecordRequest.java` — fields: userId, value, unit (TemperatureUnit enum), timestamp (Instant), deviceSource, ingestionSource (IngestionSource enum), measurementMethod; Jakarta validation annotations (`@NotNull`, `@NotBlank`, `@DecimalMin`/`@DecimalMax`)
  - `request/TemperatureBatchRequest.java` — wraps `List<TemperatureRecordRequest> records`; `@Size(min=1, max=100)`
  - `response/TemperatureRecordResponse.java` — fields: id, userId, value, unit, timestamp, deviceSource, ingestionSource, measurementMethod, createdAt
  - `response/TemperatureBatchResponse.java` — wraps `List<BatchRecordResult>`; inner record: index, status (BatchRecordStatus enum: CREATED/DUPLICATE/ERROR), id (nullable), error (nullable)
  - Create enums `com/health/charting/enums/TemperatureUnit.java` (C, F) and `com/health/charting/enums/IngestionSource.java` (device, api, manual)

---

## Phase 3 — [US1] Ingest and Store Temperature Readings (P1)

*Goal*: Single + batch ingestion, validation (range, timestamp, required fields), idempotent storage, HTTP 201/207/400/422 responses.

*Independent test*: POST `/api/v1/metrics/body-temperature` with valid Celsius reading → 201; POST with value 60 °C → 422; POST with missing `user_id` → 400; POST same record twice → 200 (idempotent); POST batch of 3 (2 valid, 1 invalid) → 207 with per-record results.

- [ ] T007 Create `TemperatureRepository` interface in `sapphire-charting-api/src/main/java/com/health/charting/repository/TemperatureRepository.java` — extends `JpaRepository<TemperatureRecord, UUID>`; add `findByUserIdAndTimestampBetween` and `existsByUserIdAndDeviceSourceAndTimestampAndValue` query methods; annotate with `@Repository`
- [ ] T008 Create `TemperatureRecord` JPA entity in `sapphire-charting-api/src/main/java/com/health/charting/entity/TemperatureRecord.java` — maps to `bodytemperature` table; all fields from data-model.md; `@Table(name = "bodytemperature")`; `@Column` annotations with correct DB column names; Lombok `@Data @Builder @NoArgsConstructor @AllArgsConstructor`
- [ ] T009 Create `TemperatureIngestionService` in `sapphire-charting-api/src/main/java/com/health/charting/service/TemperatureIngestionService.java`:
  - `ingestSingle(TemperatureRecordRequest req)` → `TemperatureRecordResponse`; validates range via `TemperatureRangeConfig`; validates timestamp ≤ now + 5 min; checks idempotency via `TemperatureRepository.existsByUserIdAndDeviceSourceAndTimestampAndValue`; on duplicate return existing record mapped to response with DUPLICATE status indicator; on success save and return with CREATED
  - `ingestBatch(TemperatureBatchRequest req)` → `TemperatureBatchResponse`; calls `ingestSingle` per record; catches `TemperatureValidationException` per record; returns 207-style list with index, status, id, error
  - Throw custom `TemperatureValidationException(String field, String message)` for range/timestamp/enum violations
- [ ] T010 [P] Create `TemperatureValidationException` in `sapphire-charting-api/src/main/java/com/health/charting/exception/TemperatureValidationException.java` — RuntimeException subclass with `field` and `message` fields; used to map to HTTP 422
- [ ] T011 Create `TemperatureController` in `sapphire-charting-api/src/main/java/com/health/charting/controller/TemperatureController.java`:
  - `POST /api/v1/metrics/body-temperature` → `ingestSingle`; HTTP 201 on CREATED, 200 on DUPLICATE; `@Valid` on request body; `@SecurityRequirement(name = "bearerAuth")`
  - `POST /api/v1/metrics/body-temperature/batch` → `ingestBatch`; HTTP 207
  - Wire `TemperatureIngestionService`; follow `MetricReadingController` patterns (pagination headers style, exception handler wiring)
- [ ] T012 [P] Add `@ExceptionHandler` for `TemperatureValidationException` in `sapphire-charting-api/src/main/java/com/health/charting/controller/GlobalExceptionHandler.java` (or create if absent) — maps to `ErrorResponse` with HTTP 422; handler for `MethodArgumentNotValidException` maps to HTTP 400 with per-field errors
- [ ] T013 [P] Write unit tests in `sapphire-charting-api/src/test/java/com/health/charting/service/TemperatureIngestionServiceTest.java`:
  - Test: valid Celsius ingestion → 201
  - Test: valid Fahrenheit ingestion → 201, unit preserved
  - Test: duplicate record → DUPLICATE status, no second DB write
  - Test: value below TEMP_MIN_CELSIUS → TemperatureValidationException on field `value`
  - Test: value above TEMP_MAX_CELSIUS → TemperatureValidationException on field `value`
  - Test: timestamp > now + 5 min → TemperatureValidationException on field `timestamp`
  - Test: batch of 3 (valid, invalid, valid) → 207, only valid records stored
  - Use `@ExtendWith(MockitoExtension.class)`; mock `TemperatureRepository` and `TemperatureRangeConfig`
- [ ] T014 [P] Write controller slice tests in `sapphire-charting-api/src/test/java/com/health/charting/controller/TemperatureControllerTest.java`:
  - `@WebMvcTest(TemperatureController.class)`; mock `TemperatureIngestionService`
  - Test: POST valid record → 201 with response body
  - Test: POST missing `user_id` → 400 with field error
  - Test: POST out-of-range value → 422 with field error
  - Test: POST batch → 207 with per-record results
- [ ] T015 [P] Write integration test in `sapphire-charting-api/src/test/java/com/health/charting/integration/TemperatureIngestionIntegrationTest.java`:
  - `@SpringBootTest` + `@Testcontainers`; use TimescaleDB container matching existing integration test pattern
  - Test: end-to-end single ingest, fetch back, assert all fields match
  - Test: batch ingest with mix of valid/invalid records

---

## Phase 4 — [US2] View Temperature History and Trends (P2)

*Goal*: Trend API (charting-api) → BFF GraphQL queries → Sapphire chart component with day/week/month selector and °C/°F toggle.

*Independent test (backend)*: GET `/api/v1/metrics/body-temperature/trends?user_id=X&range_start=...&range_end=...` → 200 with min/max/average/buckets. Empty range → empty buckets array, no error.

*Independent test (frontend)*: Render `<BodyTemperatureChart userId="X" />` with mock Apollo data → chart displays, range selector toggles data, °C/°F toggle converts values client-side.

### charting-api — Trends

- [ ] T016 Create `TemperatureTrendService` in `sapphire-charting-api/src/main/java/com/health/charting/service/TemperatureTrendService.java`:
  - `getTrends(String userId, Instant rangeStart, Instant rangeEnd, TrendGranularity granularity, String deviceSource)` → `TemperatureTrendResponse`
  - Calls `TemperatureRepository` to fetch raw records in range; groups into day/week/month buckets using Java `Instant` + `ZoneOffset.UTC`; computes min/max/average per bucket; returns `TemperatureTrendResponse` (from contracts/data-model)
  - Empty range → return response with empty `buckets` list and null min/max/average
- [ ] T017 [P] Add trend query methods to `TemperatureRepository`:
  - `findByUserIdAndTimestampBetweenOrderByTimestampAsc(String userId, Instant start, Instant end)` — returns `List<TemperatureRecord>`
  - `findByUserIdAndDeviceSourceAndTimestampBetweenOrderByTimestampAsc(String userId, String deviceSource, Instant start, Instant end)` — for filtered queries
- [ ] T018 [P] Create `TemperatureTrendResponse` in `sapphire-charting-api/src/main/java/com/health/charting/dto/response/TemperatureTrendResponse.java` and `TrendBucket` in `sapphire-charting-api/src/main/java/com/health/charting/dto/response/TrendBucket.java` — fields per data-model.md and contracts/body-temperature-rest-api.yaml; these are distinct files from T006 response DTOs (T006 covers record/batch responses only)
- [ ] T019 Add `GET /api/v1/metrics/body-temperature/trends` endpoint to `TemperatureController` — binds query params: `user_id` (required), `range_start`, `range_end` (required, ISO-8601), `granularity` (optional, default `day`), `device_source` (optional); calls `TemperatureTrendService.getTrends`; 200 response; 400 on invalid params
- [ ] T020 [P] Write unit tests in `sapphire-charting-api/src/test/java/com/health/charting/service/TemperatureTrendServiceTest.java`:
  - Test: week range with 7 records → 7 day-buckets, correct min/max/average per bucket
  - Test: empty range → empty buckets, null aggregate values
  - Test: device filter → only matching-source records included
  - Use `@ExtendWith(MockitoExtension.class)`; mock `TemperatureRepository`

### sapphire-bff-api — GraphQL Layer

- [ ] T021 Extend `sapphire-bff-api/src/schema/typeDefs.js` with the types, queries, and mutation from `specs/SDDSDLC-223/contracts/body-temperature-graphql.graphql`:
  - Add: `BodyTemperatureReading`, `BodyTemperatureTrend`, `TemperatureTrendBucket`, `AddBodyTemperatureReadingResult` types
  - Add: `TemperatureUnit`, `IngestionSource`, `TrendGranularity`, `WriteStatus` enums
  - Extend `Query`: `bodyTemperatureReadings`, `bodyTemperatureTrends`
  - Extend `Mutation`: `addBodyTemperatureReading`
- [ ] T022 [P] Create `sapphire-bff-api/src/datasources/TemperatureDataSource.js`:
  - Class extending the existing REST datasource base class pattern in the repo
  - `getReadings(userId, rangeStart, rangeEnd, deviceSource, page, pageSize)` → calls charting-api `GET /api/v1/metrics/body-temperature`
  - `getTrends(userId, rangeStart, rangeEnd, granularity, deviceSource)` → calls charting-api `GET /api/v1/metrics/body-temperature/trends`
  - `addReading(input)` → calls charting-api `POST /api/v1/metrics/body-temperature`; maps HTTP 200 to DUPLICATE status, 201 to CREATED
- [ ] T023 [P] Create `sapphire-bff-api/src/resolvers/temperatureResolvers.js`:
  - `Query.bodyTemperatureReadings` → calls `context.dataSources.temperatureDataSource.getReadings(...)`
  - `Query.bodyTemperatureTrends` → calls `context.dataSources.temperatureDataSource.getTrends(...)`
  - `Mutation.addBodyTemperatureReading` → calls `context.dataSources.temperatureDataSource.addReading(input)`
  - Export resolver map; merge into root resolver in `src/resolvers/index.js` (or equivalent entry point)
- [ ] T023a [P] Write Jest unit tests for BFF resolvers and datasource (constitution: 100% BFF resolver coverage gate):
  - `sapphire-bff-api/src/__tests__/temperatureResolvers.test.js`:
    - Mock `TemperatureDataSource`; test `bodyTemperatureReadings` resolver returns mapped data
    - Test `bodyTemperatureTrends` resolver returns trend payload
    - Test `addBodyTemperatureReading` resolver returns CREATED status
    - Test `addBodyTemperatureReading` resolver returns DUPLICATE status when datasource signals duplicate
  - `sapphire-bff-api/src/__tests__/TemperatureDataSource.test.js`:
    - Mock HTTP client; test `getReadings`, `getTrends`, `addReading` methods
    - Test that HTTP 200 from charting-api maps to DUPLICATE status
    - Test that HTTP 201 from charting-api maps to CREATED status
  - Coverage target: 100% of resolver functions and datasource methods

### Sapphire — Chart Component

- [ ] T024 Add GraphQL queries to `Sapphire/client/src/graphql/health.ts`:
  - `GET_BODY_TEMPERATURE_READINGS` — query `bodyTemperatureReadings(userId, rangeStart, rangeEnd)` selecting all BodyTemperatureReading fields
  - `GET_BODY_TEMPERATURE_TRENDS` — query `bodyTemperatureTrends(userId, rangeStart, rangeEnd, granularity)` selecting BodyTemperatureTrend fields including nested `buckets`
  - Follow the existing gql template literal pattern used in the file
- [ ] T025 [P] Create `Sapphire/client/src/components/charts/body-temperature-chart.tsx`:
  - Props: `userId: string`
  - State: `timeframe: 'day' | 'week' | 'month'` (default `'week'`); `unit: 'C' | 'F'` (default `'C'`)
  - `useQuery(GET_BODY_TEMPERATURE_TRENDS, { variables: { userId, rangeStart, rangeEnd, granularity: timeframe }, fetchPolicy: 'cache-and-network' })`
  - Loading state: skeleton / spinner (consistent with HeartRateChart)
  - Error state: error message with retry
  - Empty state: "No temperature readings for this period" message
  - Chart: Recharts `<LineChart>` with `<XAxis>` (period_start, formatted per granularity), `<YAxis>` (label: `°${unit}`), `<Line>` for average, `<Tooltip>` showing min/max/average
  - Range selector: `<Select>` from `@/components/ui/select` — options Today / Week / Month (follow HeartRateChart `useState` pattern exactly)
  - Unit toggle: button/toggle switching between `°C` and `°F`; client-side conversion: F = C × 9/5 + 32, C = (F − 32) × 5/9; applied to `average`, `min`, `max` values
  - Strict TypeScript; JSDoc on component and props
- [ ] T026 [P] Add `BodyTemperatureChart` to dashboard in `Sapphire/client/src/pages/dashboard.tsx`:
  - Import `BodyTemperatureChart` from `../components/charts/body-temperature-chart`
  - Add `<BodyTemperatureChart userId={currentUserId} />` in the metrics grid, following the placement pattern of `HeartRateChart`

---

## Phase 5 — [US3] Export and Analytics Dashboard Inclusion (P3)

*Goal*: Body temperature appears in analytics export payload and health analytics dashboard metric list.

*Independent test*: GET analytics export for user with temperature records → response body includes `body_temperature` section. GET dashboard metrics list → response includes `body_temperature` entry with latest value.

- [ ] T027 Add `BODY_TEMPERATURE` case to the analytics export assembly logic in `sapphire-charting-api` (locate the existing export service/controller that builds per-metric sections — follow the pattern used for `heartrate` or `bloodpressure`); fetch records via `TemperatureRepository`; append `body_temperature` section with per-record `{ value, unit, timestamp, device_source }`
- [ ] T028 [P] Add `body_temperature` entry to the health analytics dashboard metrics list response in `sapphire-charting-api` — locate the controller/service returning the metric catalog or summary; add an entry for `body_temperature` with the user's most recent value (query `TemperatureRepository.findTopByUserIdOrderByTimestampDesc`) and trend direction (compare latest vs previous period average)
- [ ] T029 [P] Extend `sapphire-bff-api/src/schema/typeDefs.js` to expose the dashboard body-temperature entry through the BFF: add `bodyTemperature: BodyTemperatureSummary` field to the existing `HealthDashboard` type (or equivalent root dashboard query type); create `BodyTemperatureSummary` type with fields `latestValue`, `latestUnit`, `trendDirection`; add corresponding resolver in `temperatureResolvers.js` calling `TemperatureDataSource.getDashboardSummary(userId)` which proxies `GET /api/v1/metrics/body-temperature/dashboard` (or the charting-api dashboard endpoint — match the existing BFF dashboard data-flow pattern)
- [ ] T030 [P] Update `Sapphire/client/src/pages/dashboard.tsx` metrics list section to include body temperature as a tracked metric with its latest value and trend arrow — add `bodyTemperature { latestValue latestUnit trendDirection }` to the existing dashboard GraphQL query; render an entry following the pattern of other metric entries in the list

---

## Phase 6 — Polish & Cross-Cutting Concerns

*Runs after all story phases complete.*

- [ ] T031 [P] Verify OTEL instrumentation on new charting-api endpoints (SC-007): confirm `sapphire-charting-api` Dockerfile has `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT` env vars; add `@Timed` (Micrometer) or OTEL span annotations to `TemperatureController` methods for request-count and duration metrics; confirm structured Logback MDC includes `traceId` / `spanId` on all temperature log statements
- [ ] T031b [P] Verify OTEL instrumentation on BFF temperature resolvers (SC-007, constitution V): confirm `sapphire-bff-api` container has `OTEL_SERVICE_NAME` and `OTEL_EXPORTER_OTLP_ENDPOINT` env vars set; add request-count and error-rate instrumentation to `temperatureResolvers.js` (using the existing pino/structlog/OpenTelemetry pattern in the BFF); confirm W3C `traceparent` header is forwarded from BFF to charting-api in `TemperatureDataSource` HTTP calls
- [ ] T032 [P] Verify OpenAPI spec is auto-generated from Springdoc annotations on `TemperatureController` — confirm `@Operation`, `@ApiResponse`, `@Schema` annotations are present on all endpoints and DTOs consistent with `body-temperature-rest-api.yaml` contract; run `mvn springdoc-openapi:generate` or equivalent and confirm the output matches the contract (SC-006); note: schema publication to integration partners is a release-gate check per FR-009

---

## Parallel Execution Groups

Tasks marked `[P]` within the same phase can be executed concurrently when there are no intra-phase dependencies:

| Group | Tasks | Notes |
|---|---|---|
| Phase 2 parallel | T002a, T004, T005, T006 | Contract test (must fail first), DB migration, config, DTOs — no mutual dependency |
| Phase 3 parallel | T010, T012, T013, T014 | Exception class, handler, service tests, controller tests once T007–T009 + T011 are in place |
| Phase 4 parallel (backend) | T017, T018, T020 | Repo methods, trend response DTOs, service tests parallelise once T016 is coded |
| Phase 4 parallel (BFF) | T022, T023, T023a | DataSource, resolver, and resolver tests can be written simultaneously once T021 schema is added |
| Phase 4 parallel (frontend) | T025, T026 | Chart component and dashboard wiring proceed simultaneously once T024 queries are added |
| Phase 5 parallel | T028, T029, T030 | Dashboard entries in charting-api, BFF, and Sapphire in parallel once T027 export is done |
| Phase 6 parallel | T031, T031b, T032 | Fully independent |

---

## Implementation Strategy

**MVP Scope (Phase 2 + Phase 3 only)**:
Complete T001–T015 to have a fully working ingestion and storage layer with validation, idempotency, and tests. This independently satisfies US1 and unblocks all other phases.

**Increment 2 (Phase 4)**:
Complete T016–T026 to add the full read/reporting path: trend API → BFF proxy → frontend chart. This satisfies US2 and delivers the primary user-facing value.

**Increment 3 (Phase 5 + 6)**:
Complete T027–T032 to satisfy US3 (export/dashboard inclusion) and cross-cutting polish (OTEL, OpenAPI docs).

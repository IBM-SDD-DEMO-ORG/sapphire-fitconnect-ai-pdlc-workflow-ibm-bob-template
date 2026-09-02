# Feature Specification: Add Support for Body Temperature Metric Ingestion, Storage, and Reporting

**Feature Branch**: `SDDSDLC-223`
**Created**: 2025-07-17
**Status**: Draft
**Jira Story**: [SDDSDLC-223](https://jsw.ibm.com/browse/SDDSDLC-223)
**Affected Repos**: `sapphire-fitconnect-health-service`, `sapphire-fitconnect-web`

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ingest and Store Temperature Readings (Priority: P1)

A user with a compatible smart device (e.g. a clinical thermometer or wearable with temperature sensing) triggers a temperature reading. The reading is sent to the platform — either as a single record or as part of a batch — and the system validates, stores, and associates the record with the user's account, the device, and the timestamp. The user can then see the new reading reflected in their health data.

**Why this priority**: Without reliable ingestion and storage, no downstream feature (reporting, UI, export) can function. This is the foundational capability that every other user story depends on. It also directly addresses the core problem: users with compatible devices currently have no way to get their temperature data into the platform.

**Independent Test**: Submit a valid temperature reading (single and batch) via the ingestion API. Verify the record is persisted with correct value, unit, timestamp, user ID, and device source. Verify an invalid reading (out-of-range value, missing required fields) is rejected with a meaningful error message. No UI or analytics required to validate this story.

**Acceptance Scenarios**:

1. **Given** a registered user has a connected smart device, **When** a valid temperature reading in Celsius is submitted via the ingestion API, **Then** the record is stored with value, unit (`C`), timestamp, user ID, device source, and ingestion source correctly populated.
2. **Given** a registered user has a connected smart device, **When** a valid temperature reading in Fahrenheit is submitted, **Then** the record is stored with unit (`F`) and the submitted value preserved exactly.
3. **Given** a valid batch of temperature readings, **When** the batch is submitted, **Then** all records are stored and each is individually retrievable by its timestamp and user.
4. **Given** a temperature value outside the configurable physiological range (e.g. below 25 °C or above 45 °C), **When** submitted, **Then** the system rejects the record with an HTTP 422 response and an error message identifying the invalid field and reason.
5. **Given** a request with a missing required field (user ID, timestamp, or value), **When** submitted, **Then** the system returns HTTP 400 with a field-level error description.
6. **Given** a valid reading is submitted without an optional `measurement_method` field, **When** stored, **Then** the field is recorded as absent without error.

---

### User Story 2 - View Temperature History and Trends (Priority: P2)

A user opens their health dashboard and navigates to the temperature metric view. They can see a chart of their temperature readings over selectable time ranges (day, week, month) and read the min, max, and average values for the selected range. They can filter by device source if they use more than one device.

**Why this priority**: Displaying temperature history is the primary user-facing value of this feature — it is what users and healthcare providers will interact with daily. It depends on P1 (data must exist to display), but once ingestion is working, this is the next highest-value deliverable.

**Independent Test**: With seeded temperature records in the datastore, call the reporting/trend API for a given user and date range. Verify the response contains correct min, max, and average values. Separately, render the chart component in the frontend with mock API data; verify selectable ranges render correctly and unit labels are accurate.

**Acceptance Scenarios**:

1. **Given** a user has temperature records in the system, **When** they request trend data for the past week, **Then** the response includes min, max, and average temperature values computed over that range.
2. **Given** trend data is requested for a date range with no records, **When** the API responds, **Then** it returns an empty dataset indicator rather than an error.
3. **Given** a user has records from two different devices, **When** they filter the trend view by a specific device source, **Then** only records from that device are included in the trend calculation.
4. **Given** the frontend chart component is loaded, **When** the user selects "Day", "Week", or "Month" range, **Then** the chart re-renders with data for the chosen range and the x-axis labels reflect the correct time granularity.
5. **Given** temperature records exist in Fahrenheit, **When** the chart is displayed, **Then** the unit label clearly shows `°F` and values are not silently converted.

---

### User Story 3 - Export and Analytics Dashboard Inclusion (Priority: P3)

A user (or their healthcare provider via delegated access) exports their health analytics data. Temperature metrics are included in the export alongside other metrics. The user's overall health analytics dashboard also surfaces temperature as one of the tracked metrics.

**Why this priority**: Export and dashboard inclusion are valuable for continuity of care and provider sharing, but they are dependent on P1 and P2 being complete. They add breadth rather than depth and can be delivered as an incremental enhancement after the core ingest/view flow is working.

**Independent Test**: Call the analytics export endpoint for a user with temperature records. Verify the export payload includes a `body_temperature` section with per-record data. Separately verify the health analytics dashboard response includes a `body_temperature` metric entry. No additional UI work required beyond the chart component delivered in P2.

**Acceptance Scenarios**:

1. **Given** a user has stored temperature records, **When** the analytics export endpoint is called, **Then** the export payload includes a `body_temperature` section containing individual records with value, unit, timestamp, and device source.
2. **Given** a user's health analytics dashboard is loaded, **When** the dashboard metric list is rendered, **Then** body temperature appears as a tracked metric with its most recent value and trend direction.
3. **Given** schema documentation is updated, **When** integration partners access the API schema, **Then** the `body_temperature` metric type and all its fields are documented with types, units, and validation constraints.

---

### Edge Cases

- What happens when a device submits a temperature reading with a timestamp in the future (clock drift)?
- How does the system handle duplicate readings with identical user, device, timestamp, and value?
- What if a batch submission contains a mix of valid and invalid records — are valid records stored and invalid ones reported individually, or is the entire batch rejected?
- How is the physiological validation range configured, and what happens if the configuration is absent or malformed?
- What happens if a user switches the display unit (°C ↔ °F) — is the stored value converted or is conversion view-only?
- How are daily/weekly/monthly rollups handled when records span a daylight-saving-time boundary?

---

## Requirements *(mandatory)*

### Functional Requirements

**Ingestion**
- **FR-001**: The system MUST accept body temperature readings submitted individually or in batches from integrated smart devices and third-party APIs.
- **FR-002**: The system MUST support temperature values expressed in both Celsius (°C) and Fahrenheit (°F); the submitted unit MUST be preserved as-is in storage.
- **FR-003**: The system MUST validate each temperature value against a configurable physiological range; out-of-range values MUST be rejected with a field-level error identifying the value, submitted unit, and the acceptable range bounds.
- **FR-004**: Each stored temperature record MUST be associated with: user identifier, UTC timestamp, device source identifier, ingestion source (API/device/manual), and optionally a measurement method.
- **FR-005**: For batch submissions, the system MUST process each record independently; valid records MUST be stored even if other records in the same batch are invalid, and the response MUST itemise per-record success or failure.

**Data Model**
- **FR-006**: The system MUST add `body_temperature` as a named metric type in the existing health metrics catalog.
- **FR-007**: The temperature record schema MUST include: `value` (decimal), `unit` (enum: `C` | `F`), `timestamp` (UTC ISO-8601), `device_source` (string), `ingestion_source` (string), `measurement_method` (optional string).
- **FR-008**: The updated data schema MUST be backward-compatible with existing metrics consumers; no existing metric type field MUST be renamed or removed.
- **FR-009**: Internal and external API schema documentation MUST be updated to reflect the new `body_temperature` metric type and all its fields before the feature is released.

**Storage & Processing**
- **FR-010**: Temperature records MUST be stored in the existing metrics datastore with time-series indexing sufficient to support queries filtered by user and date range without full-table scans.
- **FR-011**: Temperature records MUST follow existing retention and aggregation rules applied to other metric types.
- **FR-012**: The system MUST support pre-computed daily, weekly, and monthly rollups (min, max, average) for temperature, consistent with the rollup strategy used for existing metrics.

**Reporting**
- **FR-013**: The system MUST expose a trend data endpoint that returns min, max, and average temperature for a user-specified date range.
- **FR-014**: Trend data MUST be filterable by device source.
- **FR-015**: Temperature metrics MUST be included in analytics export endpoints alongside existing metric types.
- **FR-016**: Temperature MUST appear as a tracked metric in the user's overall health analytics dashboard.

**User Interface**
- **FR-017**: The frontend MUST display body temperature in the user's metrics list alongside existing metrics.
- **FR-018**: The frontend MUST provide a chart component for body temperature that supports selectable time ranges: day, week, and month.
- **FR-019**: The chart MUST display the unit of measurement (°C or °F) clearly on the axis or legend.
- **FR-020**: [NEEDS CLARIFICATION: Should the frontend allow users to switch the display unit between °C and °F, or is the unit fixed to what was stored? This affects both the chart component and the API contract.]

### Key Entities

- **TemperatureRecord**: A single body temperature measurement associated with a user. Key attributes: `value`, `unit`, `timestamp`, `device_source`, `ingestion_source`, `measurement_method` (optional), `user_id`. Relates to the existing `User` and `HealthMetric` catalog entities.
- **MetricType (updated)**: The catalog entry for `body_temperature` — defines the metric name, supported units, validation range bounds (configurable), and rollup strategy. Relates to all metric record types.
- **TemperatureTrend**: A computed aggregate for a user over a time range. Attributes: `min`, `max`, `average`, `record_count`, `range_start`, `range_end`, `unit`, optionally filtered by `device_source`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Valid single and batch temperature records are ingested and retrievable within 2 seconds of submission under normal load conditions.
- **SC-002**: Out-of-range and malformed temperature submissions are rejected 100% of the time with an informative error response; no invalid record is persisted.
- **SC-003**: Trend data (min, max, average) for any user-selected date range is returned within 1 second for datasets up to 365 days of daily readings.
- **SC-004**: The temperature chart in the frontend loads and renders within 2 seconds on a standard broadband connection for up to 30 days of data.
- **SC-005**: Temperature metrics appear in analytics export payloads for 100% of users who have stored temperature records.
- **SC-006**: Schema documentation for the `body_temperature` metric type is published and accessible to integration partners before the feature is released to production.
- **SC-007**: All backend services modified by this feature emit structured logs with `trace_id` and `span_id` fields and export OTEL request-count and error-rate metrics for temperature ingestion and reporting endpoints.

---

## Assumptions

- The existing metrics datastore already supports time-series storage and rollup aggregation for other metrics; adding `body_temperature` follows the same storage pattern with no new datastore infrastructure.
- Physiological range defaults (e.g. 25–45 °C / 77–113 °F) will be made configurable at the service configuration level; the spec does not prescribe exact bounds.
- Authentication and authorization for the ingestion and reporting endpoints follow the existing platform auth mechanism (assumed to be Keycloak OIDC/PKCE based on project patterns); no new auth flow is introduced.
- Unit conversion (°C ↔ °F) for display purposes, if required, is a view-only transformation; stored values are always in the submitted unit.
- Integration partner notification of schema changes (FR-009) is handled via existing documentation and API versioning channels; this spec does not include a partner notification workflow.
- The analytics export endpoint already supports plugging in new metric types; temperature is added as a new metric entry without restructuring the export response envelope.
- `sapphire-fitconnect-health-service` owns ingestion, storage, rollups, and reporting APIs; `sapphire-fitconnect-web` owns the chart component and metrics list UI.
- Rollup jobs (daily/weekly/monthly) run on a scheduled basis consistent with existing metric rollup schedules; no new scheduling infrastructure is needed.

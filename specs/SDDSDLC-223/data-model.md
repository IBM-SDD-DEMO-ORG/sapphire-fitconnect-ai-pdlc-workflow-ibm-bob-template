# Data Model: SDDSDLC-223 — Body Temperature Metric

**Branch**: `SDDSDLC-223` | **Date**: 2025-07-17

---

## Entities

### TemperatureRecord

Represents a single body temperature measurement stored in the metrics datastore.

| Field | Type | Required | Constraints | Notes |
|---|---|---|---|---|
| `id` | UUID | Yes (system-generated) | Unique, immutable | Primary key; generated on insert |
| `user_id` | String / UUID | Yes | FK → User | Identifies the owning user |
| `value` | Decimal (2 d.p.) | Yes | Configurable physiological range | Stored as submitted; no unit conversion |
| `unit` | Enum: `C` \| `F` | Yes | Must be `C` or `F` | Preserved exactly as submitted |
| `timestamp` | DateTime (UTC) | Yes | Must not exceed server time + 5 min | ISO-8601; stored in UTC |
| `device_source` | String | No (nullable) | Max 255 chars | Null for `ingestion_source: manual` |
| `ingestion_source` | Enum: `device` \| `api` \| `manual` | Yes | — | How the record entered the system |
| `measurement_method` | String | No (nullable) | Max 100 chars | e.g. `oral`, `axillary`, `tympanic` |
| `created_at` | DateTime (UTC) | Yes (system-generated) | Immutable | Server-side insert timestamp |

**Natural deduplication key**: `(user_id, device_source, timestamp, value)` — composite unique constraint used for idempotent ingestion.

**Index requirements**:
- Primary: `id`
- Compound (for time-series queries): `(user_id, timestamp DESC)` — supports trend queries without full-table scans
- Compound (for device-filtered queries): `(user_id, device_source, timestamp DESC)` — supports FR-014

---

### MetricTypeCatalog (updated)

Existing catalog entity extended with a new `body_temperature` entry.

| Field | Value for body_temperature |
|---|---|
| `metric_type` | `body_temperature` |
| `display_name` | `Body Temperature` |
| `supported_units` | `["C", "F"]` |
| `default_range_min_c` | `25.0` (configurable) |
| `default_range_max_c` | `45.0` (configurable) |
| `rollup_strategy` | `min_max_avg` |
| `retention_policy` | (same as platform default) |

---

### TemperatureTrend (computed / read model)

Returned by the trend data endpoint. Not persisted as a standalone entity — derived from TemperatureRecord or pre-computed rollup tables.

| Field | Type | Description |
|---|---|---|
| `user_id` | String | User for whom the trend was computed |
| `range_start` | DateTime (UTC) | Inclusive start of the requested range |
| `range_end` | DateTime (UTC) | Inclusive end of the requested range |
| `granularity` | Enum: `day` \| `week` \| `month` | Resolution of the trend buckets |
| `unit` | Enum: `C` \| `F` | Unit of the values (as stored) |
| `device_source` | String \| null | Device filter applied, or null for all devices |
| `min` | Decimal | Minimum value in the range |
| `max` | Decimal | Maximum value in the range |
| `average` | Decimal | Average value in the range (rounded to 2 d.p.) |
| `record_count` | Integer | Number of raw records contributing to this trend |
| `buckets` | Array of TrendBucket | Per-period breakdown (see below) |

#### TrendBucket

| Field | Type | Description |
|---|---|---|
| `period_start` | DateTime | Start of this bucket (day/week/month boundary) |
| `min` | Decimal | Min in this bucket |
| `max` | Decimal | Max in this bucket |
| `average` | Decimal | Average in this bucket |
| `count` | Integer | Record count in this bucket |

---

### TemperatureRollup (pre-computed aggregate)

Pre-computed by the scheduled rollup job. Stored in the existing rollup table with `metric_type = body_temperature`.

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | String | User |
| `metric_type` | String | `body_temperature` |
| `period` | Enum: `daily` \| `weekly` \| `monthly` | Rollup granularity |
| `period_start` | DateTime (UTC) | Start of the period |
| `unit` | Enum: `C` \| `F` | Dominant unit in the period (most common; or `C` if mixed) |
| `min` | Decimal | Min temperature in the period |
| `max` | Decimal | Max temperature in the period |
| `average` | Decimal | Average temperature in the period |
| `record_count` | Integer | Raw records aggregated |
| `computed_at` | DateTime | When this rollup was last computed |

---

## Validation Rules

| Rule | Field | Condition | Error |
|---|---|---|---|
| VR-001 | `value` | Must be within configurable range (default 25–45 °C equiv.) | HTTP 422, field: `value` |
| VR-002 | `unit` | Must be `C` or `F` | HTTP 422, field: `unit` |
| VR-003 | `timestamp` | Must not be more than 5 minutes ahead of server UTC | HTTP 422, field: `timestamp` |
| VR-004 | `user_id` | Must not be null or empty | HTTP 400, field: `user_id` |
| VR-005 | `value` | Must not be null | HTTP 400, field: `value` |
| VR-006 | `timestamp` | Must not be null | HTTP 400, field: `timestamp` |
| VR-007 | `ingestion_source` | Must be one of `device`, `api`, `manual` | HTTP 422, field: `ingestion_source` |
| VR-008 | `device_source` | Must be null when `ingestion_source = manual`; otherwise non-null | HTTP 422, field: `device_source` |

---

## State Transitions

TemperatureRecord has no lifecycle state transitions — records are immutable once stored. The only transition is `submitted → stored` (success) or `submitted → rejected` (validation failure). Rejected records are never persisted.

---

## Relationships

```
User ──────────────── 1:N ──────────────── TemperatureRecord
                                                    │
                                           references MetricTypeCatalog
                                           (body_temperature entry)
                                                    │
                               aggregated by → TemperatureRollup
                               queried as  → TemperatureTrend (computed)
```

---

## Backward Compatibility

- No existing metric type fields are renamed or removed (FR-008 compliant).
- The `body_temperature` metric type is additive to the existing `metric_type` enum.
- Existing API consumers that do not request `body_temperature` are unaffected.
- The rollup table gains new rows with `metric_type = body_temperature`; no schema change to existing columns.

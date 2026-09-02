# Quickstart: SDDSDLC-223 — Body Temperature Metric

**Branch**: `SDDSDLC-223` | **Date**: 2025-07-17

This guide validates the body temperature feature end-to-end once implementation is complete.

---

## Prerequisites

- `sapphire-fitconnect-health-service` running locally (default port 8080 or as configured)
- `sapphire-fitconnect-web` running locally (default port 3000 or as configured)
- A valid authentication token for a test user (`TEST_TOKEN`)
- A test user ID (`TEST_USER_ID`)

---

## Step 1: Ingest a Single Temperature Reading (Celsius)

```http
POST /api/v1/metrics/body-temperature
Authorization: Bearer <TEST_TOKEN>
Content-Type: application/json

{
  "user_id": "<TEST_USER_ID>",
  "value": 36.8,
  "unit": "C",
  "timestamp": "<current UTC ISO-8601>",
  "device_source": "quickstart-device",
  "ingestion_source": "api"
}
```

**Expected**: HTTP 201 with `{ id, user_id, value: 36.8, unit: "C", ... }`

---

## Step 2: Verify Idempotency (Submit Same Record Again)

Re-submit the identical request from Step 1.

**Expected**: HTTP 200 (not 201) — same record ID returned, no duplicate stored.

---

## Step 3: Ingest an Invalid Reading (Out of Range)

```http
POST /api/v1/metrics/body-temperature
Authorization: Bearer <TEST_TOKEN>
Content-Type: application/json

{
  "user_id": "<TEST_USER_ID>",
  "value": 60.0,
  "unit": "C",
  "timestamp": "<current UTC ISO-8601>",
  "device_source": "quickstart-device",
  "ingestion_source": "api"
}
```

**Expected**: HTTP 422 with `{ error: "VALIDATION_ERROR", fields: { value: "..." } }`

---

## Step 4: Ingest a Batch

```http
POST /api/v1/metrics/body-temperature/batch
Authorization: Bearer <TEST_TOKEN>
Content-Type: application/json

{
  "records": [
    { "user_id": "<TEST_USER_ID>", "value": 36.5, "unit": "C", "timestamp": "<T-2h>", "ingestion_source": "api", "device_source": "quickstart-device" },
    { "user_id": "<TEST_USER_ID>", "value": 37.1, "unit": "C", "timestamp": "<T-1h>", "ingestion_source": "api", "device_source": "quickstart-device" },
    { "user_id": "<TEST_USER_ID>", "value": 99.9, "unit": "C", "timestamp": "<T>",    "ingestion_source": "api", "device_source": "quickstart-device" }
  ]
}
```

**Expected**: HTTP 207 with:
```json
{
  "results": [
    { "index": 0, "status": "created", "id": "..." },
    { "index": 1, "status": "created", "id": "..." },
    { "index": 2, "status": "error", "error": "Value 99.9 exceeds maximum ..." }
  ]
}
```

---

## Step 5: Query Trend Data

```http
GET /api/v1/metrics/body-temperature/trends
  ?user_id=<TEST_USER_ID>
  &range_start=<today 00:00 UTC>
  &range_end=<today 23:59 UTC>
  &granularity=day
Authorization: Bearer <TEST_TOKEN>
```

**Expected**: HTTP 200 with `{ min, max, average, record_count, buckets: [...] }` populated from ingested records.

---

## Step 6: UI Validation

1. Open `sapphire-fitconnect-web` in a browser at `http://localhost:3000`
2. Log in as the test user
3. Navigate to the health metrics dashboard
4. Verify **Body Temperature** appears in the metrics list
5. Click into the temperature view — chart should display today's readings
6. Switch between **Day**, **Week**, **Month** ranges — chart re-renders each time
7. Toggle the °C/°F switch — values convert client-side; page does not reload

---

## Step 7: Export Validation

Call the analytics export endpoint for the test user and verify `body_temperature` appears in the payload alongside other metric types.

---

## Validation Checklist

- [ ] Single ingestion returns HTTP 201 with all fields populated
- [ ] Duplicate ingestion returns HTTP 200 (idempotent)
- [ ] Out-of-range value returns HTTP 422 with field-level error
- [ ] Future timestamp > 5 min returns HTTP 422
- [ ] Batch returns HTTP 207 with per-record results
- [ ] Trend endpoint returns correct min/max/average for the ingested records
- [ ] Empty date range returns HTTP 200 with `record_count: 0` and empty `buckets`
- [ ] UI metrics list includes Body Temperature
- [ ] Chart renders with selectable ranges
- [ ] °C/°F toggle works client-side
- [ ] Export payload includes `body_temperature` section

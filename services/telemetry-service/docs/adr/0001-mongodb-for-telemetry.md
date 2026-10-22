# 0001. MongoDB for telemetry storage

## Status

Accepted

## Context

Telemetry must store high-volume time-series readings from soil sensors (and later ESP32 devices) and support filtered, time-ordered queries with cursor pagination. The candidate stores were MongoDB and Milvus.

## Decision

Use MongoDB with PyMongo's async client.

- Readings are documents with a shared contract: `device_id`, `sensor_id`, `recorded_at`, `measurements`.
- Unique index `(device_id, sensor_id, recorded_at)` rejects duplicates from CSV retries or device resends.
- Compound index `(recorded_at, _id)` supports keyset pagination.
- Sensor metadata lives in a separate collection so latest readings do not require a full scan.

Milvus is a vector database and is not a fit for typed sensor readings or BI aggregations.

## Consequences

Raw readings stay in the telemetry database. The BI service reads them over gRPC and stores only derived reports in its own MongoDB database.

# 0001. BI owns derived analytics, not raw readings

## Status

Accepted

## Context

The architecture requires a single source of truth for sensor readings and a separate analytics pipeline that the dashboard can call through the gateway.

## Decision

- Telemetry is the only writer of raw readings.
- BI streams readings from telemetry over gRPC, computes summary/trend/alert results in one pass, and persists generated reports in MongoDB (`bi.reports`).
- Thresholds and silence windows are BI configuration, not telemetry schema.

## Consequences

Switching the data source from CSV import to ESP32 devices does not change BI or gateway contracts. Report documents can be listed later without recomputing history.

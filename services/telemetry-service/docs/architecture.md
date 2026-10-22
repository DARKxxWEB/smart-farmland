# Telemetry service boundaries

The Telemetry service is the source of truth for raw sensor readings and the sensor catalog. It validates incoming measurements and timestamps, stores readings in MongoDB with deduplication and query indexes, and exposes ingestion, retrieval, pagination, streaming, and sensor-catalog operations through `telemetry.v1.TelemetryService`.

The API gateway adapts client traffic to this gRPC API. BI consumes readings through the same contract and does not write to Telemetry's collections.

See the [Telemetry service guide](telemetry-service.md) for the data model and [integrated deployment](../../../README.md) for the local service topology.

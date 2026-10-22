# BI service boundaries

The BI service owns derived analytics and report documents. It reads raw readings and the sensor catalog through the Telemetry gRPC contract, calculates summaries, trends, and threshold/silence alerts, and stores generated reports in its own MongoDB database.

It does not ingest or mutate raw readings. Its Telemetry protobuf dependency is included in this repository so the service can generate and build its gRPC client independently.

See the [BI service guide](bi-service.md) for RPC behavior and the [integrated deployment](../../../README.md) for the local service topology.

# BI service boundaries

The BI service owns derived analytics and report documents. It reads raw readings and the sensor catalog through the Telemetry gRPC contract, calculates summaries, trends, and threshold/silence alerts, and stores generated reports in its own MongoDB database. An optional, on-demand assistant uses bounded BI tools and local guide retrieval with the configured OpenAI-compatible model provider; standard analytics do not depend on the model.

It does not ingest or mutate raw readings. Its Telemetry protobuf dependency is included in this repository so the service can generate and build its gRPC client independently.

See the [BI service guide](bi-service.md) for RPC behavior and the [integrated deployment](../../../README.md) for the local service topology.

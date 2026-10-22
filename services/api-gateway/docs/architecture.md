# Gateway boundaries

The FastAPI gateway is the client-facing boundary for Smart Farmland. It owns HTTP request validation, response serialization, client-facing rate limits, and WebSocket fan-out.

## Responsibilities

- Adapt auth requests to the Auth gRPC service.
- Forward reading and sensor operations to Telemetry over gRPC.
- Forward analytics and report operations to BI over gRPC.
- Authenticate user requests through Auth token verification. Device ingestion uses its separate configured device token when enabled.
- Report gateway liveness at `/health` and backend gRPC health at `/ready`.

The gateway owns no user, raw-reading, sensor-catalog, or report persistence. The other services and integrated deployment are documented in [Smart Farmland](../../../README.md).

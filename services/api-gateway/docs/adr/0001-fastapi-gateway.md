# 0001. FastAPI gateway in front of gRPC services

## Status

Accepted

## Context

Browsers and the CSV importer cannot call native gRPC. Auth, telemetry, and BI already use protobuf contracts.

## Decision

Expose REST and WebSocket from FastAPI. Keep protobuf as the service-to-service contract. Map gRPC status codes to HTTP, convert timestamps to ISO-8601 UTC, and enforce JWT at the gateway.

## Consequences

The Next.js dashboard only needs HTTP. ESP32 can later POST the same reading JSON (or Device token) without changing telemetry.

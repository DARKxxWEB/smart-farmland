# Contributing

Thanks for contributing to the Telemetry service.

- Keep raw-reading validation and persistence in `apps/telemetry-service/`; derived analytics belong in BI.
- Keep the Telemetry protobuf contract versioned and regenerate stubs when it changes.
- Add or update tests for changed validation, persistence, and RPC behavior.
- Run the Telemetry service checks and the integration project's end-to-end smoke test when the required services are available.
- Keep secrets and local environment files out of commits.

Coordinate breaking Telemetry contract changes with BI, the gateway, and integration project.

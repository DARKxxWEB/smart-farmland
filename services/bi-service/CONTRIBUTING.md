# Contributing

Thanks for contributing to the BI service.

- Keep analytics and report behavior in `apps/bi-service/`; raw-reading persistence belongs in Telemetry.
- Keep the BI protobuf contract versioned and regenerate stubs when BI or its Telemetry client contract changes.
- Add or update tests for changed calculations and RPC behavior.
- Run the BI service checks and the integration project's end-to-end smoke test when the required services are available.
- Keep secrets and local environment files out of commits.

Coordinate breaking contract changes with the Telemetry service and integration project.

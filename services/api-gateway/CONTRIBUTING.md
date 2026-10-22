# Contributing

Thanks for contributing to the API gateway.

- Keep gateway behavior in `apps/gateway/`; backend-owned business rules and persistence belong in their service repositories.
- Keep protobuf contracts versioned and update the gateway stub generation/build path when a contract changes.
- Add or update tests for changed behavior.
- Run the gateway's protobuf generation and the integration project's end-to-end smoke test when the required services are available.
- Keep secrets and local environment files out of commits.

Coordinate breaking service-contract changes with the owning service and the integration project.

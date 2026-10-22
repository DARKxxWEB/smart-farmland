# Contributing

Thanks for contributing to the Auth service.

- Keep identity, password, and token behavior in `apps/auth-service/`; browser-facing request adaptation belongs in the API gateway.
- Keep the Auth protobuf contract versioned and regenerate its stubs when it changes.
- Add or update tests for changed behavior.
- Run the Auth service checks and the integration project's end-to-end smoke test when the required services are available.
- Keep secrets and local environment files out of commits.

Coordinate breaking Auth contract changes with the gateway and integration project.

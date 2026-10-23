# Contributing

Thanks for contributing to the Notification service.

- Keep notification history, device tokens, FCM delivery, and the gRPC implementation in `apps/notification-service/`.
- Keep the versioned protobuf contract in `proto/notification/v1/notification.proto` and regenerate stubs when it changes.
- Add or update tests for changed behavior.
- Keep Firebase credentials and local environment files out of commits.
- Coordinate contract changes with the gateway and integration project.

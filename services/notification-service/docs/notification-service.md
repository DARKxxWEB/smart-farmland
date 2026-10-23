# Notification service

The service uses MongoDB for notification history and registered device tokens. It sends push messages using the Firebase Admin SDK when `FIREBASE_CREDENTIALS_PATH` points to a Firebase service-account JSON file.

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection URI |
| `MONGO_DB` | `notifications` | MongoDB database |
| `GRPC_HOST` | `0.0.0.0` | gRPC listener address |
| `GRPC_PORT` | `50054` | gRPC listener port |
| `GRPC_REFLECTION` | `false` | Enable gRPC reflection |
| `FIREBASE_CREDENTIALS_PATH` | empty | Service-account JSON path; empty disables FCM delivery |

## RPCs

- `RegisterDevice` associates an FCM token with a user.
- `RemoveDevice` removes that user's FCM token.
- `CreateNotification` stores and sends a notification. `source_id` makes source events idempotent per user; repeated IDs return the original notification without another push.
- `ListNotifications` returns a user's notification history, unread count, and a page token.
- `MarkRead` updates read state only for the specified user.

Only the API gateway should expose these operations to clients. It derives the user ID from the verified access token; clients must not choose another user's ID.

Push delivery results are reported as `sent`, `partial`, `failed`, or `no_devices`. An empty credential path permits service startup and history operations, but attempting delivery to registered tokens is reported as failed.

# Notification service boundaries

The Notification service owns device FCM tokens, per-user notification history, unread state, and Firebase Cloud Messaging delivery. MongoDB stores tokens and notifications. Firebase credentials are read from `FIREBASE_CREDENTIALS_PATH`; credentials are not stored in MongoDB or source control.

The service exposes the versioned `notification.v1.NotificationService` gRPC API. The API gateway authenticates the user and supplies that user's ID for device registration, notification history, and read-state changes. Reading BI alerts creates an idempotent notification for the current user, keyed by the BI alert ID.

The service does not own user identity and does not send email or SMS. Its gRPC listener is intended for the trusted project network only.

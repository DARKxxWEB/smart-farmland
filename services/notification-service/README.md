# Notification Service

The Notification service stores per-user in-app notification history and delivers push notifications through Firebase Cloud Messaging (FCM). It owns device tokens and notification state in MongoDB; it does not send email or SMS.

## Run locally

For the complete platform, use the [Smart Farmland integration project](../smart-farmland/README.md). To run this service independently, start MongoDB and configure an optional Firebase service-account JSON path in a local `.env` file:

```bash
cp apps/notification-service/sample.env apps/notification-service/.env
pip install -r apps/notification-service/requirements.txt
bash apps/notification-service/scripts/gen_proto.sh
cd apps/notification-service
python main.py
```

When `FIREBASE_CREDENTIALS_PATH` is empty, notification history and device registration still work, but push delivery is reported as failed when a device is registered. Never commit Firebase credentials or local environment files.

Run the service checks with `python -m unittest discover -s tests` from `apps/notification-service/`.

## API and architecture

- [Notification RPC contract and configuration](docs/notification-service.md)
- [Notification ownership and service boundaries](docs/architecture.md)
- [Contributing](CONTRIBUTING.md)

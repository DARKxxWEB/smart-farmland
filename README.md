# Smart Farmland

Smart Farmland contains the complete source for the API gateway and all backend services, alongside local orchestration and end-to-end checks. Each service is kept in its own folder under `services/`, with its Dockerfile, API contracts, and service documentation. The Docker Compose stack builds from these in-project folders and does not depend on sibling repositories.

## Included services

| Service | Responsibility | Local endpoint |
| --- | --- | --- |
| Web | Persian RTL dashboard and Inertia page server | `http://localhost:3000` |
| API gateway | REST and WebSocket client API; gRPC client for backend services | `http://localhost:8000` |
| Auth service | User login, JWT lifecycle, and identity verification | gRPC `localhost:50051` |
| Telemetry service | Validated raw sensor readings and sensor catalog | gRPC `localhost:50052` |
| BI service | Analytics and report generation from telemetry | gRPC `localhost:50053` |
| Notification service | In-app notification history and Firebase Cloud Messaging push | gRPC `localhost:50054` |
| PostgreSQL | Auth-service persistence | `localhost:5432` |
| MongoDB | Telemetry, BI, and Notification persistence | `localhost:27017` |

The sensor firmware is not included in this project. The gateway and backend services are runnable without the web dashboard.

## Start the complete local stack

Requirements: Docker Engine and Docker Compose v2.20 or later.

```bash
cp .env.example .env
```

Edit `.env` before starting. Set a unique PostgreSQL password and keep `POSTGRES_PASSWORD` and the password in `SQLALCHEMY_DATABASE_URL` in sync (URL-encode reserved URL characters). Set a random `JWT_SECRET_KEY` of at least 32 characters and a strong `ADMIN_PASSWORD`. For FCM push delivery, set `FIREBASE_CREDENTIALS_FILE` to `./firebase-service-account.json` or another Firebase service-account JSON path; leave it blank to run in-app history without push delivery. Keep `.env` and Firebase credentials local; the default credential filename is ignored by Git.

To enable the on-demand AI farm assistant, configure `AVALAI_API_KEY` and verify `AVALAI_MODEL` against your AvalAI account. The key is read only by BI service and must remain private. Set `AI_ASSISTANT_ENABLED=false` to disable assistant requests; the deterministic BI dashboard remains available either way. Sensor data used by an assistant answer is sent to the configured external model provider.

From this directory:

```bash
docker compose up --build --wait
```

The initial admin account is created on first startup when the auth database is empty. To inspect readiness:

```bash
docker compose ps
curl --fail http://localhost:3000/health
curl --fail http://localhost:8000/health
curl --fail http://localhost:8000/ready
```

Stop the services with `docker compose down`. This preserves the named database volumes; `docker compose down -v` deletes local database data.

## End-to-end smoke test

With the stack running, execute:

```bash
python3 scripts/smoke_test.py
```

The smoke test prompts for the admin password unless `ADMIN_PASSWORD` is set in the process environment. Use `--username` if `.env` configures a non-default admin name. It verifies readiness, signs in through the gateway, checks the authenticated profile, ingests a unique reading, and confirms BI can analyze that reading through telemetry. It adds one uniquely identified test reading to the local database.

## Fake sensor data for dashboard testing

Until physical sensors are connected, the repository includes a clearly synthetic CSV sample for device `E1` with four moisture sensors and one NPK sensor. It includes normal variation, a few threshold alerts, and gaps in one sensor's readings so the dashboard and BI alerts have representative data to display. Import it into the local database with the configured admin password:

```bash
export IMPORT_USERNAME=admin
read -rsp "Admin password: " IMPORT_PASSWORD
export IMPORT_PASSWORD
echo
python3 services/api-gateway/tools/fake-data/import.py \
  --file services/api-gateway/tools/fake-data/sample-readings.csv \
  --shift-to-now
```

`--shift-to-now` preserves the sample's time gaps but moves its newest timestamp to import time, so recent-data views and the sensor-silence rule work even when the checked-in sample is old. To create a fresh deterministic sample instead:

```bash
python3 services/api-gateway/tools/fake-data/generate.py \
  --days 1 \
  --interval-minutes 15 \
  --output services/api-gateway/tools/fake-data/sample-readings.csv
```

These readings are synthetic, use `source=csv_import`, and are written to the same local telemetry database as other data. Re-importing the exact sample without `--shift-to-now` is safe because duplicate device/sensor/timestamp readings are ignored. Each import with `--shift-to-now` creates a fresh set of timestamps, so avoid repeating it unless you want another demo batch. Before testing with real devices on the same `E1` identifiers, use a separate clean local database or choose different device IDs so demo and real readings are not mixed.

## Service source

- [Web dashboard](services/web/README.md)
- [API gateway](services/api-gateway/README.md)
- [Auth service](services/auth-service/README.md)
- [BI service](services/bi-service/README.md)
- [Notification service](services/notification-service/README.md)
- [Telemetry service](services/telemetry-service/README.md)

All six service implementations are present in this project and are the source used by `docker compose`. The original service forks may still be maintained separately, but they are not required to build or run this stack.

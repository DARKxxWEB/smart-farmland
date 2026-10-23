# Smart Farmland

Smart Farmland contains the complete source for the API gateway and all backend services, alongside local orchestration and end-to-end checks. Each service is kept in its own folder under `services/`, with its Dockerfile, API contracts, and service documentation. The Docker Compose stack builds from these in-project folders and does not depend on sibling repositories.

## Included services

| Service | Responsibility | Local endpoint |
| --- | --- | --- |
| API gateway | REST and WebSocket client API; gRPC client for backend services | `http://localhost:8000` |
| Auth service | User login, JWT lifecycle, and identity verification | gRPC `localhost:50051` |
| Telemetry service | Validated raw sensor readings and sensor catalog | gRPC `localhost:50052` |
| BI service | Analytics and report generation from telemetry | gRPC `localhost:50053` |
| Notification service | In-app notification history and Firebase Cloud Messaging push | gRPC `localhost:50054` |
| PostgreSQL | Auth-service persistence | `localhost:5432` |
| MongoDB | Telemetry, BI, and Notification persistence | `localhost:27017` |

The web dashboard and sensor firmware are not included in this project yet. The gateway and backend services are runnable without them.

## Start the complete local stack

Requirements: Docker Engine and Docker Compose v2.20 or later.

```bash
cp .env.example .env
```

Edit `.env` before starting. Set a unique PostgreSQL password and keep `POSTGRES_PASSWORD` and the password in `SQLALCHEMY_DATABASE_URL` in sync (URL-encode reserved URL characters). Set a random `JWT_SECRET_KEY` of at least 32 characters and a strong `ADMIN_PASSWORD`. For FCM push delivery, set `FIREBASE_CREDENTIALS_FILE` to `./firebase-service-account.json` or another Firebase service-account JSON path; leave it blank to run in-app history without push delivery. Keep `.env` and Firebase credentials local; the default credential filename is ignored by Git.

From this directory:

```bash
docker compose up --build --wait
```

The initial admin account is created on first startup when the auth database is empty. To inspect readiness:

```bash
docker compose ps
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

## Service source

- [API gateway](services/api-gateway/README.md)
- [Auth service](services/auth-service/README.md)
- [BI service](services/bi-service/README.md)
- [Notification service](services/notification-service/README.md)
- [Telemetry service](services/telemetry-service/README.md)

All five service implementations are present in this project and are the source used by `docker compose`. The original service forks may still be maintained separately, but they are not required to build or run this stack.

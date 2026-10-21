# Smart Farmland

Smart Farmland is the local integration project for the independently maintained service repositories in this workspace. It owns service orchestration and end-to-end checks; each service fork owns its implementation, Dockerfile, API, and service documentation.

## Included services

| Service | Responsibility | Local endpoint |
| --- | --- | --- |
| API gateway | REST and WebSocket client API; gRPC client for backend services | `http://localhost:8000` |
| Auth service | User login, JWT lifecycle, and identity verification | gRPC `localhost:50051` |
| Telemetry service | Validated raw sensor readings and sensor catalog | gRPC `localhost:50052` |
| BI service | Analytics and report generation from telemetry | gRPC `localhost:50053` |
| PostgreSQL | Auth-service persistence | `localhost:5432` |
| MongoDB | Telemetry and BI persistence | `localhost:27017` |

The web dashboard and sensor firmware are not present in these repositories yet. The gateway and backend services are runnable without them.

## Start the complete local stack

Requirements: Docker Engine and Docker Compose v2.20 or later.

```bash
cp .env.example .env
```

Edit `.env` before starting. Set a unique PostgreSQL password and keep `POSTGRES_PASSWORD` and the password in `SQLALCHEMY_DATABASE_URL` in sync (URL-encode reserved URL characters). Set a random `JWT_SECRET_KEY` of at least 32 characters and a strong `ADMIN_PASSWORD`. Keep `.env` local; it is ignored by Git.

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

## Service repositories

- [API gateway](../smart-farmland-api-gateway/README.md)
- [Auth service](../smart-farmland-auth-service/README.md)
- [BI service](../smart-farmland-bi-service/README.md)
- [Telemetry service](../smart-farmland-telemetry-service/README.md)

The service repositories remain independent Git repositories. Do not copy service implementation files into this integration directory; change each service in its owning repository.

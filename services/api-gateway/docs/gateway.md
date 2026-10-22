# API Gateway

The gateway is the browser-facing FastAPI boundary. Web and the CSV importer call REST (and one WebSocket). Backend services stay on gRPC.

## Auth

Gateway forwards `x-forwarded-for` to auth so login rate limits see the real client IP.

| Method | Path | Auth |
| --- | --- | --- |
| POST | `/api/v1/auth/login` | No |
| POST | `/api/v1/auth/refresh` | No |
| POST | `/api/v1/auth/logout` | No |
| GET | `/api/v1/auth/me` | Bearer |
| POST | `/api/v1/auth/change-password` | Bearer (admin) |

## Telemetry

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/api/v1/telemetry/readings` | Single reading; broadcasts on WebSocket |
| POST | `/api/v1/telemetry/readings/batch` | CSV / device batch |
| GET | `/api/v1/telemetry/readings` | Filters + `page_token` |
| GET | `/api/v1/telemetry/readings/latest` | One latest row per sensor |
| GET | `/api/v1/telemetry/readings/{id}` | By id |
| GET | `/api/v1/telemetry/sensors` | Catalog |
| PUT | `/api/v1/telemetry/sensors` | Upsert catalog row |

Ingest accepts a user Bearer token, or `Authorization: Device <DEVICE_INGEST_TOKEN>` when that env var is set (ESP32 path).

## BI

| Method | Path |
| --- | --- |
| GET | `/api/v1/bi/summary` |
| GET | `/api/v1/bi/trends` |
| GET | `/api/v1/bi/alerts` |
| POST | `/api/v1/bi/reports` |
| GET | `/api/v1/bi/reports` |
| GET | `/api/v1/bi/reports/{id}` |

## Realtime

`GET /api/v1/ws/telemetry?access_token=<jwt>` (or `Authorization: Bearer` on the upgrade).

After ingest, connected clients receive `{ "type": "reading", "data": ... }`. Slow clients drop oldest queued events. Send `ping` to receive `pong`. Disconnects are ignored by the rest of the process.

## Health

- `GET /health` — process liveness
- `GET /ready` — gRPC health of auth, telemetry, and BI

## Fake data

```bash
python tools/fake-data/generate.py --days 3 --output tools/fake-data/readings.csv
python tools/fake-data/import.py --file tools/fake-data/readings.csv --password "$ADMIN_PASSWORD"
```

The importer logs in through the gateway, posts batches, and retries on 429/503.

## Run

```bash
pip install -r apps/gateway/requirements.txt
bash apps/gateway/scripts/gen_proto.sh
cp apps/gateway/sample.env apps/gateway/.env
cd apps/gateway
python main.py
```

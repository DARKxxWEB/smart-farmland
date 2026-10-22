# Telemetry Service

The telemetry service owns raw farmland sensor readings. It speaks **gRPC** on port `50052` by default. Storage is **MongoDB** via PyMongo.

The contract is [`proto/telemetry/v1/telemetry.proto`](../proto/telemetry/v1/telemetry.proto).

## Shared reading contract

Every reading, whether it came from `tools/fake-data` or a future ESP32 node, uses:

| Field | Meaning |
| --- | --- |
| `device_id` | Gateway node, currently `E1` |
| `sensor_id` | `M1`–`M4` or `NPK-1` |
| `recorded_at` | Sensor clock, stored in UTC |
| `measurements` | `metric`, `value`, `unit` |
| `source` | `csv_import`, `device`, or `gateway` |

Naive timestamps are treated as UTC. Readings more than five minutes in the future are rejected.

## Default plot layout

10 m × 10 m field, ESP32 `E1` at `(5, 5)`:

| Sensor | Kind | Coordinates (m) |
| --- | --- | --- |
| M1 | moisture | 2.5, 2.5 |
| M2 | moisture | 7.5, 2.5 |
| M3 | moisture | 2.5, 7.5 |
| M4 | moisture | 7.5, 7.5 |
| NPK-1 | NPK | 3.5, 5.5 |

## RPCs

| RPC | Purpose |
| --- | --- |
| `IngestReading` | Store one reading; duplicates return `duplicate=true` |
| `IngestBatch` | Bulk ingest, max 500 |
| `GetReading` | Fetch by Mongo id |
| `ListReadings` | Filtered keyset pagination |
| `StreamReadings` | Same filters, streamed for BI |
| `GetLatestReadings` | Latest value per sensor |
| `ListSensors` / `UpsertSensor` | Sensor catalog |

List pagination uses `page_token` encoded from `(recorded_at, _id)` and sorts newest first.

## MongoDB

Database `telemetry` (override with `MONGO_DB`):

- `readings` — unique `(device_id, sensor_id, recorded_at)`
- `sensors` — last seen measurements and plot coordinates

## Run

```bash
pip install -r apps/telemetry-service/requirements.txt
bash apps/telemetry-service/scripts/gen_proto.sh
cp apps/telemetry-service/sample.env apps/telemetry-service/.env
cd apps/telemetry-service
python main.py
```

Requires a MongoDB instance at `MONGO_URI`.

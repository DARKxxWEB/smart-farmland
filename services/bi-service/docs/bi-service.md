# BI Service

The BI service owns aggregations, trends, alerts, and stored reports. It speaks **gRPC** on port `50053`. It never writes raw readings.

## Inputs

Analytics methods take an `AnalyticsQuery`:

- `device_id`, `sensor_id` (optional filters)
- `from_time`, `to_time` (default last 24 hours)

Readings are streamed from telemetry. Reports are stored in MongoDB database `bi`, collection `reports`.

## Outputs

| RPC | Result |
| --- | --- |
| `GetSummary` | Reading counts, per-sensor min/max/avg/last |
| `GetTrends` | Hour or day buckets |
| `GetSensorStats` | Per-sensor metric stats |
| `GetAlerts` | Threshold breaches and silent sensors |
| `GenerateReport` | Persist a full report document |
| `ListReports` / `GetReport` | Retrieve stored reports |

## Default thresholds

| Metric | Low | High |
| --- | --- | --- |
| moisture_pct | 20 | 80 |
| nitrogen_mgkg | 20 | 80 |
| phosphorus_mgkg | 10 | 50 |
| potassium_mgkg | 80 | 300 |
| temperature_c | 5 | 40 |

A sensor is silent when `last_recorded_at` is older than `SILENCE_MINUTES` (default 30).

## Run

```bash
pip install -r apps/bi-service/requirements.txt
bash apps/bi-service/scripts/gen_proto.sh
cp apps/bi-service/sample.env apps/bi-service/.env
cd apps/bi-service
python main.py
```

`TELEMETRY_GRPC_TARGET` must point at a running telemetry service.

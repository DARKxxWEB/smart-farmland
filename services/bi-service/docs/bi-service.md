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
| `ChatAssistant` | On-demand, tool-using RAG assistant for farm data and local metric guidance |

## AI farm assistant

The assistant runs only when a chat request is made; dashboard summary and alert APIs remain deterministic and do not call a model. It uses the OpenAI-compatible Chat Completions interface, asks the model to select among bounded BI tools (live summary, alerts, trends, and local guide retrieval), and returns the model answer with the sources used. Local guide retrieval uses a small in-process text index rather than a vector database, which keeps the single-user deployment lightweight. It does not train a model or write AI output back into telemetry.

Set `AI_ASSISTANT_ENABLED`, `AVALAI_API_KEY`, `AVALAI_BASE_URL`, and `AVALAI_MODEL`. The default API base URL is `https://api.avalai.ir/v1`; confirm available model IDs and any provider-specific compatibility details in the [AvalAI documentation](https://avalai.ir/). Never commit the API key. If no key is set, the assistant endpoint explicitly reports that it is unavailable; all existing BI features continue to work.

When chat is used, the user's message and only the requested tool results (which can include sensor/device identifiers and measurements) are sent to the configured external model provider. Do not send personal or sensitive information in a chat prompt. Replies are generated guidance, not agronomic prescriptions; AI tool use is bounded and the service's existing thresholds remain the source of truth for alerts. Gateway chat requests are rate-limited by `AI_CHAT_RATE_LIMIT` (default `10/hour`).

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

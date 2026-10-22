# Telemetry Service

This repository owns ingestion, validation, indexing, and retrieval of raw sensor readings. It exposes the versioned Telemetry gRPC API and stores readings and the sensor catalog in MongoDB.

## Run locally

For the complete platform, use the [Smart Farmland integration project](../smart-farmland/README.md). To run this service independently, start MongoDB, install the requirements, generate the telemetry protobuf stubs, configure `apps/telemetry-service/sample.env`, and start the service:

```bash
pip install -r apps/telemetry-service/requirements.txt
bash apps/telemetry-service/scripts/gen_proto.sh
cd apps/telemetry-service
python main.py
```

## Documentation

- [Telemetry RPCs, data model, and configuration](docs/telemetry-service.md)
- [Telemetry ownership and service boundaries](docs/architecture.md)
- [Contributing](CONTRIBUTING.md)

# BI Service

This repository owns derived analytics, trends, alerts, and report documents. It reads sensor readings through the Telemetry gRPC contract and stores generated reports in its MongoDB database; it never writes raw readings.

## Run locally

For the complete platform, use the [Smart Farmland integration project](../smart-farmland/README.md). To run this service independently, start MongoDB and Telemetry, install the requirements, generate the BI and Telemetry protobuf stubs, configure `apps/bi-service/sample.env`, and start the service:

```bash
pip install -r apps/bi-service/requirements.txt
bash apps/bi-service/scripts/gen_proto.sh
cd apps/bi-service
python main.py
```

The Telemetry contract is retained here as a build-time dependency because this service's gRPC client generates its own stubs from it.

## Documentation

- [BI RPCs, calculations, and configuration](docs/bi-service.md)
- [BI ownership and service boundaries](docs/architecture.md)
- [Contributing](CONTRIBUTING.md)

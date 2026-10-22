# API Gateway

This repository owns the FastAPI client boundary for Smart Farmland. It exposes REST and WebSocket endpoints and forwards authentication, telemetry, and analytics requests to their gRPC services. It does not own user, reading, or report persistence.

## Run locally

For the complete stack, use the [Smart Farmland integration project](../smart-farmland/README.md). To run the gateway independently, install `apps/gateway/requirements.txt`, generate the gRPC stubs, set the targets in `apps/gateway/sample.env`, and start `python main.py` from `apps/gateway/`.

```bash
pip install -r apps/gateway/requirements.txt
bash apps/gateway/scripts/gen_proto.sh
cd apps/gateway
python main.py
```

The Auth, Telemetry, and BI gRPC services must be reachable at the configured targets.

## Documentation

- [Gateway API and runtime configuration](docs/gateway.md)
- [Gateway ownership and service boundaries](docs/architecture.md)
- [Contributing](CONTRIBUTING.md)

`tools/fake-data/` contains a CSV generator and importer that submit readings through the gateway.

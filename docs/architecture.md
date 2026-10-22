# Integrated architecture

This repository contains the complete implementations of the gateway and backend services, as well as local orchestration and end-to-end validation. Each service has its own directory under `services/` and remains independently buildable. The external service forks are not needed to build or run this project.

```text
Browser / device / importer
            |
            v
      FastAPI gateway
       |     |     |
      gRPC  gRPC  gRPC
       |     |     |
      Auth  Telemetry  BI
       |       |       |
    Postgres  MongoDB  MongoDB
                    |
                    +-- reads through Telemetry gRPC
```

## Service boundaries

- **Gateway** owns the browser-facing REST/WebSocket boundary and adapts requests to the service contracts. It does not own domain persistence.
- **Auth** owns user identity, password verification, and access/refresh token behavior; PostgreSQL is its datastore.
- **Telemetry** validates and stores the source-of-truth sensor readings in MongoDB.
- **BI** reads telemetry through its versioned gRPC contract and owns derived analytics and report documents in MongoDB.
- **This project** owns all service source under `services/`, local Compose orchestration, environment setup, and end-to-end validation. Each service retains its own implementation boundary, Dockerfile, and service-level documentation.

Compose builds every service from its local `services/` folder, starts database dependencies before their services, and checks each gRPC/HTTP health endpoint before starting dependent services. Services communicate over their existing versioned gRPC contracts; Compose supplies the local network and service discovery. Local service ports bind to loopback only. The gRPC listeners use plaintext inside that network; do not expose it or these listeners to an untrusted network.

The current workspace does not contain the web application or device firmware. Device provisioning, deployment secrets, production TLS, and production orchestration remain separate release requirements.

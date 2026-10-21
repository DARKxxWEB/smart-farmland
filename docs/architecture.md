# Integrated architecture

This directory is the integration and local-operations project; it does not own backend implementation code.

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

## Ownership

- **Gateway** owns the browser-facing REST/WebSocket boundary and adapts requests to the service contracts. It does not own domain persistence.
- **Auth** owns user identity, password verification, and access/refresh token behavior; PostgreSQL is its datastore.
- **Telemetry** validates and stores the source-of-truth sensor readings in MongoDB.
- **BI** reads telemetry through its versioned gRPC contract and owns derived analytics and report documents in MongoDB.
- **This project** owns local Compose orchestration, environment setup, and end-to-end validation. The four services remain independently buildable and versioned in their own Git repositories.

Compose starts the database dependencies before their services and checks each gRPC/HTTP health endpoint before starting dependent services. Local service ports bind to loopback only. The gRPC listeners use plaintext inside the local Compose network; do not expose that network or these listeners to an untrusted network.

The current workspace does not contain the web application or device firmware. Device provisioning, deployment secrets, production TLS, and production orchestration remain separate release requirements.

# Integrated architecture

This repository contains the complete implementations of the gateway and backend services, as well as local orchestration and end-to-end validation. Each service has its own directory under `services/` and remains independently buildable. The external service forks are not needed to build or run this project.

```text
Browser / device / importer
            |
            v
      Vue / Inertia web
            |
            v
      FastAPI gateway
       |     |       |       |
      gRPC  gRPC    gRPC    gRPC
       |     |       |       |
      Auth  Telemetry <---- BI ----> AvalAI (optional)
       |       |               |
    Postgres  MongoDB         MongoDB
       |
       +---------------- Notification
                              |      |
                           MongoDB  Firebase FCM
```

## Service boundaries

- **Gateway** owns the browser-facing REST/WebSocket boundary and adapts requests to the service contracts. It does not own domain persistence.
- **Web** owns the Persian RTL dashboard and Inertia page responses. It proxies browser API requests to the gateway and does not own domain logic or persistence.
- **Auth** owns user identity, password verification, and access/refresh token behavior; PostgreSQL is its datastore.
- **Telemetry** validates and stores the source-of-truth sensor readings in MongoDB.
- **BI** reads telemetry through its versioned gRPC contract and owns derived analytics and report documents in MongoDB.
- **BI assistant** is optional and runs only when a user sends a chat message. It uses bounded BI tools and local guide retrieval with the configured AvalAI-compatible model; standard dashboard calculations do not call AI.
- **Notification** owns device FCM tokens and per-user notification history in MongoDB, and sends push messages only through Firebase Cloud Messaging. The gateway routes authenticated alert reads and device registrations to it.
- **This project** owns all service source under `services/`, local Compose orchestration, environment setup, and end-to-end validation. Each service retains its own implementation boundary, Dockerfile, and service-level documentation.

Compose builds every service from its local `services/` folder, starts database dependencies before their services, and checks each gRPC/HTTP health endpoint before starting dependent services. Services communicate over their existing versioned gRPC contracts; Compose supplies the local network and service discovery. Local service ports bind to loopback only. The gRPC listeners use plaintext inside that network; do not expose it or these listeners to an untrusted network. Firebase credentials are optional for local startup and must be supplied through the ignored `FIREBASE_CREDENTIALS_FILE` setting; never commit service-account credentials.

Device firmware is not included. Device provisioning, deployment secrets, production TLS, and production orchestration remain separate release requirements.

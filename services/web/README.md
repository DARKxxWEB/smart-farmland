# Web Dashboard

Persian, right-to-left farm dashboard built with Vue 3, Inertia, and Tailwind CSS. The Node service provides Inertia page responses and proxies `/api/*` requests to the existing FastAPI gateway; it does not own domain logic or data.

## Run locally

Requirements: Node.js 22 or later and a running API gateway.

```bash
npm ci
npm run dev
```

Open `http://localhost:3000`. The local server proxies API requests to `http://localhost:8000`; set `API_GATEWAY_URL` to override the gateway address.

## Production

```bash
npm ci
npm run build
npm start
```

The integrated Docker Compose stack builds and runs this service on `http://localhost:3000`. It starts after the gateway is healthy. The web service uses the `API_GATEWAY_URL` environment variable to find the gateway inside the Compose network.

Login uses the existing gateway endpoint. Access and refresh tokens are held in the browser session storage and are cleared when the session ends.

The signed-in dashboard shell includes the on-demand AI farm assistant. It needs the BI service's AvalAI configuration; when the key is not configured, the assistant presents the service's explicit unavailable message while other dashboard functionality keeps working.

import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import express from "express";
import { createProxyMiddleware } from "http-proxy-middleware";

const root = path.dirname(fileURLToPath(import.meta.url));
const port = Number(process.env.PORT ?? 3000);
const isProduction = process.env.NODE_ENV === "production";
const apiGatewayUrl = process.env.API_GATEWAY_URL ?? "http://localhost:8000";
const app = express();
const pageRoutes = new Map([
  ["/", "Dashboard"],
  ["/dashboard", "Dashboard"],
  ["/login", "Login"],
  ["/sensors", "Sensors"],
  ["/readings", "Readings"],
  ["/reports", "Reports"],
  ["/settings", "Settings"],
]);
let vite;

if (!isProduction) {
  const { createServer } = await import("vite");
  vite = await createServer({
    configFile: path.join(root, "vite.config.ts"),
    server: { middlewareMode: true },
    appType: "custom",
  });
  app.use(vite.middlewares);
} else {
  app.use(express.static(path.join(root, "dist"), { index: false, maxAge: "1y", immutable: true }));
}

app.get("/health", (_request, response) => {
  response.json({ status: "ok" });
});

app.use(
  createProxyMiddleware({
    pathFilter: ["/api/**"],
    target: apiGatewayUrl,
    changeOrigin: true,
    ws: false,
  }),
);

app.use(async (request, response) => {
  const route = new URL(request.originalUrl, "http://localhost");
  const component = pageRoutes.get(route.pathname);
  if (!component) {
    response.status(404).send("صفحه پیدا نشد");
    return;
  }

  try {
    const indexPath = path.join(root, isProduction ? "dist/index.html" : "index.html");
    let html = await readFile(indexPath, "utf8");
    if (vite) html = await vite.transformIndexHtml(request.originalUrl, html);

    const page = {
      component,
      props: {},
      url: request.originalUrl,
      version: createHash("sha256").update(html).digest("hex"),
    };
    const requestedVersion = request.get("X-Inertia-Version");

    if (
      request.get("X-Inertia") === "true" &&
      requestedVersion &&
      requestedVersion !== page.version
    ) {
      response
        .status(409)
        .set("X-Inertia-Location", request.originalUrl)
        .end();
      return;
    }

    response.set("Vary", "X-Inertia");
    response.set("Cache-Control", "no-store");

    if (request.get("X-Inertia") === "true") {
      response.set("X-Inertia", "true").json(page);
      return;
    }

    const serializedPage = JSON.stringify(page)
      .replaceAll("&", "\\u0026")
      .replaceAll("<", "\\u003c")
      .replaceAll(">", "\\u003e");
    response.type("html").send(
      html.replace('<div id="app"></div>', `<div id="app" data-page="${serializedPage.replaceAll('"', "&quot;")}"></div>`),
    );
  } catch (error) {
    if (vite) vite.ssrFixStacktrace(error);
    console.error("Could not render Inertia page", error);
    response.status(500).send("خطا در بارگذاری صفحه");
  }
});

const server = app.listen(port, "0.0.0.0", () => {
  console.info(`Web service listening on port ${port}`);
});

async function shutdown() {
  server.close();
  if (vite) await vite.close();
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "gen"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from grpc_clients import clients
from routes import auth, bi, health, notifications, telemetry, ws
from settings import CORS_ORIGINS, HTTP_HOST, HTTP_PORT
from utils.errors import rate_limit_handler
from utils.rate_limiter import RateLimitExceeded, limiter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("gateway")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await clients.start()
    logger.info("gRPC clients connected")
    yield
    await limiter.close()
    await clients.close()
    logger.info("Gateway shutdown complete")


app = FastAPI(
    title="Smart Farmland Gateway",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(telemetry.router)
app.include_router(bi.router)
app.include_router(notifications.router)
app.include_router(ws.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=HTTP_HOST, port=HTTP_PORT, reload=False)

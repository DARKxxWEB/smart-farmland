from fastapi import APIRouter

from grpc_clients.clients import grpc_healthy
from settings import (
    AUTH_GRPC_TARGET,
    BI_GRPC_TARGET,
    NOTIFICATION_GRPC_TARGET,
    TELEMETRY_GRPC_TARGET,
)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/ready")
async def ready():
    checks = {
        "auth": await grpc_healthy(AUTH_GRPC_TARGET),
        "telemetry": await grpc_healthy(TELEMETRY_GRPC_TARGET),
        "bi": await grpc_healthy(BI_GRPC_TARGET),
        "notifications": await grpc_healthy(NOTIFICATION_GRPC_TARGET),
    }
    status = "ok" if all(checks.values()) else "degraded"
    return {"status": status, "services": checks}

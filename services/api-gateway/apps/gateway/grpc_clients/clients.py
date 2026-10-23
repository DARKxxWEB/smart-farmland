import grpc
from grpc_health.v1 import health_pb2, health_pb2_grpc

from auth.v1 import auth_pb2_grpc
from bi.v1 import bi_pb2_grpc
from notification.v1 import notification_pb2_grpc
from settings import (
    AUTH_GRPC_TARGET,
    BI_GRPC_TARGET,
    NOTIFICATION_GRPC_TARGET,
    TELEMETRY_GRPC_TARGET,
)
from telemetry.v1 import telemetry_pb2_grpc

auth_channel: grpc.aio.Channel | None = None
telemetry_channel: grpc.aio.Channel | None = None
bi_channel: grpc.aio.Channel | None = None
notification_channel: grpc.aio.Channel | None = None

auth_stub: auth_pb2_grpc.AuthServiceStub | None = None
telemetry_stub: telemetry_pb2_grpc.TelemetryServiceStub | None = None
bi_stub: bi_pb2_grpc.BIServiceStub | None = None
notification_stub: notification_pb2_grpc.NotificationServiceStub | None = None


async def start() -> None:
    global auth_channel, telemetry_channel, bi_channel, notification_channel
    global auth_stub, telemetry_stub, bi_stub, notification_stub
    auth_channel = grpc.aio.insecure_channel(AUTH_GRPC_TARGET)
    telemetry_channel = grpc.aio.insecure_channel(TELEMETRY_GRPC_TARGET)
    bi_channel = grpc.aio.insecure_channel(BI_GRPC_TARGET)
    notification_channel = grpc.aio.insecure_channel(NOTIFICATION_GRPC_TARGET)
    auth_stub = auth_pb2_grpc.AuthServiceStub(auth_channel)
    telemetry_stub = telemetry_pb2_grpc.TelemetryServiceStub(telemetry_channel)
    bi_stub = bi_pb2_grpc.BIServiceStub(bi_channel)
    notification_stub = notification_pb2_grpc.NotificationServiceStub(
        notification_channel
    )


async def close() -> None:
    for channel in (
        auth_channel,
        telemetry_channel,
        bi_channel,
        notification_channel,
    ):
        if channel is not None:
            await channel.close()


def metadata(access_token: str | None = None, ip: str | None = None) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    if access_token:
        items.append(("authorization", f"Bearer {access_token}"))
    if ip:
        items.append(("x-forwarded-for", ip))
    return items


async def grpc_healthy(target: str) -> bool:
    channel = grpc.aio.insecure_channel(target)
    try:
        stub = health_pb2_grpc.HealthStub(channel)
        response = await stub.Check(
            health_pb2.HealthCheckRequest(service=""), timeout=2
        )
        return response.status == health_pb2.HealthCheckResponse.SERVING
    except Exception:
        return False
    finally:
        await channel.close()

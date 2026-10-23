import asyncio
import logging
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "gen"))

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from db.mongo import close, connect
from grpc_api.servicer import NotificationServicer
from settings import (
    FIREBASE_CREDENTIALS_PATH,
    GRPC_HOST,
    GRPC_PORT,
    GRPC_REFLECTION,
)
from notification.v1 import notification_pb2, notification_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("notification-service")

SERVICE_NAME = notification_pb2.DESCRIPTOR.services_by_name[
    "NotificationService"
].full_name


async def serve() -> None:
    await connect()
    if not FIREBASE_CREDENTIALS_PATH:
        logger.warning("Firebase FCM is disabled: credentials path is not configured")

    server = grpc.aio.server()
    notification_pb2_grpc.add_NotificationServiceServicer_to_server(
        NotificationServicer(), server
    )
    health_servicer = health.aio.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
    if GRPC_REFLECTION:
        reflection.enable_server_reflection(
            (SERVICE_NAME, reflection.SERVICE_NAME), server
        )

    server.add_insecure_port(f"{GRPC_HOST}:{GRPC_PORT}")
    await server.start()
    await health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)
    await health_servicer.set(SERVICE_NAME, health_pb2.HealthCheckResponse.SERVING)
    logger.info("Notification gRPC server listening on %s:%s", GRPC_HOST, GRPC_PORT)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    await stop.wait()

    await health_servicer.enter_graceful_shutdown()
    await server.stop(grace=5)
    await close()


if __name__ == "__main__":
    asyncio.run(serve())

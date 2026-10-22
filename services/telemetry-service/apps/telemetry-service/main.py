import asyncio
import logging
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "gen"))

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from db.mongo import close, connect, seed_default_sensors
from grpc_api.servicer import TelemetryServicer
from settings import GRPC_HOST, GRPC_PORT, GRPC_REFLECTION, SEED_DEFAULT_SENSORS
from telemetry.v1 import telemetry_pb2, telemetry_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("telemetry-service")

SERVICE_NAME = telemetry_pb2.DESCRIPTOR.services_by_name["TelemetryService"].full_name


async def serve() -> None:
    database = await connect()
    if SEED_DEFAULT_SENSORS:
        await seed_default_sensors(database)

    server = grpc.aio.server()
    telemetry_pb2_grpc.add_TelemetryServiceServicer_to_server(TelemetryServicer(), server)

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
    logger.info("Telemetry gRPC server listening on %s:%s", GRPC_HOST, GRPC_PORT)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    await stop.wait()
    logger.info("Shutting down...")
    await health_servicer.enter_graceful_shutdown()
    await server.stop(grace=5)
    await close()


if __name__ == "__main__":
    asyncio.run(serve())

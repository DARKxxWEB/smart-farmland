import grpc

from settings import TELEMETRY_GRPC_TARGET
from telemetry.v1 import telemetry_pb2, telemetry_pb2_grpc
from utils.time import to_timestamp

_channel: grpc.aio.Channel | None = None
_stub: telemetry_pb2_grpc.TelemetryServiceStub | None = None


async def start() -> None:
    global _channel, _stub
    _channel = grpc.aio.insecure_channel(TELEMETRY_GRPC_TARGET)
    _stub = telemetry_pb2_grpc.TelemetryServiceStub(_channel)


async def close() -> None:
    global _channel, _stub
    if _channel is not None:
        await _channel.close()
    _channel, _stub = None, None


def stub() -> telemetry_pb2_grpc.TelemetryServiceStub:
    if _stub is None:
        raise RuntimeError("Telemetry client is not started")
    return _stub


def _query_request(device_id, sensor_id, from_time, to_time, metric="", page_size=200):
    req = telemetry_pb2.ListReadingsRequest(
        device_id=device_id or "",
        sensor_id=sensor_id or "",
        metric=metric or "",
        page_size=page_size,
    )
    if from_time:
        req.from_time.CopyFrom(to_timestamp(from_time))
    if to_time:
        req.to_time.CopyFrom(to_timestamp(to_time))
    return req


async def stream_readings(
    device_id: str = "",
    sensor_id: str = "",
    from_time=None,
    to_time=None,
    metric: str = "",
):
    request = _query_request(device_id, sensor_id, from_time, to_time, metric)
    async for reading in stub().StreamReadings(request):
        yield reading


async def list_sensors(device_id: str = ""):
    response = await stub().ListSensors(
        telemetry_pb2.ListSensorsRequest(device_id=device_id or "")
    )
    return list(response.sensors)

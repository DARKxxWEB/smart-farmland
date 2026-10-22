from datetime import datetime

import grpc
from fastapi import APIRouter, Query, Request

from grpc_clients import clients
from schema._input import BatchReadingsBody, ReadingBody, SensorBody
from telemetry.v1 import telemetry_pb2
from utils import proto_json
from utils.deps import IngestDep, IngestLimit, ReadLimit, UserDep
from utils.errors import grpc_http_error
from utils.ws_manager import manager

router = APIRouter(prefix="/api/v1/telemetry", tags=["telemetry"])


def _reading_input(body: ReadingBody) -> telemetry_pb2.ReadingInput:
    msg = telemetry_pb2.ReadingInput(
        device_id=body.device_id,
        sensor_id=body.sensor_id,
        source=body.source,
        measurements=[
            telemetry_pb2.Measurement(metric=m.metric, value=m.value, unit=m.unit)
            for m in body.measurements
        ],
    )
    proto_json.apply_timestamp(msg.recorded_at, body.recorded_at)
    return msg


@router.post("/readings")
async def ingest_reading(body: ReadingBody, request: Request, _p=IngestDep, _l=IngestLimit):
    try:
        response = await clients.telemetry_stub.IngestReading(
            telemetry_pb2.IngestReadingRequest(reading=_reading_input(body))
        )
    except grpc.aio.AioRpcError as e:
        raise grpc_http_error(e) from e
    payload = proto_json.reading(response.reading)
    payload["duplicate"] = response.duplicate
    if not response.duplicate:
        await manager.broadcast({"type": "reading", "data": payload})
    return payload


@router.post("/readings/batch")
async def ingest_batch(body: BatchReadingsBody, request: Request, _p=IngestDep, _l=IngestLimit):
    try:
        response = await clients.telemetry_stub.IngestBatch(
            telemetry_pb2.IngestBatchRequest(
                readings=[_reading_input(item) for item in body.readings]
            )
        )
    except grpc.aio.AioRpcError as e:
        raise grpc_http_error(e) from e
    await manager.broadcast(
        {
            "type": "batch",
            "data": {
                "accepted": response.accepted,
                "duplicates": response.duplicates,
            },
        }
    )
    return {
        "accepted": response.accepted,
        "duplicates": response.duplicates,
        "rejected": response.rejected,
        "errors": list(response.errors),
    }


@router.get("/readings")
async def list_readings(
    request: Request,
    _u=UserDep,
    _l=ReadLimit,
    device_id: str = "",
    sensor_id: str = "",
    metric: str = "",
    from_time: datetime | None = None,
    to_time: datetime | None = None,
    page_size: int = Query(default=50, ge=1, le=200),
    page_token: str = "",
):
    req = telemetry_pb2.ListReadingsRequest(
        device_id=device_id,
        sensor_id=sensor_id,
        metric=metric,
        page_size=page_size,
        page_token=page_token,
    )
    proto_json.apply_timestamp(req.from_time, from_time)
    proto_json.apply_timestamp(req.to_time, to_time)
    try:
        response = await clients.telemetry_stub.ListReadings(req)
    except grpc.aio.AioRpcError as e:
        raise grpc_http_error(e) from e
    return {
        "items": [proto_json.reading(item) for item in response.readings],
        "next_page_token": response.next_page_token,
        "page_size": response.page_size,
    }


@router.get("/readings/latest")
async def latest_readings(device_id: str = "", _u=UserDep, _l=ReadLimit):
    try:
        response = await clients.telemetry_stub.GetLatestReadings(
            telemetry_pb2.GetLatestReadingsRequest(device_id=device_id)
        )
    except grpc.aio.AioRpcError as e:
        raise grpc_http_error(e) from e
    return {"items": [proto_json.reading(item) for item in response.readings]}


@router.get("/readings/{reading_id}")
async def get_reading(reading_id: str, _u=UserDep, _l=ReadLimit):
    try:
        response = await clients.telemetry_stub.GetReading(
            telemetry_pb2.GetReadingRequest(id=reading_id)
        )
    except grpc.aio.AioRpcError as e:
        raise grpc_http_error(e) from e
    return proto_json.reading(response)


@router.get("/sensors")
async def list_sensors(device_id: str = "", _u=UserDep, _l=ReadLimit):
    try:
        response = await clients.telemetry_stub.ListSensors(
            telemetry_pb2.ListSensorsRequest(device_id=device_id)
        )
    except grpc.aio.AioRpcError as e:
        raise grpc_http_error(e) from e
    return {"items": [proto_json.sensor(item) for item in response.sensors]}


@router.put("/sensors")
async def upsert_sensor(body: SensorBody, _u=UserDep, _l=IngestLimit):
    sensor = telemetry_pb2.Sensor(
        sensor_id=body.sensor_id,
        device_id=body.device_id,
        kind=body.kind,
    )
    if body.x is not None and body.y is not None:
        sensor.location.x = body.x
        sensor.location.y = body.y
        sensor.location.unit = body.unit
    try:
        response = await clients.telemetry_stub.UpsertSensor(
            telemetry_pb2.UpsertSensorRequest(sensor=sensor)
        )
    except grpc.aio.AioRpcError as e:
        raise grpc_http_error(e) from e
    return proto_json.sensor(response)

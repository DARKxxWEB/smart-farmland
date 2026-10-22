import functools
import logging

import grpc
from pydantic import ValidationError

from schema._input import ReadingInputModel
from services.telemetry import TelemetryError, TelemetryStore
from telemetry.v1 import telemetry_pb2, telemetry_pb2_grpc
from utils.time import from_timestamp, to_timestamp

logger = logging.getLogger(__name__)


def _first_validation_message(e: ValueError) -> str:
    if isinstance(e, ValidationError):
        msg = e.errors()[0]["msg"]
        return msg.removeprefix("Value error, ")
    return str(e)


def handle_errors(func):
    @functools.wraps(func)
    async def wrapper(self, request, context):
        try:
            return await func(self, request, context)
        except grpc.aio.AbortError:
            raise
        except TelemetryError as e:
            code = {
                "not_found": grpc.StatusCode.NOT_FOUND,
                "invalid": grpc.StatusCode.INVALID_ARGUMENT,
            }.get(e.code, grpc.StatusCode.INVALID_ARGUMENT)
            await context.abort(code, str(e))
        except ValueError as e:
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT, _first_validation_message(e)
            )
        except Exception:
            logger.exception("Unhandled error in %s", func.__name__)
            await context.abort(grpc.StatusCode.INTERNAL, "Internal server error")

    return wrapper


def _measurements_from_proto(items) -> list[dict]:
    return [{"metric": m.metric, "value": m.value, "unit": m.unit} for m in items]


def _input_from_proto(msg) -> ReadingInputModel:
    recorded_at = from_timestamp(msg.recorded_at)
    if recorded_at is None:
        raise ValueError("recorded_at is required")
    return ReadingInputModel(
        device_id=msg.device_id,
        sensor_id=msg.sensor_id,
        recorded_at=recorded_at,
        measurements=_measurements_from_proto(msg.measurements),
        source=msg.source or "gateway",
    )


def _measurement_msgs(items: list[dict]):
    return [
        telemetry_pb2.Measurement(
            metric=item["metric"],
            value=item["value"],
            unit=item.get("unit", ""),
        )
        for item in items
    ]


def _reading_msg(doc: dict) -> telemetry_pb2.Reading:
    reading_id = str(doc["_id"]) if doc.get("_id") is not None else ""
    kwargs = dict(
        id=reading_id,
        device_id=doc["device_id"],
        sensor_id=doc["sensor_id"],
        measurements=_measurement_msgs(doc.get("measurements") or []),
        source=doc.get("source", ""),
    )
    recorded = to_timestamp(doc.get("recorded_at"))
    received = to_timestamp(doc.get("received_at"))
    msg = telemetry_pb2.Reading(**kwargs)
    if recorded:
        msg.recorded_at.CopyFrom(recorded)
    if received:
        msg.received_at.CopyFrom(received)
    return msg


def _sensor_msg(doc: dict) -> telemetry_pb2.Sensor:
    msg = telemetry_pb2.Sensor(
        sensor_id=doc["sensor_id"],
        device_id=doc["device_id"],
        kind=doc.get("kind", ""),
        last_measurements=_measurement_msgs(doc.get("last_measurements") or []),
    )
    location = doc.get("location") or {}
    if location:
        msg.location.x = float(location.get("x") or 0)
        msg.location.y = float(location.get("y") or 0)
        msg.location.unit = location.get("unit") or "m"
    last = to_timestamp(doc.get("last_recorded_at"))
    updated = to_timestamp(doc.get("updated_at"))
    if last:
        msg.last_recorded_at.CopyFrom(last)
    if updated:
        msg.updated_at.CopyFrom(updated)
    return msg


class TelemetryServicer(telemetry_pb2_grpc.TelemetryServiceServicer):
    @handle_errors
    async def IngestReading(self, request, context):
        store = TelemetryStore()
        data = _input_from_proto(request.reading)
        doc, duplicate = await store.ingest(data)
        return telemetry_pb2.IngestReadingResponse(
            reading=_reading_msg(doc),
            duplicate=duplicate,
        )

    @handle_errors
    async def IngestBatch(self, request, context):
        store = TelemetryStore()
        items = [_input_from_proto(item) for item in request.readings]
        result = await store.ingest_batch(items)
        return telemetry_pb2.IngestBatchResponse(
            accepted=result["accepted"],
            duplicates=result["duplicates"],
            rejected=result["rejected"],
            errors=result["errors"],
        )

    @handle_errors
    async def GetReading(self, request, context):
        store = TelemetryStore()
        return _reading_msg(await store.get_reading(request.id))

    @handle_errors
    async def ListReadings(self, request, context):
        store = TelemetryStore()
        docs, token, size = await store.list_readings(
            device_id=request.device_id,
            sensor_id=request.sensor_id,
            from_time=from_timestamp(request.from_time),
            to_time=from_timestamp(request.to_time),
            metric=request.metric,
            page_size=request.page_size,
            page_token=request.page_token,
        )
        return telemetry_pb2.ListReadingsResponse(
            readings=[_reading_msg(doc) for doc in docs],
            next_page_token=token,
            page_size=size,
        )

    async def StreamReadings(self, request, context):
        try:
            store = TelemetryStore()
            async for doc in store.iter_readings(
                device_id=request.device_id,
                sensor_id=request.sensor_id,
                from_time=from_timestamp(request.from_time),
                to_time=from_timestamp(request.to_time),
                metric=request.metric,
                page_size=request.page_size or 200,
            ):
                yield _reading_msg(doc)
        except TelemetryError as e:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
        except ValueError as e:
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT, _first_validation_message(e)
            )
        except Exception:
            logger.exception("Unhandled error in StreamReadings")
            await context.abort(grpc.StatusCode.INTERNAL, "Internal server error")

    @handle_errors
    async def GetLatestReadings(self, request, context):
        store = TelemetryStore()
        docs = await store.latest_readings(request.device_id)
        return telemetry_pb2.GetLatestReadingsResponse(
            readings=[_reading_msg(doc) for doc in docs]
        )

    @handle_errors
    async def ListSensors(self, request, context):
        store = TelemetryStore()
        docs = await store.list_sensors(request.device_id)
        return telemetry_pb2.ListSensorsResponse(
            sensors=[_sensor_msg(doc) for doc in docs]
        )

    @handle_errors
    async def UpsertSensor(self, request, context):
        store = TelemetryStore()
        sensor = request.sensor
        location = None
        if sensor.HasField("location"):
            location = {
                "x": sensor.location.x,
                "y": sensor.location.y,
                "unit": sensor.location.unit or "m",
            }
        doc = await store.upsert_sensor(
            {
                "sensor_id": sensor.sensor_id,
                "device_id": sensor.device_id,
                "kind": sensor.kind,
                "location": location,
            }
        )
        return _sensor_msg(doc)

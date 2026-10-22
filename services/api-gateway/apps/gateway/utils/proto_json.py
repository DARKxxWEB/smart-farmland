from datetime import datetime, timezone

from google.protobuf.timestamp_pb2 import Timestamp
from pydantic import BaseModel


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_timestamp(dt: datetime | None) -> Timestamp | None:
    if dt is None:
        return None
    ts = Timestamp()
    ts.FromDatetime(ensure_utc(dt))
    return ts


def apply_timestamp(target: Timestamp, dt: datetime | None) -> None:
    ts = to_timestamp(dt)
    if ts:
        target.CopyFrom(ts)


def ts_to_iso(ts: Timestamp | None) -> str | None:
    if ts is None or (ts.seconds == 0 and ts.nanos == 0):
        return None
    dt = ts.ToDatetime()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def measurement(msg) -> dict:
    return {"metric": msg.metric, "value": msg.value, "unit": msg.unit}


def reading(msg) -> dict:
    return {
        "id": msg.id,
        "device_id": msg.device_id,
        "sensor_id": msg.sensor_id,
        "recorded_at": ts_to_iso(msg.recorded_at),
        "received_at": ts_to_iso(msg.received_at),
        "measurements": [measurement(item) for item in msg.measurements],
        "source": msg.source,
    }


def sensor(msg) -> dict:
    location = None
    if msg.HasField("location"):
        location = {"x": msg.location.x, "y": msg.location.y, "unit": msg.location.unit}
    return {
        "sensor_id": msg.sensor_id,
        "device_id": msg.device_id,
        "kind": msg.kind,
        "location": location,
        "last_recorded_at": ts_to_iso(msg.last_recorded_at),
        "last_measurements": [measurement(item) for item in msg.last_measurements],
        "updated_at": ts_to_iso(msg.updated_at),
    }


def user(msg) -> dict:
    return {
        "id": msg.id,
        "username": msg.username,
        "role": msg.role,
        "is_active": msg.is_active,
        "created_at": ts_to_iso(msg.created_at),
        "updated_at": ts_to_iso(msg.updated_at),
    }


def tokens(msg) -> dict:
    return {
        "access_token": msg.access_token,
        "refresh_token": msg.refresh_token,
        "token_type": msg.token_type,
        "expires_in": msg.expires_in,
    }


def metric_stats(msg) -> dict:
    return {
        "metric": msg.metric,
        "unit": msg.unit,
        "count": msg.count,
        "min": msg.min,
        "max": msg.max,
        "avg": msg.avg,
        "last": msg.last,
    }


def sensor_stats(msg) -> dict:
    return {
        "sensor_id": msg.sensor_id,
        "device_id": msg.device_id,
        "kind": msg.kind,
        "metrics": [metric_stats(item) for item in msg.metrics],
        "last_recorded_at": ts_to_iso(msg.last_recorded_at),
    }


def trend(msg) -> dict:
    return {
        "sensor_id": msg.sensor_id,
        "metric": msg.metric,
        "unit": msg.unit,
        "points": [
            {
                "bucket_start": ts_to_iso(point.bucket_start),
                "avg": point.avg,
                "min": point.min,
                "max": point.max,
                "count": point.count,
            }
            for point in msg.points
        ],
    }


def alert(msg) -> dict:
    return {
        "id": msg.id,
        "type": msg.type,
        "severity": msg.severity,
        "sensor_id": msg.sensor_id,
        "device_id": msg.device_id,
        "metric": msg.metric,
        "value": msg.value,
        "threshold": msg.threshold,
        "comparator": msg.comparator,
        "message": msg.message,
        "recorded_at": ts_to_iso(msg.recorded_at),
    }


def summary(msg) -> dict:
    return {
        "reading_count": msg.reading_count,
        "sensor_count": msg.sensor_count,
        "alert_count": msg.alert_count,
        "from_time": ts_to_iso(msg.from_time),
        "to_time": ts_to_iso(msg.to_time),
        "sensors": [sensor_stats(item) for item in msg.sensors],
    }


def report(msg, include_details: bool = True) -> dict:
    payload = {
        "id": msg.id,
        "title": msg.title,
        "generated_by": msg.generated_by,
        "generated_at": ts_to_iso(msg.generated_at),
        "from_time": ts_to_iso(msg.from_time),
        "to_time": ts_to_iso(msg.to_time),
        "summary": summary(msg.summary),
    }
    if include_details:
        payload["sensor_stats"] = [sensor_stats(item) for item in msg.sensor_stats]
        payload["trends"] = [trend(item) for item in msg.trends]
        payload["alerts"] = [alert(item) for item in msg.alerts]
        payload["sections"] = [
            {"title": item.title, "body": item.body} for item in msg.sections
        ]
    return payload


class MeasurementIn(BaseModel):
    metric: str
    value: float
    unit: str = ""


class ReadingIn(BaseModel):
    device_id: str
    sensor_id: str
    recorded_at: datetime
    measurements: list[MeasurementIn]
    source: str = "gateway"


class SensorIn(BaseModel):
    sensor_id: str
    device_id: str
    kind: str = "unknown"
    location: dict | None = None

from datetime import datetime, timezone

from google.protobuf.timestamp_pb2 import Timestamp


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


def from_timestamp(ts: Timestamp | None) -> datetime | None:
    if ts is None or (ts.seconds == 0 and ts.nanos == 0):
        return None
    return ensure_utc(ts.ToDatetime())

import logging
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError, DuplicateKeyError

from db.mongo import get_db
from schema._input import ReadingInputModel
from settings import DEFAULT_PAGE_SIZE, FUTURE_SKEW_SECONDS, MAX_BATCH_SIZE, MAX_PAGE_SIZE
from utils.paging import decode_page_token, encode_page_token

logger = logging.getLogger(__name__)


class TelemetryError(Exception):
    def __init__(self, message: str, code: str = "invalid") -> None:
        super().__init__(message)
        self.code = code


def _now() -> datetime:
    return datetime.now(timezone.utc)


def reading_doc(data: ReadingInputModel, received_at: datetime | None = None) -> dict:
    received = received_at or _now()
    return {
        "device_id": data.device_id,
        "sensor_id": data.sensor_id,
        "recorded_at": data.recorded_at,
        "received_at": received,
        "measurements": [m.model_dump() for m in data.measurements],
        "source": data.source,
    }


class TelemetryStore:
    def __init__(self) -> None:
        database = get_db()
        self.readings = database["readings"]
        self.sensors = database["sensors"]

    async def _touch_sensor(self, data: ReadingInputModel, recorded_at: datetime) -> None:
        await self.sensors.update_one(
            {"device_id": data.device_id, "sensor_id": data.sensor_id},
            {
                "$set": {
                    "device_id": data.device_id,
                    "sensor_id": data.sensor_id,
                    "last_recorded_at": recorded_at,
                    "last_measurements": [m.model_dump() for m in data.measurements],
                    "updated_at": _now(),
                },
                "$setOnInsert": {"kind": "unknown", "location": None},
            },
            upsert=True,
        )

    async def ingest(self, data: ReadingInputModel) -> tuple[dict, bool]:
        data.reject_future(FUTURE_SKEW_SECONDS)
        doc = reading_doc(data)
        try:
            result = await self.readings.insert_one(doc)
            doc["_id"] = result.inserted_id
            await self._touch_sensor(data, data.recorded_at)
            return doc, False
        except DuplicateKeyError:
            existing = await self.readings.find_one(
                {
                    "device_id": data.device_id,
                    "sensor_id": data.sensor_id,
                    "recorded_at": data.recorded_at,
                }
            )
            return existing, True

    async def ingest_batch(self, items: list[ReadingInputModel]) -> dict:
        if len(items) > MAX_BATCH_SIZE:
            raise TelemetryError(
                f"Batch exceeds maximum of {MAX_BATCH_SIZE} readings", "invalid"
            )
        accepted = 0
        duplicates = 0
        rejected = 0
        errors: list[str] = []
        received_at = _now()
        docs = []
        valid: list[ReadingInputModel] = []

        for index, item in enumerate(items):
            try:
                item.reject_future(FUTURE_SKEW_SECONDS)
                docs.append(reading_doc(item, received_at))
                valid.append(item)
            except ValueError as e:
                rejected += 1
                errors.append(f"index {index}: {e}")

        if docs:
            try:
                result = await self.readings.insert_many(docs, ordered=False)
                accepted = len(result.inserted_ids)
            except BulkWriteError as e:
                write_errors = e.details.get("writeErrors", [])
                n_inserted = e.details.get("nInserted", 0)
                accepted = n_inserted
                for err in write_errors:
                    if err.get("code") == 11000:
                        duplicates += 1
                    else:
                        rejected += 1
                        errors.append(err.get("errmsg", "write error"))

            ops = []
            for item in valid:
                ops.append(
                    UpdateOne(
                        {"device_id": item.device_id, "sensor_id": item.sensor_id},
                        {
                            "$set": {
                                "device_id": item.device_id,
                                "sensor_id": item.sensor_id,
                                "last_measurements": [
                                    m.model_dump() for m in item.measurements
                                ],
                                "updated_at": received_at,
                            },
                            "$setOnInsert": {"kind": "unknown", "location": None},
                            "$max": {"last_recorded_at": item.recorded_at},
                        },
                        upsert=True,
                    )
                )
            if ops:
                await self.sensors.bulk_write(ops, ordered=False)

        return {
            "accepted": accepted,
            "duplicates": duplicates,
            "rejected": rejected,
            "errors": errors[:20],
        }

    async def get_reading(self, reading_id: str) -> dict:
        try:
            oid = ObjectId(reading_id)
        except InvalidId as e:
            raise TelemetryError("Invalid reading id", "invalid") from e
        doc = await self.readings.find_one({"_id": oid})
        if not doc:
            raise TelemetryError("Reading not found", "not_found")
        return doc

    def _list_filter(
        self,
        device_id: str,
        sensor_id: str,
        from_time: datetime | None,
        to_time: datetime | None,
        metric: str,
        page_token: str,
    ) -> dict:
        query: dict = {}
        if device_id:
            query["device_id"] = device_id
        if sensor_id:
            query["sensor_id"] = sensor_id
        recorded: dict = {}
        if from_time:
            recorded["$gte"] = from_time
        if to_time:
            recorded["$lte"] = to_time
        if page_token:
            token_time, token_id = decode_page_token(page_token)
            cursor_clause = {
                "$or": [
                    {"recorded_at": {"$lt": token_time}},
                    {"recorded_at": token_time, "_id": {"$lt": token_id}},
                ]
            }
            if recorded:
                query["$and"] = [{"recorded_at": recorded}, cursor_clause]
            else:
                query.update(cursor_clause)
        elif recorded:
            query["recorded_at"] = recorded
        if metric:
            query["measurements.metric"] = metric
        return query

    async def list_readings(
        self,
        device_id: str = "",
        sensor_id: str = "",
        from_time: datetime | None = None,
        to_time: datetime | None = None,
        metric: str = "",
        page_size: int = 0,
        page_token: str = "",
    ) -> tuple[list[dict], str, int]:
        size = page_size or DEFAULT_PAGE_SIZE
        size = max(1, min(size, MAX_PAGE_SIZE))
        query = self._list_filter(
            device_id, sensor_id, from_time, to_time, metric, page_token
        )
        cursor = (
            self.readings.find(query)
            .sort([("recorded_at", -1), ("_id", -1)])
            .limit(size + 1)
        )
        docs = await cursor.to_list(length=size + 1)
        next_token = ""
        if len(docs) > size:
            last = docs[size - 1]
            next_token = encode_page_token(last["recorded_at"], last["_id"])
            docs = docs[:size]
        return docs, next_token, size

    async def iter_readings(self, **kwargs):
        token = kwargs.pop("page_token", "")
        while True:
            docs, token, _ = await self.list_readings(page_token=token, **kwargs)
            if not docs:
                break
            for doc in docs:
                yield doc
            if not token:
                break

    async def latest_readings(self, device_id: str = "") -> list[dict]:
        query = {"last_recorded_at": {"$ne": None}}
        if device_id:
            query["device_id"] = device_id
        sensors = await self.sensors.find(query).to_list(length=200)
        readings = []
        for sensor in sensors:
            readings.append(
                {
                    "_id": None,
                    "device_id": sensor["device_id"],
                    "sensor_id": sensor["sensor_id"],
                    "recorded_at": sensor.get("last_recorded_at"),
                    "received_at": sensor.get("updated_at"),
                    "measurements": sensor.get("last_measurements") or [],
                    "source": "latest",
                }
            )
        return readings

    async def list_sensors(self, device_id: str = "") -> list[dict]:
        query = {"device_id": device_id} if device_id else {}
        return await self.sensors.find(query).sort("sensor_id", 1).to_list(length=200)

    async def upsert_sensor(self, sensor: dict) -> dict:
        sensor_id = (sensor.get("sensor_id") or "").strip()
        device_id = (sensor.get("device_id") or "").strip()
        if not sensor_id or not device_id:
            raise TelemetryError("sensor_id and device_id are required")
        now = _now()
        payload = {
            "sensor_id": sensor_id,
            "device_id": device_id,
            "kind": sensor.get("kind") or "unknown",
            "location": sensor.get("location"),
            "updated_at": now,
        }
        await self.sensors.update_one(
            {"device_id": device_id, "sensor_id": sensor_id},
            {"$set": payload, "$setOnInsert": {"last_measurements": []}},
            upsert=True,
        )
        return await self.sensors.find_one(
            {"device_id": device_id, "sensor_id": sensor_id}
        )

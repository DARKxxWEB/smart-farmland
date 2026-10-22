import logging

from pymongo import ASCENDING, DESCENDING, AsyncMongoClient

from settings import MONGO_DB, MONGO_URI
from utils.catalog import DEFAULT_SENSORS

logger = logging.getLogger(__name__)

client: AsyncMongoClient | None = None
db = None


async def connect():
    global client, db
    if db is not None:
        return db
    client = AsyncMongoClient(MONGO_URI)
    db = client[MONGO_DB]
    await ensure_indexes(db)
    return db


async def close() -> None:
    global client, db
    if client is not None:
        await client.close()
    client, db = None, None


def get_db():
    if db is None:
        raise RuntimeError("MongoDB is not connected")
    return db


async def ensure_indexes(database) -> None:
    readings = database["readings"]
    sensors = database["sensors"]

    await readings.create_index(
        [("device_id", ASCENDING), ("sensor_id", ASCENDING), ("recorded_at", DESCENDING)],
        unique=True,
        name="uniq_device_sensor_time",
    )
    await readings.create_index(
        [("recorded_at", DESCENDING), ("_id", DESCENDING)],
        name="time_id_desc",
    )
    await readings.create_index(
        [("sensor_id", ASCENDING), ("recorded_at", DESCENDING)],
        name="sensor_time_desc",
    )
    await sensors.create_index(
        [("device_id", ASCENDING), ("sensor_id", ASCENDING)],
        unique=True,
        name="uniq_device_sensor",
    )
    logger.info("MongoDB indexes are ready")


async def seed_default_sensors(database) -> None:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    for sensor in DEFAULT_SENSORS:
        await database["sensors"].update_one(
            {"device_id": sensor["device_id"], "sensor_id": sensor["sensor_id"]},
            {
                "$setOnInsert": {
                    **sensor,
                    "last_recorded_at": None,
                    "last_measurements": [],
                    "updated_at": now,
                }
            },
            upsert=True,
        )
    logger.info("Default farmland sensors are present")

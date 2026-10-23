import logging

from pymongo import ASCENDING, DESCENDING, AsyncMongoClient

from settings import MONGO_DB, MONGO_URI

logger = logging.getLogger(__name__)

client: AsyncMongoClient | None = None
db = None


async def connect():
    global client, db
    if db is None:
        client = AsyncMongoClient(MONGO_URI)
        db = client[MONGO_DB]
        await db["device_tokens"].create_index(
            [("token", ASCENDING)], unique=True, name="uniq_device_token"
        )
        await db["notifications"].create_index(
            [("dedupe_key", ASCENDING)], unique=True, name="uniq_notification_dedupe"
        )
        await db["notifications"].create_index(
            [("user_id", ASCENDING), ("created_at", DESCENDING), ("_id", DESCENDING)],
            name="user_notifications",
        )
        await db["notifications"].create_index(
            [("user_id", ASCENDING), ("read_at", ASCENDING)],
            name="user_unread_notifications",
        )
        logger.info("Notification MongoDB indexes are ready")
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

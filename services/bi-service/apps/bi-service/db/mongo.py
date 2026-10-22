import logging

from pymongo import DESCENDING, AsyncMongoClient

from settings import MONGO_DB, MONGO_URI

logger = logging.getLogger(__name__)

client: AsyncMongoClient | None = None
db = None


async def connect():
    global client, db
    if db is not None:
        return db
    client = AsyncMongoClient(MONGO_URI)
    db = client[MONGO_DB]
    await db["reports"].create_index(
        [("generated_at", DESCENDING), ("_id", DESCENDING)],
        name="report_time_id_desc",
    )
    logger.info("BI MongoDB indexes are ready")
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

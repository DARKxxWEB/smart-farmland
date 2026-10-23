import asyncio
import base64
import binascii
import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import DESCENDING, ReturnDocument
from pymongo.errors import DuplicateKeyError

from db.mongo import get_db
from settings import DEFAULT_PAGE_SIZE, FIREBASE_CREDENTIALS_PATH, MAX_PAGE_SIZE

logger = logging.getLogger(__name__)


class NotificationError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _page_token(created_at: datetime, notification_id: ObjectId) -> str:
    payload = {"t": created_at.isoformat(), "id": str(notification_id)}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def _decode_page_token(token: str) -> tuple[datetime, ObjectId]:
    try:
        payload = json.loads(base64.urlsafe_b64decode(token.encode()).decode())
        created_at = datetime.fromisoformat(payload["t"])
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        return created_at.astimezone(timezone.utc), ObjectId(payload["id"])
    except (
        KeyError,
        ValueError,
        TypeError,
        binascii.Error,
        json.JSONDecodeError,
        InvalidId,
    ) as exc:
        raise NotificationError("invalid", "Invalid page token") from exc


class NotificationStore:
    async def register_device(self, user_id: str, token: str) -> None:
        now = datetime.now(timezone.utc)
        await get_db()["device_tokens"].update_one(
            {"token": token},
            {
                "$set": {"user_id": user_id, "updated_at": now},
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )

    async def remove_device(self, user_id: str, token: str) -> bool:
        result = await get_db()["device_tokens"].delete_one(
            {"user_id": user_id, "token": token}
        )
        return result.deleted_count > 0

    async def create(
        self,
        user_id: str,
        title: str,
        body: str,
        data: dict[str, str],
        source_id: str,
    ) -> tuple[dict, bool]:
        now = datetime.now(timezone.utc)
        seed = f"{user_id}:{source_id}" if source_id else f"{user_id}:{uuid.uuid4()}"
        dedupe_key = hashlib.sha256(seed.encode()).hexdigest()
        collection = get_db()["notifications"]
        doc = {
            "dedupe_key": dedupe_key,
            "user_id": user_id,
            "title": title,
            "body": body,
            "data": data,
            "delivery_status": "pending",
            "sent_count": 0,
            "failed_count": 0,
            "created_at": now,
            "read_at": None,
        }
        try:
            result = await collection.insert_one(doc)
        except DuplicateKeyError:
            doc = await collection.find_one({"dedupe_key": dedupe_key})
            if doc is None:
                raise
            return doc, False

        doc["_id"] = result.inserted_id
        return doc, True

    async def list_for_user(
        self, user_id: str, page_size: int, page_token: str, unread_only: bool
    ) -> tuple[list[dict], str, int]:
        size = page_size or DEFAULT_PAGE_SIZE
        if size < 1 or size > MAX_PAGE_SIZE:
            raise NotificationError(
                "invalid", f"page_size must be between 1 and {MAX_PAGE_SIZE}"
            )
        collection = get_db()["notifications"]
        base_query: dict = {"user_id": user_id}
        unread_query = {**base_query, "read_at": None}
        unread_count = await collection.count_documents(unread_query)
        query = unread_query if unread_only else base_query
        if page_token:
            created_at, oid = _decode_page_token(page_token)
            query = {
                **query,
                "$or": [
                    {"created_at": {"$lt": created_at}},
                    {"created_at": created_at, "_id": {"$lt": oid}},
                ],
            }
        docs = await (
            collection.find(query)
            .sort([("created_at", DESCENDING), ("_id", DESCENDING)])
            .limit(size + 1)
            .to_list(length=size + 1)
        )
        next_token = ""
        if len(docs) > size:
            docs.pop()
            last = docs[-1]
            next_token = _page_token(last["created_at"], last["_id"])
        return docs, next_token, unread_count

    async def mark_read(self, user_id: str, notification_id: str) -> dict:
        try:
            oid = ObjectId(notification_id)
        except InvalidId as exc:
            raise NotificationError("invalid", "Invalid notification id") from exc
        doc = await get_db()["notifications"].find_one_and_update(
            {"_id": oid, "user_id": user_id},
            {"$set": {"read_at": datetime.now(timezone.utc)}},
            return_document=ReturnDocument.AFTER,
        )
        if doc is None:
            raise NotificationError("not_found", "Notification not found")
        return doc


class FirebaseSender:
    def __init__(self) -> None:
        self.enabled = bool(FIREBASE_CREDENTIALS_PATH)
        if self.enabled:
            import firebase_admin
            from firebase_admin import credentials

            firebase_admin.initialize_app(
                credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            )

    async def send(
        self, token: str, title: str, body: str, data: dict[str, str]
    ) -> None:
        if not self.enabled:
            raise RuntimeError("Firebase FCM credentials are not configured")
        from firebase_admin import messaging

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data,
            token=token,
        )
        await asyncio.to_thread(messaging.send, message)


class NotificationService:
    def __init__(self, sender: FirebaseSender | None = None) -> None:
        self.store = NotificationStore()
        self.sender = sender or FirebaseSender()

    async def create(
        self,
        user_id: str,
        title: str,
        body: str,
        data: dict[str, str],
        source_id: str = "",
    ) -> tuple[dict, bool]:
        doc, inserted = await self.store.create(user_id, title, body, data, source_id)
        if not inserted:
            return doc, False

        tokens = await get_db()["device_tokens"].distinct("token", {"user_id": user_id})
        sent = failed = 0
        for token in tokens:
            try:
                await self.sender.send(token, title, body, data)
                sent += 1
            except Exception as exc:
                failed += 1
                logger.error(
                    "FCM delivery failed for notification %s (%s)",
                    doc["_id"],
                    type(exc).__name__,
                )
        if sent and not failed:
            status = "sent"
        elif sent:
            status = "partial"
        elif failed:
            status = "failed"
        else:
            status = "no_devices"
        await get_db()["notifications"].update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "delivery_status": status,
                    "sent_count": sent,
                    "failed_count": failed,
                }
            },
        )
        doc.update(
            delivery_status=status,
            sent_count=sent,
            failed_count=failed,
        )
        return doc, True

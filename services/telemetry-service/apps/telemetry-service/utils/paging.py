import base64
import json
from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId

from utils.time import ensure_utc


def encode_page_token(recorded_at: datetime, oid: ObjectId) -> str:
    payload = {"t": ensure_utc(recorded_at).isoformat(), "id": str(oid)}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def decode_page_token(token: str) -> tuple[datetime, ObjectId]:
    try:
        raw = json.loads(base64.urlsafe_b64decode(token.encode()).decode())
        recorded_at = ensure_utc(datetime.fromisoformat(raw["t"]))
        return recorded_at, ObjectId(raw["id"])
    except (KeyError, ValueError, json.JSONDecodeError, InvalidId) as e:
        raise ValueError("Invalid page token") from e

from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId

from db.mongo import get_db
from settings import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class ReportError(Exception):
    def __init__(self, message: str, code: str = "invalid") -> None:
        super().__init__(message)
        self.code = code


class ReportStore:
    def __init__(self) -> None:
        self.collection = get_db()["reports"]

    async def save(self, report: dict) -> dict:
        report = dict(report)
        report["generated_at"] = report.get("generated_at") or datetime.now(timezone.utc)
        result = await self.collection.insert_one(report)
        report["_id"] = result.inserted_id
        return report

    async def get(self, report_id: str) -> dict:
        try:
            oid = ObjectId(report_id)
        except InvalidId as e:
            raise ReportError("Invalid report id") from e
        doc = await self.collection.find_one({"_id": oid})
        if not doc:
            raise ReportError("Report not found", "not_found")
        return doc

    async def list_reports(self, page_size: int = 0, page_token: str = "") -> tuple[list[dict], str]:
        size = page_size or DEFAULT_PAGE_SIZE
        size = max(1, min(size, MAX_PAGE_SIZE))
        query = {}
        if page_token:
            try:
                query["_id"] = {"$lt": ObjectId(page_token)}
            except InvalidId as e:
                raise ReportError("Invalid page token") from e
        docs = (
            await self.collection.find(query)
            .sort([("generated_at", -1), ("_id", -1)])
            .limit(size + 1)
            .to_list(length=size + 1)
        )
        token = ""
        if len(docs) > size:
            token = str(docs[size - 1]["_id"])
            docs = docs[:size]
        return docs, token

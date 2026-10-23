import functools
import logging

import grpc
from google.protobuf.timestamp_pb2 import Timestamp

from notification.v1 import notification_pb2, notification_pb2_grpc
from services.notifications import NotificationError, NotificationService

logger = logging.getLogger(__name__)


def _notification_msg(doc: dict) -> notification_pb2.Notification:
    msg = notification_pb2.Notification(
        id=str(doc["_id"]),
        user_id=doc["user_id"],
        title=doc["title"],
        body=doc["body"],
        data=doc.get("data") or {},
        delivery_status=doc.get("delivery_status", ""),
        sent_count=doc.get("sent_count", 0),
        failed_count=doc.get("failed_count", 0),
    )
    for field in ("created_at", "read_at"):
        value = doc.get(field)
        if value is not None:
            timestamp = Timestamp()
            timestamp.FromDatetime(value)
            getattr(msg, field).CopyFrom(timestamp)
    return msg


def handle_errors(func):
    @functools.wraps(func)
    async def wrapper(self, request, context):
        try:
            return await func(self, request, context)
        except grpc.aio.AbortError:
            raise
        except NotificationError as exc:
            code = {
                "invalid": grpc.StatusCode.INVALID_ARGUMENT,
                "not_found": grpc.StatusCode.NOT_FOUND,
            }[exc.code]
            await context.abort(code, str(exc))
        except Exception:
            logger.exception("Unhandled error in %s", func.__name__)
            await context.abort(grpc.StatusCode.INTERNAL, "Internal server error")

    return wrapper


class NotificationServicer(notification_pb2_grpc.NotificationServiceServicer):
    def __init__(self) -> None:
        self.service = NotificationService()

    @handle_errors
    async def RegisterDevice(self, request, context):
        if not request.user_id or not request.token:
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT, "user_id and token are required"
            )
        await self.service.store.register_device(request.user_id, request.token)
        return notification_pb2.DeviceResponse(registered=True)

    @handle_errors
    async def RemoveDevice(self, request, context):
        if not request.user_id or not request.token:
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT, "user_id and token are required"
            )
        await self.service.store.remove_device(request.user_id, request.token)
        return notification_pb2.DeviceResponse(registered=False)

    @handle_errors
    async def CreateNotification(self, request, context):
        if not request.user_id or not request.title or not request.body:
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "user_id, title and body are required",
            )
        doc, created = await self.service.create(
            request.user_id,
            request.title,
            request.body,
            dict(request.data),
            request.source_id,
        )
        return notification_pb2.CreateNotificationResponse(
            notification=_notification_msg(doc),
            duplicate=not created,
            sent_count=doc.get("sent_count", 0),
            failed_count=doc.get("failed_count", 0),
        )

    @handle_errors
    async def ListNotifications(self, request, context):
        if not request.user_id:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "user_id is required")
        docs, next_token, unread_count = await self.service.store.list_for_user(
            request.user_id,
            request.page_size,
            request.page_token,
            request.unread_only,
        )
        return notification_pb2.ListNotificationsResponse(
            notifications=[_notification_msg(doc) for doc in docs],
            next_page_token=next_token,
            unread_count=unread_count,
        )

    @handle_errors
    async def MarkRead(self, request, context):
        if not request.user_id or not request.notification_id:
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "user_id and notification_id are required",
            )
        doc = await self.service.store.mark_read(
            request.user_id, request.notification_id
        )
        return _notification_msg(doc)

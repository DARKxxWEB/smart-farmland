import grpc
from fastapi import APIRouter, Query

from grpc_clients import clients
from notification.v1 import notification_pb2
from schema.notifications import DeviceTokenBody
from utils import proto_json
from utils.deps import ReadLimit, UserDep
from utils.errors import grpc_http_error

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.post("/devices")
async def register_device(body: DeviceTokenBody, user=UserDep):
    try:
        response = await clients.notification_stub.RegisterDevice(
            notification_pb2.RegisterDeviceRequest(
                user_id=user.user_id,
                token=body.token,
            )
        )
    except grpc.aio.AioRpcError as exc:
        raise grpc_http_error(exc) from exc
    return {"registered": response.registered}


@router.delete("/devices")
async def remove_device(body: DeviceTokenBody, user=UserDep):
    try:
        await clients.notification_stub.RemoveDevice(
            notification_pb2.RemoveDeviceRequest(
                user_id=user.user_id,
                token=body.token,
            )
        )
    except grpc.aio.AioRpcError as exc:
        raise grpc_http_error(exc) from exc
    return {"registered": False}


@router.get("")
async def list_notifications(
    user=UserDep,
    _limit=ReadLimit,
    page_size: int = Query(default=20, ge=1, le=100),
    page_token: str = "",
    unread_only: bool = False,
):
    try:
        response = await clients.notification_stub.ListNotifications(
            notification_pb2.ListNotificationsRequest(
                user_id=user.user_id,
                page_size=page_size,
                page_token=page_token,
                unread_only=unread_only,
            )
        )
    except grpc.aio.AioRpcError as exc:
        raise grpc_http_error(exc) from exc
    return {
        "items": [proto_json.notification(item) for item in response.notifications],
        "next_page_token": response.next_page_token,
        "unread_count": response.unread_count,
    }


@router.patch("/{notification_id}/read")
async def mark_read(notification_id: str, user=UserDep):
    try:
        response = await clients.notification_stub.MarkRead(
            notification_pb2.MarkReadRequest(
                user_id=user.user_id,
                notification_id=notification_id,
            )
        )
    except grpc.aio.AioRpcError as exc:
        raise grpc_http_error(exc) from exc
    return proto_json.notification(response)

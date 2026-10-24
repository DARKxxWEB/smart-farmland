from datetime import datetime
import logging

import grpc
from fastapi import APIRouter, Query, Request

from bi.v1 import bi_pb2
from grpc_clients import clients
from notification.v1 import notification_pb2
from schema._input import AssistantChatBody, GenerateReportBody
from utils import proto_json
from utils.deps import AiChatLimit, ReadLimit, UserDep
from utils.errors import grpc_http_error

router = APIRouter(prefix="/api/v1/bi", tags=["bi"])
logger = logging.getLogger(__name__)


def _query(
    device_id: str,
    sensor_id: str,
    from_time: datetime | None,
    to_time: datetime | None,
) -> bi_pb2.AnalyticsQuery:
    query = bi_pb2.AnalyticsQuery(device_id=device_id, sensor_id=sensor_id)
    proto_json.apply_timestamp(query.from_time, from_time)
    proto_json.apply_timestamp(query.to_time, to_time)
    return query


@router.post("/assistant/chat")
async def assistant_chat(body: AssistantChatBody, _u=UserDep, _l=AiChatLimit):
    grpc_request = bi_pb2.AssistantChatRequest(
        message=body.message,
        history=[
            bi_pb2.AssistantChatMessage(role=item.role, content=item.content)
            for item in body.history
        ],
    )
    try:
        response = await clients.bi_stub.ChatAssistant(grpc_request, timeout=55)
    except grpc.aio.AioRpcError as e:
        raise grpc_http_error(e) from e
    return {
        "answer": response.answer,
        "sources": list(response.sources),
        "model": response.model,
    }


@router.get("/summary")
async def summary(
    _u=UserDep,
    _l=ReadLimit,
    device_id: str = "",
    sensor_id: str = "",
    from_time: datetime | None = None,
    to_time: datetime | None = None,
):
    try:
        response = await clients.bi_stub.GetSummary(_query(device_id, sensor_id, from_time, to_time))
    except grpc.aio.AioRpcError as e:
        raise grpc_http_error(e) from e
    return proto_json.summary(response)


@router.get("/trends")
async def trends(
    _u=UserDep,
    _l=ReadLimit,
    device_id: str = "",
    sensor_id: str = "",
    metric: str = "",
    interval: str = "hour",
    from_time: datetime | None = None,
    to_time: datetime | None = None,
):
    request = bi_pb2.TrendsRequest(
        query=_query(device_id, sensor_id, from_time, to_time),
        interval=interval,
        metric=metric,
    )
    try:
        response = await clients.bi_stub.GetTrends(request)
    except grpc.aio.AioRpcError as e:
        raise grpc_http_error(e) from e
    return {
        "interval": response.interval,
        "series": [proto_json.trend(item) for item in response.series],
    }


@router.get("/alerts")
async def alerts(
    user=UserDep,
    _l=ReadLimit,
    device_id: str = "",
    sensor_id: str = "",
    from_time: datetime | None = None,
    to_time: datetime | None = None,
):
    try:
        response = await clients.bi_stub.GetAlerts(_query(device_id, sensor_id, from_time, to_time))
    except grpc.aio.AioRpcError as e:
        raise grpc_http_error(e) from e
    for alert in response.alerts:
        if not alert.id:
            continue
        try:
            await clients.notification_stub.CreateNotification(
                notification_pb2.CreateNotificationRequest(
                    user_id=user.user_id,
                    title=f"{alert.severity.title()} farm alert",
                    body=alert.message,
                    source_id=alert.id,
                    data={
                        "type": "bi_alert",
                        "alert_id": alert.id,
                        "severity": alert.severity,
                        "device_id": alert.device_id,
                        "sensor_id": alert.sensor_id,
                    },
                )
            )
        except grpc.aio.AioRpcError as exc:
            logger.warning(
                "Could not publish BI alert %s as a notification: %s",
                alert.id,
                exc.details(),
            )
    return {"items": [proto_json.alert(item) for item in response.alerts]}


@router.post("/reports")
async def generate_report(body: GenerateReportBody, request: Request, user=UserDep):
    grpc_request = bi_pb2.GenerateReportRequest(
        title=body.title,
        generated_by=user.username,
        interval=body.interval,
        query=_query(body.device_id, body.sensor_id, body.from_time, body.to_time),
    )
    try:
        response = await clients.bi_stub.GenerateReport(grpc_request)
    except grpc.aio.AioRpcError as e:
        raise grpc_http_error(e) from e
    return proto_json.report(response)


@router.get("/reports")
async def list_reports(
    _u=UserDep,
    _l=ReadLimit,
    page_size: int = Query(default=20, ge=1, le=100),
    page_token: str = "",
):
    try:
        response = await clients.bi_stub.ListReports(
            bi_pb2.ListReportsRequest(page_size=page_size, page_token=page_token)
        )
    except grpc.aio.AioRpcError as e:
        raise grpc_http_error(e) from e
    return {
        "items": [proto_json.report(item, include_details=False) for item in response.reports],
        "next_page_token": response.next_page_token,
    }


@router.get("/reports/{report_id}")
async def get_report(report_id: str, _u=UserDep, _l=ReadLimit):
    try:
        response = await clients.bi_stub.GetReport(bi_pb2.GetReportRequest(id=report_id))
    except grpc.aio.AioRpcError as e:
        raise grpc_http_error(e) from e
    return proto_json.report(response)

import functools
import logging

import grpc

from bi.v1 import bi_pb2, bi_pb2_grpc
from services.bi import BIService
from services.reports import ReportError, ReportStore
from utils.time import from_timestamp, to_timestamp

logger = logging.getLogger(__name__)


def handle_errors(func):
    @functools.wraps(func)
    async def wrapper(self, request, context):
        try:
            return await func(self, request, context)
        except grpc.aio.AbortError:
            raise
        except ReportError as e:
            code = grpc.StatusCode.NOT_FOUND if e.code == "not_found" else grpc.StatusCode.INVALID_ARGUMENT
            await context.abort(code, str(e))
        except ValueError as e:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
        except Exception:
            logger.exception("Unhandled error in %s", func.__name__)
            await context.abort(grpc.StatusCode.INTERNAL, "Internal server error")

    return wrapper


def _copy_ts(target, value):
    ts = to_timestamp(value)
    if ts:
        target.CopyFrom(ts)


def _metric_stats_msg(item: dict) -> bi_pb2.MetricStats:
    return bi_pb2.MetricStats(
        metric=item["metric"],
        unit=item.get("unit", ""),
        count=int(item.get("count") or 0),
        min=float(item.get("min") or 0),
        max=float(item.get("max") or 0),
        avg=float(item.get("avg") or 0),
        last=float(item.get("last") or 0),
    )


def _sensor_stats_msg(item: dict) -> bi_pb2.SensorStats:
    msg = bi_pb2.SensorStats(
        sensor_id=item["sensor_id"],
        device_id=item.get("device_id", ""),
        kind=item.get("kind", ""),
        metrics=[_metric_stats_msg(m) for m in item.get("metrics") or []],
    )
    _copy_ts(msg.last_recorded_at, item.get("last_recorded_at"))
    return msg


def _trend_msg(item: dict) -> bi_pb2.MetricTrend:
    points = []
    for point in item.get("points") or []:
        p = bi_pb2.TrendPoint(
            avg=point["avg"],
            min=point["min"],
            max=point["max"],
            count=int(point["count"]),
        )
        _copy_ts(p.bucket_start, point.get("bucket_start"))
        points.append(p)
    return bi_pb2.MetricTrend(
        sensor_id=item["sensor_id"],
        metric=item["metric"],
        unit=item.get("unit", ""),
        points=points,
    )


def _alert_msg(item: dict) -> bi_pb2.Alert:
    msg = bi_pb2.Alert(
        id=item.get("id", ""),
        type=item.get("type", ""),
        severity=item.get("severity", ""),
        sensor_id=item.get("sensor_id", ""),
        device_id=item.get("device_id", ""),
        metric=item.get("metric", ""),
        value=float(item.get("value") or 0),
        threshold=float(item.get("threshold") or 0),
        comparator=item.get("comparator", ""),
        message=item.get("message", ""),
    )
    _copy_ts(msg.recorded_at, item.get("recorded_at"))
    return msg


def _summary_msg(analyzer) -> bi_pb2.SummaryResponse:
    stats = analyzer.sensor_stats()
    msg = bi_pb2.SummaryResponse(
        reading_count=analyzer.reading_count,
        sensor_count=len(stats),
        alert_count=len(analyzer.alerts),
        sensors=[_sensor_stats_msg(item) for item in stats],
    )
    _copy_ts(msg.from_time, getattr(analyzer, "from_time", None))
    _copy_ts(msg.to_time, getattr(analyzer, "to_time", None))
    return msg


def _summary_from_doc(doc: dict) -> bi_pb2.SummaryResponse:
    summary = doc.get("summary") or {}
    msg = bi_pb2.SummaryResponse(
        reading_count=int(summary.get("reading_count") or 0),
        sensor_count=int(summary.get("sensor_count") or 0),
        alert_count=int(summary.get("alert_count") or 0),
        sensors=[_sensor_stats_msg(item) for item in summary.get("sensors") or []],
    )
    _copy_ts(msg.from_time, summary.get("from_time") or doc.get("from_time"))
    _copy_ts(msg.to_time, summary.get("to_time") or doc.get("to_time"))
    return msg


def _report_msg(doc: dict, include_details: bool = True) -> bi_pb2.Report:
    msg = bi_pb2.Report(
        id=str(doc["_id"]),
        title=doc.get("title", ""),
        generated_by=doc.get("generated_by", ""),
        summary=_summary_from_doc(doc),
    )
    _copy_ts(msg.generated_at, doc.get("generated_at"))
    _copy_ts(msg.from_time, doc.get("from_time"))
    _copy_ts(msg.to_time, doc.get("to_time"))
    if include_details:
        msg.sensor_stats.extend(_sensor_stats_msg(s) for s in doc.get("sensor_stats") or [])
        msg.trends.extend(_trend_msg(t) for t in doc.get("trends") or [])
        msg.alerts.extend(_alert_msg(a) for a in doc.get("alerts") or [])
        msg.sections.extend(
            bi_pb2.ReportSection(title=s.get("title", ""), body=s.get("body", ""))
            for s in doc.get("sections") or []
        )
    return msg


class BIServicer(bi_pb2_grpc.BIServiceServicer):
    def __init__(self) -> None:
        self.service = BIService()

    def _query_args(self, query):
        return dict(
            device_id=query.device_id,
            sensor_id=query.sensor_id,
            from_time=from_timestamp(query.from_time),
            to_time=from_timestamp(query.to_time),
        )

    @handle_errors
    async def GetSummary(self, request, context):
        analyzer = await self.service.analyze(**self._query_args(request))
        return _summary_msg(analyzer)

    @handle_errors
    async def GetTrends(self, request, context):
        analyzer = await self.service.analyze(
            **self._query_args(request.query),
            interval=request.interval,
            metric=request.metric,
            include_silence=False,
        )
        return bi_pb2.TrendsResponse(
            interval=analyzer.interval,
            series=[_trend_msg(item) for item in analyzer.trends()],
        )

    @handle_errors
    async def GetSensorStats(self, request, context):
        analyzer = await self.service.analyze(**self._query_args(request), include_silence=False)
        return bi_pb2.SensorStatsResponse(
            sensors=[_sensor_stats_msg(item) for item in analyzer.sensor_stats()]
        )

    @handle_errors
    async def GetAlerts(self, request, context):
        analyzer = await self.service.analyze(**self._query_args(request))
        return bi_pb2.AlertsResponse(alerts=[_alert_msg(item) for item in analyzer.alerts])

    @handle_errors
    async def GenerateReport(self, request, context):
        doc = await self.service.generate_report(
            title=request.title,
            generated_by=request.generated_by,
            interval=request.interval,
            **self._query_args(request.query),
        )
        return _report_msg(doc)

    @handle_errors
    async def GetReport(self, request, context):
        return _report_msg(await ReportStore().get(request.id))

    @handle_errors
    async def ListReports(self, request, context):
        docs, token = await ReportStore().list_reports(request.page_size, request.page_token)
        return bi_pb2.ListReportsResponse(
            reports=[_report_msg(doc, include_details=False) for doc in docs],
            next_page_token=token,
        )

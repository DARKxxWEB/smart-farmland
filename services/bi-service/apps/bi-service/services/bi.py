from datetime import datetime, timedelta, timezone

from grpc_clients import telemetry as telemetry_client
from services.analyzer import Analyzer
from services.reports import ReportStore
from settings import DEFAULT_INTERVAL, SILENCE_MINUTES
from utils.time import from_timestamp


class BIService:
    async def analyze(
        self,
        device_id: str = "",
        sensor_id: str = "",
        from_time: datetime | None = None,
        to_time: datetime | None = None,
        interval: str = DEFAULT_INTERVAL,
        metric: str = "",
        include_silence: bool = True,
    ) -> Analyzer:
        now = datetime.now(timezone.utc)
        to_time = to_time or now
        from_time = from_time or (to_time - timedelta(days=1))
        analyzer = Analyzer(interval=interval, metric_filter=metric)
        async for reading in telemetry_client.stream_readings(
            device_id=device_id,
            sensor_id=sensor_id,
            from_time=from_time,
            to_time=to_time,
            metric=metric,
        ):
            analyzer.add_reading(reading)
        if include_silence:
            sensors = await telemetry_client.list_sensors(device_id)
            analyzer.add_silence_alerts(sensors, now=now)
        analyzer.from_time = from_time
        analyzer.to_time = to_time
        return analyzer

    async def generate_report(
        self,
        title: str,
        generated_by: str,
        device_id: str = "",
        sensor_id: str = "",
        from_time: datetime | None = None,
        to_time: datetime | None = None,
        interval: str = DEFAULT_INTERVAL,
    ) -> dict:
        analyzer = await self.analyze(
            device_id, sensor_id, from_time, to_time, interval
        )
        stats = analyzer.sensor_stats()
        trends = analyzer.trends()
        alerts = analyzer.alerts
        sections = [
            {
                "title": "Overview",
                "body": (
                    f"{analyzer.reading_count} readings from {len(stats)} sensors "
                    f"produced {len(alerts)} alerts."
                ),
            },
            {
                "title": "Silence window",
                "body": f"Sensors are flagged silent after {SILENCE_MINUTES} minutes.",
            },
        ]
        doc = {
            "title": title or "Farmland report",
            "generated_by": generated_by or "system",
            "generated_at": datetime.now(timezone.utc),
            "from_time": analyzer.from_time,
            "to_time": analyzer.to_time,
            "interval": analyzer.interval,
            "summary": {
                "reading_count": analyzer.reading_count,
                "sensor_count": len(stats),
                "alert_count": len(alerts),
                "from_time": analyzer.from_time,
                "to_time": analyzer.to_time,
                "sensors": stats,
            },
            "sensor_stats": stats,
            "trends": trends,
            "alerts": alerts,
            "sections": sections,
        }
        return await ReportStore().save(doc)

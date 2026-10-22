from collections import defaultdict
from datetime import datetime, timedelta, timezone
from math import inf

from settings import DEFAULT_INTERVAL, SILENCE_MINUTES
from utils.thresholds import THRESHOLDS
from utils.time import from_timestamp


def _bucket_start(dt: datetime, interval: str) -> datetime:
    dt = dt.astimezone(timezone.utc)
    if interval == "day":
        return datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc)
    return datetime(dt.year, dt.month, dt.day, dt.hour, tzinfo=timezone.utc)


def _kind_for(sensor_id: str, metrics: set[str]) -> str:
    if sensor_id.startswith("M"):
        return "moisture"
    if "NPK" in sensor_id.upper() or any(
        m in metrics for m in ("nitrogen_mgkg", "phosphorus_mgkg", "potassium_mgkg")
    ):
        return "npk"
    return "unknown"


class Analyzer:
    def __init__(self, interval: str = DEFAULT_INTERVAL, metric_filter: str = "") -> None:
        self.interval = interval if interval in {"hour", "day"} else DEFAULT_INTERVAL
        self.metric_filter = metric_filter
        self.reading_count = 0
        self.stats = defaultdict(
            lambda: {
                "device_id": "",
                "metrics": defaultdict(
                    lambda: {
                        "count": 0,
                        "min": inf,
                        "max": -inf,
                        "sum": 0.0,
                        "last": 0.0,
                        "unit": "",
                    }
                ),
                "last_recorded_at": None,
            }
        )
        self.buckets = defaultdict(
            lambda: {"count": 0, "min": inf, "max": -inf, "sum": 0.0, "unit": ""}
        )
        self.alerts: list[dict] = []

    def _add_threshold_alert(self, sensor_id, device_id, metric, value, recorded_at):
        spec = THRESHOLDS.get(metric)
        if not spec:
            return
        if value < spec["low"]:
            self.alerts.append(
                {
                    "id": f"thr-{sensor_id}-{metric}-low-{int(recorded_at.timestamp())}",
                    "type": "threshold",
                    "severity": "critical" if value < spec["low"] * 0.75 else "warning",
                    "sensor_id": sensor_id,
                    "device_id": device_id,
                    "metric": metric,
                    "value": value,
                    "threshold": spec["low"],
                    "comparator": "lt",
                    "message": f"{sensor_id} {metric} {value:.2f} is below {spec['low']}",
                    "recorded_at": recorded_at,
                }
            )
        elif value > spec["high"]:
            self.alerts.append(
                {
                    "id": f"thr-{sensor_id}-{metric}-high-{int(recorded_at.timestamp())}",
                    "type": "threshold",
                    "severity": "critical" if value > spec["high"] * 1.15 else "warning",
                    "sensor_id": sensor_id,
                    "device_id": device_id,
                    "metric": metric,
                    "value": value,
                    "threshold": spec["high"],
                    "comparator": "gt",
                    "message": f"{sensor_id} {metric} {value:.2f} is above {spec['high']}",
                    "recorded_at": recorded_at,
                }
            )

    def add_reading(self, reading) -> None:
        recorded_at = from_timestamp(reading.recorded_at)
        if recorded_at is None:
            return
        self.reading_count += 1
        key = (reading.device_id, reading.sensor_id)
        sensor = self.stats[key]
        sensor["device_id"] = reading.device_id
        if sensor["last_recorded_at"] is None or recorded_at > sensor["last_recorded_at"]:
            sensor["last_recorded_at"] = recorded_at

        for measurement in reading.measurements:
            if self.metric_filter and measurement.metric != self.metric_filter:
                continue
            metric_stats = sensor["metrics"][measurement.metric]
            metric_stats["count"] += 1
            metric_stats["min"] = min(metric_stats["min"], measurement.value)
            metric_stats["max"] = max(metric_stats["max"], measurement.value)
            metric_stats["sum"] += measurement.value
            metric_stats["last"] = measurement.value
            metric_stats["unit"] = measurement.unit
            bucket_key = (
                reading.sensor_id,
                measurement.metric,
                _bucket_start(recorded_at, self.interval),
            )
            bucket = self.buckets[bucket_key]
            bucket["count"] += 1
            bucket["min"] = min(bucket["min"], measurement.value)
            bucket["max"] = max(bucket["max"], measurement.value)
            bucket["sum"] += measurement.value
            bucket["unit"] = measurement.unit
            self._add_threshold_alert(
                reading.sensor_id,
                reading.device_id,
                measurement.metric,
                measurement.value,
                recorded_at,
            )

    def add_silence_alerts(self, sensors, now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=SILENCE_MINUTES)
        for sensor in sensors:
            last = from_timestamp(sensor.last_recorded_at)
            key = (sensor.device_id, sensor.sensor_id)
            if key in self.stats:
                last = self.stats[key]["last_recorded_at"] or last
            if last is None or last < cutoff:
                self.alerts.append(
                    {
                        "id": f"silence-{sensor.sensor_id}",
                        "type": "silence",
                        "severity": "warning",
                        "sensor_id": sensor.sensor_id,
                        "device_id": sensor.device_id,
                        "metric": "",
                        "value": 0.0,
                        "threshold": float(SILENCE_MINUTES),
                        "comparator": "stale",
                        "message": (
                            f"{sensor.sensor_id} has not reported within "
                            f"{SILENCE_MINUTES} minutes"
                        ),
                        "recorded_at": last,
                    }
                )

    def sensor_stats(self) -> list[dict]:
        result = []
        for (device_id, sensor_id), payload in sorted(self.stats.items()):
            metrics = []
            for metric, stats in sorted(payload["metrics"].items()):
                metrics.append(
                    {
                        "metric": metric,
                        "unit": stats["unit"],
                        "count": stats["count"],
                        "min": stats["min"] if stats["count"] else 0,
                        "max": stats["max"] if stats["count"] else 0,
                        "avg": (stats["sum"] / stats["count"]) if stats["count"] else 0,
                        "last": stats["last"],
                    }
                )
            result.append(
                {
                    "sensor_id": sensor_id,
                    "device_id": device_id,
                    "kind": _kind_for(sensor_id, set(payload["metrics"])),
                    "metrics": metrics,
                    "last_recorded_at": payload["last_recorded_at"],
                }
            )
        return result

    def trends(self) -> list[dict]:
        grouped = defaultdict(list)
        for (sensor_id, metric, start), bucket in self.buckets.items():
            grouped[(sensor_id, metric, bucket["unit"])].append(
                {
                    "bucket_start": start,
                    "avg": bucket["sum"] / bucket["count"] if bucket["count"] else 0,
                    "min": bucket["min"] if bucket["count"] else 0,
                    "max": bucket["max"] if bucket["count"] else 0,
                    "count": bucket["count"],
                }
            )
        series = []
        for (sensor_id, metric, unit), points in sorted(grouped.items()):
            series.append(
                {
                    "sensor_id": sensor_id,
                    "metric": metric,
                    "unit": unit,
                    "points": sorted(points, key=lambda p: p["bucket_start"]),
                }
            )
        return series

from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator, model_validator

from utils.catalog import ALLOWED_METRICS, ALLOWED_SOURCES
from utils.time import ensure_utc


class MeasurementInput(BaseModel):
    metric: str
    value: float
    unit: str = ""

    @field_validator("metric")
    @classmethod
    def validate_metric(cls, v: str) -> str:
        metric = v.strip()
        if metric not in ALLOWED_METRICS:
            raise ValueError(f"Unsupported metric: {v}")
        return metric

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: float) -> float:
        if v != v or v in (float("inf"), float("-inf")):
            raise ValueError("Measurement value must be finite")
        return v

    @model_validator(mode="after")
    def validate_range_and_unit(self):
        spec = ALLOWED_METRICS[self.metric]
        if self.value < spec["min"] or self.value > spec["max"]:
            raise ValueError(
                f"{self.metric} must be between {spec['min']} and {spec['max']}"
            )
        if not self.unit:
            self.unit = spec["unit"]
        return self


class ReadingInputModel(BaseModel):
    device_id: str
    sensor_id: str
    recorded_at: datetime
    measurements: list[MeasurementInput] = Field(min_length=1)
    source: str = "gateway"

    @field_validator("device_id", "sensor_id")
    @classmethod
    def nonempty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("id cannot be empty")
        return v

    @field_validator("recorded_at")
    @classmethod
    def validate_recorded_at(cls, v: datetime) -> datetime:
        return ensure_utc(v)

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        source = (v or "gateway").strip() or "gateway"
        if source not in ALLOWED_SOURCES:
            raise ValueError(f"Unsupported source: {v}")
        return source

    def reject_future(self, skew_seconds: int) -> None:
        now = datetime.now(timezone.utc)
        if (self.recorded_at - now).total_seconds() > skew_seconds:
            raise ValueError("recorded_at is too far in the future")

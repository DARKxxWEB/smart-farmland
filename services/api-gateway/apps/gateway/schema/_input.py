from datetime import datetime

from pydantic import BaseModel, Field


class LoginBody(BaseModel):
    username: str
    password: str


class RefreshBody(BaseModel):
    refresh_token: str


class LogoutBody(BaseModel):
    refresh_token: str


class ChangePasswordBody(BaseModel):
    old_password: str
    new_password: str


class MeasurementBody(BaseModel):
    metric: str
    value: float
    unit: str = ""


class ReadingBody(BaseModel):
    device_id: str
    sensor_id: str
    recorded_at: datetime
    measurements: list[MeasurementBody] = Field(min_length=1)
    source: str = "gateway"


class BatchReadingsBody(BaseModel):
    readings: list[ReadingBody] = Field(min_length=1)


class SensorBody(BaseModel):
    sensor_id: str
    device_id: str
    kind: str = "unknown"
    x: float | None = None
    y: float | None = None
    unit: str = "m"


class GenerateReportBody(BaseModel):
    title: str = "Farmland report"
    device_id: str = ""
    sensor_id: str = ""
    from_time: datetime | None = None
    to_time: datetime | None = None
    interval: str = "hour"

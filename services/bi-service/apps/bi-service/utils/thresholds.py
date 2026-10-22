from settings import (
    MOISTURE_HIGH,
    MOISTURE_LOW,
    NITROGEN_HIGH,
    NITROGEN_LOW,
    PHOSPHORUS_HIGH,
    PHOSPHORUS_LOW,
    POTASSIUM_HIGH,
    POTASSIUM_LOW,
    TEMPERATURE_HIGH,
    TEMPERATURE_LOW,
)

THRESHOLDS = {
    "moisture_pct": {"low": MOISTURE_LOW, "high": MOISTURE_HIGH, "unit": "percent"},
    "nitrogen_mgkg": {"low": NITROGEN_LOW, "high": NITROGEN_HIGH, "unit": "mg/kg"},
    "phosphorus_mgkg": {"low": PHOSPHORUS_LOW, "high": PHOSPHORUS_HIGH, "unit": "mg/kg"},
    "potassium_mgkg": {"low": POTASSIUM_LOW, "high": POTASSIUM_HIGH, "unit": "mg/kg"},
    "temperature_c": {"low": TEMPERATURE_LOW, "high": TEMPERATURE_HIGH, "unit": "celsius"},
}

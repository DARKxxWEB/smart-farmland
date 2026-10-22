DEVICE_ID = "E1"

ALLOWED_METRICS = {
    "moisture_pct": {"unit": "percent", "min": 0.0, "max": 100.0},
    "nitrogen_mgkg": {"unit": "mg/kg", "min": 0.0, "max": 1000.0},
    "phosphorus_mgkg": {"unit": "mg/kg", "min": 0.0, "max": 1000.0},
    "potassium_mgkg": {"unit": "mg/kg", "min": 0.0, "max": 2000.0},
    "temperature_c": {"unit": "celsius", "min": -20.0, "max": 60.0},
}

ALLOWED_SOURCES = {"csv_import", "device", "gateway"}

DEFAULT_SENSORS = (
    {
        "sensor_id": "M1",
        "device_id": DEVICE_ID,
        "kind": "moisture",
        "location": {"x": 2.5, "y": 2.5, "unit": "m"},
    },
    {
        "sensor_id": "M2",
        "device_id": DEVICE_ID,
        "kind": "moisture",
        "location": {"x": 7.5, "y": 2.5, "unit": "m"},
    },
    {
        "sensor_id": "M3",
        "device_id": DEVICE_ID,
        "kind": "moisture",
        "location": {"x": 2.5, "y": 7.5, "unit": "m"},
    },
    {
        "sensor_id": "M4",
        "device_id": DEVICE_ID,
        "kind": "moisture",
        "location": {"x": 7.5, "y": 7.5, "unit": "m"},
    },
    {
        "sensor_id": "NPK-1",
        "device_id": DEVICE_ID,
        "kind": "npk",
        "location": {"x": 3.5, "y": 5.5, "unit": "m"},
    },
)

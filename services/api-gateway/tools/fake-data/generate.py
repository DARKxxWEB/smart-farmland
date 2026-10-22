#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEVICE_ID = "E1"
MOISTURE_SENSORS = {
    "M1": (2.5, 2.5, 0.0),
    "M2": (7.5, 2.5, 1.8),
    "M3": (2.5, 7.5, -1.2),
    "M4": (7.5, 7.5, 0.7),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=3)
    parser.add_argument("--interval-minutes", type=int, default=15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("readings.csv"),
    )
    return parser.parse_args()


def moisture(base: float, hour: float, offset: float, rng: random.Random) -> float:
    diurnal = 8.0 * math.sin((hour - 6.0) / 24.0 * 2 * math.pi)
    value = base + offset + diurnal + rng.uniform(-2.2, 2.2)
    return round(min(95.0, max(8.0, value)), 2)


def npk(hour: float, rng: random.Random) -> tuple[float, float, float]:
    nitrogen = 42 + 6 * math.sin(hour / 24 * 2 * math.pi) + rng.uniform(-3, 3)
    phosphorus = 22 + rng.uniform(-2, 2)
    potassium = 160 + 10 * math.cos(hour / 36 * 2 * math.pi) + rng.uniform(-8, 8)
    return round(nitrogen, 2), round(phosphorus, 2), round(potassium, 2)


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(days=args.days)
    step = timedelta(minutes=args.interval_minutes)

    rows: list[dict] = []
    current = start
    while current <= end:
        hour = current.hour + current.minute / 60
        iso = current.strftime("%Y-%m-%dT%H:%M:%SZ")
        for sensor_id, (_x, _y, offset) in MOISTURE_SENSORS.items():
            if sensor_id == "M3" and current.hour in {3, 4} and current.minute == 0:
                continue
            value = moisture(34.0, hour, offset, rng)
            if sensor_id == "M1" and current.hour == 14 and current.minute == 0:
                value = 16.4
            rows.append(
                {
                    "device_id": DEVICE_ID,
                    "sensor_id": sensor_id,
                    "recorded_at": iso,
                    "moisture_pct": value,
                    "nitrogen_mgkg": "",
                    "phosphorus_mgkg": "",
                    "potassium_mgkg": "",
                    "temperature_c": round(18 + 7 * math.sin((hour - 8) / 24 * 2 * math.pi) + rng.uniform(-0.4, 0.4), 2),
                    "source": "csv_import",
                }
            )
        if current.minute in {0, 30}:
            nitrogen, phosphorus, potassium = npk(hour, rng)
            if current.hour == 11 and current.minute == 0:
                nitrogen = 14.0
            rows.append(
                {
                    "device_id": DEVICE_ID,
                    "sensor_id": "NPK-1",
                    "recorded_at": iso,
                    "moisture_pct": "",
                    "nitrogen_mgkg": nitrogen,
                    "phosphorus_mgkg": phosphorus,
                    "potassium_mgkg": potassium,
                    "temperature_c": "",
                    "source": "csv_import",
                }
            )
        current += step

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "device_id",
                "sensor_id",
                "recorded_at",
                "moisture_pct",
                "nitrogen_mgkg",
                "phosphorus_mgkg",
                "potassium_mgkg",
                "temperature_c",
                "source",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} readings to {args.output}")


if __name__ == "__main__":
    main()

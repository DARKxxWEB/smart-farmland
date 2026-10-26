#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

METRIC_COLUMNS = {
    "moisture_pct": "percent",
    "nitrogen_mgkg": "mg/kg",
    "phosphorus_mgkg": "mg/kg",
    "potassium_mgkg": "mg/kg",
    "temperature_c": "celsius",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--file",
        type=Path,
        default=Path(__file__).with_name("readings.csv"),
    )
    parser.add_argument("--gateway", default=os.getenv("GATEWAY_URL", "http://localhost:8000"))
    parser.add_argument("--username", default=os.getenv("IMPORT_USERNAME", "admin"))
    parser.add_argument("--password", default=os.getenv("IMPORT_PASSWORD", ""))
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument(
        "--shift-to-now",
        action="store_true",
        help="Shift all reading timestamps so the latest sample is imported now.",
    )
    return parser.parse_args()


def row_to_reading(row: dict) -> dict | None:
    measurements = []
    for metric, unit in METRIC_COLUMNS.items():
        raw = (row.get(metric) or "").strip()
        if raw == "":
            continue
        measurements.append({"metric": metric, "value": float(raw), "unit": unit})
    if not measurements:
        return None
    return {
        "device_id": row["device_id"].strip(),
        "sensor_id": row["sensor_id"].strip(),
        "recorded_at": row["recorded_at"].strip(),
        "measurements": measurements,
        "source": (row.get("source") or "csv_import").strip() or "csv_import",
    }


def shift_readings_to_now(readings: list[dict]) -> None:
    timestamps = [
        datetime.fromisoformat(item["recorded_at"].replace("Z", "+00:00"))
        for item in readings
    ]
    if not timestamps:
        return
    latest = max(
        timestamp.replace(tzinfo=timezone.utc)
        if timestamp.tzinfo is None
        else timestamp.astimezone(timezone.utc)
        for timestamp in timestamps
    )
    offset = datetime.now(timezone.utc) - latest
    for item, timestamp in zip(readings, timestamps):
        timestamp = (
            timestamp.replace(tzinfo=timezone.utc)
            if timestamp.tzinfo is None
            else timestamp.astimezone(timezone.utc)
        )
        item["recorded_at"] = (timestamp + offset).isoformat().replace("+00:00", "Z")


def login(client: httpx.Client, gateway: str, username: str, password: str) -> str:
    response = client.post(
        f"{gateway}/api/v1/auth/login",
        json={"username": username, "password": password},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def post_batch(client: httpx.Client, url: str, headers: dict, batch: list[dict], retries: int) -> dict:
    delay = 1.0
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = client.post(
                url,
                json={"readings": batch},
                headers=headers,
                timeout=30,
            )
            if response.status_code in {429, 503, 504}:
                raise httpx.HTTPStatusError("retryable", request=response.request, response=response)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, httpx.HTTPStatusError) as exc:
            last_error = exc
            if attempt == retries:
                break
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"Batch import failed after {retries} attempts: {last_error}")


def main() -> None:
    args = parse_args()
    if not args.password:
        print("IMPORT_PASSWORD or --password is required", file=sys.stderr)
        sys.exit(1)
    if not args.file.exists():
        print(f"CSV file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    readings: list[dict] = []
    with args.file.open() as handle:
        for row in csv.DictReader(handle):
            reading = row_to_reading(row)
            if reading:
                readings.append(reading)

    if args.shift_to_now:
        shift_readings_to_now(readings)

    url = f"{args.gateway.rstrip('/')}/api/v1/telemetry/readings/batch"
    accepted = duplicates = rejected = 0
    with httpx.Client() as client:
        token = login(client, args.gateway.rstrip("/"), args.username, args.password)
        headers = {"Authorization": f"Bearer {token}"}
        for start in range(0, len(readings), args.batch_size):
            batch = readings[start : start + args.batch_size]
            result = post_batch(client, url, headers, batch, args.retries)
            accepted += int(result.get("accepted") or 0)
            duplicates += int(result.get("duplicates") or 0)
            rejected += int(result.get("rejected") or 0)
            print(
                f"batch {start // args.batch_size + 1}: "
                f"accepted={result.get('accepted')} duplicates={result.get('duplicates')} "
                f"rejected={result.get('rejected')}"
            )
    print(
        f"Imported {len(readings)} rows "
        f"(accepted={accepted}, duplicates={duplicates}, rejected={rejected})"
    )


if __name__ == "__main__":
    main()

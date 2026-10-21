#!/usr/bin/env python3
"""Exercise the local auth -> gateway -> telemetry -> BI request path."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from getpass import getpass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4


def request_json(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: dict | None = None,
    access_token: str = "",
) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(request, timeout=10) as response:
            body = response.read()
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"{method} {path} returned HTTP {error.code}: {detail}"
        ) from error
    except URLError as error:
        raise RuntimeError(f"Cannot reach {base_url}: {error.reason}") from error
    return json.loads(body) if body else {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=os.getenv("GATEWAY_URL", "http://localhost:8000"),
    )
    parser.add_argument("--username", default=os.getenv("ADMIN_USERNAME", "admin"))
    args = parser.parse_args()

    base_url = args.base_url
    username = args.username
    password = os.getenv("ADMIN_PASSWORD") or getpass("Admin password: ")
    if not password:
        raise RuntimeError("Set ADMIN_PASSWORD or enter the admin password")

    health = request_json(base_url, "/health")
    if health.get("status") != "ok":
        raise RuntimeError(f"Gateway liveness check failed: {health}")

    readiness = request_json(base_url, "/ready")
    if readiness.get("status") != "ok" or not all(
        (readiness.get("services") or {}).values()
    ):
        raise RuntimeError(f"Backend readiness check failed: {readiness}")
    print("PASS: gateway and backend services are ready")

    tokens = request_json(
        base_url,
        "/api/v1/auth/login",
        method="POST",
        payload={"username": username, "password": password},
    )
    access_token = tokens.get("access_token")
    if not access_token:
        raise RuntimeError("Login response did not contain an access token")

    profile = request_json(
        base_url, "/api/v1/auth/me", access_token=access_token
    )
    if profile.get("username") != username:
        raise RuntimeError("Authenticated profile does not match the admin user")
    print("PASS: admin authentication and profile lookup")

    device_id = f"smoke-{uuid4().hex[:12]}"
    sensor_id = "M-SMOKE"
    recorded_at = datetime.now(timezone.utc)
    request_json(
        base_url,
        "/api/v1/telemetry/readings",
        method="POST",
        access_token=access_token,
        payload={
            "device_id": device_id,
            "sensor_id": sensor_id,
            "recorded_at": recorded_at.isoformat(),
            "source": "gateway",
            "measurements": [
                {"metric": "moisture_pct", "value": 42.5, "unit": "percent"}
            ],
        },
    )

    query = urlencode(
        {
            "device_id": device_id,
            "sensor_id": sensor_id,
            "from_time": (recorded_at - timedelta(minutes=1)).isoformat(),
            "to_time": (recorded_at + timedelta(minutes=1)).isoformat(),
        }
    )
    summary = request_json(
        base_url,
        f"/api/v1/bi/summary?{query}",
        access_token=access_token,
    )
    sensors = summary.get("sensors") or []
    if summary.get("reading_count") != 1 or not any(
        item.get("device_id") == device_id and item.get("sensor_id") == sensor_id
        for item in sensors
    ):
        raise RuntimeError(f"BI did not analyze the ingested reading: {summary}")
    print("PASS: telemetry ingestion and BI analysis")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)

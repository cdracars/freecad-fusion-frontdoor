"""Opt-in local performance records for repeatable Windows validation."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
from typing import Any


def append_startup_measurement(
    log_path: Path,
    *,
    profile: str,
    ready: dict[str, Any],
) -> None:
    """Append one workbench-ready sample to an explicitly selected local log."""
    duration = ready.get("startup_duration_ms")
    try:
        valid_duration = (
            not isinstance(duration, bool)
            and isinstance(duration, (int, float))
            and math.isfinite(float(duration))
            and duration >= 0
        )
    except (OverflowError, ValueError):
        valid_duration = False
    if not valid_duration:
        raise ValueError("A non-negative measured startup duration is required.")
    if profile != "fusion":
        raise ValueError("Only Fusion launches produce a Frontdoor workbench-ready measurement.")

    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "metric": "frontdoor_workbench_ready",
        "profile": profile,
        "freecad_version": ready.get("freecad_version"),
        "freecad_pid": ready.get("pid"),
        "duration_ms": round(float(duration), 3),
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    payload = (json.dumps(record, separators=(",", ":")) + "\n").encode("utf-8")
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, payload)
    finally:
        os.close(descriptor)

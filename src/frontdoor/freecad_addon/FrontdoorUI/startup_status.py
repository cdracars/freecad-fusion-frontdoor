"""Token-scoped readiness signal shared by the launcher and Frontdoor workbench."""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any


_TOKEN_PATTERN = re.compile(r"^[0-9a-f]{32}$")


def launch_ready_marker(profile: Path, token: str) -> Path:
    if not _TOKEN_PATTERN.fullmatch(token):
        raise ValueError("Frontdoor launch token must be a 32-character lowercase hexadecimal UUID.")
    return Path(profile) / ".frontdoor-runtime" / f"ready-{token}.json"


def write_launch_ready_marker(
    profile: Path,
    token: str,
    *,
    process_id: int,
    freecad_version: str,
    startup_started_ns: int | None = None,
) -> Path:
    marker = launch_ready_marker(profile, token)
    marker.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {
        "token": token,
        "state": "ready",
        "pid": process_id,
        "freecad_version": freecad_version,
    }
    if startup_started_ns is not None:
        if (
            isinstance(startup_started_ns, bool)
            or not isinstance(startup_started_ns, int)
            or startup_started_ns <= 0
        ):
            raise ValueError("Frontdoor startup timestamp is invalid.")
        duration_ns = time.perf_counter_ns() - startup_started_ns
        if duration_ns < 0:
            raise ValueError("Frontdoor startup timestamp is invalid.")
        data["startup_duration_ms"] = round(duration_ns / 1_000_000, 3)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f"ready-{token}.", suffix=".tmp", dir=marker.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(data, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, marker)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise
    return marker


def read_launch_ready_marker(profile: Path, token: str) -> dict[str, Any] | None:
    marker = launch_ready_marker(profile, token)
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    if (
        not isinstance(data, dict)
        or data.get("token") != token
        or data.get("state") != "ready"
        or not isinstance(data.get("pid"), int)
        or not isinstance(data.get("freecad_version"), str)
    ):
        return None
    duration = data.get("startup_duration_ms")
    if duration is not None:
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
            return None
    return data

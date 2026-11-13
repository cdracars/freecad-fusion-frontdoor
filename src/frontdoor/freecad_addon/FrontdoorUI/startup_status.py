"""Token-scoped readiness signal shared by the launcher and Frontdoor workbench."""

from __future__ import annotations

import json
import os
import re
import tempfile
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
) -> Path:
    marker = launch_ready_marker(profile, token)
    marker.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f"ready-{token}.", suffix=".tmp", dir=marker.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(
                {
                    "token": token,
                    "state": "ready",
                    "pid": process_id,
                    "freecad_version": freecad_version,
                },
                stream,
            )
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
    return data

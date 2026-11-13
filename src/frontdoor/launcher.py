from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .errors import FrontdoorError
from .paths import launch_environment


def launch_freecad(
    executable: Path,
    profile: str,
    arguments: tuple[str, ...] = (),
    *,
    launch_token: str | None = None,
) -> subprocess.Popen[bytes]:
    if not executable.is_file():
        raise FrontdoorError(f"FreeCAD executable was not found: {executable}")
    if os.name != "nt" and not os.access(executable, os.X_OK):
        raise FrontdoorError(f"FreeCAD is not executable: {executable}")
    environment = launch_environment(profile)
    if launch_token is not None:
        environment["FRONTDOOR_LAUNCH_TOKEN"] = launch_token
    try:
        process = subprocess.Popen(
            [str(executable), *arguments],
            cwd=str(executable.parent),
            env=environment,
            # A GUI app must outlive this short-lived CLI (and should not
            # receive terminal-session signals when the caller exits).
            start_new_session=(os.name != "nt"),
        )
    except OSError as exc:
        raise FrontdoorError(f"Could not launch FreeCAD: {exc}") from exc
    return process

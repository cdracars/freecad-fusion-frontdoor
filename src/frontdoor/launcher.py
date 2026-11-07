from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .errors import FrontdoorError
from .paths import launch_environment


def launch_freecad(executable: Path, profile: str, arguments: tuple[str, ...] = ()) -> None:
    if not executable.is_file():
        raise FrontdoorError(f"FreeCAD executable was not found: {executable}")
    if os.name != "nt" and not os.access(executable, os.X_OK):
        raise FrontdoorError(f"FreeCAD is not executable: {executable}")
    try:
        subprocess.Popen(
            [str(executable), *arguments],
            cwd=str(executable.parent),
            env=launch_environment(profile),
        )
    except OSError as exc:
        raise FrontdoorError(f"Could not launch FreeCAD: {exc}") from exc

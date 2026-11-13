from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Callable

from .errors import FrontdoorError
from .models import ReleaseAsset
from .paths import executable_candidates
from .release import download_verified_installer

Progress = Callable[[str, int], None]
EXPECTED_PUBLISHER = "freecad project association aisbl"


def _is_expected_publisher(subject: str) -> bool:
    fields: dict[str, str] = {}
    component: list[str] = []
    components: list[str] = []
    escaped = False
    for character in subject:
        if escaped:
            component.append(character)
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == ",":
            components.append("".join(component).strip())
            component.clear()
        else:
            component.append(character)
    if escaped:
        return False
    components.append("".join(component).strip())

    for item in components:
        name, separator, value = item.partition("=")
        name = name.strip().upper()
        if not separator or not name:
            return False
        if name in {"CN", "O"} and name in fields:
            return False
        fields.setdefault(name, value.strip())

    def matches_legal_name(value: str | None) -> bool:
        normalized = " ".join((value or "").casefold().split())
        if normalized.startswith("the "):
            normalized = normalized[4:]
        return normalized == EXPECTED_PUBLISHER

    return matches_legal_name(fields.get("CN")) and matches_legal_name(fields.get("O"))


def install_windows_freecad(asset: ReleaseAsset, target: Path, progress: Progress) -> Path:
    """Verify and install one official FreeCAD Windows release without elevation."""
    if os.name != "nt":
        raise FrontdoorError("The Windows FreeCAD installer can only run on Windows.")
    installer = download_verified_installer(asset, progress)
    _verify_authenticode(installer)
    target.parent.mkdir(parents=True, exist_ok=True)
    progress(f"Installing FreeCAD {asset.version} for this Windows user…", 0)
    try:
        completed = subprocess.run(
            [str(installer), "/S", f"/D={target}"],
            check=False,
            timeout=30 * 60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise FrontdoorError(f"Could not complete the FreeCAD installer: {exc}") from exc
    if completed.returncode != 0:
        raise FrontdoorError(f"The FreeCAD installer exited with code {completed.returncode}.")
    executable = next((path for path in executable_candidates(target) if path.is_file()), None)
    if executable is None:
        raise FrontdoorError("The installer finished, but FreeCAD.exe was not found in its app-managed folder.")
    installer.unlink(missing_ok=True)
    return executable


def _verify_authenticode(installer: Path) -> None:
    if os.name != "nt":
        raise FrontdoorError("Windows Authenticode verification is available only on Windows.")
    escaped = str(installer).replace("'", "''")
    script = (
        f"$s=Get-AuthenticodeSignature -LiteralPath '{escaped}'; "
        "[pscustomobject]@{Status=[string]$s.Status;Subject=[string]$s.SignerCertificate.Subject} "
        "| ConvertTo-Json -Compress"
    )
    try:
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        result = json.loads(completed.stdout.strip())
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        raise FrontdoorError(f"Could not verify the Windows publisher signature: {exc}") from exc
    subject = result.get("Subject", "")
    if completed.returncode != 0 or result.get("Status") != "Valid":
        raise FrontdoorError(f"Windows reports an invalid or missing installer signature ({result.get('Status', 'unknown')}).")
    if not _is_expected_publisher(subject):
        raise FrontdoorError(f"The signed installer publisher was not the expected FreeCAD project ({subject or 'unknown'}).")

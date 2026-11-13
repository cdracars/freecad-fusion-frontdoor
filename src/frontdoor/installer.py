from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

from .errors import FrontdoorError
from .models import ReleaseAsset
from .paths import data_root, environment_for_profile, executable_candidates
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


def installed_freecad_version(executable: Path) -> str:
    """Read the actual managed build's version without using a normal FreeCAD profile."""
    install_directory = (
        executable.parent.parent
        if executable.parent.name.casefold() == "bin"
        else executable.parent
    )
    adjacent_command = executable.with_name("FreeCADCmd.exe")
    other_layout_command = (
        install_directory / "FreeCADCmd.exe"
        if executable.parent.name.casefold() == "bin"
        else install_directory / "bin" / "FreeCADCmd.exe"
    )
    command_candidates = (adjacent_command, other_layout_command)
    command = next((path for path in command_candidates if path.is_file()), None)
    if command is None:
        raise FrontdoorError(
            f"FreeCAD was installed at {executable}, but its FreeCADCmd.exe version checker was not found. "
            "Retry setup after checking the managed installation."
        )

    root = data_root()
    root.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="version-check-", dir=root) as temporary:
            environment = environment_for_profile(Path(temporary))
            completed = subprocess.run(
                [str(command), "--version"],
                cwd=str(command.parent),
                env=environment,
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise FrontdoorError(
            f"Could not verify the installed FreeCAD version with {command}: {exc}. "
            "Close any managed FreeCAD window and retry setup."
        ) from exc

    output = (completed.stdout or completed.stderr).strip()
    if completed.returncode != 0:
        detail = output or completed.stderr.strip() or f"exit code {completed.returncode}"
        raise FrontdoorError(
            f"Could not verify the installed FreeCAD version: {detail}. "
            "Close any managed FreeCAD window and retry setup."
        )
    match = re.search(r"(?<![\w.])(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)(?![\w.])", output)
    if not match:
        raise FrontdoorError(
            f"FreeCAD's version checker returned an unrecognized result: {output or '(no output)'}. "
            "Close any managed FreeCAD window and retry setup."
        )
    return match.group(1)


def verify_installed_freecad_version(executable: Path, expected_version: str) -> str:
    actual_version = installed_freecad_version(executable)
    if actual_version != expected_version:
        raise FrontdoorError(
            f"The managed FreeCAD copy reports version {actual_version}, but setup expected "
            f"{expected_version}. Close any managed FreeCAD window and retry setup. "
            "The managed version record was not updated."
        )
    return actual_version


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

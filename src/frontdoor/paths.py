from __future__ import annotations

import json
import os
from pathlib import Path

from .errors import FrontdoorError

APP_FOLDER = "FreeCAD Fusion Frontdoor"
MANAGED_INSTALL = "FreeCAD"
FUSION_PROFILE_NAME = "fusion"
FULL_PROFILE_NAME = "full"
MANAGED_MARKER = ".frontdoor-managed.json"


def data_root() -> Path:
    """Return this app's per-user data root without touching FreeCAD's normal profile."""
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / APP_FOLDER
    return Path.home() / ".local" / "share" / "freecad-fusion-frontdoor"


def install_root() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / "Programs" / APP_FOLDER / MANAGED_INSTALL
    return data_root() / "programs" / MANAGED_INSTALL


def profile_root(name: str) -> Path:
    if name not in {FUSION_PROFILE_NAME, FULL_PROFILE_NAME}:
        raise ValueError(f"Unknown profile: {name}")
    return data_root() / "profiles" / name


def ensure_profile(name: str) -> Path:
    """Create one owned profile, refusing to adopt a populated unmarked folder."""
    profile = profile_root(name)
    ownership_file = profile / ".frontdoor-profile.json"
    if profile.exists() and ownership_file.is_file():
        try:
            ownership = json.loads(ownership_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise FrontdoorError(f"Could not read the profile ownership record at {profile}.") from exc
        if ownership.get("product") != "FreeCAD Fusion Frontdoor" or ownership.get("profile") != name:
            raise FrontdoorError(f"The profile path is owned by a different setup: {profile}")
    elif profile.exists() and any(profile.iterdir()):
        raise FrontdoorError(f"Refusing to use a populated profile directory without this app's ownership marker: {profile}")

    for folder in (profile, profile / "Mod", profile / "temp"):
        folder.mkdir(parents=True, exist_ok=True)
    if not ownership_file.exists():
        temporary = ownership_file.with_suffix(".tmp")
        temporary.write_text(
            json.dumps({"product": "FreeCAD Fusion Frontdoor", "profile": name}, indent=2),
            encoding="utf-8",
        )
        temporary.replace(ownership_file)
    return profile


def ensure_profiles(names: tuple[str, ...]) -> dict[str, Path]:
    if not names or len(set(names)) != len(names):
        raise FrontdoorError("Select one or more distinct profiles to prepare.")
    return {name: ensure_profile(name) for name in names}


def executable_candidates(root: Path | None = None) -> tuple[Path, ...]:
    base = root or install_root()
    return (base / "bin" / "FreeCAD.exe", base / "FreeCAD.exe")


def _managed_record() -> dict[str, object] | None:
    marker = data_root() / MANAGED_MARKER
    if not marker.is_file():
        return None
    try:
        record = json.loads(marker.read_text(encoding="utf-8"))
        if record.get("product") != "FreeCAD Fusion Frontdoor":
            return None
        root = Path(str(record["install_path"]))
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if root.resolve() != install_root().resolve():
        return None
    return record


def managed_executable() -> Path | None:
    record = _managed_record()
    if record is None:
        return None
    root = Path(str(record["install_path"]))
    return next((path for path in executable_candidates(root) if path.is_file()), None)


def managed_version() -> str | None:
    record = _managed_record()
    version = record.get("freecad_version") if record else None
    return str(version) if version else None


def fusion_addon_ready() -> bool:
    addon = profile_root(FUSION_PROFILE_NAME) / "Mod" / "freecad-fusion"
    return (addon / ".frontdoor-addon.json").is_file() and (addon / "InitGui.py").is_file()


def write_managed_marker(*, executable: Path, version: str) -> None:
    root = data_root()
    root.mkdir(parents=True, exist_ok=True)
    marker = root / MANAGED_MARKER
    temporary = marker.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(
            {
                "product": "FreeCAD Fusion Frontdoor",
                "install_path": str(install_root()),
                "executable": str(executable),
                "freecad_version": version,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    temporary.replace(marker)


def launch_environment(profile_name: str) -> dict[str, str]:
    """Build a launch-only environment for a Frontdoor-managed profile."""
    profile = ensure_profile(profile_name)
    environment = os.environ.copy()
    environment["FREECAD_USER_HOME"] = str(profile)
    environment["FREECAD_USER_DATA"] = str(profile)
    environment["FREECAD_USER_TEMP"] = str(profile / "temp")
    return environment

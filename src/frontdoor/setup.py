from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable

from .addon import install_pinned_fusion_addon
from .errors import FrontdoorError
from .installer import (
    install_windows_freecad,
    installed_freecad_version,
    verify_installed_freecad_version,
)
from .models import ReleaseAsset, SetupResult
from .paths import (
    MANAGED_MARKER,
    data_root,
    executable_candidates,
    ensure_profiles,
    fusion_addon_ready,
    install_root,
    managed_executable,
    write_managed_marker,
)
from .preferences import ensure_default_start_page_hidden
from .release import latest_windows_release
from .theme import ensure_default_theme
from .ui_addon import ensure_default_workbench, install_frontdoor_ui
from .window_state import ensure_initial_maximized

Progress = Callable[[str, int], None]


def setup_existing_freecad(
    executable: Path,
    *,
    profiles: tuple[str, ...] = ("fusion",),
    progress: Progress,
    version: str = "existing installation",
) -> SetupResult:
    """Prepare isolated Frontdoor profiles around a FreeCAD executable already on this machine."""
    executable = executable.expanduser().resolve()
    if not executable.is_file():
        raise FrontdoorError(f"FreeCAD executable was not found: {executable}")
    if os.name != "nt" and not os.access(executable, os.X_OK):
        raise FrontdoorError(f"FreeCAD is not executable: {executable}")
    if not profiles or any(name not in {"fusion", "full"} for name in profiles):
        raise FrontdoorError("Choose the Fusion profile, the Full FreeCAD profile, or both.")
    roots = ensure_profiles(profiles)
    for profile_root in roots.values():
        ensure_initial_maximized(profile_root)
    if "fusion" in profiles:
        ensure_default_theme(roots["fusion"])
        ensure_default_start_page_hidden(roots["fusion"])
        install_frontdoor_ui(roots["fusion"])
        ensure_default_workbench(roots["fusion"])
        install_pinned_fusion_addon(progress)
    progress("The selected isolated profile is ready.", 100)
    return SetupResult(
        executable=executable,
        version=version,
        fusion_profile=roots.get("fusion"),
        full_profile=roots.get("full"),
    )


def install_managed_copy(asset: ReleaseAsset, progress: Progress) -> SetupResult:
    """Install/update FreeCAD in Frontdoor's user directory, then set up both isolated modes."""
    if os.name != "nt":
        raise FrontdoorError("Installing a managed FreeCAD copy requires Windows.")
    roots = ensure_profiles(("fusion", "full"))
    for profile_root in roots.values():
        ensure_initial_maximized(profile_root)
    ensure_default_theme(roots["fusion"])
    ensure_default_start_page_hidden(roots["fusion"])
    install_frontdoor_ui(roots["fusion"])
    ensure_default_workbench(roots["fusion"])
    downloads = data_root() / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    executable = managed_executable()
    if executable is None:
        _claim_install_directory()
        progress(f"Installing a separate FreeCAD {asset.version} copy…", 0)
        executable = install_windows_freecad(asset, install_root(), progress)
        installed_version = verify_installed_freecad_version(executable, asset.version)
    else:
        installed_version = installed_freecad_version(executable)
        if installed_version != asset.version:
            progress(f"Updating the app-managed FreeCAD copy from {installed_version} to {asset.version}…", 0)
            executable = install_windows_freecad(asset, install_root(), progress)
            installed_version = verify_installed_freecad_version(executable, asset.version)

    write_managed_marker(executable=executable, version=installed_version)
    if not fusion_addon_ready():
        install_pinned_fusion_addon(progress)
    return SetupResult(
        executable=executable,
        version=installed_version,
        fusion_profile=roots["fusion"],
        full_profile=roots["full"],
    )


def _claim_install_directory() -> None:
    root = data_root()
    marker = root / MANAGED_MARKER
    target = install_root()
    target.parent.mkdir(parents=True, exist_ok=True)
    if marker.is_file():
        try:
            record = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise FrontdoorError("The app's install ownership record could not be read safely.") from exc
        if record.get("product") != "FreeCAD Fusion Frontdoor":
            raise FrontdoorError("The install directory has an ownership record from another application.")
        if Path(str(record.get("install_path", ""))).resolve() != target.resolve():
            raise FrontdoorError("The install ownership record points somewhere unexpected.")
        return
    if target.exists() and any(target.iterdir()):
        raise FrontdoorError(f"Refusing to overwrite an unowned install directory: {target}")
    temporary = marker.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(
            {"product": "FreeCAD Fusion Frontdoor", "install_path": str(target), "state": "installing"},
            indent=2,
        ),
        encoding="utf-8",
    )
    temporary.replace(marker)

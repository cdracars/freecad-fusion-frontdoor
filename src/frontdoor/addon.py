from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Callable

from .errors import FrontdoorError
from .paths import data_root, ensure_profile
from .release import download_file

Progress = Callable[[str, int], None]
ADDON_COMMIT = "332ba07bdcaca194e5a3010d1fc0a365eeaefcf1"
ADDON_ARCHIVE_URL = f"https://github.com/arxdsilva/freecad-fusion/archive/{ADDON_COMMIT}.zip"
ADDON_FOLDER = "freecad-fusion"
ADDON_MARKER = ".frontdoor-addon.json"


def install_pinned_fusion_addon(progress: Progress) -> Path:
    """Stage the pinned community add-on only inside Frontdoor's Fusion profile."""
    profile = ensure_profile("fusion")
    mod_directory = profile / "Mod"
    archive = data_root() / "downloads" / f"freecad-fusion-{ADDON_COMMIT}.zip"
    try:
        progress("Downloading the pinned Fusion navigation add-on…", 0)
        download_file(
            ADDON_ARCHIVE_URL,
            archive,
            expected_size=None,
            progress=progress,
            label="Downloading Fusion add-on",
        )
        progress("Installing Fusion mode into its separate profile…", 0)
        return _extract_profile_addon(archive, mod_directory)
    finally:
        archive.unlink(missing_ok=True)


def _extract_profile_addon(archive: Path, destination: Path) -> Path:
    staging = Path(tempfile.mkdtemp(prefix="frontdoor-addon-", dir=data_root()))
    try:
        with zipfile.ZipFile(archive) as bundle:
            entries = bundle.infolist()
            if len(entries) > 1500 or sum(entry.file_size for entry in entries) > 100 * 1024 * 1024:
                raise FrontdoorError("The add-on archive is unexpectedly large and was rejected.")
            staging_root = staging.resolve()
            for entry in entries:
                relative = PurePosixPath(entry.filename)
                if (
                    "\\" in entry.filename
                    or not relative.parts
                    or ":" in relative.parts[0]
                    or relative.is_absolute()
                    or ".." in relative.parts
                ):
                    raise FrontdoorError("The add-on archive contains an unsafe path and was rejected.")
                if entry.external_attr >> 16 & 0o170000 == 0o120000:
                    raise FrontdoorError("The add-on archive contains a symbolic link and was rejected.")
                target = (staging / Path(*relative.parts)).resolve()
                if not target.is_relative_to(staging_root):
                    raise FrontdoorError("The add-on archive attempted to write outside its staging directory.")
            bundle.extractall(staging)

        package_roots = [
            path
            for path in staging.iterdir()
            if path.is_dir() and (path / "InitGui.py").is_file() and (path / "package.xml").is_file()
        ]
        if len(package_roots) != 1:
            raise FrontdoorError("The pinned add-on archive did not have the expected FreeCAD package layout.")
        addon = destination / ADDON_FOLDER
        ownership = addon / ADDON_MARKER
        if addon.exists() and not ownership.is_file():
            raise FrontdoorError(f"Refusing to overwrite an unowned add-on directory: {addon}")
        replacement = destination / f".{ADDON_FOLDER}.new"
        if replacement.exists():
            shutil.rmtree(replacement)
        shutil.copytree(package_roots[0], replacement)
        (replacement / ADDON_MARKER).write_text(
            json.dumps({"commit": ADDON_COMMIT, "license": "MIT"}, indent=2), encoding="utf-8"
        )
        if addon.exists():
            shutil.rmtree(addon)
        replacement.replace(addon)
        return addon
    except zipfile.BadZipFile as exc:
        raise FrontdoorError("The downloaded add-on archive is not a valid ZIP file.") from exc
    finally:
        shutil.rmtree(staging, ignore_errors=True)

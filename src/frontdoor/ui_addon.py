from __future__ import annotations

import json
import os
import shutil
import stat
import tempfile
from importlib.resources import as_file, files
from pathlib import Path
from pathlib import PurePosixPath
import xml.etree.ElementTree as ET
import zipfile

from .errors import FrontdoorError
from .paths import ensure_profile

UI_ADDON_FOLDER = "FrontdoorUI"
UI_MARKER = ".frontdoor-ui.json"
UI_VERSION = "0.1.2"


def frontdoor_ui_ready(profile: Path | None = None) -> bool:
    root = profile or ensure_profile("fusion")
    addon = root / "Mod" / UI_ADDON_FOLDER
    return (addon / UI_MARKER).is_file() and (addon / "InitGui.py").is_file()


def ensure_default_workbench(profile: Path) -> None:
    """Select Frontdoor on first launch without replacing a saved workbench choice."""
    config = profile / "user.cfg"
    try:
        if config.exists():
            tree = ET.parse(config)
            root = tree.getroot()
        else:
            root = ET.Element("FCParameters")
            tree = ET.ElementTree(root)
        general = _ensure_group(root, ("Root", "BaseApp", "Preferences", "General"))
        autoload = next(
            (node for node in general.findall("FCText") if node.get("Name") == "AutoloadModule"),
            None,
        )
        if autoload is not None and (autoload.text or "").strip():
            return
        if autoload is None:
            autoload = ET.SubElement(general, "FCText", {"Name": "AutoloadModule"})
        autoload.text = "FrontdoorWorkbench"
        _write_config(tree, config)
    except (OSError, ET.ParseError) as exc:
        raise FrontdoorError(f"Could not set the initial Frontdoor workbench in {config}: {exc}") from exc


def install_frontdoor_ui(profile: Path | None = None) -> Path:
    """Stage the owned task-based FreeCAD workbench into a managed profile."""
    root = profile or ensure_profile("fusion")
    mod = root / "Mod"
    mod.mkdir(parents=True, exist_ok=True)
    destination = mod / UI_ADDON_FOLDER
    marker = destination / UI_MARKER
    if marker.is_file():
        try:
            installed = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise FrontdoorError("The Frontdoor workbench ownership record could not be read.") from exc
        if installed.get("version") == UI_VERSION:
            return destination
    elif destination.exists():
        raise FrontdoorError(f"Refusing to overwrite an unowned FreeCAD add-on directory: {destination}")

    replacement = mod / f".{UI_ADDON_FOLDER}.new"
    backup = mod / f".{UI_ADDON_FOLDER}.old"
    for candidate in (replacement, backup):
        if candidate.exists():
            if not (candidate / UI_MARKER).is_file():
                raise FrontdoorError(f"Refusing to remove an unowned staging directory: {candidate}")
            shutil.rmtree(candidate)

    try:
        package = files("frontdoor.freecad_addon").joinpath(UI_ADDON_FOLDER)
        required = ("InitGui.py", "task_surface.py", "package.xml")
        if package.is_dir() and all(package.joinpath(name).is_file() for name in required):
            with as_file(package) as source:
                shutil.copytree(source, replacement)
        else:
            payload = files("frontdoor.freecad_addon").joinpath("frontdoor_ui_payload.zip")
            if not payload.is_file():
                raise FrontdoorError("The packaged Frontdoor workbench resource is missing.")
            with as_file(payload) as source:
                _extract_frontdoor_ui_payload(Path(source), replacement)
        (replacement / UI_MARKER).write_text(
            json.dumps({"product": "FreeCAD Fusion Frontdoor", "version": UI_VERSION}, indent=2),
            encoding="utf-8",
        )
        if destination.exists():
            destination.replace(backup)
        try:
            replacement.replace(destination)
        except OSError:
            if backup.exists() and not destination.exists():
                backup.replace(destination)
            raise
        if backup.exists():
            shutil.rmtree(backup)
        return destination
    except FrontdoorError:
        shutil.rmtree(replacement, ignore_errors=True)
        raise
    except (OSError, zipfile.BadZipFile, ValueError) as exc:
        shutil.rmtree(replacement, ignore_errors=True)
        raise FrontdoorError(f"Could not stage the Frontdoor workbench in {destination}: {exc}") from exc


def _extract_frontdoor_ui_payload(archive_path: Path, destination: Path) -> None:
    required = {"initgui.py", "task_surface.py", "package.xml"}
    seen: set[str] = set()
    total_size = 0
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(archive_path) as archive:
        for entry in archive.infolist():
            relative = PurePosixPath(entry.filename)
            if (
                relative.is_absolute()
                or len(relative.parts) != 1
                or relative.name in {"", ".", ".."}
                or entry.is_dir()
                or entry.flag_bits & 1
                or stat.S_ISLNK(entry.external_attr >> 16)
            ):
                raise FrontdoorError("The packaged Frontdoor workbench archive contains an unsafe entry.")
            name_key = relative.name.casefold()
            if name_key in seen:
                raise FrontdoorError("The packaged Frontdoor workbench archive contains duplicate filenames.")
            seen.add(name_key)
            total_size += entry.file_size
            if entry.file_size > 25 * 1024 * 1024 or total_size > 50 * 1024 * 1024:
                raise FrontdoorError("The packaged Frontdoor workbench archive is larger than expected.")
            with archive.open(entry) as source, (destination / relative.name).open("wb") as target:
                shutil.copyfileobj(source, target)

    if not required.issubset(seen):
        raise FrontdoorError("The packaged Frontdoor workbench archive is missing required files.")


def _ensure_group(parent: ET.Element, names: tuple[str, ...]) -> ET.Element:
    node = parent
    for name in names:
        child = next(
            (item for item in node.findall("FCParamGroup") if item.get("Name") == name),
            None,
        )
        if child is None:
            child = ET.SubElement(node, "FCParamGroup", {"Name": name})
        node = child
    return node


def _write_config(tree: ET.ElementTree, config: Path) -> None:
    config.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_path = tempfile.mkstemp(prefix="user.", suffix=".tmp", dir=config.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            tree.write(stream, encoding="utf-8", xml_declaration=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, config)
    except OSError:
        try:
            os.unlink(temporary_path)
        except OSError:
            pass
        raise

from __future__ import annotations

import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from .errors import FrontdoorError


def ensure_initial_maximized(profile: Path) -> None:
    """Maximize FreeCAD on first launch without overriding a saved user choice."""
    config = profile / "user.cfg"
    try:
        if config.exists():
            tree = ET.parse(config)
            root = tree.getroot()
        else:
            root = ET.Element("FCParameters")
            tree = ET.ElementTree(root)

        main_window = _ensure_group(
            root, ("Root", "BaseApp", "Preferences", "MainWindow")
        )
        maximized = next(
            (
                node
                for node in main_window.findall("FCBool")
                if node.get("Name") == "Maximized"
            ),
            None,
        )
        if maximized is not None:
            return

        ET.SubElement(main_window, "FCBool", {"Name": "Maximized", "Value": "1"})
        config.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_path = tempfile.mkstemp(
            prefix="user.", suffix=".tmp", dir=config.parent
        )
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
    except (OSError, ET.ParseError) as exc:
        raise FrontdoorError(
            f"Could not set the initial FreeCAD window state in {config}: {exc}"
        ) from exc


def _ensure_group(parent: ET.Element, names: tuple[str, ...]) -> ET.Element:
    node = parent
    for name in names:
        child = next(
            (
                item
                for item in node.findall("FCParamGroup")
                if item.get("Name") == name
            ),
            None,
        )
        if child is None:
            child = ET.SubElement(node, "FCParamGroup", {"Name": name})
        node = child
    return node

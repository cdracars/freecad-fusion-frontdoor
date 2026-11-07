from __future__ import annotations

import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from .errors import FrontdoorError


def ensure_default_theme(profile: Path, theme: str = "FreeCAD Dark") -> None:
    """Set a default theme in a Frontdoor-owned profile without overwriting a choice."""
    config = profile / "user.cfg"
    try:
        if config.exists():
            parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
            tree = ET.parse(config, parser=parser)
            root = tree.getroot()
        else:
            root = ET.Element("FCParameters")
            tree = ET.ElementTree(root)

        preferences = _ensure_group(root, ("Root", "BaseApp", "Preferences", "MainWindow"))
        theme_node = next(
            (node for node in preferences.findall("FCText") if node.get("Name") == "Theme"),
            None,
        )
        if theme_node is not None and (theme_node.text or "").strip():
            return

        if theme_node is None:
            theme_node = ET.SubElement(preferences, "FCText", {"Name": "Theme"})
        theme_node.text = theme
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
    except (OSError, ET.ParseError) as exc:
        raise FrontdoorError(f"Could not set the default FreeCAD theme in {config}: {exc}") from exc


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

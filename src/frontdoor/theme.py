from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from .errors import FrontdoorError
from .freecad_config import ensure_param_group, read_user_config, write_user_config


def ensure_default_theme(profile: Path, theme: str = "FreeCAD Dark") -> None:
    """Set a default theme in a Frontdoor-owned profile without overwriting a choice."""
    config = profile / "user.cfg"
    try:
        config, tree, root = read_user_config(profile)
        preferences = ensure_param_group(root, ("Root", "BaseApp", "Preferences", "MainWindow"))
        theme_node = next(
            (node for node in preferences.findall("FCText") if node.get("Name") == "Theme"),
            None,
        )
        if theme_node is not None and (theme_node.text or "").strip():
            return

        if theme_node is None:
            theme_node = ET.SubElement(preferences, "FCText", {"Name": "Theme"})
        theme_node.text = theme
        write_user_config(tree, config)
    except (OSError, ET.ParseError) as exc:
        raise FrontdoorError(f"Could not set the default FreeCAD theme in {config}: {exc}") from exc

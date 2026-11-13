from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from .errors import FrontdoorError
from .freecad_config import ensure_param_group, read_user_config, write_user_config


def ensure_initial_maximized(profile: Path) -> None:
    """Maximize FreeCAD on first launch without overriding a saved user choice."""
    config = profile / "user.cfg"
    try:
        config, tree, root = read_user_config(profile)
        main_window = ensure_param_group(root, ("Root", "BaseApp", "Preferences", "MainWindow"))
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
        write_user_config(tree, config)
    except (OSError, ET.ParseError) as exc:
        raise FrontdoorError(
            f"Could not set the initial FreeCAD window state in {config}: {exc}"
        ) from exc

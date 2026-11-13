from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from .errors import FrontdoorError
from .freecad_config import ensure_param_group, read_user_config, write_user_config


def ensure_default_start_page_hidden(profile: Path) -> None:
    """Hide FreeCAD's Start workbench page by default in a Frontdoor profile.

    An existing ShowOnStartup value belongs to the user and is left alone.
    """
    config = profile / "user.cfg"
    try:
        config, tree, root = read_user_config(profile)
        start_preferences = ensure_param_group(
            root,
            ("Root", "BaseApp", "Preferences", "Mod", "Start"),
        )
        existing = [node for node in start_preferences if node.get("Name") == "ShowOnStartup"]
        if existing:
            value = existing[0].get("Value") if len(existing) == 1 and existing[0].tag == "FCBool" else None
            if value not in {"0", "1"}:
                raise FrontdoorError(
                    f"The Start page preference has an unexpected format in {config}; it was left unchanged."
                )
            return

        ET.SubElement(start_preferences, "FCBool", {"Name": "ShowOnStartup", "Value": "0"})
        write_user_config(tree, config)
    except FrontdoorError:
        raise
    except (OSError, ET.ParseError) as exc:
        raise FrontdoorError(f"Could not set the default FreeCAD Start page preference in {config}: {exc}") from exc

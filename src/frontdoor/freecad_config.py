from __future__ import annotations

import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


def read_user_config(profile: Path) -> tuple[Path, ET.ElementTree, ET.Element]:
    """Load FreeCAD's user.cfg while retaining comments and unrelated settings."""
    config = profile / "user.cfg"
    if config.exists():
        parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
        tree = ET.parse(config, parser=parser)
        root = tree.getroot()
    else:
        root = ET.Element("FCParameters")
        tree = ET.ElementTree(root)
    return config, tree, root


def ensure_param_group(parent: ET.Element, names: tuple[str, ...]) -> ET.Element:
    """Find or create a path of FreeCAD FCParamGroup nodes."""
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


def write_user_config(tree: ET.ElementTree, config: Path) -> None:
    """Atomically persist a FreeCAD user.cfg edit beside its destination."""
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

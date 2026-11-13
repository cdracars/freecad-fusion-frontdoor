"""Build the source archive that the frozen app stages as FreeCAD's add-on."""

from __future__ import annotations

import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_SOURCE = ROOT / "src" / "frontdoor" / "freecad_addon" / "FrontdoorUI"
OUTPUT = ROOT / "src" / "frontdoor" / "freecad_addon" / "frontdoor_ui_payload.zip"
REQUIRED_FILES = {"InitGui.py", "task_surface.py", "package.xml"}


def build_payload(source: Path = ADDON_SOURCE, output: Path = OUTPUT) -> Path:
    source = Path(source)
    output = Path(output)
    files = sorted(
        path for path in source.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )
    names = {path.relative_to(source).as_posix() for path in files}
    if not REQUIRED_FILES.issubset(names):
        raise RuntimeError(f"Frontdoor workbench payload is missing required files: {REQUIRED_FILES - names}")
    if any(".." in Path(name).parts or name.startswith("/") for name in names):
        raise RuntimeError("Frontdoor workbench payload contains an unsafe path.")

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            info = zipfile.ZipInfo(path.relative_to(source).as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (0o100644 & 0xFFFF) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return output


if __name__ == "__main__":
    print(build_payload())

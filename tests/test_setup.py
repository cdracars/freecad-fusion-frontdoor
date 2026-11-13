from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from frontdoor import setup
from frontdoor.errors import FrontdoorError
from frontdoor.models import ReleaseAsset
from frontdoor.paths import DATA_ROOT_ENV, MANAGED_MARKER


class ManagedInstallVersionTests(unittest.TestCase):
    def test_mismatched_updated_binary_does_not_replace_managed_version_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = root / "data"
            data.mkdir()
            marker = data / MANAGED_MARKER
            previous = {
                "product": "FreeCAD Fusion Frontdoor",
                "install_path": str(root / "programs" / "FreeCAD"),
                "executable": str(root / "programs" / "FreeCAD" / "bin" / "FreeCAD.exe"),
                "freecad_version": "1.1.3",
            }
            original = json.dumps(previous, indent=2)
            marker.write_text(original, encoding="utf-8")
            executable = Path(previous["executable"])
            roots = {"fusion": root / "profiles" / "fusion", "full": root / "profiles" / "full"}
            asset = ReleaseAsset(
                name="FreeCAD_1.1.4-Windows-x86_64-installer.exe",
                version="1.1.4",
                download_url="https://github.com/FreeCAD/FreeCAD/releases/download/1.1.4/installer.exe",
                size=1,
                sha256="a" * 64,
            )

            with (
                patch.dict(os.environ, {DATA_ROOT_ENV: str(data)}),
                patch("frontdoor.setup.os.name", "nt"),
                patch.object(setup, "ensure_profiles", return_value=roots),
                patch.object(setup, "ensure_initial_maximized"),
                patch.object(setup, "ensure_default_theme"),
                patch.object(setup, "install_frontdoor_ui"),
                patch.object(setup, "ensure_default_workbench"),
                patch.object(setup, "data_root", return_value=data),
                patch.object(setup, "install_root", return_value=root / "programs" / "FreeCAD"),
                patch.object(setup, "managed_executable", return_value=executable),
                patch.object(setup, "installed_freecad_version", return_value="1.1.3"),
                patch.object(
                    setup,
                    "verify_installed_freecad_version",
                    side_effect=FrontdoorError(
                        "The managed FreeCAD copy reports version 1.1.3, but setup expected 1.1.4. "
                        "The managed version record was not updated."
                    ),
                ),
                patch.object(setup, "install_windows_freecad", return_value=executable) as install,
            ):
                with self.assertRaisesRegex(FrontdoorError, "version record was not updated"):
                    setup.install_managed_copy(asset, lambda _message, _percentage: None)

            install.assert_called_once()
            self.assertEqual(marker.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()

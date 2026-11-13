from __future__ import annotations

import tempfile
import unittest
import zipfile
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch

from frontdoor.errors import FrontdoorError
from frontdoor.ui_addon import _extract_frontdoor_ui_payload, install_frontdoor_ui


class FrontdoorPayloadTests(unittest.TestCase):
    def test_extracts_required_addon_sources_from_portable_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive_path = root / "payload.zip"
            destination = root / "FrontdoorUI"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("InitGui.py", "# init")
                archive.writestr("task_surface.py", "# tasks")
                archive.writestr("package.xml", "<package />")
                archive.writestr("README.md", "Usage")

            _extract_frontdoor_ui_payload(archive_path, destination)

            self.assertEqual((destination / "InitGui.py").read_text(encoding="utf-8"), "# init")
            self.assertEqual((destination / "task_surface.py").read_text(encoding="utf-8"), "# tasks")
            self.assertTrue((destination / "package.xml").is_file())

    def test_rejects_paths_that_escape_the_staging_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive_path = root / "payload.zip"
            destination = root / "FrontdoorUI"
            escaped = root / "escaped.txt"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("../escaped.txt", "no")

            with self.assertRaises(FrontdoorError):
                _extract_frontdoor_ui_payload(archive_path, destination)

            self.assertFalse(escaped.exists())

    def test_rejects_duplicate_names_case_insensitively(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive_path = root / "payload.zip"
            destination = root / "FrontdoorUI"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("InitGui.py", "# init")
                archive.writestr("initgui.py", "# shadow")

            with self.assertRaises(FrontdoorError):
                _extract_frontdoor_ui_payload(archive_path, destination)

    def test_install_uses_zip_resource_when_addon_directory_is_not_packaged(self) -> None:
        class PayloadResource:
            def is_file(self) -> bool:
                return True

        class AddonDirectoryResource:
            def is_dir(self) -> bool:
                return False

        class PackageResource:
            def joinpath(self, name: str) -> object:
                if name == "FrontdoorUI":
                    return AddonDirectoryResource()
                if name == "frontdoor_ui_payload.zip":
                    return PayloadResource()
                raise AssertionError(name)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive_path = root / "payload.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("InitGui.py", "# init")
                archive.writestr("task_surface.py", "# tasks")
                archive.writestr("package.xml", "<package />")

            with (
                patch("frontdoor.ui_addon.files", return_value=PackageResource()),
                patch("frontdoor.ui_addon.as_file", side_effect=lambda _resource: nullcontext(archive_path)),
            ):
                installed = install_frontdoor_ui(root / "profile")

            self.assertEqual((installed / "InitGui.py").read_text(encoding="utf-8"), "# init")
            self.assertTrue((installed / ".frontdoor-ui.json").is_file())


if __name__ == "__main__":
    unittest.main()

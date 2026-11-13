from __future__ import annotations

import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from frontdoor.addon import ADDON_COMMIT, ADDON_FOLDER, ADDON_MARKER, _extract_profile_addon
from frontdoor.errors import FrontdoorError


class PinnedAddonInstallTests(unittest.TestCase):
    def _archive(self, root: Path) -> Path:
        archive = root / "addon.zip"
        with zipfile.ZipFile(archive, "w") as bundle:
            bundle.writestr("upstream/InitGui.py", "# new addon")
            bundle.writestr("upstream/package.xml", "<package />")
        return archive

    def _owned_addon(self, path: Path, content: str = "# old addon") -> None:
        path.mkdir(parents=True)
        (path / "InitGui.py").write_text(content, encoding="utf-8")
        (path / ADDON_MARKER).write_text('{"commit":"old"}', encoding="utf-8")

    def test_failed_activation_restores_previous_owned_addon(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "Mod"
            destination.mkdir()
            addon = destination / ADDON_FOLDER
            self._owned_addon(addon)
            archive = self._archive(root)
            real_replace = Path.replace

            def fail_new_activation(path: Path, target: Path) -> Path:
                if path.name == f".{ADDON_FOLDER}.new":
                    raise OSError("simulated activation failure")
                return real_replace(path, target)

            with patch("frontdoor.addon.data_root", return_value=root), patch.object(
                Path, "replace", fail_new_activation
            ):
                with self.assertRaisesRegex(FrontdoorError, "could not activate"):
                    _extract_profile_addon(archive, destination)

            self.assertEqual((addon / "InitGui.py").read_text(encoding="utf-8"), "# old addon")
            self.assertFalse((destination / f".{ADDON_FOLDER}.backup").exists())

    def test_failed_backup_rename_keeps_current_addon_active(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "Mod"
            destination.mkdir()
            addon = destination / ADDON_FOLDER
            self._owned_addon(addon)
            archive = self._archive(root)
            real_replace = Path.replace

            def fail_backup(path: Path, target: Path) -> Path:
                if path == addon:
                    raise OSError("simulated backup rename failure")
                return real_replace(path, target)

            with patch("frontdoor.addon.data_root", return_value=root), patch.object(
                Path, "replace", fail_backup
            ):
                with self.assertRaisesRegex(FrontdoorError, "existing version remains active"):
                    _extract_profile_addon(archive, destination)

            self.assertEqual((addon / "InitGui.py").read_text(encoding="utf-8"), "# old addon")

    def test_unowned_stale_replacement_is_preserved_and_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "Mod"
            destination.mkdir()
            replacement = destination / f".{ADDON_FOLDER}.new"
            replacement.mkdir()
            (replacement / "user.txt").write_text("keep", encoding="utf-8")
            archive = self._archive(root)

            with patch("frontdoor.addon.data_root", return_value=root):
                with self.assertRaisesRegex(FrontdoorError, "unowned replacement"):
                    _extract_profile_addon(archive, destination)

            self.assertEqual((replacement / "user.txt").read_text(encoding="utf-8"), "keep")

    def test_retry_replaces_an_owned_partial_staging_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "Mod"
            destination.mkdir()
            replacement = destination / f".{ADDON_FOLDER}.new"
            self._owned_addon(replacement, "# partial staging")
            archive = self._archive(root)

            with patch("frontdoor.addon.data_root", return_value=root):
                installed = _extract_profile_addon(archive, destination)

            self.assertEqual((installed / "InitGui.py").read_text(encoding="utf-8"), "# new addon")
            self.assertFalse(replacement.exists())

    def test_interrupted_swap_restores_owned_backup_before_retry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "Mod"
            destination.mkdir()
            backup = destination / f".{ADDON_FOLDER}.backup"
            self._owned_addon(backup)
            archive = self._archive(root)

            with patch("frontdoor.addon.data_root", return_value=root):
                installed = _extract_profile_addon(archive, destination)

            self.assertEqual(installed, destination / ADDON_FOLDER)
            self.assertEqual((installed / "InitGui.py").read_text(encoding="utf-8"), "# new addon")
            self.assertEqual(json_read(installed / ADDON_MARKER)["commit"], ADDON_COMMIT)
            self.assertFalse(backup.exists())

    def test_backup_cleanup_failure_is_retryable_after_activation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "Mod"
            destination.mkdir()
            addon = destination / ADDON_FOLDER
            backup = destination / f".{ADDON_FOLDER}.backup"
            self._owned_addon(addon)
            archive = self._archive(root)
            real_rmtree = shutil.rmtree

            def fail_backup_cleanup(path: Path, *args: object, **kwargs: object) -> None:
                if Path(path) == backup:
                    raise OSError("simulated cleanup failure")
                real_rmtree(path, *args, **kwargs)

            with patch("frontdoor.addon.data_root", return_value=root), patch(
                "frontdoor.addon.shutil.rmtree", fail_backup_cleanup
            ):
                with self.assertRaisesRegex(FrontdoorError, "Retry setup"):
                    _extract_profile_addon(archive, destination)

            self.assertEqual((addon / "InitGui.py").read_text(encoding="utf-8"), "# new addon")
            self.assertTrue(backup.exists())

            with patch("frontdoor.addon.data_root", return_value=root):
                _extract_profile_addon(archive, destination)

            self.assertFalse(backup.exists())


def json_read(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

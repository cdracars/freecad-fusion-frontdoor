from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from frontdoor.errors import FrontdoorError
from frontdoor.paths import DATA_ROOT_ENV, MANAGED_MARKER, ensure_profile, install_root
from frontdoor.setup import _claim_install_directory


class ProfileOwnershipTests(unittest.TestCase):
    def test_creates_and_reuses_only_its_owned_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with patch.dict("os.environ", {DATA_ROOT_ENV: temporary}):
                profile = ensure_profile("fusion")
                marker = json.loads((profile / ".frontdoor-profile.json").read_text(encoding="utf-8"))

                self.assertEqual(marker["product"], "FreeCAD Fusion Frontdoor")
                self.assertEqual(marker["profile"], "fusion")
                self.assertTrue((profile / "Mod").is_dir())
                self.assertTrue((profile / "temp").is_dir())
                self.assertEqual(ensure_profile("fusion"), profile)

    def test_refuses_populated_unowned_profile_without_changing_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with patch.dict("os.environ", {DATA_ROOT_ENV: temporary}):
                profile = Path(temporary) / "profiles" / "fusion"
                profile.mkdir(parents=True)
                existing = profile / "user.cfg"
                existing.write_text("user settings", encoding="utf-8")

                with self.assertRaisesRegex(FrontdoorError, "without this app's ownership marker"):
                    ensure_profile("fusion")

                self.assertEqual(existing.read_text(encoding="utf-8"), "user settings")
                self.assertFalse((profile / ".frontdoor-profile.json").exists())

    def test_refuses_profile_with_another_products_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with patch.dict("os.environ", {DATA_ROOT_ENV: temporary}):
                profile = Path(temporary) / "profiles" / "full"
                profile.mkdir(parents=True)
                marker = profile / ".frontdoor-profile.json"
                marker.write_text(
                    json.dumps({"product": "Other CAD", "profile": "full"}),
                    encoding="utf-8",
                )

                with self.assertRaisesRegex(FrontdoorError, "owned by a different setup"):
                    ensure_profile("full")

                self.assertEqual(
                    json.loads(marker.read_text(encoding="utf-8"))["product"],
                    "Other CAD",
                )

    def test_refuses_populated_unowned_install_directory_without_claiming_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with patch.dict("os.environ", {DATA_ROOT_ENV: temporary}):
                target = install_root()
                target.mkdir(parents=True)
                existing = target / "keep.txt"
                existing.write_text("existing installation", encoding="utf-8")

                with self.assertRaisesRegex(FrontdoorError, "unowned install directory"):
                    _claim_install_directory()

                self.assertEqual(existing.read_text(encoding="utf-8"), "existing installation")
                self.assertFalse((Path(temporary) / MANAGED_MARKER).exists())

    def test_claims_empty_managed_directory_with_an_installing_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with patch.dict("os.environ", {DATA_ROOT_ENV: temporary}):
                _claim_install_directory()
                marker = json.loads(
                    (Path(temporary) / MANAGED_MARKER).read_text(encoding="utf-8")
                )

                self.assertEqual(marker["product"], "FreeCAD Fusion Frontdoor")
                self.assertEqual(marker["install_path"], str(install_root()))
                self.assertEqual(marker["state"], "installing")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.build_frontdoor_payload import build_payload


class BuildFrontdoorPayloadTests(unittest.TestCase):
    def test_payload_bytes_are_stable_across_source_mtime_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "FrontdoorUI"
            source.mkdir()
            (source / "InitGui.py").write_text("# init\n", encoding="utf-8")
            (source / "task_surface.py").write_text("# tasks\n", encoding="utf-8")
            (source / "package.xml").write_text("<package />\n", encoding="utf-8")
            first = build_payload(source, root / "one.zip")
            for file in source.iterdir():
                file.touch()
            second = build_payload(source, root / "two.zip")

            self.assertEqual(
                hashlib.sha256(first.read_bytes()).digest(),
                hashlib.sha256(second.read_bytes()).digest(),
            )
            with zipfile.ZipFile(second) as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    {"InitGui.py", "task_surface.py", "package.xml"},
                )


if __name__ == "__main__":
    unittest.main()

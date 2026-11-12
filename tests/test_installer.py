from __future__ import annotations

import unittest

from frontdoor.installer import _is_expected_publisher


class ExpectedPublisherTests(unittest.TestCase):
    def test_accepts_actual_freecad_signer_subject_case_insensitively(self) -> None:
        subject = (
            "CN=The FreeCAD project association AISBL, "
            "O=The FreeCAD project association AISBL, L=Brussels, C=BE"
        )

        self.assertTrue(_is_expected_publisher(subject))

    def test_rejects_unrelated_publisher(self) -> None:
        self.assertFalse(_is_expected_publisher("CN=FreeCAD Tools Ltd, O=FreeCAD Tools Ltd"))


if __name__ == "__main__":
    unittest.main()

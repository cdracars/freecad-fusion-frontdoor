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

    def test_rejects_impostor_company_name_containing_expected_name(self) -> None:
        self.assertFalse(
            _is_expected_publisher(
                "CN=Unrelated Vendor, O=FreeCAD Project Association AISBL Impostor, C=US"
            )
        )

    def test_requires_common_name_and_organization_to_match(self) -> None:
        self.assertFalse(
            _is_expected_publisher(
                "CN=FreeCAD Project Association AISBL, O=Unrelated Vendor, C=US"
            )
        )

    def test_accepts_exact_subject_without_leading_article(self) -> None:
        self.assertTrue(
            _is_expected_publisher(
                "C=BE, O=FreeCAD Project Association AISBL, CN=FreeCAD Project Association AISBL"
            )
        )

    def test_accepts_repeated_unrelated_fields_and_escaped_delimiters(self) -> None:
        self.assertTrue(
            _is_expected_publisher(
                r"CN=The FreeCAD project association AISBL, O=The FreeCAD project association AISBL, "
                r"OU=Research\, Development, OU=CAD, C=BE"
            )
        )

    def test_rejects_ambiguous_duplicate_common_name(self) -> None:
        self.assertFalse(
            _is_expected_publisher(
                "CN=FreeCAD Project Association AISBL, CN=Unrelated Vendor, "
                "O=FreeCAD Project Association AISBL"
            )
        )

    def test_rejects_malformed_trailing_escape(self) -> None:
        self.assertFalse(
            _is_expected_publisher(
                "CN=FreeCAD Project Association AISBL, O=FreeCAD Project Association AISBL\\"
            )
        )


if __name__ == "__main__":
    unittest.main()

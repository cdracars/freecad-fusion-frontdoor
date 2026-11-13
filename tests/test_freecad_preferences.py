from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from frontdoor.errors import FrontdoorError
from frontdoor.preferences import ensure_default_start_page_hidden


class StartPagePreferenceTests(unittest.TestCase):
    def test_hides_start_page_when_no_user_choice_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary)
            config = profile / "user.cfg"
            config.write_text(
                '<FCParameters><FCParamGroup Name="Root"><FCText Name="Keep">value</FCText>'
                "</FCParamGroup></FCParameters>",
                encoding="utf-8",
            )

            ensure_default_start_page_hidden(profile)

            root = ET.parse(config).getroot()
            preference = root.find(
                ".//FCParamGroup[@Name='Root']/FCParamGroup[@Name='BaseApp']/FCParamGroup[@Name='Preferences']"
                "/FCParamGroup[@Name='Mod']/FCParamGroup[@Name='Start']/FCBool[@Name='ShowOnStartup']"
            )
            self.assertIsNotNone(preference)
            self.assertEqual(preference.get("Value"), "0")
            self.assertEqual(
                root.find("./FCParamGroup[@Name='Root']/FCText[@Name='Keep']").text,
                "value",
            )

    def test_preserves_an_existing_user_choice_to_show_start_page(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary)
            config = profile / "user.cfg"
            config.write_text(
                "<FCParameters><FCParamGroup Name='Root'><FCParamGroup Name='BaseApp'>"
                "<FCParamGroup Name='Preferences'><FCParamGroup Name='Mod'>"
                "<FCParamGroup Name='Start'><FCBool Name='ShowOnStartup' Value='1'/>"
                "</FCParamGroup></FCParamGroup></FCParamGroup></FCParamGroup></FCParamGroup></FCParameters>",
                encoding="utf-8",
            )

            ensure_default_start_page_hidden(profile)

            preference = ET.parse(config).getroot().find(
                "./FCParamGroup[@Name='Root']/FCParamGroup[@Name='BaseApp']"
                "/FCParamGroup[@Name='Preferences']/FCParamGroup[@Name='Mod']"
                "/FCParamGroup[@Name='Start']/FCBool[@Name='ShowOnStartup']"
            )
            self.assertEqual(
                len(ET.parse(config).getroot().findall(".//FCBool[@Name='ShowOnStartup']")),
                1,
            )
            self.assertEqual(preference.get("Value"), "1")

    def test_rejects_a_malformed_saved_boolean_without_changing_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary)
            config = profile / "user.cfg"
            original = (
                "<FCParameters><FCParamGroup Name='Root'><FCParamGroup Name='BaseApp'>"
                "<FCParamGroup Name='Preferences'><FCParamGroup Name='Mod'>"
                "<FCParamGroup Name='Start'><FCBool Name='ShowOnStartup' Value='maybe'/>"
                "</FCParamGroup></FCParamGroup></FCParamGroup></FCParamGroup>"
                "</FCParamGroup></FCParameters>"
            )
            config.write_text(original, encoding="utf-8")

            with self.assertRaisesRegex(FrontdoorError, "unexpected format"):
                ensure_default_start_page_hidden(profile)

            self.assertEqual(config.read_text(encoding="utf-8"), original)

    def test_does_not_replace_a_malformed_profile_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary)
            config = profile / "user.cfg"
            original = "<FCParameters>"
            config.write_text(original, encoding="utf-8")

            with self.assertRaises(FrontdoorError):
                ensure_default_start_page_hidden(profile)

            self.assertEqual(config.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()

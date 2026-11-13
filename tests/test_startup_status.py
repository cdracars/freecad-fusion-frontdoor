from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from frontdoor.freecad_addon.FrontdoorUI.startup_status import (
    launch_ready_marker,
    read_launch_ready_marker,
    write_launch_ready_marker,
)


class StartupStatusTests(unittest.TestCase):
    def test_frontdoor_activation_writes_token_scoped_ready_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary)
            token = "0123456789abcdef0123456789abcdef"

            marker = write_launch_ready_marker(
                profile,
                token,
                process_id=321,
                freecad_version="1.1.4",
            )

            self.assertEqual(marker, launch_ready_marker(profile, token))
            self.assertEqual(
                read_launch_ready_marker(profile, token),
                {
                    "token": token,
                    "state": "ready",
                    "pid": 321,
                    "freecad_version": "1.1.4",
                },
            )

    def test_marker_from_another_launch_cannot_confirm_this_launch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary)
            old_token = "0123456789abcdef0123456789abcdef"
            current_token = "abcdef0123456789abcdef0123456789"
            write_launch_ready_marker(
                profile,
                old_token,
                process_id=321,
                freecad_version="1.1.4",
            )

            self.assertIsNone(read_launch_ready_marker(profile, current_token))

    def test_marker_reports_launch_to_workbench_ready_duration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary)
            token = "0123456789abcdef0123456789abcdef"

            marker = write_launch_ready_marker(
                profile,
                token,
                process_id=321,
                freecad_version="1.1.4",
                startup_started_ns=time.perf_counter_ns() - 5_000_000,
            )

            data = read_launch_ready_marker(profile, token)
            self.assertIsNotNone(data)
            self.assertGreaterEqual(data["startup_duration_ms"], 5)
            self.assertLess(data["startup_duration_ms"], 1000)

    def test_invalid_measured_duration_cannot_confirm_startup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary)
            token = "0123456789abcdef0123456789abcdef"
            marker = launch_ready_marker(profile, token)
            marker.parent.mkdir(parents=True)
            marker.write_text(
                '{"token":"%s","state":"ready","pid":321,'
                '"freecad_version":"1.1.4","startup_duration_ms":NaN}' % token,
                encoding="utf-8",
            )

            self.assertIsNone(read_launch_ready_marker(profile, token))

    def test_unrepresentable_duration_cannot_confirm_startup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary)
            token = "0123456789abcdef0123456789abcdef"
            marker = launch_ready_marker(profile, token)
            marker.parent.mkdir(parents=True)
            marker.write_text(
                '{"token":"%s","state":"ready","pid":321,'
                '"freecad_version":"1.1.4","startup_duration_ms":%s}'
                % (token, "9" * 400),
                encoding="utf-8",
            )

            self.assertIsNone(read_launch_ready_marker(profile, token))

    def test_invalid_launch_token_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                launch_ready_marker(Path(temporary), "not-a-launch-token")

    def test_malformed_marker_cannot_confirm_startup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary)
            token = "0123456789abcdef0123456789abcdef"
            marker = launch_ready_marker(profile, token)
            marker.parent.mkdir(parents=True)
            marker.write_text('{"token":"wrong","state":"ready"}', encoding="utf-8")

            self.assertIsNone(read_launch_ready_marker(profile, token))


if __name__ == "__main__":
    unittest.main()

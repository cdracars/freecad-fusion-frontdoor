from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from frontdoor.performance import append_startup_measurement


class StartupMeasurementTests(unittest.TestCase):
    def test_appends_only_the_requested_local_startup_measurement(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            log_path = Path(temporary) / "logs" / "startup.jsonl"
            append_startup_measurement(
                log_path,
                profile="fusion",
                ready={
                    "startup_duration_ms": 2840.1256,
                    "freecad_version": "1.1.4",
                    "pid": 1234,
                },
            )

            record = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(record["metric"], "frontdoor_workbench_ready")
            self.assertEqual(record["profile"], "fusion")
            self.assertEqual(record["freecad_version"], "1.1.4")
            self.assertEqual(record["freecad_pid"], 1234)
            self.assertEqual(record["duration_ms"], 2840.126)
            self.assertIn("recorded_at_utc", record)

    def test_rejects_missing_duration_and_non_fusion_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            log_path = Path(temporary) / "startup.jsonl"
            with self.assertRaises(ValueError):
                append_startup_measurement(
                    log_path,
                    profile="fusion",
                    ready={"freecad_version": "1.1.4", "pid": 1234},
                )
            with self.assertRaises(ValueError):
                append_startup_measurement(
                    log_path,
                    profile="full",
                    ready={"startup_duration_ms": 10, "freecad_version": "1.1.4", "pid": 1234},
                )
            with self.assertRaises(ValueError):
                append_startup_measurement(
                    log_path,
                    profile="fusion",
                    ready={"startup_duration_ms": float("inf")},
                )
            self.assertFalse(log_path.exists())


if __name__ == "__main__":
    unittest.main()

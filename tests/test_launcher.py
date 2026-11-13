from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from frontdoor import launcher


class LaunchEnvironmentTests(unittest.TestCase):
    def test_fusion_launch_receives_a_launch_specific_token(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            executable = Path(temporary) / "FreeCAD"
            executable.write_text("", encoding="utf-8")
            executable.chmod(executable.stat().st_mode | 0o111)
            process = object()
            token = "0123456789abcdef0123456789abcdef"
            environment = {"FRONTDOOR_TEST": "1"}

            with (
                patch.object(launcher, "launch_environment", return_value=environment),
                patch.object(launcher.subprocess, "Popen", return_value=process) as popen,
            ):
                result = launcher.launch_freecad(executable, "fusion", launch_token=token)

            self.assertIs(result, process)
            self.assertEqual(popen.call_args.kwargs["env"]["FRONTDOOR_LAUNCH_TOKEN"], token)
            self.assertGreater(
                int(popen.call_args.kwargs["env"]["FRONTDOOR_LAUNCH_STARTED_NS"]),
                0,
            )

    def test_full_profile_does_not_receive_frontdoor_readiness_token(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            executable = Path(temporary) / "FreeCAD"
            executable.write_text("", encoding="utf-8")
            executable.chmod(executable.stat().st_mode | 0o111)
            environment = {"FRONTDOOR_TEST": "1"}

            with (
                patch.object(launcher, "launch_environment", return_value=environment),
                patch.object(launcher.subprocess, "Popen", return_value=object()) as popen,
            ):
                launcher.launch_freecad(executable, "full")

            self.assertNotIn("FRONTDOOR_LAUNCH_TOKEN", popen.call_args.kwargs["env"])
            self.assertNotIn("FRONTDOOR_LAUNCH_STARTED_NS", popen.call_args.kwargs["env"])


if __name__ == "__main__":
    unittest.main()

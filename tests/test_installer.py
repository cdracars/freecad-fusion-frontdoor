from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from frontdoor import installer
from frontdoor.errors import FrontdoorError
from frontdoor.installer import _is_expected_publisher
from frontdoor.paths import DATA_ROOT_ENV


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


class InstalledFreeCADVersionTests(unittest.TestCase):
    def test_reads_installed_version_with_temporary_isolated_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / "FreeCAD.exe"
            executable.touch()
            command = root / "FreeCADCmd.exe"
            command.touch()
            completed = unittest.mock.Mock(returncode=0, stdout="FreeCAD 1.1.4\n", stderr="")

            with (
                patch.dict(os.environ, {DATA_ROOT_ENV: str(root / "frontdoor-data")}),
                patch.object(installer.subprocess, "run", return_value=completed) as run,
            ):
                self.assertEqual(installer.installed_freecad_version(executable), "1.1.4")

            self.assertEqual(run.call_args.args[0], [str(command), "--version"])
            environment = run.call_args.kwargs["env"]
            self.assertTrue(environment["FREECAD_USER_HOME"].startswith(str(root / "frontdoor-data")))
            self.assertNotEqual(environment["FREECAD_USER_HOME"], os.environ.get("HOME"))
            self.assertEqual(run.call_args.kwargs["timeout"], 60)

    def test_rejects_unrecognized_version_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / "FreeCAD.exe"
            executable.touch()
            (root / "FreeCADCmd.exe").touch()
            completed = unittest.mock.Mock(returncode=0, stdout="no version here", stderr="")

            with (
                patch.dict(os.environ, {DATA_ROOT_ENV: str(root / "frontdoor-data")}),
                patch.object(installer.subprocess, "run", return_value=completed),
                self.assertRaisesRegex(FrontdoorError, "unrecognized result"),
            ):
                installer.installed_freecad_version(executable)

    def test_does_not_use_a_version_checker_outside_the_install_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            install = root / "managed"
            install.mkdir()
            executable = install / "FreeCAD.exe"
            executable.touch()
            (root / "FreeCADCmd.exe").touch()

            with self.assertRaisesRegex(FrontdoorError, "version checker was not found"):
                installer.installed_freecad_version(executable)

    def test_prefers_version_checker_adjacent_to_freecad_for_each_supported_layout(self) -> None:
        for executable_in_bin in (False, True):
            with self.subTest(executable_in_bin=executable_in_bin), tempfile.TemporaryDirectory() as temporary:
                install = Path(temporary) / "managed"
                bin_directory = install / "bin"
                bin_directory.mkdir(parents=True)
                executable_directory = bin_directory if executable_in_bin else install
                executable = executable_directory / "FreeCAD.exe"
                executable.touch()
                adjacent = executable_directory / "FreeCADCmd.exe"
                adjacent.touch()
                other_directory = install if executable_in_bin else bin_directory
                other = other_directory / "FreeCADCmd.exe"
                other.touch()
                versions = {str(adjacent): "1.1.3", str(other): "1.1.4"}

                def run_version_check(arguments, **_kwargs):
                    return unittest.mock.Mock(
                        returncode=0,
                        stdout=f"FreeCAD {versions[arguments[0]]}",
                        stderr="",
                    )

                with (
                    patch.dict(os.environ, {DATA_ROOT_ENV: str(Path(temporary) / "frontdoor-data")}),
                    patch.object(installer.subprocess, "run", side_effect=run_version_check) as run,
                ):
                    self.assertEqual(installer.installed_freecad_version(executable), "1.1.3")

                self.assertEqual(run.call_args.args[0][0], str(adjacent))

    def test_reads_version_from_stderr_when_command_writes_no_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / "FreeCAD.exe"
            executable.touch()
            (root / "FreeCADCmd.exe").touch()
            completed = unittest.mock.Mock(returncode=0, stdout="", stderr="FreeCAD 1.1.4")

            with (
                patch.dict(os.environ, {DATA_ROOT_ENV: str(root / "frontdoor-data")}),
                patch.object(installer.subprocess, "run", return_value=completed),
            ):
                self.assertEqual(installer.installed_freecad_version(executable), "1.1.4")

    def test_refuses_to_accept_a_mismatched_installed_version(self) -> None:
        with patch.object(installer, "installed_freecad_version", return_value="1.1.3"):
            with self.assertRaisesRegex(FrontdoorError, "version record was not updated"):
                installer.verify_installed_freecad_version(Path("FreeCAD.exe"), "1.1.4")


if __name__ == "__main__":
    unittest.main()

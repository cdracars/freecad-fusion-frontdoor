from __future__ import annotations

import unittest
import os
import ssl
from unittest.mock import call, patch

from frontdoor import release


class GithubTlsTests(unittest.TestCase):
    def test_builds_windows_context_from_server_trusted_system_certs(self) -> None:
        context = unittest.mock.Mock()
        windows_certificates = [
            [(b"root", "x509_asn", True), (b"client-only", "x509_asn", {"1.3.6.1.5.5.7.3.2"})],
            [(b"server-intermediate", "x509_asn", {"1.3.6.1.5.5.7.3.1"}), (b"other", "pkcs_7_asn", True)],
        ]

        with (
            patch.object(release, "os", os, create=True),
            patch.object(os, "name", "nt"),
            patch.object(release, "ssl", ssl, create=True),
            patch.object(ssl, "create_default_context", return_value=context),
            patch.object(ssl, "enum_certificates", side_effect=windows_certificates, create=True),
            patch.object(
                ssl,
                "DER_cert_to_PEM_cert",
                side_effect=lambda cert: f"PEM-{cert.decode()}",
            ),
        ):
            built = release._github_ssl_context()

        self.assertIs(built, context)
        self.assertEqual(
            context.load_verify_locations.call_args_list,
            [call(cadata="PEM-root"), call(cadata="PEM-server-intermediate")],
        )

    def test_passes_validated_context_to_urlopen(self) -> None:
        response = unittest.mock.Mock()
        response.geturl.return_value = "https://api.github.com/repos/FreeCAD/FreeCAD/releases/latest"
        context = unittest.mock.sentinel.context

        with (
            patch.object(release, "_github_ssl_context", return_value=context),
            patch.object(release.urllib.request, "urlopen", return_value=response) as urlopen,
        ):
            self.assertIs(
                release.open_github_url("https://api.github.com/repos/FreeCAD/FreeCAD/releases/latest"),
                response,
            )

        self.assertIs(urlopen.call_args.kwargs["context"], context)


if __name__ == "__main__":
    unittest.main()

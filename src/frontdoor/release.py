from __future__ import annotations

import hashlib
import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache
from pathlib import Path
from typing import Callable

from .errors import FrontdoorError
from .models import ReleaseAsset
from .paths import data_root

Progress = Callable[[str, int], None]
FREECAD_RELEASES_API = "https://api.github.com/repos/FreeCAD/FreeCAD/releases/latest"
ALLOWED_GITHUB_HOSTS = {
    "api.github.com",
    "github.com",
    "codeload.github.com",
    "release-assets.githubusercontent.com",
    "objects.githubusercontent.com",
}
SERVER_AUTH_OIDS = {"1.3.6.1.5.5.7.3.1", "2.5.29.37.0"}


@lru_cache(maxsize=1)
def _github_ssl_context() -> ssl.SSLContext:
    """Use the platform's trusted server CAs, including Windows-managed roots."""
    context = ssl.create_default_context()
    if os.name != "nt" or not hasattr(ssl, "enum_certificates"):
        return context

    for store in ("ROOT", "CA"):
        try:
            certificates = ssl.enum_certificates(store)
        except OSError:
            continue
        for certificate, encoding, trust in certificates:
            if encoding != "x509_asn":
                continue
            trusted_for_server = trust is True or (
                isinstance(trust, set) and bool(trust & SERVER_AUTH_OIDS)
            )
            if trusted_for_server:
                context.load_verify_locations(cadata=ssl.DER_cert_to_PEM_cert(certificate))
    return context


def open_github_url(url: str):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "FreeCAD-Fusion-Frontdoor/0.1", "Accept": "application/vnd.github+json"},
    )
    response = urllib.request.urlopen(request, timeout=30, context=_github_ssl_context())
    final = urllib.parse.urlsplit(response.geturl())
    if final.scheme != "https" or final.hostname not in ALLOWED_GITHUB_HOSTS:
        response.close()
        raise FrontdoorError(f"Download redirected to an unexpected host: {response.geturl()}")
    return response


def latest_windows_release(progress: Progress | None = None) -> ReleaseAsset:
    """Return the latest stable x64 Windows installer and its GitHub SHA-256."""
    if progress:
        progress("Checking the latest stable FreeCAD release…", 0)
    try:
        with open_github_url(FREECAD_RELEASES_API) as response:
            release = json.loads(response.read().decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, urllib.error.URLError) as exc:
        raise FrontdoorError(f"Could not read official FreeCAD release information: {exc}") from exc

    if release.get("draft") or release.get("prerelease"):
        raise FrontdoorError("GitHub did not return a stable FreeCAD release.")
    candidates = [
        asset
        for asset in release.get("assets", [])
        if "-Windows-x86_64-" in asset.get("name", "")
        and asset.get("name", "").endswith("-installer.exe")
    ]
    if not candidates:
        raise FrontdoorError("The latest stable release has no Windows x64 installer asset.")
    asset = candidates[0]
    parsed_url = urllib.parse.urlsplit(asset.get("browser_download_url", ""))
    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname != "github.com"
        or not parsed_url.path.startswith("/FreeCAD/FreeCAD/releases/download/")
    ):
        raise FrontdoorError("The release metadata points to an unexpected installer download location.")
    digest = asset.get("digest")
    if not isinstance(digest, str) or not digest.startswith("sha256:") or len(digest.removeprefix("sha256:")) != 64:
        raise FrontdoorError("The release metadata has no usable SHA-256 digest for the Windows installer.")
    try:
        size = int(asset["size"])
    except (KeyError, ValueError, TypeError) as exc:
        raise FrontdoorError("The release metadata has no usable installer size.") from exc
    return ReleaseAsset(
        name=asset["name"],
        version=str(release.get("tag_name", "unknown")),
        download_url=asset["browser_download_url"],
        size=size,
        sha256=digest.removeprefix("sha256:").lower(),
    )


def download_file(
    url: str,
    destination: Path,
    *,
    expected_size: int | None,
    progress: Progress,
    label: str,
) -> Path:
    """Download to a temporary file and atomically publish it at destination."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    total = 0
    try:
        with open_github_url(url) as response, partial.open("wb") as output:
            content_length = response.headers.get("Content-Length")
            reported_size = int(content_length) if content_length and content_length.isdigit() else expected_size
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                output.write(block)
                total += len(block)
                percentage = int(total * 100 / reported_size) if reported_size else 0
                progress(f"{label} ({total // (1024 * 1024)} MB)", min(percentage, 100))
        if expected_size is not None and total != expected_size:
            raise FrontdoorError(f"Download size mismatch: expected {expected_size} bytes, received {total}.")
        partial.replace(destination)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    return destination


def download_verified_installer(asset: ReleaseAsset, progress: Progress) -> Path:
    installer = data_root() / "downloads" / asset.name
    if installer.is_file() and installer.stat().st_size == asset.size:
        if sha256_file(installer) == asset.sha256:
            progress("Using the verified installer already downloaded by this app…", 100)
            return installer
        installer.unlink()
    download_file(
        asset.download_url,
        installer,
        expected_size=asset.size,
        progress=progress,
        label="Downloading FreeCAD",
    )
    progress("Verifying the installer digest…", 0)
    if sha256_file(installer) != asset.sha256:
        installer.unlink(missing_ok=True)
        raise FrontdoorError("FreeCAD installer SHA-256 did not match the official release metadata. The file was removed.")
    return installer


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

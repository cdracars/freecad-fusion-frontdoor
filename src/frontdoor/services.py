from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Callable

from .models import ReleaseAsset, SetupResult
from .paths import (
    FUSION_PROFILE_NAME,
    MANAGED_MARKER,
    data_root,
    executable_candidates,
    install_root,
    managed_executable,
    managed_version,
    profile_root,
    write_managed_marker,
)

Progress = Callable[[str, int], None]
FREECAD_RELEASES_API = "https://api.github.com/repos/FreeCAD/FreeCAD/releases/latest"
ADDON_COMMIT = "332ba07bdcaca194e5a3010d1fc0a365eeaefcf1"
ADDON_ARCHIVE_URL = (
    "https://github.com/arxdsilva/freecad-fusion/archive/"
    f"{ADDON_COMMIT}.zip"
)
ADDON_FOLDER = "freecad-fusion"
ADDON_MARKER = ".frontdoor-addon.json"


class FrontdoorError(RuntimeError):
    """An expected setup failure that is safe to show to the user."""


def _open(url: str) -> object:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "FreeCAD-Fusion-Frontdoor/0.1", "Accept": "application/vnd.github+json"},
    )
    response = urllib.request.urlopen(request, timeout=30)
    final = urllib.parse.urlsplit(response.geturl())
    allowed_hosts = {
        "api.github.com",
        "github.com",
        "codeload.github.com",
        "release-assets.githubusercontent.com",
        "objects.githubusercontent.com",
    }
    if final.scheme != "https" or final.hostname not in allowed_hosts:
        response.close()
        raise FrontdoorError(f"Download redirected to an unexpected host: {response.geturl()}")
    return response


def latest_release(progress: Progress | None = None) -> ReleaseAsset:
    if progress:
        progress("Checking the latest stable FreeCAD release…", 0)
    try:
        with _open(FREECAD_RELEASES_API) as response:
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
        raise FrontdoorError(
            "The latest stable release does not contain a Windows x64 installer. "
            "No alternative download was selected."
        )
    asset = candidates[0]
    parsed_url = urllib.parse.urlsplit(asset.get("browser_download_url", ""))
    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname != "github.com"
        or not parsed_url.path.startswith("/FreeCAD/FreeCAD/releases/download/")
    ):
        raise FrontdoorError("The release metadata points to an unexpected installer download location.")
    digest = asset.get("digest", "")
    if not isinstance(digest, str) or not digest.startswith("sha256:") or len(digest.removeprefix("sha256:")) != 64:
        raise FrontdoorError("The release metadata has no usable SHA-256 digest for the Windows installer.")
    return ReleaseAsset(
        name=asset["name"],
        version=str(release.get("tag_name", "unknown")),
        download_url=asset["browser_download_url"],
        size=int(asset["size"]),
        sha256=digest.removeprefix("sha256:").lower(),
    )


def _download(url: str, destination: Path, expected_size: int | None, progress: Progress, label: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    total = 0
    try:
        with _open(url) as response, partial.open("wb") as output:
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


def download_release_asset(asset: ReleaseAsset, progress: Progress) -> Path:
    installer = data_root() / "downloads" / asset.name
    if installer.is_file() and installer.stat().st_size == asset.size:
        digest = _sha256(installer)
        if digest == asset.sha256:
            progress("Using the verified installer already downloaded by this app…", 100)
            return installer
        installer.unlink()
    _download(asset.download_url, installer, asset.size, progress, "Downloading FreeCAD")
    progress("Verifying the installer digest…", 0)
    digest = _sha256(installer)
    if digest != asset.sha256:
        installer.unlink(missing_ok=True)
        raise FrontdoorError("FreeCAD installer SHA-256 did not match the official release metadata. The file was removed.")
    return installer


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_authenticode(installer: Path) -> None:
    if os.name != "nt":
        raise FrontdoorError("Windows Authenticode verification is available only on Windows.")
    escaped = str(installer).replace("'", "''")
    script = (
        f"$s=Get-AuthenticodeSignature -LiteralPath '{escaped}'; "
        "[pscustomobject]@{Status=[string]$s.Status;Subject=[string]$s.SignerCertificate.Subject} "
        "| ConvertTo-Json -Compress"
    )
    try:
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        result = json.loads(completed.stdout.strip())
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        raise FrontdoorError(f"Could not verify the Windows publisher signature: {exc}") from exc
    subject = result.get("Subject", "")
    if completed.returncode != 0 or result.get("Status") != "Valid":
        raise FrontdoorError(f"Windows reports an invalid or missing installer signature ({result.get('Status', 'unknown')}).")
    if "FreeCAD Project Association AISBL" not in subject:
        raise FrontdoorError(f"The signed installer publisher was not the expected FreeCAD project ({subject or 'unknown'}).")


def _run_installer(installer: Path, target: Path, progress: Progress) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    progress("Installing a separate FreeCAD copy for this Windows user…", 0)
    # FreeCAD's Windows installer documents /S and /D=PATH for per-user silent setup.
    # Keep /NCRC disabled: its integrity check remains on.
    try:
        completed = subprocess.run(
            [str(installer), "/S", f"/D={target}"],
            check=False,
            timeout=30 * 60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise FrontdoorError(f"Could not complete the FreeCAD installer: {exc}") from exc
    if completed.returncode != 0:
        raise FrontdoorError(f"The FreeCAD installer exited with code {completed.returncode}.")
    executable = next((path for path in executable_candidates(target) if path.is_file()), None)
    if executable is None:
        raise FrontdoorError("The installer finished, but FreeCAD.exe was not found in the selected app-managed folder.")


def _safe_extract_addon(archive: Path, destination: Path) -> Path:
    staging = Path(tempfile.mkdtemp(prefix="frontdoor-addon-", dir=data_root()))
    try:
        with zipfile.ZipFile(archive) as bundle:
            entries = bundle.infolist()
            if len(entries) > 1500 or sum(entry.file_size for entry in entries) > 100 * 1024 * 1024:
                raise FrontdoorError("The add-on archive is unexpectedly large and was rejected.")
            for entry in entries:
                relative = PurePosixPath(entry.filename)
                if (
                    "\\" in entry.filename
                    or not relative.parts
                    or (relative.parts and ":" in relative.parts[0])
                    or relative.is_absolute()
                    or ".." in relative.parts
                ):
                    raise FrontdoorError("The add-on archive contains an unsafe path and was rejected.")
                if entry.external_attr >> 16 & 0o170000 == 0o120000:
                    raise FrontdoorError("The add-on archive contains a symbolic link and was rejected.")
                target = (staging / Path(*relative.parts)).resolve()
                if not target.is_relative_to(staging.resolve()):
                    raise FrontdoorError("The add-on archive attempted to write outside its staging directory.")
            bundle.extractall(staging)
        roots = [p for p in staging.iterdir() if p.is_dir() and (p / "InitGui.py").is_file() and (p / "package.xml").is_file()]
        if len(roots) != 1:
            raise FrontdoorError("The pinned add-on archive did not have the expected FreeCAD package layout.")
        addon_destination = destination / ADDON_FOLDER
        marker = addon_destination / ADDON_MARKER
        if addon_destination.exists() and not marker.is_file():
            raise FrontdoorError(
                f"Refusing to overwrite an add-on folder without this app's ownership marker: {addon_destination}"
            )
        replacement = destination / f".{ADDON_FOLDER}.new"
        if replacement.exists():
            shutil.rmtree(replacement)
        shutil.copytree(roots[0], replacement)
        (replacement / ADDON_MARKER).write_text(
            json.dumps({"commit": ADDON_COMMIT, "license": "MIT"}, indent=2), encoding="utf-8"
        )
        if addon_destination.exists():
            shutil.rmtree(addon_destination)
        replacement.replace(addon_destination)
        return addon_destination
    except zipfile.BadZipFile as exc:
        raise FrontdoorError("The downloaded add-on archive is not a valid ZIP file.") from exc
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def install_pinned_addon(progress: Progress) -> Path:
    profile = profile_root(FUSION_PROFILE_NAME)
    mod_directory = profile / "Mod"
    mod_directory.mkdir(parents=True, exist_ok=True)
    archive = data_root() / "downloads" / f"freecad-fusion-{ADDON_COMMIT}.zip"
    if not archive.is_file():
        progress("Downloading the pinned Fusion navigation add-on…", 0)
        _download(ADDON_ARCHIVE_URL, archive, None, progress, "Downloading Fusion add-on")
    progress("Installing Fusion mode into its separate profile…", 0)
    try:
        return _safe_extract_addon(archive, mod_directory)
    except FrontdoorError:
        archive.unlink(missing_ok=True)
        raise


def install_separate_setup(asset: ReleaseAsset, progress: Progress) -> SetupResult:
    if os.name != "nt":
        raise FrontdoorError("The installer can only run on Windows. This development host cannot execute Windows setup.")
    root = data_root()
    root.mkdir(parents=True, exist_ok=True)
    for name in ("fusion", "full"):
        profile = profile_root(name)
        ownership_file = profile / ".frontdoor-profile.json"
        if profile.exists() and ownership_file.is_file():
            try:
                ownership = json.loads(ownership_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise FrontdoorError(f"Could not read the profile ownership record at {profile}.") from exc
            if ownership.get("product") != "FreeCAD Fusion Frontdoor" or ownership.get("profile") != name:
                raise FrontdoorError(f"The profile path is owned by a different setup: {profile}")
        elif profile.exists() and any(profile.iterdir()):
            raise FrontdoorError(
                f"Refusing to use an existing profile directory without this app's ownership marker: {profile}"
            )
    for child in (root / "downloads", install_root(), profile_root("fusion"), profile_root("full")):
        child.mkdir(parents=True, exist_ok=True)
    for profile_name in ("fusion", "full"):
        ownership = profile_root(profile_name) / ".frontdoor-profile.json"
        if not ownership.exists():
            ownership.write_text(
                json.dumps({"product": "FreeCAD Fusion Frontdoor", "profile": profile_name}, indent=2),
                encoding="utf-8",
            )

    marker = root / MANAGED_MARKER
    executable = managed_executable()
    installed_version = managed_version()
    if executable is None:
        if marker.is_file():
            try:
                ownership = json.loads(marker.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise FrontdoorError("The app's install ownership record could not be read safely.") from exc
            if ownership.get("product") != "FreeCAD Fusion Frontdoor":
                raise FrontdoorError("The install directory has an ownership record from another application.")
            if Path(str(ownership.get("install_path", ""))).resolve() != install_root().resolve():
                raise FrontdoorError("The install ownership record points somewhere unexpected.")
        elif install_root().exists() and any(install_root().iterdir()):
            raise FrontdoorError(
                f"The app's install directory already contains files but is not a recognized FreeCAD install: {install_root()}"
            )
        else:
            root.mkdir(parents=True, exist_ok=True)
            marker.write_text(
                json.dumps(
                    {"product": "FreeCAD Fusion Frontdoor", "install_path": str(install_root()), "state": "installing"},
                    indent=2,
                ),
                encoding="utf-8",
            )
        installer = download_release_asset(asset, progress)
        verify_authenticode(installer)
        _run_installer(installer, install_root(), progress)
        executable = next((path for path in executable_candidates() if path.is_file()), None)
        if executable is None:
            raise FrontdoorError("FreeCAD setup returned successfully, but the executable could not be located.")
        installer.unlink(missing_ok=True)
        installed_version = asset.version
    elif installed_version != asset.version:
        progress(f"Updating the app-managed FreeCAD copy to {asset.version}…", 0)
        installer = download_release_asset(asset, progress)
        verify_authenticode(installer)
        _run_installer(installer, install_root(), progress)
        executable = next((path for path in executable_candidates() if path.is_file()), None)
        if executable is None:
            raise FrontdoorError("FreeCAD updated, but its executable could not be located.")
        installer.unlink(missing_ok=True)
        installed_version = asset.version

    # Record ownership only after the executable exists; retries can safely reuse this copy.
    installed_version = installed_version or asset.version
    write_managed_marker(executable=executable, version=installed_version)
    addon_directory = install_pinned_addon(progress)
    if not (addon_directory / "InitGui.py").is_file():
        raise FrontdoorError("The Fusion add-on was copied, but its startup file is missing.")
    return SetupResult(
        executable=executable,
        version=installed_version,
        fusion_profile=profile_root("fusion"),
        full_profile=profile_root("full"),
    )


def launch_freecad(executable: Path, profile_name: str) -> None:
    if not executable.is_file():
        raise FrontdoorError(f"FreeCAD executable was not found: {executable}")
    environment = os.environ.copy()
    from .paths import launch_environment

    environment.update(launch_environment(profile_name))
    try:
        subprocess.Popen([str(executable)], cwd=str(executable.parent), env=environment)
    except OSError as exc:
        raise FrontdoorError(f"Could not launch FreeCAD: {exc}") from exc

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    version: str
    download_url: str
    size: int
    sha256: str


@dataclass(frozen=True)
class SetupResult:
    executable: Path
    version: str
    fusion_profile: Path
    full_profile: Path

# Installation and profile isolation

## User-facing setup contract

The Windows setup path installs an app-managed FreeCAD copy beside any existing copy and prepares two isolated user profiles. Before installation begins, the user must be able to review:

- The FreeCAD version, official download source, installer size, and publisher.
- The managed install directory and both profile directories.
- Which pinned add-on and Frontdoor files will be staged.
- A plain statement that this creates a second copy and does not change the user's ordinary FreeCAD profile.

The desktop UI asks the user to confirm the version, installer size and source, install location, both profile locations, pinned add-on revision, and expected publisher before setup starts. Publisher identity is enforced against the certificate's `CN` and `O` fields; both must exactly match `FreeCAD Project Association AISBL` after case folding and optional removal of the legal leading article `The`. Substring matches and one-field matches are rejected. The UI still needs a Windows visual/interaction review.

## Managed Windows install

1. Read the latest stable x64 Windows installer metadata from the official FreeCAD GitHub releases API. Ignore draft, prerelease, and development releases.
2. Require HTTPS and expected GitHub release hosts. Require an asset size and SHA-256 digest from release metadata.
3. Download to Frontdoor's data area using a temporary file. Verify size and SHA-256 before use.
4. Verify the Windows Authenticode signature and expected FreeCAD Project Association publisher before execution. Require both certificate `CN` and `O` fields to exactly match `FreeCAD Project Association AISBL` case-insensitively, allowing the legal leading article “The”; reject substring and one-field matches. Require signature status `Valid`.
5. Install silently into the app's per-user managed program directory. Do not elevate, change `PATH`, or use `/NCRC`.
6. Confirm the expected `FreeCAD.exe` exists, then query the installed copy with its sibling `FreeCADCmd.exe --version` in a temporary, app-owned profile isolated from the Fusion, Full, and ordinary FreeCAD profiles. Require its reported FreeCAD version to exactly match the selected release before writing or updating the managed-install record or labeling setup ready; release metadata alone is not proof of an installed update.
7. If the installed version does not match, leave the previous managed-install record unchanged and show a retryable error that tells the user to close the managed FreeCAD window and retry setup. Never record the requested release version just because the installer returned success and `FreeCAD.exe` exists.
8. On retry, reuse/repair a correctly owned app-managed directory. Refuse to overwrite an unowned populated directory.

**Windows test evidence (2026-11-12):** the official stable FreeCAD 1.1.4 x64 installer asset (`FreeCAD_1.1.4-Windows-x86_64-py311-installer.exe`) matched release metadata SHA-256 `845f7101d33faf257a82a0cadc5f4f3804441f46ee493eb32b92fcf9c7147a24`. Windows reported Authenticode status `Valid` and signer subject `CN=The FreeCAD project association AISBL, O=The FreeCAD project association AISBL, L=Brussels, C=BE`; the original substring-only publisher check accepted this subject. The managed install completed under the isolated test root, and `FreeCADCmd --version` reported 1.1.4. The Fusion profile, Frontdoor UI, and pinned navigation add-on were staged, and the GUI launched into the Frontdoor workbench. The stricter `CN`/`O` comparison added afterward still needs verification against the real Windows certificate. The setup confirmation exists in source but needs visual/interaction review; upgrade/repair behavior, no-elevation evidence, and preservation of an existing FreeCAD profile remain unverified.

## Profile contract

| Profile | Purpose | Contents |
|---|---|---|
| `fusion` | Frontdoor's Fusion-friendly experience | Isolated FreeCAD config/data/temp paths; Frontdoor UI; pinned navigation add-on; initial theme/workbench/window defaults |
| `full` | Native FreeCAD escape route | Separate clean FreeCAD profile without Frontdoor UI/navigation changes |
| ordinary FreeCAD | User's pre-existing setup | Must not be read-modified or used as Frontdoor's profile |

Profiles live under Frontdoor's app-owned data root and carry ownership markers. Refuse to adopt a populated directory without a valid Frontdoor ownership marker. For each child launch, set FreeCAD's `FREECAD_USER_HOME`, `FREECAD_USER_DATA`, and `FREECAD_USER_TEMP`; redirect `APPDATA`/`LOCALAPPDATA` on Windows or `HOME`/XDG directories on Linux into the selected app-owned profile.

The existing-install CLI can prepare a selected profile around an executable already on the machine. This path must not install, update, or modify that executable. It is a developer/recovery seam, not proof of the managed Windows installer flow.

## Desktop packaging and release candidate

The Windows desktop frontdoor is frozen with Qt for Python's `pyside6-deploy` in explicit `standalone` mode. The first candidate build recipe pins Python 3.13.17 x64, PySide6 6.12.0, Nuitka 4.3.4, ordered-set 4.1.0, and zstandard 0.25.0 in `requirements/windows-build.txt`. It requires Windows x64 and Visual Studio Build Tools with `dumpbin`. Keep high-level deployment settings in `pyproject.toml`; preserve the generated deployment specification under ignored `build/windows/` as build evidence, not in the user-facing ZIP, because it may contain machine-specific paths. Record the build command and revision in candidate evidence. Bundle the Frontdoor workbench source as a resource so the packaged app can stage it into an isolated FreeCAD profile. This exact-version input list is not yet a hash-locked build or proof of byte-for-byte reproducibility.

The project code is MIT-licensed. The first review candidate is an unsigned portable ZIP containing the standalone output, concise setup instructions, the project license, third-party notices, build identity, and a separate SHA-256 sidecar. It is not a final end-user release. Authenticode signing is a separate protected step after the packaged app and complete Windows workflow have passed validation. Review the exact bundled Qt components and required license notices before distributing it. Do not call the artifact reproducible until a second clean Windows build has been compared; pinned inputs alone do not prove byte-for-byte reproducibility.

**Packaging research:** [Windows PySide6 packaging](../research/windows-pyside6-packaging.md) records official Qt, Python packaging, Nuitka, and Microsoft signing sources and the remaining Windows-only checks.

## First-launch defaults

- Fusion profile: select FreeCAD Dark only when no theme choice exists; select Frontdoor as the initial workbench only when no workbench preference exists; maximize the initial window only when no saved window preference exists.
- Fusion profile: default FreeCAD's Start workbench page to hidden using `BaseApp/Preferences/Mod/Start/ShowOnStartup = false` only when that preference is absent. Preserve an existing valid preference value; fail setup with a clear error if the saved value is malformed. This setting is scoped to the Fusion profile.
- Full profile: do not install Frontdoor UI or the Fusion navigation add-on.
- Default sketch: if no face/plane is selected, Frontdoor preselects the active body's XY origin plane. A contextual planar face/plane selection should be respected.
- First start should be ready to model without asking the user to separately choose theme, navigation, or workbench. The Start page default is configured in source; verify on a fresh Windows profile that it no longer replaces the Frontdoor workspace. The Full profile keeps FreeCAD's native Start experience.
- No add-on-specific long data-generation or other blocking modal prerequisite may be left to the user on the first launch. Provision required data in setup when supported; otherwise expose an actionable progress state.

## Readiness and failure reporting

Do not label setup complete until the executable, profile ownership records, staged add-on directories, required files, and intended initial preferences are present. Report each stage distinctly (download, verification, install, profile preparation, extension staging, launch). A process surviving a short startup check is not evidence that the workbench loaded. For a Fusion launch, the app must wait for a token-matched marker written in-process only after `FrontdoorWorkbench` activates and the task surface is shown. This confirms the Frontdoor workbench loaded, not that every modeling command or the navigation add-on is healthy. A stale marker or a successful launcher-process exit cannot confirm workbench load. For Full FreeCAD, report process/handoff state without claiming the Frontdoor workbench is ready.

On failure, preserve enough state to retry or repair safely. Never claim that an existing FreeCAD profile was unchanged without evidence from the path/environment isolation design.

### Pinned add-on replacement and recovery

Install or repair the pinned Fusion navigation add-on transactionally inside the Fusion profile. Refuse to replace an existing add-on unless it contains Frontdoor's ownership marker. Stage and validate the complete replacement before touching the active directory. Activate it with same-volume directory renames, retaining the previous owned directory as a backup until activation succeeds. If activation fails, restore the previous directory before reporting the error. A later retry must recover an interrupted swap: restore the owned backup when the active directory is absent; when a valid active directory exists, remove an owned backup only after confirming activation. Remove stale replacement or backup directories only when they carry the expected Frontdoor ownership marker; leave unowned paths untouched and fail with a clear error. The operation must be idempotent and preserve the prior working add-on across rename failures and process interruption.


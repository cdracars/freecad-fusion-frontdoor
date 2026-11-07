# Installation and profile isolation

## User-facing setup contract

The Windows setup path installs an app-managed FreeCAD copy beside any existing copy and prepares two isolated user profiles. Before installation begins, the user must be able to review:

- The FreeCAD version, official download source, installer size, and publisher.
- The managed install directory and both profile directories.
- Which pinned add-on and Frontdoor files will be staged.
- A plain statement that this creates a second copy and does not change the user's ordinary FreeCAD profile.

The user confirms the setup before any installer is executed. The current desktop UI shows release information and paths but does not yet implement a distinct review/confirmation step; this is an acceptance gap.

## Managed Windows install

1. Read the latest stable x64 Windows installer metadata from the official FreeCAD GitHub releases API. Ignore draft, prerelease, and development releases.
2. Require HTTPS and expected GitHub release hosts. Require an asset size and SHA-256 digest from release metadata.
3. Download to Frontdoor's data area using a temporary file. Verify size and SHA-256 before use.
4. Verify the Windows Authenticode signature and expected FreeCAD Project Association publisher before execution.
5. Install silently into the app's per-user managed program directory. Do not elevate, change `PATH`, or use `/NCRC`.
6. Confirm the expected `FreeCAD.exe` exists before writing the managed-install record or labeling setup ready.
7. On retry, reuse/repair a correctly owned app-managed directory. Refuse to overwrite an unowned populated directory.

The installation code implements the digest, publisher, path, and ownership checks. Windows execution has not been validated in this development environment.

## Profile contract

| Profile | Purpose | Contents |
|---|---|---|
| `fusion` | Frontdoor's Fusion-friendly experience | Isolated FreeCAD config/data/temp paths; Frontdoor UI; pinned navigation add-on; initial theme/workbench/window defaults |
| `full` | Native FreeCAD escape route | Separate clean FreeCAD profile without Frontdoor UI/navigation changes |
| ordinary FreeCAD | User's pre-existing setup | Must not be read-modified or used as Frontdoor's profile |

Profiles live under Frontdoor's app-owned data root and carry ownership markers. Refuse to adopt a populated directory without a valid Frontdoor ownership marker. For each child launch, set FreeCAD's `FREECAD_USER_HOME`, `FREECAD_USER_DATA`, and `FREECAD_USER_TEMP`; redirect `APPDATA`/`LOCALAPPDATA` on Windows or `HOME`/XDG directories on Linux into the selected app-owned profile.

The existing-install CLI can prepare a selected profile around an executable already on the machine. This path must not install, update, or modify that executable. It is a developer/recovery seam, not proof of the managed Windows installer flow.

## First-launch defaults

- Fusion profile: select FreeCAD Dark only when no theme choice exists; select Frontdoor as the initial workbench only when no workbench preference exists; maximize the initial window only when no saved window preference exists.
- Full profile: do not install Frontdoor UI or the Fusion navigation add-on.
- Default sketch: if no face/plane is selected, Frontdoor preselects the active body's XY origin plane. A contextual planar face/plane selection should be respected.
- First start should be ready to model without asking the user to separately choose theme, navigation, or workbench. FreeCAD's Welcome panel still appears in the tested profile; handling or replacing it is unresolved.
- No add-on-specific long data-generation or other blocking modal prerequisite may be left to the user on the first launch. Provision required data in setup when supported; otherwise expose an actionable progress state.

## Readiness and failure reporting

Do not label setup complete until the executable, profile ownership records, staged add-on directories, required files, and intended initial preferences are present. Report each stage distinctly (download, verification, install, profile preparation, extension staging, launch). A process surviving a short startup check is not evidence that the workbench loaded.

On failure, preserve enough state to retry or repair safely. Never claim that an existing FreeCAD profile was unchanged without evidence from the path/environment isolation design.


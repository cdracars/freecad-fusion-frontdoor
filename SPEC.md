# FreeCAD Fusion Frontdoor — Windows MVP specification

## Goal

Give a Fusion user one clear route to a separate FreeCAD installation that starts with Fusion-style navigation and shortcuts, while preserving the user's existing FreeCAD installation and preferences.

This is an independent community tool. It is not affiliated with Autodesk or the FreeCAD project.

## MVP user and platform

- User: a Windows 10/11 x64 Fusion user who wants to try FreeCAD without first learning how to assemble add-ons and preferences.
- App: Python 3.12+ with PySide6; package as a signed Windows desktop app after the workflow has passed Windows validation.
- Setup core: a Python module plus `frontdoor-setup` CLI with no Qt dependency. It can configure an existing FreeCAD executable on Windows or Linux using an isolated profile, independently of the Windows installer flow.
- FreeCAD: latest stable x64 Windows installer published by the official `FreeCAD/FreeCAD` GitHub releases. Exclude prereleases and development builds.
- Fusion add-on: `arxdsilva/freecad-fusion`, pinned to commit `332ba07bdcaca194e5a3010d1fc0a365eeaefcf1` (package version 0.1.1 at that commit). Do not silently follow `main`.
- FreeCAD installation reference: [official Windows installation guide](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Installing_on_Windows.md).
- Profile environment reference: [official startup and configuration guide](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Start_up_and_Configuration.md).

## First-run flow

1. **Review** — show the FreeCAD version, installer size, install location, add-on source, and the exact directories this setup will create. Say plainly that setup creates a second FreeCAD copy and a separate profile.
2. **Install FreeCAD** — download the x64 installer over HTTPS from the selected official release. Verify the downloaded bytes against the SHA-256 digest in GitHub's release metadata. Check the Windows Authenticode signature and expected FreeCAD publisher before running it. Install silently into the app's per-user directory; never request elevation. Do not use the installer `/NCRC` option.
3. **Set up Fusion mode** — unpack the pinned add-on into the Fusion profile's `Mod/freecad-fusion` directory. Set FreeCAD's documented `FREECAD_USER_HOME`, `FREECAD_USER_DATA`, and `FREECAD_USER_TEMP` variables only for this app's launch process, after creating those directories. Never edit the user's regular FreeCAD configuration or `%APPDATA%\FreeCAD` add-on folders.
4. **Launch** — offer `Fusion mode` and `Full FreeCAD`. Both use the app-managed FreeCAD executable. Fusion mode gets the add-on profile; Full FreeCAD gets a clean separate profile without the add-on. The user's original FreeCAD shortcut remains independent.

## Existing-install setup seam

`setup_existing_freecad(executable, profiles, progress)` accepts an existing FreeCAD executable and the requested isolated profiles. It stages the pinned add-on only for Fusion mode and returns the paths needed to launch either profile. It does not download, install, or modify the selected FreeCAD executable. `frontdoor-setup` exposes this operation for local smoke runs; `--launch` opts into starting FreeCAD with the selected profile.

## Safety and recovery

- No administrator rights, registry edits, changes to PATH, or modification of a pre-existing FreeCAD profile.
- Require an explicit confirmation that names the download source, size, install directory, and profile directory before setup starts.
- Do not run an installer if its SHA-256 digest or Authenticode signature is missing or invalid. Show an actionable error instead.
- Download into the app's own data directory; use temporary files and atomic rename; never extract archive entries outside the intended add-on directory.
- Make retry safe: detect an existing app-managed install and offer repair/reuse instead of overwriting an unrelated directory.
- Recovery in this first development slice uses the add-on's `Tools > Restore my previous FreeCAD settings` entry and keeps the profile in place. One-click profile cleanup and app uninstallation are follow-up work; never imply that they are implemented.
- Do not collect telemetry or require an account.

## MVP screens

- **Launchpad/setup**: clear primary setup action, latest stable version and source, install destination, progress and failure details, and a compact explanation of what stays separate.
- **Ready**: two launch actions (Fusion mode / Full FreeCAD), installed version, profile locations, and a link to the add-on's restore instructions.

The existing `prototype.html` remains a visual reference, not the application implementation.

## Explicit non-goals

- Replacing or patching FreeCAD's UI, rebranding FreeCAD, or reproducing Autodesk assets.
- Importing Fusion accounts, cloud projects, or Fusion files.
- Installing unrelated workbenches, CAM post-processors, or Python packages.
- Claiming that the community add-on is Windows-validated before a Windows run confirms it.
- Automatically modifying an existing FreeCAD copy or migrating its settings.

## Acceptance criteria

- A Windows user can install a second FreeCAD copy without admin rights and without changing an existing copy's configuration.
- Downloads are pinned to official release metadata and checked before execution; add-on source is pinned to a commit.
- The add-on is installed only under the isolated Fusion profile; Full FreeCAD launches with a separate clean profile.
- Errors identify the failed step and leave enough state to retry or clean up the app-managed files.
- The UI does not label setup complete until the executable and add-on directory are present.
- The app does not perform Windows installation or profile claims on a non-Windows host.

## Validation still required on Windows

The current development host has no discoverable FreeCAD executable and no PySide6 installed. The setup CLI can target an existing FreeCAD path elsewhere, but a real local launch is still required to confirm profile isolation and add-on startup. A real Windows run is required to confirm NSIS silent-install behavior, publisher certificate subject, Windows profile isolation, and retry behavior. These are release blockers, not implied successes. One-click uninstall is explicitly follow-up work.

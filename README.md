# FreeCAD Fusion Frontdoor

A Windows-first frontdoor for trying FreeCAD with a Fusion-familiar navigation setup and a separate, reversible profile.

## Status

The repo contains a visual mockup and an early Python/PySide6 MVP. The app is designed for Windows. This Linux development environment cannot validate the Windows installer, FreeCAD profile isolation, or add-on startup; see [SPEC.md](SPEC.md) for the release blockers.

The expanded product, UX, architecture, workflow, navigation, and validation specifications are indexed in [`docs/specs/`](docs/specs/README.md).

Track the Windows V1 acceptance gates, evidence, blockers, and next actions in [`docs/v1-progress.md`](docs/v1-progress.md).

## Preview

Open `prototype.html` in a browser. Use the arrows at the bottom of the page (or the left/right arrow keys) to compare the three screens:

- Launchpad
- Guided setup
- Workspace preview

You can also open a specific screen with `?variant=launchpad`, `?variant=guided`, or `?variant=workspace`.

The static visual reference does not install or launch software. The desktop MVP entry point and setup behavior are documented in [SPEC.md](SPEC.md).

## Existing FreeCAD setup command

The setup command is separate from the Qt desktop app, so it can work with a FreeCAD executable already installed on the machine. Run these commands from the repository root (the directory containing `pyproject.toml`). Use a virtual environment; do not install this project into Debian's system Python. It writes only under this app's data directory; it does not modify the selected FreeCAD installation or the normal FreeCAD profile. For example, on Linux:

```sh
cd /path/to/freecad-fusion-frontdoor
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/frontdoor-setup --freecad /usr/bin/freecad --mode fusion
.venv/bin/frontdoor-setup --freecad /usr/bin/freecad --mode fusion --launch fusion
```

Replace `/usr/bin/freecad` with the executable path on your machine. If `python3 -m venv` reports that `ensurepip` is unavailable, install your distribution's `python3-venv` package first.

For a local profile test that keeps all Frontdoor files under the current directory, set a temporary data root before running the command:

```sh
FREECAD_FUSION_FRONTDOOR_HOME="$PWD/.frontdoor-test" .venv/bin/frontdoor-setup --freecad /usr/bin/freecad --mode fusion --launch fusion
```

Use the actual executable path on the machine. `--mode both` prepares both isolated profiles; `--mode full` prepares a clean profile without the add-on. The existing FreeCAD preferences are not intentionally changed. Windows and Linux profile isolation still need an actual local launch to confirm FreeCAD honors the environment variables.

### Managed local smoke windows

On Linux/X11, `frontdoor-smoke` opens up to three FreeCAD windows with unique disposable profiles and records their process and window identities. It closes only windows whose process still carries the matching test profile marker, requests a normal window close first, and confirms the processes exited. Use the same `FREECAD_FUSION_FRONTDOOR_HOME` value for open, status, and close:

```sh
FREECAD_FUSION_FRONTDOOR_HOME="$PWD/.frontdoor-test" .venv/bin/frontdoor-smoke open --freecad /path/to/FreeCAD.AppImage --count 3
FREECAD_FUSION_FRONTDOOR_HOME="$PWD/.frontdoor-test" .venv/bin/frontdoor-smoke status
FREECAD_FUSION_FRONTDOOR_HOME="$PWD/.frontdoor-test" .venv/bin/frontdoor-smoke close --all
```

To inspect a fresh Frontdoor UI startup and native command registration, add `--frontdoor-ui --probe` to `open`. Add `--exercise-new-design` to click the actual New Design button and record the enabled state of the modeling actions. The deterministic modeling pass adds `--exercise-create-sketch --exercise-sketch-geometry --exercise-pocket --exercise-dressups`; it creates a body-owned XY sketch, inserts fixed test profiles through FreeCAD's API, then clicks the Frontdoor Pad, Pocket, Fillet, and Chamfer actions and records solid validity and volume. This validates the command wiring and feature results, not mouse-driven sketching. The runner stages the current task workbench into the disposable profile and writes a JSON report under `.frontdoor-test/smoke-tests/`.

The runner requires an active X11 desktop with `xprop`; it refuses to close an unowned profile. Windows and Wayland smoke-run management are not implemented yet.

## Desktop app development

On a Windows 10/11 x64 machine with Python 3.12+, install the project and launch it with:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[desktop]"
freecad-frontdoor
```

Setup is intentionally disabled on non-Windows hosts. Windows installation and profile isolation still need a real Windows run before this should be used as an installer.

### Build an unsigned Windows preview

The first packaged build is a portable ZIP, not an installer. Build it on Windows x64 with Python 3.13.17 x64 and Visual Studio Build Tools 2022 or later, including the x64 MSVC tools (`dumpbin`). From a PowerShell prompt at the repository root, run:

```powershell
.\scripts\build_windows.ps1
```

The script creates its own `.venv-windows-build`, installs the exact versions in `requirements/windows-build.txt`, and writes the ZIP and SHA-256 sidecar under `dist/`. The candidate is unsigned. It has not yet been built or tested on Windows; do not distribute it as a release. Follow `docs/portable-windows-preview.txt` for the required clean-machine smoke checks. The generated `pysidedeploy.spec` is local build state and is intentionally not included in the candidate.

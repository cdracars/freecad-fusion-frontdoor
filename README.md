# FreeCAD Fusion Frontdoor

A Windows-first frontdoor for trying FreeCAD with a Fusion-familiar navigation setup and a separate, reversible profile.

## Status

The repo contains a visual mockup and an early Python/PySide6 MVP. The app is designed for Windows. This Linux development environment cannot validate the Windows installer, FreeCAD profile isolation, or add-on startup; see [SPEC.md](SPEC.md) for the release blockers.

## Preview

Open `prototype.html` in a browser. Use the arrows at the bottom of the page (or the left/right arrow keys) to compare the three screens:

- Launchpad
- Guided setup
- Workspace preview

You can also open a specific screen with `?variant=launchpad`, `?variant=guided`, or `?variant=workspace`.

The static visual reference does not install or launch software. The desktop MVP entry point and setup behavior are documented in [SPEC.md](SPEC.md).

## Existing FreeCAD setup command

The setup command is separate from the Qt desktop app, so it can work with a FreeCAD executable already installed on the machine. Use a virtual environment; do not install this project into Debian's system Python. It writes only under this app's data directory; it does not modify the selected FreeCAD installation or the normal FreeCAD profile. For example, on Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/frontdoor-setup --freecad /usr/bin/freecad --mode fusion
.venv/bin/frontdoor-setup --freecad /usr/bin/freecad --mode fusion --launch fusion
```

Replace `/usr/bin/freecad` with the executable path on your machine. If `python3 -m venv` reports that `ensurepip` is unavailable, install your distribution's `python3-venv` package first.

Use the actual executable path on the machine. `--mode both` prepares both isolated profiles; `--mode full` prepares a clean profile without the add-on. The existing FreeCAD preferences are not intentionally changed. Windows and Linux profile isolation still need an actual local launch to confirm FreeCAD honors the environment variables.

## Desktop app development

On a Windows 10/11 x64 machine with Python 3.12+, install the project and launch it with:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[desktop]"
freecad-frontdoor
```

Setup is intentionally disabled on non-Windows hosts. Windows installation and profile isolation still need a real Windows run before this should be used as an installer.

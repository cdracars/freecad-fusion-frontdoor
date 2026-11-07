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

## Desktop app development

On a Windows 10/11 x64 machine with Python 3.12+, install the project and launch it with:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
freecad-frontdoor
```

Setup is intentionally disabled on non-Windows hosts. Windows installation and profile isolation still need a real Windows run before this should be used as an installer.

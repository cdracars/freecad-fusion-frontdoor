# Theme and navigation specification

## Theme positioning

No FreeCAD theme has been proven to be a Fusion theme. FreeCAD Dark is the current pragmatic default; describe it as a dark FreeCAD theme. Fusion familiarity should come primarily from the task organization, modeling workflow, command placement, and navigation behavior—not from a palette name.

The Theme module sets `FreeCAD Dark` only in the isolated Fusion profile and only when that profile has no saved theme. It must preserve a later user choice. Theme and canvas/background appearance are distinct settings and should not be conflated. The Full FreeCAD profile remains independent.

Theme comparisons and add-on feasibility evidence are in [the theme and Fusion comparison](../../research/freecad-theme-fusion-comparison.md). OpenDark, Dark-modern, and ProDark are candidates, not accepted Fusion matches. FreeCAD-Ribbon and NeoRibbon are not product dependencies because their documented tab model does not meet Frontdoor's task-navigation goal.

## Navigation behavior

The Fusion-friendly profile stages the `arxdsilva/freecad-fusion` add-on at pinned commit `332ba07bdcaca194e5a3010d1fc0a365eeaefcf1` (recorded package version 0.1.1). The add-on is separate from Frontdoor UI and theme code, and is staged only in the Fusion profile.

Target behavior:

- Familiar pan, orbit, and zoom mappings for mouse and supported input devices.
- Zoom toward the cursor where the FreeCAD build/add-on supports it.
- Drag-to-orbit NaviCube behavior.
- Clickable standard views: Front, Back, Left, Right, Top, Bottom, and Isometric.
- Visible indication of the active navigation style and a reversible native-FreeCAD option.

The add-on's repository describes Fusion-style navigation and drag-to-orbit NaviCube behavior. The local FreeCAD 1.1.1 Linux run is initial smoke evidence only. Windows support, every gesture mapping, saved preferences, high-DPI behavior, and interactions with custom task layouts remain unverified.

## First-launch setup choices

- Do not ask the user to choose a theme or navigation preset that the Fusion profile already selected.
- Avoid third-party theme preference packs that make broad, hard-to-reverse UI changes unless a backup/rollback path is specified.
- Do not expose arbitrary navigation add-on settings in the first-run UI. Keep advanced settings behind an optional preferences surface after the default behavior is verified.
- If an add-on requires first-use data generation, pre-create it when supported or show a Frontdoor-owned progress state; do not strand a new user in an unexplained modal.

## Compatibility declaration

An add-on's upstream Windows claim is not proof of Frontdoor compatibility. Record tested FreeCAD version, OS, display/navigation settings, and observed behaviors before marking a combination ready. Never infer compatibility from a successful download or a process that stays open.


# Theme and navigation specification

## Theme positioning

No FreeCAD theme has been proven to be a Fusion theme. FreeCAD Dark is the current pragmatic default; describe it as a dark FreeCAD theme. Fusion familiarity should come primarily from the task organization, modeling workflow, command placement, and navigation behavior—not from a palette name.

The Theme module sets `FreeCAD Dark` only in the isolated Fusion profile and only when that profile has no saved theme. It must preserve a later user choice. Theme and canvas/background appearance are distinct settings and should not be conflated. The Full FreeCAD profile remains independent.

Theme comparisons and add-on feasibility evidence are in [the theme and Fusion comparison](../../research/freecad-theme-fusion-comparison.md). OpenDark, Dark-modern, and ProDark are candidates, not accepted Fusion matches. FreeCAD-Ribbon and NeoRibbon are not product dependencies because their documented tab model does not meet Frontdoor's task-navigation goal.

## Navigation behavior

The Fusion-friendly profile stages the `arxdsilva/freecad-fusion` add-on at pinned commit `332ba07bdcaca194e5a3010d1fc0a365eeaefcf1` (recorded package version 0.1.1). The add-on is separate from Frontdoor UI and theme code, and is staged only in the Fusion profile.

Target behavior:

- Mouse wheel zooms toward the cursor; middle-button drag pans; Shift + middle-button drag orbits.
- Dragging the center of the NaviCube orbits the model; clicking its faces, edges, or corners selects standard views.
- Clickable standard views include Front, Back, Left, Right, Top, Bottom, and Isometric.
- Show a compact `Fusion navigation` active indicator in Frontdoor's existing task surface. Do not add a toolbar for it. Keep the native menus and add-on's Tools > Restore my previous FreeCAD settings command available.
- Restoring native FreeCAD settings must remove the Fusion indicator and keep the Fusion preset disabled on later starts. Applying the preset again must restore the indicator and mappings.

The pinned add-on implements these mouse mappings through FreeCAD's built-in Revit navigation style and adds drag-to-orbit to the NaviCube. This is a compatibility technique; the user-facing mode name remains `Fusion navigation`. Its keyboard-shortcut remapping is a separate add-on behavior and must remain reversible through the same restore command. The local FreeCAD 1.1.1 Linux run is initial smoke evidence only. Windows behavior, saved preferences, high-DPI behavior, and interactions with custom task layouts remain unverified until the Windows acceptance checks pass.

### Acceptance checks for the Windows navigation pass

1. Start the isolated Fusion profile and confirm the active indicator appears only when the add-on's Fusion preset is enabled.
2. Use a visible test solid and verify wheel zoom is cursor-centered, middle-drag pans, and Shift + middle-drag orbits. Record before/after camera state so a successful launch alone cannot pass this check.
3. Drag the NaviCube center to orbit, then click a face and an edge/corner to confirm orbit and standard-view hit targets remain distinct.
4. Use Tools > Restore my previous FreeCAD settings. Confirm the indicator changes to native navigation, the mouse mapping returns to the saved native setting, and the restored choice persists through a restart.
5. Reapply Fusion navigation and confirm the indicator and mapping return. Confirm the separate Full FreeCAD profile remains unchanged.
6. Repeat the checks at 100% and 150% display scaling. Keep menus usable and do not introduce a new toolbar or hide menus to accommodate the indicator.

Do not mark the navigation pass verified when only the profile, add-on package, startup process, or preference value is present. Gesture and restore behavior must be observed on the stated Windows FreeCAD build.

## First-launch setup choices

- Do not ask the user to choose a theme or navigation preset that the Fusion profile already selected.
- Avoid third-party theme preference packs that make broad, hard-to-reverse UI changes unless a backup/rollback path is specified.
- Do not expose arbitrary navigation add-on settings in the first-run UI. Keep advanced settings behind an optional preferences surface after the default behavior is verified.
- If an add-on requires first-use data generation, pre-create it when supported or show a Frontdoor-owned progress state; do not strand a new user in an unexplained modal.

## Compatibility declaration

An add-on's upstream Windows claim is not proof of Frontdoor compatibility. Record tested FreeCAD version, OS, display/navigation settings, and observed behaviors before marking a combination ready. Never infer compatibility from a successful download or a process that stays open.


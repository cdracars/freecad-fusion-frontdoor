# FreeCAD Fusion Frontdoor — Windows MVP specification

Detailed topic specifications and their status index are maintained in [`docs/specs/`](docs/specs/README.md). This file remains the integration-level MVP acceptance spec.

## Goal

Give a Fusion user one clear route to a separate FreeCAD installation with a curated, familiar modeling experience: a coherent theme, task-based command tabs, and Fusion-style navigation and shortcuts. Keep the user's existing FreeCAD installation and preferences untouched. Describe the result as Fusion-friendly; do not claim that FreeCAD becomes Fusion or is an exact visual clone.

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
2. **Install FreeCAD** — download the x64 installer over HTTPS from the selected official release. Verify the downloaded bytes against the SHA-256 digest in GitHub's release metadata. Check the Windows Authenticode signature and expected FreeCAD publisher before running it. Compare the publisher identity case-insensitively and accept the signer’s legal subject with or without a leading “The”; require signature status `Valid`. Install silently into the app's per-user directory; never request elevation. Do not use the installer `/NCRC` option.
3. **Set up Fusion-friendly mode** — create the isolated profile, install the pinned navigation add-on and Frontdoor-owned UI workbench, and apply the Frontdoor theme. Run compatibility checks before marking each feature ready. Set FreeCAD's documented `FREECAD_USER_HOME`, `FREECAD_USER_DATA`, and `FREECAD_USER_TEMP` variables only for this app's launch process, after creating those directories. Never edit the user's regular FreeCAD configuration or `%APPDATA%\FreeCAD` add-on folders.
4. **Launch** — offer `Fusion-friendly FreeCAD` and `Full FreeCAD`. The first uses the app-managed experience profile; Full FreeCAD uses a clean separate profile without Frontdoor UI changes. The user's original FreeCAD shortcut remains independent.

## Fusion-friendly experience profile

### User experience

- First launch opens a ready-to-model workspace with the Fusion profile's theme and navigation defaults already applied. FreeCAD's first-start setup surface may remain accessible, but should not require the user to select these defaults. The current 1.1.1 test still shows the Welcome panel, so this acceptance condition is not yet met.
- New Frontdoor profiles start FreeCAD maximized. Preserve a later window-size choice once FreeCAD has written one.
- The default theme is FreeCAD Dark. Users can change it later; setup does not ask them to choose among raw FreeCAD theme names.
- Do not show FreeCAD's installed workbenches as the primary tab row. The Fusion-friendly profile uses one Frontdoor-owned **Design** workspace with task tabs modeled on Fusion's Design workspace: `Solid`, `Surface`, `Mesh`, `Sheet Metal`, and `Tools`. Start on `Solid`; hide a task tab when its commands are unavailable in the installed FreeCAD build or staged add-ons.
- Inside task tabs, group commands into short, stable panels such as `Create`, `Modify`, `Assemble`, and `Inspect`. Map buttons to native FreeCAD commands or supported add-on commands; do not invent unavailable functionality. Favor high-frequency actions and put advanced commands in dropdowns or secondary panels.
- Provide a workspace selector for `Design`, `Manufacture`, and `Drawing`. `Manufacture` exposes the installed CAM flow; `Drawing` exposes TechDraw. Workbench internals remain implementation details and must not become the default navigation model.
- Keep FreeCAD's model tree as the Browser and feature-history surface. Do not imitate Fusion's timeline; explain that FreeCAD represents history in its model tree. Provide a clear `Full FreeCAD` launch and an in-app escape route to native menus/workbenches. Specialized BIM, FEM, robot, mesh-processing, and other workbenches remain available there.
- Show a control only when its command exists in the installed FreeCAD/workbench configuration. Do not silently add newly installed workbenches to the Fusion-friendly UI; make expansion deliberate and user-controlled.
- Fusion mode applies the pinned navigation behavior: Fusion-like pan/orbit/zoom mapping, zoom-at-cursor where supported, and draggable NaviCube. Show the active navigation mode in the UI and make the mapping reversible.
- Use original Frontdoor icons and styling. Do not copy Autodesk logos, proprietary icons, or branded assets; do not describe the product as Autodesk Fusion.

### Modular design

The **Experience Profile** module is the single coordinator. Its interface accepts a FreeCAD executable/version, an owned profile path, and requested experience features; it returns a per-feature readiness report and actionable failures. It owns ordering, version checks, staging, and rollback. UI widgets and the installer call this interface instead of installing add-ons or editing FreeCAD preferences themselves.

The coordinator composes these internal modules:

- **Theme module** — set FreeCAD Dark as the initial Fusion-profile theme before first launch; preserve an existing user theme choice on later setup runs. Users can change it later in FreeCAD. OS-matched light/dark switching is follow-up work.
- **Frontdoor UI module** — provide the owned Design/Manufacture/Drawing workspaces, task tabs, command panels, capability checks, and mapping to FreeCAD command IDs. Keep it independent from the launcher, theme, and navigation modules.
- **Navigation module** — stage and configure the pinned navigation add-on, and report whether it loaded. It must not own theme or Frontdoor UI preferences.
- **Recovery module** — disable the Frontdoor workbench and launch the clean Full FreeCAD profile without deleting the user's settings.

Each module may change only the Frontdoor-owned profile. Installing, updating, applying, or disabling any experience feature must leave the user's ordinary FreeCAD profile untouched. Pin every bundled extension to an immutable revision and record its source, version, license, and compatibility status in the installation manifest.

### Frontdoor UI decision

Build a small **Frontdoor-owned FreeCAD workbench** for the task-based command surface. The local FreeCAD-Ribbon test proves that a community add-on can supply a ribbon-shaped control layout, but its tabs remain workbenches. NeoRibbon's sections also follow the active workbench. Neither meets the required task-tab model, so neither is the product UI provider. Keep FreeCAD-Ribbon as an optional disposable-profile reference for layout, command density, and panel behavior; do not make the MVP depend on it or bundle it.

The custom workbench must use FreeCAD's supported workbench/GUI extension points and run inside the FreeCAD process. It must not patch or fork FreeCAD core. Before expanding beyond the initial `Design > Solid` flow, validate that the chosen Qt/FreeCAD APIs can create, switch, and restore task tabs without breaking native command activation. If the API cannot support a stable in-process tab surface, record that constraint and reconsider the UI boundary before adding workflows.

The first prototype slice is deliberately narrow: `Design > Solid` exposes real `Create Sketch`, `Pad`, `Pocket`, `Fillet`, and `Chamfer` actions. Actions invoke FreeCAD's native commands, respect selection/precondition requirements, and are disabled or explained when unavailable. The Frontdoor surface must initialize the native Sketcher and Part Design commands it needs; a fresh Frontdoor launch must not require the user to switch to those workbenches first. If FreeCAD registers a command only after its provider workbench is activated, Frontdoor should load that provider in a controlled way and return to its own workbench before presenting the task surface. Do not report a feature unavailable solely because its provider workbench has not yet been activated. FreeCAD 1.1.1 on Linux registers these commands when `SketcherGui` and `PartDesignGui` are imported; Frontdoor now imports them before constructing the task surface.

The implementation smoke flow uses deterministic geometry: launch a fresh isolated profile directly into Frontdoor; confirm all five task actions are present; create a new design; use Frontdoor's `Create Sketch` action backed by FreeCAD's Part Design New Sketch command, which creates and activates a Part Design body when needed and places the sketch inside it; when nothing is selected, preselect that body's XY origin plane so the default sketch starts without a separate orientation chooser; make a closed 20 × 20 mm rectangle; finish the sketch and use Pad at 10 mm; confirm the body is one valid solid with volume 4,000 mm³ (±0.1 mm³). On the top face, make a closed 10 × 10 mm rectangle; use Pocket at 5 mm and confirm one valid solid with volume 3,500 mm³ (±0.1 mm³). From copies of that result, use Fillet at 1 mm on a valid edge and Chamfer at 1 mm on a valid edge; after each operation confirm the body remains one valid solid. Use the Frontdoor task buttons for each command. Native modeling tasks may briefly show FreeCAD's task controls, but Frontdoor must restore its task surface while preserving the active task; the user must not be left in a native workbench or its toolbar layout. Commands whose preconditions are not met remain disabled with a concise explanation. This prototype validates the interface seam; it does not imply the other task tabs or workspaces are implemented.

## Existing-install setup seam

`setup_existing_freecad(executable, profiles, progress)` accepts an existing FreeCAD executable and the requested isolated profiles. It stages the pinned navigation add-on and Frontdoor UI only for Fusion-friendly mode and returns the paths needed to launch either profile. It does not download, install, or modify the selected FreeCAD executable. `frontdoor-setup` exposes this operation for local smoke runs; `--launch` opts into starting FreeCAD with the selected profile.

For sandboxed local runs, `FREECAD_FUSION_FRONTDOOR_HOME` redirects Frontdoor's data and managed-install paths. The launcher also redirects HOME/XDG (Linux) or APPDATA/LOCALAPPDATA (Windows) for the child FreeCAD process into that profile.

### Test launch lifecycle

Manual FreeCAD smoke runs must have an explicit, reliable lifecycle so repeated UI testing cannot leave ambiguous FreeCAD windows behind. This is a development/test-harness requirement, not a change to the user's ordinary FreeCAD launch behavior.

- Every smoke launch uses a named, isolated Frontdoor test profile and records enough launch identity to distinguish that run from the user's regular FreeCAD processes and other Frontdoor test profiles.
- The harness retains control of the launched GUI process for its full lifetime. If the executable is a wrapper such as an AppImage launcher that hands off to another process, the harness must track the actual GUI process as well as the wrapper; wrapper exit alone does not mean the window closed.
- The harness provides a cleanup action that requests a graceful close and waits for the test-owned GUI process to exit. Force termination is allowed only for a process positively identified as belonging to the selected Frontdoor test profile, after graceful close times out.
- Cleanup must never target a regular FreeCAD process, a process owned by another test profile, or a window selected only by its generic title. If ownership cannot be established, cleanup stops and reports the unresolved process rather than guessing.
- Before starting another smoke run for a profile, the harness checks for an existing process for that same profile and offers/requires cleanup instead of silently opening another copy.
- A run is considered cleaned up only after the harness confirms its test-owned GUI process has exited. A detached GUI process or an untracked window is a failed cleanup outcome and blocks the next run for that profile.

The test harness may be a small wrapper script or an application-owned process manager. Its implementation should prefer stable process ownership and profile-specific identity over desktop automation; window-control tools are optional and are not a substitute for process identity.

The current development harness is `frontdoor-smoke` for Linux/X11. It tags each process with a unique profile path, maps X11 windows to PIDs, requests `WM_DELETE_WINDOW`, and only escalates signals to PIDs whose process environment still matches that exact test profile. Windows and Wayland test-run management remain unimplemented.

## Safety and recovery

- No administrator rights, registry edits, changes to PATH, or modification of a pre-existing FreeCAD profile.
- Require an explicit confirmation that names the download source, size, install directory, and profile directory before setup starts.
- Do not run an installer if its SHA-256 digest or Authenticode signature is missing or invalid. Show an actionable error instead.
- Download into the app's own data directory; use temporary files and atomic rename; never extract archive entries outside the intended add-on directory.
- Make retry safe: detect an existing app-managed install and offer repair/reuse instead of overwriting an unrelated directory.
- Recovery in this first development slice uses the add-on's `Tools > Restore my previous FreeCAD settings` entry and keeps the profile in place. One-click profile cleanup and app uninstallation are follow-up work; never imply that they are implemented.
- Frontdoor UI failure or disable must leave the native FreeCAD interface usable in the app-managed profile. Provide a recovery action that launches clean Full FreeCAD even if the custom workbench fails during startup.
- Theme, Frontdoor UI, and navigation changes must be independently selectable and reversible inside the app-managed profile; failure of one feature must not prevent launching the others or Full FreeCAD.
- Do not collect telemetry or require an account.

## MVP screens

- **Launchpad/setup**: clear primary setup action, latest stable version and source, install destination, progress and failure details, and a compact explanation of what stays separate.
- **Ready**: two launch actions (Fusion mode / Full FreeCAD), installed version, profile locations, and a link to the add-on's restore instructions.

The existing `prototype.html` remains a visual reference, not the application implementation.

## Explicit non-goals

- Forking or patching FreeCAD core, rebranding FreeCAD, or reproducing Autodesk's exact UI or assets.
- Claiming that a dark palette alone makes FreeCAD Fusion-like.
- Importing Fusion accounts, cloud projects, or Fusion files.
- Installing unrelated workbenches, CAM post-processors, or Python packages.
- Claiming that the community add-on is Windows-validated before a Windows run confirms it.
- Automatically modifying an existing FreeCAD copy or migrating its settings.

## Acceptance criteria

- A Windows user can install a second FreeCAD copy without admin rights and without changing an existing copy's configuration.
- Downloads are pinned to official release metadata and checked before execution; add-on source is pinned to a commit.
- The navigation add-on and Frontdoor UI workbench are installed only under the isolated Fusion profile; Full FreeCAD launches with a separate clean profile.
- Fusion-friendly mode has its theme and navigation defaults applied before first launch, so the user does not need to choose them in FreeCAD's first-start setup.
- The first FreeCAD window opens maximized while respecting any window size the user saves afterward.
- The Fusion-friendly UI opens in `Design > Solid` and shows task-oriented tabs and command panels, not a row of FreeCAD workbench names. `Manufacture` and `Drawing` expose available CAM and TechDraw commands. Missing capabilities are omitted cleanly. Specialized workbenches remain accessible through Full FreeCAD.
- On a fresh Frontdoor launch, `Create Sketch`, `Pad`, `Pocket`, `Fillet`, and `Chamfer` are registered and visible without first activating Sketcher or Part Design; their enabled state follows document, sketch, and selection preconditions.
- The deterministic Solid smoke flow completes the specified sketch, Pad, Pocket, Fillet, and Chamfer operations through Frontdoor task buttons; resulting solids pass the stated validity and volume checks. Default XY sketch creation skips the plane chooser when no contextual face or plane is selected. Native modeling tasks preserve the Frontdoor task surface while remaining editable.
- Users can switch independently between Frontdoor theme, UI, and navigation behaviors; disabling the Frontdoor UI restores usable native FreeCAD menus/toolbars without editing the ordinary profile.
- Fusion navigation mappings and NaviCube behavior are verified on each supported FreeCAD/platform combination before being reported ready.
- The Frontdoor's experience is visibly more coherent and familiar in a side-by-side review, while avoiding Autodesk branding/assets and unsupported exact-equivalence claims.
- Errors identify the failed step and leave enough state to retry or clean up the app-managed files.
- The UI does not label setup complete until the executable and add-on directory are present.
- The app does not perform Windows installation or profile claims on a non-Windows host.
- A launcher process that survives its short startup check is not proof that FreeCAD loaded the add-on; manual UI/log confirmation remains necessary.
- Repeated local GUI smoke runs can be started and closed through a tracked lifecycle; cleanup confirms the process for the selected test profile has exited and demonstrably leaves ordinary FreeCAD processes untouched.

## Validation still required on Windows

Local smoke work has used the FreeCAD 1.1.1 Linux AppImage with isolated profiles. An early FreeCAD-Ribbon prototype loaded six curated workbench tabs and opened maximized. An early Frontdoor render showed only the visual `Design > Solid` surface; at that point command availability and modeling behavior had not been tested. Theme persistence, onboarding, and full navigation behavior remain unverified.

The Linux/X11 `frontdoor-smoke` lifecycle was exercised against the FreeCAD 1.1.1 AppImage: it opened three windows, mapped each to a distinct test-profile process, sent a graceful window-close request to each, and confirmed all three processes exited. The recorded run reported `0/3 instance(s) running` afterward. This verifies the local test harness, not the Windows launcher lifecycle.

A fresh Frontdoor profile passed the command-availability check: all five task actions were registered and visible, and `FrontdoorWorkbench` remained active. `New Design` created a document and enabled `Create Sketch`, while feature actions stayed disabled until their preconditions were met. Create Sketch initially used `Sketcher_NewSketch`; the resulting standalone sketch made Pad fail with `Active Body Required`. Frontdoor now maps Create Sketch to `PartDesign_NewSketch`, creates and activates a Part Design body when needed, and selects that body's XY origin plane when nothing is selected.

The deterministic local smoke flow then created a body-owned XY sketch from the Frontdoor button. The probe inserted the closed rectangles through FreeCAD's sketch API to make the geometry repeatable; a real user's mouse-driven drawing gestures have not been validated. It used the Frontdoor Pad action at 10 mm and confirmed one valid solid at 3,999.999999999999 mm³. It selected the top face, created a second body-owned sketch, inserted a closed 10 × 10 mm profile, then used the Frontdoor Pocket action at 5 mm and confirmed one valid solid at 3,499.999999999999 mm³. It deep-copied the Pocket body into separate Fillet and Chamfer branches, invoked each Frontdoor action on an edge, and confirmed each result was one valid solid. The Fillet branch volume was 3,495.707963267949 mm³; the Chamfer branch volume was 3,490 mm³. `FrontdoorWorkbench` remained active, no modal errors occurred, and the isolated run was closed afterward. This validates native command wiring and the deterministic feature flow on Linux/FreeCAD 1.1.1; it does not validate mouse-driven sketching or Windows compatibility.

A real Windows run is required to confirm the installer, publisher certificate subject, Windows profile isolation, theme behavior, Frontdoor UI recovery, navigation behavior, and retry behavior. Windows compatibility and mouse-driven sketching remain unverified. One-click uninstall is explicitly follow-up work.

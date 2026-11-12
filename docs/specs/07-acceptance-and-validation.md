# Acceptance and validation plan

## Evidence labels

- **Verified locally** — observed in the described isolated Linux/X11 FreeCAD 1.1.1 smoke run.
- **Verified on Windows** — observed on the isolated Windows 11 test host with the managed FreeCAD 1.1.4 build; scope is limited to the evidence below.
- **Implemented, unverified** — code exists, but the target behavior has not passed a representative run.
- **Open** — decision or implementation remains incomplete.
- **Deferred** — outside the first usable slice.

## Platform matrix

| Area | Linux FreeCAD 1.1.1 | Windows FreeCAD 1.1.4 | Status |
|---|---|---|---|
| Frontdoor profile starts and loads workbench | Isolated X11 smoke run | GUI smoke: Frontdoor workbench and visible task surface | Both platforms verified for startup; Windows scope is one clean launch |
| Native Solid command registration | Verified | Six required commands present | Windows startup registration verified |
| Sketch, Pad, Pocket | Deterministic API geometry + actual Frontdoor buttons; volumes/validity verified | New Design and Create Sketch buttons; body-owned XY sketch entered edit mode | Windows sketch entry verified; geometry/Pad/Pocket open |
| Fillet/Chamfer branches | Deep-copy branches produced valid single solids | Not run | Linux locally verified; Windows open; 1 mm saved property assertion remains open |
| Smoke process ownership and cleanup | Three-window run closed and confirmed; current modeling run closed | Single test GUI exited with status 0; exact managed executable absent afterward | Linux multi-window harness verified; Windows multi-window lifecycle open |
| Managed FreeCAD download/install | Not applicable in this environment | Official 1.1.4 installer verified and installed to app-owned test path; `FreeCADCmd --version` returned 1.1.4 | Windows managed install path verified in isolated test root |
| SHA-256 and publisher verification | Code present | Release digest matched; Authenticode status `Valid`; signer accepted | Windows verification passed for 1.1.4 asset |
| Profile environment isolation | Used by local test harness | GUI reported `App.getUserAppDataDir()` inside the isolated Fusion profile | Both platforms locally verified for tested launches |
| Theme persistence and first-run Welcome panel | Theme is prefilled; Welcome panel remains | Not assessed | Partial; first-run choice and Windows theme persistence open |
| Fusion navigation mappings/NaviCube | Initial add-on launch only | Add-on staged; navigation behavior not exercised | Open |
| Frontdoor task UI recovery / Full FreeCAD profile | Profile/code path exists; release acceptance incomplete | Full profile not launched | Open |

### Windows smoke evidence (2026-11-12)

On the attached Windows test host, installed the official stable FreeCAD 1.1.4 x64 build under the test root, verified the release SHA-256 and a valid Authenticode signature, and staged the isolated Fusion profile and pinned add-on. The GUI smoke launched that managed executable with `FrontdoorWorkbench`; the Frontdoor Design task surface was visible, all six required commands were registered, and the task buttons created a new document and entered an XY sketch owned by a Part Design body. FreeCAD reported its user data directory inside the isolated Fusion profile, no modal dialogs were observed during the probe, and the process exited with status 0 after the probe closed its document and window. A follow-up process query found no remaining process for that exact managed executable.

This does not validate first-run Welcome behavior, theme or navigation behavior, actual sketch drawing, Pad/Pocket/Fillet/Chamfer modeling, Full FreeCAD recovery, preservation of a pre-existing FreeCAD profile, or opening and closing multiple Windows instances. The test host had no pre-existing FreeCAD installation to compare against.

## Required local test flow

Use the managed `frontdoor-smoke` lifecycle with a disposable profile. Run the command documented in the root README with `--exercise-new-design --exercise-create-sketch --exercise-sketch-geometry --exercise-pocket --exercise-dressups`. Check the emitted report for:

- Native command registration and expected enabled/disabled button states.
- Body-owned sketch, closed wire geometry, correct sketch support.
- Pad/Pocket lengths, one-solid validity, and volume tolerances.
- Separate deep-copy branches for Fillet and Chamfer, valid single-solid results, and feature parameters.
- Frontdoor active after task completion, no unexplained modal errors.
- Test process confirmed exited, without affecting ordinary FreeCAD processes.

The current run confirms feature validity/volume and task-workbench restoration; it does not assert Fillet/Chamfer parameter properties or perform mouse-driven drawing.

## Required Windows validation before release claims

On a real Windows 10/11 x64 host, verify:

1. Official stable metadata, digest, Authenticode chain, expected publisher, installer result, and no elevation.
2. Install beside an existing FreeCAD copy; compare ordinary profile/config files before and after to prove they were not changed.
3. Fusion and Full profile environment variables point only into their respective app-owned directories.
4. Fresh Fusion launch applies the selected theme, navigation behavior, Frontdoor workbench, and initial maximized state without requiring raw preference choices.
5. Saved window-size and theme choices survive repair/relaunch.
6. Core create-sketch/Pad/Pocket/Fillet/Chamfer flow in the actual Windows FreeCAD build.
7. Disable/recovery path reaches usable native Full FreeCAD when Frontdoor UI fails.
8. Retry/update refuses unowned paths, preserves user-selected settings, and leaves ordinary FreeCAD usable.

## Product validation

Before broad distribution, observe Fusion users attempting the first Solid flow without coaching. Record completion, backtracking, disabled-button misunderstandings, and time-to-first-solid. Do not use anecdotal screenshots or internal smoke runs as user-acceptance evidence.

## Release blockers and deferred work

**Release blockers:** actual Windows installer and profile run; Authenticode publisher confirmation; first-run Welcome/onboarding decision; Windows navigation and UI recovery; parameterized Windows Solid workflow; user-facing review/confirmation before install; setup status tied to actual readiness.

**Deferred:** one-click uninstall/profile cleanup, OS-matched themes, importing Fusion data, broad customization of task commands, advanced workspaces beyond validated capabilities, and any assumption that visual similarity alone converts users.


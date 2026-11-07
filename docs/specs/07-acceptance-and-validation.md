# Acceptance and validation plan

## Evidence labels

- **Verified locally** — observed in the described isolated Linux/X11 FreeCAD 1.1.1 smoke run.
- **Implemented, unverified** — code exists, but the target behavior has not passed a representative run.
- **Open** — decision or implementation remains incomplete.
- **Deferred** — outside the first usable slice.

## Platform matrix

| Area | Linux FreeCAD 1.1.1 | Windows target | Status |
|---|---|---|---|
| Frontdoor profile starts and loads workbench | Isolated X11 smoke run | Not run | Linux locally verified; Windows open |
| Native Solid command registration | Verified | Not run | Linux locally verified |
| Sketch, Pad, Pocket | Deterministic API geometry + actual Frontdoor buttons; volumes/validity verified | Not run | Linux command wiring verified; mouse gestures open |
| Fillet/Chamfer branches | Deep-copy branches produced valid single solids | Not run | Linux locally verified; 1 mm saved property assertion remains open |
| Smoke process ownership and cleanup | Three-window run closed and confirmed; current modeling run closed | Not implemented | Linux/X11 harness verified |
| Managed FreeCAD download/install | Not applicable in this environment | Not run | Open |
| SHA-256 and publisher verification | Code present | Not run against Windows installer | Implemented, unverified |
| Profile environment isolation | Used by local test harness | Not run on Windows | Linux smoke isolation verified; Windows open |
| Theme persistence and first-run Welcome panel | Theme is prefilled; Welcome panel remains | Not run | Partial; first-run choice open |
| Fusion navigation mappings/NaviCube | Initial add-on launch only | Not run | Open |
| Frontdoor task UI recovery / Full FreeCAD profile | Profile/code path exists; release acceptance incomplete | Not run | Open |

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


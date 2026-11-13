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
| First-action progression and idle Tasks dock | Linux harness predates this iteration | Fresh isolated profile showed New Design → Create Sketch → native sketch edit → Pad; empty Tasks dock hidden at rest and visible during edit; 1280 × 720 window passed at Qt scale factors 1.0 and 1.5 | Windows verified; Linux and other FreeCAD versions open |
| Native Solid command registration | Verified | Six required commands present | Windows startup registration verified |
| Sketch, Pad, Pocket | Deterministic API geometry + actual Frontdoor buttons; volumes/validity verified | New Design and Create Sketch buttons; body-owned XY sketch entered edit mode | Windows sketch entry verified; geometry/Pad/Pocket open |
| Fillet/Chamfer branches | Deep-copy branches produced valid single solids | Not run | Linux locally verified; Windows open; 1 mm saved property assertion remains open |
| Smoke process ownership and cleanup | Three-window run closed and confirmed; current modeling run closed | Single test GUI exited with status 0; exact managed executable absent afterward | Linux multi-window harness verified; Windows multi-window lifecycle open |
| Frontdoor native toolbar focus | Not run | Idle rows hidden; menus retained; only Edit Mode/Geometries/Constraints shown during sketch; Pad task excludes Sketcher rows; toggle and workbench exit/return restore expected visibility at Qt scale 1.0 and 1.5 | Windows 1.1.4 verified; other builds open |
| Managed FreeCAD download/install | Not applicable in this environment | Official 1.1.4 installer verified and installed to app-owned test path; `FreeCADCmd --version` returned 1.1.4. Current code also verifies the runtime version before recording install/update success, with local regression coverage; the changed verification path has not yet run on Windows. | Windows managed install path previously verified in isolated test root; new version-check behavior pending Windows validation |
| SHA-256 and publisher verification | Code present | Release digest matched; Authenticode status `Valid`; signer accepted | Windows verification passed for 1.1.4 asset |
| Profile environment isolation | Used by local test harness | GUI reported `App.getUserAppDataDir()` inside the isolated Fusion profile | Both platforms locally verified for tested launches |
| Theme persistence and first-run Welcome panel | Theme is prefilled; Fusion setup now defaults `Mod/Start/ShowOnStartup` to false without overriding an existing choice; Full profile is unchanged | Existing Windows smoke opened directly into Frontdoor, but it predates this preference change. The smoke macro now records the effective preference and whether FreeCAD's native `StartView` is open, then asserts the Start page is absent; focused setup tests confirm the value is written only to Fusion. This updated macro has not run on Windows yet; fresh-profile theme persistence not assessed. | Verify a new Windows Fusion profile opens directly to Frontdoor with no Welcome page; verify Full profile keeps native Start behavior; theme persistence and fresh Linux launch open |
| Launch readiness reporting | Token-scoped in-process signal reports Frontdoor workbench/task-surface load for Fusion; Full FreeCAD reports process/handoff without claiming Frontdoor readiness | Unit tests validate marker serialization and token isolation; the signal does not certify all commands or navigation add-on health; Windows FreeCAD activation and process-exit/handoff cases remain untested | Partial; verify the handshake in Windows FreeCAD and exercise delayed activation, early exit, and timeout cases |
| Windows desktop package | Local `pyside6-deploy` standalone ZIP build scaffold; exact-version tool inputs and payload staging code | No Windows build has run; output executable/DLLs, payload staging in frozen runtime, clean-system launch, checksums, and reproducibility remain unverified | Open; build and smoke-test unsigned ZIP on the existing Windows host before signing/release |
| Windows performance baseline | Opt-in local logger estimates launch-request to Frontdoor task-surface `show()` call duration when `FRONTDOOR_PERF_LOG` is set; the core benchmark records model-update/recompute durations | No Windows samples; surface paint/interactive readiness and UI responsiveness are not measured | Open; follow [Windows performance validation](../windows-performance-validation.md), capture ten startup and ten core-operation samples, and add interactive responsiveness measurements before claiming optimization |
| Fusion navigation mappings/NaviCube | Initial add-on launch only | The disabled-preset status displayed `FreeCAD navigation` in an isolated Windows 1.1.4 profile at 100% scale. The 150% smoke exited with `-1073740791` before writing its report. Fusion-enabled status, mouse gestures, NaviCube hit targets, restore/reapply persistence, and Full FreeCAD isolation remain unverified. | Open; Windows acceptance pass defined in [theme and navigation](06-theme-and-navigation.md) |
| Frontdoor task UI recovery / Full FreeCAD profile | Profile/code path exists; release acceptance incomplete | Full profile not launched | Open |

### Windows smoke evidence (2026-11-12)

On the attached Windows test host, installed the official stable FreeCAD 1.1.4 x64 build under the test root, verified the release SHA-256 and a valid Authenticode signature, and staged the isolated Fusion profile and pinned add-on. The GUI smoke launched that managed executable with `FrontdoorWorkbench`; the Frontdoor Design task surface was visible, all six required commands were registered, and the task buttons created a new document and entered an XY sketch owned by a Part Design body. FreeCAD reported its user data directory inside the isolated Fusion profile, no modal dialogs were observed during the probe, and the process exited with status 0 after the probe closed its document and window. A follow-up process query found no remaining process for that exact managed executable.

The managed-install smoke above did not validate theme or navigation behavior, actual sketch drawing, Pad/Pocket/Fillet/Chamfer modeling, Full FreeCAD recovery, preservation of a pre-existing FreeCAD profile, or opening and closing multiple Windows instances. The test host had no pre-existing FreeCAD installation to compare against. First-action startup behavior is covered separately below in a configured fresh profile.

### Windows first-action UI evidence (2026-11-12)

Ran [`tests/frontdoor_first_action_smoke.FCMacro`](../../tests/frontdoor_first_action_smoke.FCMacro) in a newly created, app-owned Fusion test profile with the configured theme and Frontdoor workbench. The captured workspace opened directly in `Design > Solid` without a modal chooser or FreeCAD Basic Setup/Welcome page. The macro verified one visible primary `New Design` action and no downstream modeling commands; after creating a document it verified `Create Sketch` became primary. Sketch creation entered native edit mode on the default XY plane without an orientation dialog, showed the native `Tasks` dock for the edit, and hid it again after the sketch closed. The macro added a closed 20 × 20 mm profile and verified `Pad` became primary, then closed the document and FreeCAD process. All macro assertions passed and the process exited with status 0.

This run verifies command progression and dock visibility, not visual acceptance by Fusion users. It tested a 1280 × 720 logical window with `QT_SCALE_FACTOR=1.0` and `1.5`; it did not change Windows' global display-scaling setting. It does not test a clean unconfigured FreeCAD profile, actual mouse-drawn sketch geometry, feature execution, or ordinary-profile preservation.

### Windows native toolbar focus evidence (2026-11-12)

Ran the expanded [`tests/frontdoor_first_action_smoke.FCMacro`](../../tests/frontdoor_first_action_smoke.FCMacro) after staging the current Frontdoor workbench into the isolated FreeCAD 1.1.4 Fusion test profile. At `QT_SCALE_FACTOR=1.0` and `1.5`, all assertions passed in a 1280 × 720 logical window. The probe confirmed that idle Frontdoor hides native toolbar rows while the menu bar remains visible; the `Toggle Native Toolbars` command restores their captured visibility and toggles back; switching to Part restores visibility and returning to Frontdoor reapplies its focused state. The seven FreeCAD 1.1.4 Sketcher toolbar groups were visible during sketch editing, while unrelated toolbar groups remained hidden. The test sketch progressed through edit and closed-profile states; the document closed, the managed FreeCAD process exited with status 0, and no FreeCAD process remained afterward. This is platform/build-specific UI evidence, not user testing or a guarantee for other FreeCAD releases.

### Windows focused sketch toolbar evidence (2026-11-12)

The same isolated FreeCAD 1.1.4 smoke passed at both Qt scale factors. During sketch edit, its toolbar inventory and action assertions found exactly `Edit Mode`, `Geometries`, and `Constraints` visible, including Line, Rectangle, Dimension, Horizontal/Vertical Constraint, and Leave Sketch. Sketcher management, transform, B-Spline, and Visual Helpers groups were hidden. A native Pad edit remained usable without exposing Sketcher-only toolbar groups; canceling Pad restored the idle Frontdoor layout. The test document and managed FreeCAD process exited cleanly. Sketch geometry was inserted by the test macro, not drawn with a mouse.

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

**Release blockers:** repeatable Windows installer/profile run; Authenticode publisher check against the real signer after hardening; Linux and other-build first-run Welcome behavior; Windows navigation and UI recovery; parameterized Windows Solid workflow; setup status tied to actual readiness.

**Deferred:** one-click uninstall/profile cleanup, OS-matched themes, importing Fusion data, broad customization of task commands, advanced workspaces beyond validated capabilities, and any assumption that visual similarity alone converts users.


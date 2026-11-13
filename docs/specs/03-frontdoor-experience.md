# Frontdoor workspace and first-run experience

## Navigation model

The default experience has two levels:

1. **Workspace:** `Design`, `Manufacture`, or `Drawing` when the corresponding FreeCAD capability is present.
2. **Task tabs:** for Design, start with `Solid`, `Surface`, `Mesh`, `Sheet Metal`, and `Tools`; show only a task surface whose required commands are available.

The primary interface must not be a list of every installed FreeCAD workbench. A new Fusion user should see the common task flow, while specialized BIM, FEM, robotics, mesh-processing, and other capabilities remain reachable through **Full FreeCAD**. Do not silently add newly installed workbenches to Frontdoor.

## Solid layout

- Keep FreeCAD's model tree as the Browser and feature-history surface. Do not manufacture a Fusion-style timeline; explain that FreeCAD represents feature history in its model tree.
- Keep the 3D viewport as the main working area.
- Group the first commands into small `Create` and `Modify` panels. Use short labels and original Frontdoor styling/icons.
- Core Solid workflow commands: `Create Sketch`, `Pad`, `Pocket`, `Fillet`, and `Chamfer`; reveal each when its model prerequisites are met.
- Advanced commands and less common FreeCAD capabilities are not added to the first Solid surface merely because they exist. Add them only after a specific user task justifies them.
- Keep an obvious route to Full FreeCAD and a route back to Frontdoor.

## Next GUI iteration: reduce duplicate native toolbar chrome

**Status: implemented; Windows smoke verified on isolated FreeCAD 1.1.4 at 100% and 150% Qt scale factors.** Frontdoor's task surface already presents the next modeling action, while FreeCAD's native toolbars add a second, dense command surface above it. This iteration makes the Frontdoor workbench feel intentional without removing FreeCAD menus or native task controls. Linux and other FreeCAD builds remain unverified.

- While Frontdoor is active and no native modeling task is being edited, keep FreeCAD's menu bar, document tabs, status bar, model tree, and viewport. Hide the native toolbar rows that duplicate or distract from Frontdoor's task actions.
- Do not remove, replace, or intercept native menus or command behavior. File, Edit, View, and other menus remain available. Frontdoor's own task actions remain the primary modeling entry point.
- During native Sketcher edit, keep the drawing, constraint, and finish-editing tools available without interrupting native task controls. The focused toolbar selection is specified in the next iteration below.
- When sketch edit ends, return to the focused Frontdoor toolbar state. When the user leaves Frontdoor, restore the toolbar visibility that was in effect before Frontdoor changed it.
- Provide a visible, reversible **Toggle Native Toolbars** command in the Frontdoor menu while idle so users can temporarily reveal the regular toolbar set without leaving the task workflow. The command must not persistently rewrite the user's toolbar layout.
- Toolbar control is scoped to the Frontdoor process/profile and is best-effort: unknown or add-on toolbars must not be deleted, renamed, or have their commands modified. If visibility cannot be determined safely, leave that toolbar visible.

### Acceptance checks for native toolbar focus

- On Frontdoor idle launch, the menu bar and normal window/status affordances remain usable, while duplicate native toolbar rows do not compete with the task surface.
- Start native sketch editing and verify the Sketcher drawing/constraining toolbars are available throughout the edit. Finish or cancel the edit and verify Frontdoor's idle toolbar state returns without interrupting the modeling task.
- Toggle **Native Toolbars** on and off and verify each toolbar's prior visibility is restored correctly, including toolbars that were already hidden by the user.
- Switch away from Frontdoor and verify the pre-Frontdoor toolbar visibility is restored. Switch back and verify the focused Frontdoor state is reapplied.
- Close FreeCAD and verify the ordinary FreeCAD profile's toolbar preferences are unchanged.
- Exercise fresh launch, idle, sketch edit, completed edit, canceled edit, temporary toggle, and workbench exit on isolated Windows FreeCAD 1.1.4. Recheck at 100% and 150% scaling and record any version-specific toolbar names or visibility limitations.

### Windows smoke evidence (2026-11-12)

On the isolated Windows FreeCAD 1.1.4 profile, the task smoke passed at Qt scale factors 1.0 and 1.5 in a 1280 × 720 logical-pixel window. It confirmed that idle Frontdoor hides native toolbar rows and preserves the menu bar; the `Toggle Native Toolbars` command restores the visibility captured on Frontdoor entry and toggles back to the focused layout; leaving for Part restores that captured visibility; returning to Frontdoor reapplies the focused layout. The probe deliberately marked the File toolbar as previously hidden to verify that the toggle and workbench exit preserve a hidden state. In this pass, all seven observed Sketcher toolbar groups appeared during edit; the next iteration below narrows this to the groups used for drawing, constraints, and finishing a basic sketch. The native `Tasks` dock remained usable. No smoke assertion failed, the test document closed, and the managed FreeCAD process exited with status 0 at both scale factors. This verifies the toolbar behavior on the tested build, not Linux, other FreeCAD releases, or Fusion-user preference.

## Next GUI iteration: keep sketch edit tools focused

**Status: implemented; Windows smoke verified on isolated FreeCAD 1.1.4 at 100% and 150% Qt scale factors.** The Windows FreeCAD 1.1.4 toolbar inventory showed seven Sketcher groups. Several focus on managing, transforming, or refining specialized geometry: the Sketcher group includes attach/merge/mirror actions, Sketcher Tools includes transforms and offsets, B-Spline Tools contains spline-specific editing commands, and Visual Helpers manages selection overlays. These compete with the first task: draw a profile, apply constraints, and finish the sketch. Linux and other FreeCAD builds remain unverified.

- During native sketch edit, show only `Edit Mode`, `Geometries`, and `Constraints` toolbar groups. These provide Leave Sketch, common profile geometry, and common dimensions/constraints.
- Hide the `Sketcher`, `Sketcher Tools`, `B-Spline Tools`, and `Visual Helpers` groups during basic sketch edit. Their native commands remain available through FreeCAD's menus or the native toolbar restore path; do not unregister or disable commands.
- Keep FreeCAD's sketch task panel and its native accept/cancel controls visible. Maintain Frontdoor's one-line next-step hint.
- When sketch edit ends, hide the native Sketcher groups again and restore the idle Frontdoor layout. A different native edit task must not accidentally show Sketcher-only toolbar groups.
- The `Toggle Native Toolbars` menu command is idle-only. Do not offer it as active during a native task where changing toolbar visibility could obscure editor tools.
- Treat toolbar names not in the known FreeCAD Sketcher set conservatively: preserve their commands and their captured visibility on workbench exit.

### Acceptance checks for focused sketch tools

- In a sketch-edit task, `Geometries`, `Constraints`, and `Edit Mode` are visible, including Line/Rectangle, Dimension/Horizontal/Vertical, and Leave Sketch actions.
- `Sketcher`, `Sketcher Tools`, `B-Spline Tools`, and `Visual Helpers` are hidden while editing a basic sketch; no command is unregistered or removed from menus.
- The native Tasks panel stays visible, sketch geometry can still be created, and finishing/canceling the sketch returns to Frontdoor's idle toolbar state.
- A non-sketch native task does not expose Sketcher-only groups.
- At 100% and 150% Qt scaling, the visible toolbar row set remains usable in a 1280 × 720 logical-pixel window.

### Windows smoke evidence (2026-11-12)

On isolated FreeCAD 1.1.4, the smoke passed at Qt scale factors 1.0 and 1.5 in a 1280 × 720 logical-pixel window. During sketch editing, the only visible Sketcher groups were `Edit Mode`, `Geometries`, and `Constraints`; action assertions confirmed Line, Rectangle, Dimension, Horizontal/Vertical Constraint, and Leave Sketch are present. The Sketcher management, transform, B-Spline, and Visual Helpers groups were hidden. The native Tasks panel remained visible. The probe then entered a native Pad edit task and confirmed Sketcher-only groups stayed hidden; canceling Pad returned to the idle state. All smoke assertions passed, the test document closed, and the managed FreeCAD process exited with status 0 at both scale factors. The probe adds geometry through FreeCAD's API, so mouse-drawn sketching and Fusion-user acceptance remain unverified.

## Next GUI iteration: keep common file and edit actions close

**Status: implemented; isolated Windows smoke verified on FreeCAD 1.1.4 at 100% and 150% Qt scaling.** Hiding FreeCAD's native toolbar rows declutters the idle workspace, but it also removes the one-click New/Open/Save/Undo/Redo controls users commonly expect. `New Design` already provides the New action in every Solid state, so do not duplicate it. The Frontdoor workspace heading now has a compact quick-access group for **Open**, **Save**, **Undo**, and **Redo**.

- Reuse FreeCAD's native command actions so shortcuts, enabled state, file dialogs, undo history, and save behavior remain native. Do not change or duplicate their command implementations.
- Use the existing native icons and tooltips when available. Give each control an accessible name. If a native action cannot be resolved safely, keep the corresponding menu command available and record the limitation rather than creating an unverified substitute.
- Keep the group compact and on the existing workspace-heading row; it must not increase the task surface's vertical height. Separate file actions from undo/redo with a subtle divider.
- **Open** remains available without a document. **Save**, **Undo**, and **Redo** follow FreeCAD's native enabled state and are unavailable when their commands are unavailable.
- Do not add a second New control: the `New Design` task action remains the only New entry point in the Solid workspace.
- Keep the Frontdoor action hierarchy and native toolbar focus behavior unchanged. Quick access remains visible during sketch editing without obscuring native task controls.

The isolated Windows smoke confirmed the four controls are the same native `QAction` objects used by FreeCAD, checked their icons, accessible names and enabled states, and canceled the native Open and Save dialogs while confirming Frontdoor remained usable. It activated Quick Access Undo against a native sketch creation transaction and confirmed the sketch was removed; Quick Access Redo restored it. The probe document was then closed, a fresh document was opened, and the sketch-to-Pad task flow completed. The smoke passed at 1280 × 720 logical pixels at both scale factors, with sketch editing and a feature task still working.

### Acceptance checks for quick access

- The heading row shows Open, Save, Undo, and Redo with their native icons/tooltips; all four use the native FreeCAD command actions.
- There is exactly one New action in the Solid surface in each state: `New Design` in the task action area, with no Quick Access duplicate.
- Open is enabled with or without a document. Save/Undo/Redo enabled state matches FreeCAD's corresponding native actions as the document and undo stack change.
- Invoking Open/Save uses the native file dialog; canceling either dialog leaves the active document and Frontdoor state intact.
- Undo and Redo operate on the active document's native history and return the model to the expected prior/next state.
- The added controls fit on the heading row at 1280 × 720 and 100%/150% Qt scale factors without increasing the task surface's minimum height or covering task controls.
- Sketch and feature tasks remain active and editable when quick-access commands are used or canceled.

## Next GUI iteration: make the first action obvious

**Status: implemented; Windows smoke verified with isolated FreeCAD 1.1.4.** This iteration is limited to the first `Design > Solid` launch and the transition into the first sketch. It does not redesign the complete ribbon, other task tabs, or the launcher. Linux and other FreeCAD versions remain unverified for this iteration.

### First-launch hierarchy

- Open directly in `Design > Solid`. Do not make the user choose a theme, navigation style, or FreeCAD workbench before reaching the modeling workspace.
- When there is no active document, show one visually primary action: **New Design**. Put it at the start of the Solid command area, where the user's next modeling action belongs. Remove the separate, same-priority `New Design` control from the far-right workspace heading; do not duplicate the primary action.
- Keep the viewport as the main area. Pair the primary action with one short, plain-language hint that a new design opens here and the next step is creating a sketch. Do not cover the viewport with a blocking dialog or long onboarding text.
- Keep FreeCAD's native `Tasks` dock hidden when it has no active task content; show it while a native sketch/feature task is active and hide it again when that task closes. An empty dock must not consume canvas space or suggest an unfinished setup step.
- In this no-document state, hide model commands that cannot yet be used (`Create Sketch`, `Pad`, `Pocket`, `Fillet`, `Chamfer`). Do not present a row of disabled controls as if they were equally relevant choices.
- Default `BaseApp/Preferences/Mod/Start/ShowOnStartup` to false in the Fusion profile so FreeCAD does not replace the configured Frontdoor workspace with its Start page. FreeCAD 1.1.4 checks this value before invoking `Start_Start` ([upstream source](https://github.com/FreeCAD/FreeCAD/blob/1.1.4/src/Mod/Start/Gui/AppStartGui.cpp#L77-L86)). Preserve a valid existing value and do not write this preference to the Full profile.
- Do not show FreeCAD's first-run Basic Setup/Welcome page as the main content in the Fusion profile after Frontdoor has configured the requested defaults. Preserve the native Welcome experience in the clean Full FreeCAD profile. If FreeCAD cannot suppress its page safely, keep the Frontdoor task strip and its primary action visible and record the limitation rather than blocking entry to the workspace.

### Progressive next action

1. **No active document:** `New Design` is the sole primary Solid action. Activating it creates one new document and leaves the user in `Design > Solid`.
2. **Empty document:** promote **Create Sketch** to the primary action. Keep `New Design` available as a secondary command. Do not show downstream solid operations until their model prerequisites exist.
3. **Sketch being edited:** retain the native sketch tools and task controls. Show one short instruction that the user should draw a closed profile and finish the sketch to continue. Do not cancel or obscure the native sketch task.
4. **Closed profile ready:** make **Pad** the primary next action. Show other valid, common sketch operations only as secondary actions. Do not show Fillet or Chamfer until a solid and valid edge selection make them applicable.
5. **Existing document opened or restored:** bypass the no-document prompt and choose the next action from the actual document and selection state. Closing the last document returns to the no-document state.

Use one stable primary-action location so the user can follow the sequence without scanning the whole surface. Use a single accent treatment for that action; inactive or secondary actions must not compete with it. Native FreeCAD modeling dialogs and properties remain authoritative for setting operation parameters.

### Acceptance checks for this iteration

- On a fresh Fusion-profile launch with no document, `Design > Solid` is active and the primary `New Design` action is visible without scrolling or opening a menu. The configured Start-page preference prevents the FreeCAD Start page from replacing the Frontdoor workspace; no theme/navigation chooser or FreeCAD Basic Setup/Welcome page blocks entry.
- The native `Tasks` dock is hidden when empty, appears for the native sketch edit task, and is hidden again when that task closes.
- The no-document state does not show disabled sketch/solid commands as prominent choices. One hint explains what `New Design` does and what follows.
- One activation of `New Design` opens exactly one document and changes the primary action to `Create Sketch` in the same location.
- `Create Sketch` uses the active body's XY origin plane when there is no contextual planar selection, opens the native sketch task, and does not show an orientation chooser. Frontdoor stays available while the sketch is edited.
- The sketch-edit state gives a concise next-step instruction. Finishing a closed profile promotes `Pad`; canceling or closing the sketch returns to the correct prior state without creating a duplicate document.
- Opening an existing document does not replace it with the no-document prompt or silently create another document.
- At the supported Windows test size and at a compact 1280 × 720 logical-pixel window, the current state, primary action, and hint remain visible and readable at 100% and 150% display scaling. Controls may reflow, but the primary action must not disappear into overflow.
- Exercise empty, document-open, sketch-edit, sketch-finished, canceled-sketch, and existing-document states in the managed Windows FreeCAD profile. Confirm native modeling behavior and the user's ordinary FreeCAD profile remain unaffected.

## Command states

The Frontdoor surface reflects model context; it does not expose every command as always clickable.

| Context | Primary action | Other visible actions |
|---|---|---|
| No document | New Design | No model commands; Full FreeCAD remains reachable outside the Solid action area |
| Empty document/body | Create Sketch | New Design as a secondary action |
| Sketch being edited | Native sketch tools and task controls | One next-step hint; do not interrupt the edit |
| Closed profile ready in active body | Pad | Other valid sketch operations as secondary actions |
| Valid solid edge selected | Create Sketch remains in the stable primary-action slot | Fillet and Chamfer appear in `Modify` only for valid body-edge selections |

Progressively reveal actions when their prerequisites are met instead of keeping the full command list disabled on the first-run surface. If a visible action becomes unavailable because of a transient context change, provide a concise reason rather than a dead button or raw FreeCAD error.

## Sketch and feature interaction

- `Create Sketch` uses FreeCAD's Part Design New Sketch command so a body is created/activated when needed and the sketch belongs to that body.
- With no contextual selection, create the sketch on the body's XY origin plane without a separate plane chooser.
- With a planar face/plane selected, attach the sketch to that selected context.
- FreeCAD may switch its active workbench while starting a native task. Restore Frontdoor's workbench/task surface without canceling the sketch or feature edit task.
- Pad, Pocket, Fillet, and Chamfer are native FreeCAD operations. The Frontdoor button is the entry point; native task controls remain usable to set/accept/cancel operation parameters.
- Keep the user's current document and native FreeCAD command behavior intact. Frontdoor is a command surface, not a new modeling backend.

## Navigation and view cube

Fusion-friendly mode uses the pinned navigation add-on's mouse gestures: middle-drag pans, Shift + middle-drag orbits, and the wheel zooms toward the cursor. Dragging the center of the NaviCube orbits; clicking its faces, edges, and corners selects standard views. Provide Front/Back/Left/Right/Top/Bottom/Isometric standard views. Standard view controls orient the camera around the model; they do not imply that a particular component (for example, a monitor stand) should be isolated or framed automatically.

Show a compact `Fusion navigation` status in the existing Frontdoor task surface when the preset is active. Keep native menus and the add-on's reversible Tools menu commands; do not add a navigation toolbar. When the user restores native FreeCAD settings, update the status and preserve that choice at later launches. Verify mappings, NaviCube hit targets, restore behavior, and platform behavior per supported FreeCAD version/platform before claiming support.

## First-run behavior

- Default directly to `Design > Solid` after the profile is ready.
- Preconfigure theme, navigation, initial workbench, and initial window state so the user does not need to pick among FreeCAD settings before modeling.
- Do not block the viewport with a long add-on data-generation prompt. If first-use data must be created, provision it before launch when safe or present progress with a clear status.
- A Linux FreeCAD 1.1.1 test previously showed the native Welcome/Start content. Frontdoor now configures the Fusion profile's Start-page preference to hidden when no user choice exists and preserves any existing choice. Verify that behavior on a fresh Windows profile and supported Linux build; until then, treat the source change as implemented but runtime confirmation as open.

## Later workspaces

- `Manufacture` should organize the installed FreeCAD CAM flow, not install unrelated CAM engines or post-processors.
- `Drawing` should organize installed TechDraw commands.
- Surface, Mesh, Sheet Metal, and Tools are target Design task categories, not proof that equivalent command mappings have been implemented. Hide empty/unavailable categories until validated.


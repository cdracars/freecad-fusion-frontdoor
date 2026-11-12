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

## Next GUI iteration: make the first action obvious

**Status: implemented; Windows smoke verified with isolated FreeCAD 1.1.4.** This iteration is limited to the first `Design > Solid` launch and the transition into the first sketch. It does not redesign the complete ribbon, other task tabs, or the launcher. Linux and other FreeCAD versions remain unverified for this iteration.

### First-launch hierarchy

- Open directly in `Design > Solid`. Do not make the user choose a theme, navigation style, or FreeCAD workbench before reaching the modeling workspace.
- When there is no active document, show one visually primary action: **New Design**. Put it at the start of the Solid command area, where the user's next modeling action belongs. Remove the separate, same-priority `New Design` control from the far-right workspace heading; do not duplicate the primary action.
- Keep the viewport as the main area. Pair the primary action with one short, plain-language hint that a new design opens here and the next step is creating a sketch. Do not cover the viewport with a blocking dialog or long onboarding text.
- Keep FreeCAD's native `Tasks` dock hidden when it has no active task content; show it while a native sketch/feature task is active and hide it again when that task closes. An empty dock must not consume canvas space or suggest an unfinished setup step.
- In this no-document state, hide model commands that cannot yet be used (`Create Sketch`, `Pad`, `Pocket`, `Fillet`, `Chamfer`). Do not present a row of disabled controls as if they were equally relevant choices.
- Do not show FreeCAD's first-run Basic Setup/Welcome page as the main content in the Fusion profile after Frontdoor has configured the requested defaults. Preserve the native Welcome experience in the clean Full FreeCAD profile. If FreeCAD cannot suppress its page safely, keep the Frontdoor task strip and its primary action visible and record the limitation rather than blocking entry to the workspace.

### Progressive next action

1. **No active document:** `New Design` is the sole primary Solid action. Activating it creates one new document and leaves the user in `Design > Solid`.
2. **Empty document:** promote **Create Sketch** to the primary action. Keep `New Design` available as a secondary command. Do not show downstream solid operations until their model prerequisites exist.
3. **Sketch being edited:** retain the native sketch tools and task controls. Show one short instruction that the user should draw a closed profile and finish the sketch to continue. Do not cancel or obscure the native sketch task.
4. **Closed profile ready:** make **Pad** the primary next action. Show other valid, common sketch operations only as secondary actions. Do not show Fillet or Chamfer until a solid and valid edge selection make them applicable.
5. **Existing document opened or restored:** bypass the no-document prompt and choose the next action from the actual document and selection state. Closing the last document returns to the no-document state.

Use one stable primary-action location so the user can follow the sequence without scanning the whole surface. Use a single accent treatment for that action; inactive or secondary actions must not compete with it. Native FreeCAD modeling dialogs and properties remain authoritative for setting operation parameters.

### Acceptance checks for this iteration

- On a fresh Fusion-profile launch with no document, `Design > Solid` is active and the primary `New Design` action is visible without scrolling or opening a menu. No theme/navigation chooser or FreeCAD Basic Setup/Welcome page replaces the Frontdoor workspace.
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

Fusion-friendly mode should provide predictable pan, orbit, and zoom gestures, zoom-at-cursor where supported, and a drag-enabled NaviCube. Provide Front/Back/Left/Right/Top/Bottom/Isometric standard views. Standard view controls orient the camera around the model; they do not imply that a particular component (for example, a monitor stand) should be isolated or framed automatically.

Show the active navigation mode and provide a reversible way to select native FreeCAD navigation. Exact mapping, middle-button orbit focus, NaviCube hit testing, and platform behavior must be verified per supported FreeCAD version/platform.

## First-run behavior

- Default directly to `Design > Solid` after the profile is ready.
- Preconfigure theme, navigation, initial workbench, and initial window state so the user does not need to pick among FreeCAD settings before modeling.
- Do not block the viewport with a long add-on data-generation prompt. If first-use data must be created, provision it before launch when safe or present progress with a clear status.
- FreeCAD's current Welcome panel remains visible in Linux 1.1.1 testing. Decide whether to dismiss it, replace it, or retain it with Frontdoor defaults prefilled; do not imply the choice is settled.

## Later workspaces

- `Manufacture` should organize the installed FreeCAD CAM flow, not install unrelated CAM engines or post-processors.
- `Drawing` should organize installed TechDraw commands.
- Surface, Mesh, Sheet Metal, and Tools are target Design task categories, not proof that equivalent command mappings have been implemented. Hide empty/unavailable categories until validated.


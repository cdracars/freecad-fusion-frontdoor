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
- Initial actions: `Create Sketch`, `Pad`, `Pocket`, `Fillet`, `Chamfer`.
- Advanced commands and less common FreeCAD capabilities are not added to the first Solid surface merely because they exist. Add them only after a specific user task justifies them.
- Keep an obvious route to Full FreeCAD and a route back to Frontdoor.

## Command states

The Frontdoor surface reflects model context; it does not expose every command as always clickable.

| Context | Enabled action | Disabled actions |
|---|---|---|
| No document | New Design | Sketch and feature commands |
| Empty document/body | Create Sketch | Pad, Pocket, Fillet, Chamfer |
| Sketch being edited | Native sketch tools and task controls remain usable; Frontdoor surface stays available | Solid feature buttons until a valid sketch is selected/closed |
| Sketch selected in active body | Pad, Pocket | Fillet and Chamfer until a valid edge selection |
| Valid edge selected in active body | Fillet, Chamfer | Unrelated feature actions follow their own preconditions |

When an action is unavailable, show a concise reason rather than a dead button or raw FreeCAD error. The current surface includes context-sensitive enabled state and a short hint; richer per-button explanations remain a design requirement.

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


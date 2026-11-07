# Solid modeling workflow specification

## Scope

This is the first real modeling slice for Frontdoor. It verifies that the task surface can organize native FreeCAD operations, maintain body/sketch context, and remain present when native workbench commands change the active workbench. It is not a claim that other Fusion workspaces or task tabs are ready.

## Command map

| Frontdoor label | FreeCAD command | Preconditions |
|---|---|---|
| New Design | `Std_New` | Always |
| Create Sketch | `PartDesign_NewSketch` | Active document |
| Pad | `PartDesign_Pad` | Closed/selectable sketch in active Part Design body |
| Pocket | `PartDesign_Pocket` | Closed/selectable sketch in active Part Design body |
| Fillet | `PartDesign_Fillet` | Valid edge(s) in active body |
| Chamfer | `PartDesign_Chamfer` | Valid edge(s) in active body |

The task action may create and activate a Part Design body when the document has none. When the user has no contextual face/plane selected, it chooses that body's XY origin plane. FreeCAD's Part Design New Sketch command is used because the generic Sketcher command can make a standalone sketch that cannot be padded in the intended workflow.

## User flow and measurable acceptance

1. Start a fresh isolated profile directly in Frontdoor.
2. Confirm all five modeling actions are registered and visible. With no document, only New Design is enabled.
3. Click New Design. Confirm a document is created and Create Sketch becomes enabled.
4. Click Create Sketch. Confirm the sketch is inside an active Part Design body, on XY when there is no contextual selection, and remains in edit mode while Frontdoor remains the active workbench/task surface.
5. Draw a closed 20 × 20 mm rectangle. Finish sketch and click Pad. Use 10 mm. Confirm one valid solid with volume 4,000 mm³ ±0.1 mm³.
6. Select the top face and create a face-attached sketch. Draw a closed 10 × 10 mm rectangle. Finish sketch and click Pocket. Use 5 mm. Confirm one valid solid with volume 3,500 mm³ ±0.1 mm³.
7. Make two deep copies of the Pocket result. On one branch, select a valid edge, apply a 1 mm Fillet, and confirm one valid solid. On the other, select a valid edge, apply a 1 mm Chamfer, and confirm one valid solid.
8. Confirm Frontdoor remains active after each native task, no unrelated modal error remains, and cleanup confirms the smoke-test process exited.

The smoke harness currently inserts the rectangle geometry through FreeCAD's API so feature tests are deterministic. It clicks the actual Frontdoor command buttons, but it does not validate a person's mouse-driven rectangle drawing, constraints, or dimension entry. Add a separate interactive acceptance run before calling the complete first-modeling experience verified.

## Current verification record

On FreeCAD 1.1.1 Linux AppImage, isolated profile, the deterministic smoke run confirmed:

- `PartDesign_NewSketch` created a body-owned XY sketch.
- Four sketch edges formed one valid closed wire.
- Pad created one valid solid, length 10 mm, volume 3,999.999999999999 mm³.
- Pocket was attached to the Pad's top face, created one valid solid, length 5 mm, volume 3,499.999999999999 mm³.
- Deep-copy Fillet branch created a valid single solid with volume 3,495.707963267949 mm³.
- Deep-copy Chamfer branch created a valid single solid with volume 3,490 mm³.
- Frontdoor remained active; the probe recorded no modal errors; the managed smoke process exited.

The probe relied on FreeCAD's default Fillet/Chamfer parameter values and did not independently assert the saved Radius/Size property value. Add that assertion before marking the 1 mm parameter criterion verified.

## Failure and recovery behavior

- No document: keep feature buttons disabled; no raw traceback in the user-facing task surface.
- No active body: Create Sketch should establish one before invoking the native command.
- Invalid or open sketch: Pad/Pocket remain disabled or surface a concise native validation error while keeping the document usable.
- No valid edge selection: Fillet/Chamfer remain disabled.
- Native command changes the active workbench: restore Frontdoor without closing the native task.
- Operation fails: retain the document and selection context for correction; do not mark the profile setup as failed.


# Frontdoor FreeCAD workbench prototype

This workbench is the first in-process UI slice for FreeCAD Fusion Frontdoor. It adds a top-docked `Design > Solid` task surface and calls FreeCAD's native Sketcher and Part Design commands.

Prototype actions:

- New Design (`Std_New`)
- Create Sketch (`PartDesign_NewSketch`)
- Pad and Pocket (`PartDesign_Pad`, `PartDesign_Pocket`)
- Fillet and Chamfer (`PartDesign_Fillet`, `PartDesign_Chamfer`)

Create Sketch uses Part Design's native command so the sketch belongs to an active Part Design body. If no body exists, Frontdoor creates and activates one; when no face or plane is selected, it preselects the body's XY origin plane. After a native modeling command changes the active workbench, Frontdoor restores its workbench while keeping the native edit task active.

The UI is intentionally limited to the Solid task for now. It keeps FreeCAD's native menus and task dialogs available, and does not patch FreeCAD core. The task surface is hidden when the user leaves the Frontdoor workbench.

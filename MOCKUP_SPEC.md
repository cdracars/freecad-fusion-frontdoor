# Fusion-to-FreeCAD Frontdoor Mockup

## Purpose

Visualize a Windows frontdoor installer/launcher that helps Fusion users start FreeCAD in a familiar, focused workspace. The mockup should make the intended first-run experience easy to judge quickly.

## Audience and job

Fusion users considering FreeCAD should be able to understand, at a glance, what the setup changes, what it keeps safe, and how they get into modeling.

## First screen should communicate

- This is a setup concept for FreeCAD users coming from Fusion.
- The setup is meant to provide familiar navigation and a focused workspace.
- Existing FreeCAD setup and preferences should be kept separate and easy to restore.
- Full FreeCAD remains available when needed.
- The current artifact is a visual mockup; no installation or configuration will run.

## Three visual layouts

- **Launchpad:** a compact desktop control center with a clear primary setup action, a small step rail, and a visible resulting-workspace preview.
- **Guided setup:** a linear, low-noise sequence with setup choices and safety details grouped by step.
- **Workspace preview:** the FreeCAD canvas is the main event; the frontdoor previews the focused workspace and exposes setup controls beside it.

All variants share the same content and product claims. They differ in hierarchy, layout, and primary visual focus, and are switchable through a prototype-only bottom bar and `?variant=` URL parameter.

## Visual direction

Use a polished desktop CAD application language that feels familiar to Fusion users without copying Fusion's branding: deep graphite surfaces, restrained warm-orange action color, compact engineering controls, a substantial model viewport, and Windows-style application framing. Favor an explicit setup sequence and restrained material detail over a generic web dashboard.

## Scope and constraints

- Single self-contained HTML/CSS/JS file; no framework or backend.
- Desktop-first Windows application mockup, responsive enough to inspect on a narrow viewport.
- No downloads, file changes, account flow, telemetry, or installer behavior.
- No claims that Windows compatibility is already verified.
- No invented customer quotes, adoption statistics, or product proof.
- Prototype controls only switch between the three visual variants.

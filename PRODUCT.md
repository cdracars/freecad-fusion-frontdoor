# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Single-file HTML/CSS/JS mockup, selected by the user for immediate sharing and iteration.

## Users

Autodesk Fusion users on Windows who are considering switching to FreeCAD and want a familiar, low-friction first run.

## Product Purpose

A frontdoor installer and launcher that sets up FreeCAD in a Fusion-familiar mode, then starts the configured application. Success means users can install and launch a usable FreeCAD setup without manually finding extensions, themes, and preferences.

## Positioning

Keep FreeCAD's full capability while making the first-run experience feel familiar to Fusion users through a curated, reversible setup.

## Operating Context

The first target is Windows. The frontdoor should install FreeCAD alongside any existing installation, apply a separate user profile, and provide a launcher for the configured experience.

## Capabilities and Constraints

- The current deliverable is an interactive visual mockup, not a working installer.
- A proposed Fusion-like navigation add-on exists, but its Windows behavior needs validation.
- The intended experience includes a focused workspace and a clear route back to full FreeCAD.
- FreeCAD already includes CAM; any guided CAM flow in this product would organize existing FreeCAD capabilities.
- Product name, installer technology, and detailed setup steps remain undecided.

## Evidence on Hand

- Existing community add-on: https://github.com/arxdsilva/freecad-fusion. Its README describes Fusion-style mouse navigation, NaviCube drag-to-orbit, and keyboard shortcuts. It says it was tested on FreeCAD 1.1 on macOS; Windows support is claimed by an installer script but is not confirmed by that test note.
- No user testing, installer implementation, or Windows compatibility results exist yet.

## Product Principles

- Make the setup reversible and keep the user's existing FreeCAD configuration safe.
- Let users reach familiar modeling work quickly.
- Keep the full FreeCAD toolset available when they need it.
- Treat compatibility and installation progress honestly; don't claim success before it is verified.

## Accessibility & Inclusion

No product-specific accessibility requirements have been established yet.

# Product

<!-- impeccable:product-schema 1 -->

## Platform

Windows 10/11 x64 desktop app (MVP)

## Stack

Python 3.12+ setup core and CLI, with PySide6 as an optional desktop UI dependency. The existing single-file HTML/CSS/JS mockup remains a visual reference.

## Users

Autodesk Fusion users on Windows who are considering switching to FreeCAD and want a familiar, low-friction first run.

## Product Purpose

A frontdoor installer and launcher that sets up FreeCAD in a Fusion-familiar mode, then starts the configured application. Success means users can install and launch a usable FreeCAD setup without manually finding extensions, themes, and preferences.

## Positioning

Keep FreeCAD's full capability while making the first-run experience feel familiar to Fusion users through a curated, reversible setup.

## Operating Context

The first target is Windows. The frontdoor should install FreeCAD alongside any existing installation, apply a separate user profile, and provide a launcher for the configured experience.

## Capabilities and Constraints

- The frontdoor implementation is an MVP in development; the current HTML deliverable remains visual-only.
- A proposed Fusion-like navigation add-on exists, but its Windows behavior needs validation.
- Install the current stable official Windows FreeCAD release into a separate per-user location; configure an app-managed profile without changing existing FreeCAD settings.
- Pin the community add-on to a specific commit rather than tracking its moving default branch.
- Provide a standalone setup command that can prepare an isolated Fusion profile around an existing FreeCAD executable, without installing or modifying that executable.
- The intended experience includes a focused workspace and a clear route back to full FreeCAD.
- FreeCAD already includes CAM; any guided CAM flow in this product would organize existing FreeCAD capabilities.
- Product name and overall technology are working choices; signing, packaging, and one-click cleanup remain future work.

## Evidence on Hand

- Existing community add-on: https://github.com/arxdsilva/freecad-fusion. Its README describes Fusion-style mouse navigation, NaviCube drag-to-orbit, and keyboard shortcuts. It says it was tested on FreeCAD 1.1 on macOS; Windows support is claimed by an installer script but is not confirmed by that test note.
- No real Windows execution, user testing, or Windows compatibility results exist yet.

## Product Principles

- Make the setup reversible and keep the user's existing FreeCAD configuration safe.
- Let users reach familiar modeling work quickly.
- Keep the full FreeCAD toolset available when they need it.
- Treat compatibility and installation progress honestly; don't claim success before it is verified.

## Accessibility & Inclusion

No product-specific accessibility requirements have been established yet.

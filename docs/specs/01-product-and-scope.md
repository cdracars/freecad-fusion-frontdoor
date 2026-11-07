# Product goals and scope

## User problem

FreeCAD can do far more than a first-time user needs, but its workbench-oriented interface, configuration choices, navigation differences, and extension setup make the first modeling session difficult for a Fusion user to pick up. Frontdoor should make the first useful task obvious and make the separate setup safe to try.

## Primary user and job

**Primary user:** a Windows 10/11 x64 Autodesk Fusion user evaluating FreeCAD for personal or professional design work.

**Job:** “When I try FreeCAD, help me get to familiar sketch-and-feature modeling without first sorting through every workbench and preference. Keep my current CAD setup intact, and let me switch to the full FreeCAD interface whenever I need it.”

The product has not yet completed customer interviews or usability testing. This is a target-user hypothesis, not a validated market claim.

## Product outcome

A user can install a second FreeCAD copy, launch a curated Fusion-friendly profile, create a first solid through a task-oriented interface, and return to a clean Full FreeCAD profile without changing their ordinary FreeCAD settings.

The tool is an independent community project. It is not affiliated with Autodesk or the FreeCAD project. Describe the result as **Fusion-friendly**; do not claim exact equivalence or use Autodesk branding and proprietary assets.

## Product principles

1. **Protect the existing setup.** Use a separate app-managed installation and separate profiles. Never silently edit or migrate ordinary FreeCAD preferences.
2. **Start with common work.** Show a short, useful Solid workflow first. Keep advanced and specialized tools reachable through Full FreeCAD.
3. **Use native FreeCAD behavior.** Frontdoor organizes commands and defaults; it does not replace FreeCAD's modeling kernel, document format, feature history, or command implementation.
4. **Be honest about compatibility.** A profile being staged or a process remaining open does not prove that an add-on loaded or that a feature works.
5. **Keep features modular and reversible.** Theme, navigation, and Frontdoor UI have distinct responsibilities and should be independently recoverable.
6. **No account or telemetry requirement.** The MVP is a local desktop setup tool.

## MVP scope

- Windows x64 installer and launcher for a separate stable FreeCAD copy.
- A no-Qt setup core and CLI usable with an existing FreeCAD executable for development and recovery scenarios.
- Two app-owned profiles: Fusion-friendly and Full FreeCAD.
- Pinned Fusion-navigation add-on, a Frontdoor-owned in-process workbench, a default dark FreeCAD theme, and first-launch window sizing in the Fusion-friendly profile.
- The initial Frontdoor work surface is **Design > Solid** with `Create Sketch`, `Pad`, `Pocket`, `Fillet`, and `Chamfer`.
- Release/setup information, progress, actionable failure state, and separate launch actions.
- Explicit recovery access to native FreeCAD and to Full FreeCAD.

## Non-goals for the MVP

- Reproducing Fusion's exact look, icons, branding, timeline, cloud services, or file format.
- Replacing FreeCAD or modifying/forking its core.
- Importing a Fusion account, cloud project, or Fusion document.
- Presenting every installed FreeCAD workbench in the default UI.
- Bundling FreeCAD-Ribbon, NeoRibbon, or unrelated workbenches as a prerequisite.
- Automatic migration of existing FreeCAD preferences or files.
- One-click app uninstall or removal of the managed profile.
- Claiming Windows compatibility before an actual Windows run.

## Decisions and remaining choices

| Topic | Current direction | Status |
|---|---|---|
| Product platform | Windows 10/11 x64 first | Decision |
| Setup implementation | Python 3.12+, optional PySide6 desktop UI; no Rust requirement | Decision |
| Visual prototype | One self-contained HTML/CSS/JS artifact; visual reference only | Implemented |
| FreeCAD integration | Frontdoor-owned Python workbench using supported GUI extension points | Implemented for initial Solid slice |
| Default appearance | FreeCAD Dark as an initial default, not branded as a Fusion theme | Implemented; first-run surface unresolved |
| Command navigation | Task tabs and short command groups, not a full workbench list or generic ribbon | Decision; Solid slice implemented |
| Product name and icon | Working name/identity; final branding not settled | Open |
| Accessibility requirements | No product-specific acceptance set yet | Open |
| Business model | No paid account/subscription is in scope for the local MVP; long-term funding not settled | Open |


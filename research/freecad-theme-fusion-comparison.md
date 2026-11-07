# FreeCAD themes compared with Fusion

**Research date:** 2026-11-06  
**Question:** Is there an existing FreeCAD theme that can fairly be described as Fusion-like?

## Finding

The sources confirm several dark FreeCAD themes, but do not identify any as a Fusion match. The earlier suggestion that OpenDark was the closest was not supported by a comparison; it should be treated as a candidate, not a recommendation.

Fusion has multiple interface themes: Classic, Dark Blue, Dark Gray, Light Gray, and Match Device Theme. Autodesk describes the theme system as a change to its UI appearance. Its interface also has a workspace toolbar with tabs, a Browser, ViewCube, navigation bar, and (in parametric mode) a timeline. A color theme alone cannot reproduce those structural elements. [Autodesk theme API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_UserInterfaceThemes.htm) · [Fusion interface overview](https://help.autodesk.com/cloudhelp/ENU/Fusion-GetStarted/files/GS-THE-FUSION-INTERFACE.htm)

FreeCAD's first-party theme collection includes Behave-dark, Behave-dark_1_1_Plus, Dark-contrast, Dark-modern, Darker, Light-modern, and ProDark. The project says to install themes through Addon Manager and select them in **Edit → Preferences → General → Themes**. These are FreeCAD themes; the repository does not claim that any recreates Fusion's visual design. [FreeCAD theme repository](https://github.com/FreeCAD/FreeCAD-themes)

OpenTheme supplies OpenDark, OpenLight, and OpenSystem. Its documentation treats the color theme and its optional OpenPreferences layout/settings pack as separate things. It also warns that applying the preference pack is a one-way operation and recommends backing up `user.cfg`. OpenTheme requires FreeCAD's YAML style-parameter support; older builds need its Legacy branch. It is therefore a possible visual candidate, not a proven Fusion-like preset. [OpenTheme repository](https://github.com/obelisk79/opentheme)

## What the user's screenshot shows

The first-run dialog in the screenshot offers the built-in FreeCAD Light and FreeCAD Dark choices. The other packs are not present in that picker by default; FreeCAD's theme repository documents installing them first through Addon Manager. The bottom status area showing **Revit** is a separate navigation-style setting and does not indicate which UI theme is active.

## Recommendation for the Frontdoor

Do not label OpenDark, Dark-modern, or ProDark “Fusion-like” based on their names or dark palettes. A reliable winner requires side-by-side screenshots of the current Fusion themes and FreeCAD themes at the same window size, with the same workbench and panels visible. Compare at least Fusion Dark Blue/Dark Gray against FreeCAD Dark-modern, ProDark, and OpenDark.

The Frontdoor can eventually choose a tested theme automatically inside its isolated profile. Until that comparison exists, use a neutral product description such as “dark FreeCAD theme” and avoid promising a Fusion visual match. The larger Fusion resemblance—workspace tabs, command grouping, browser placement, and a persistent timeline—requires layout/workflow changes beyond a theme.

## Plugin feasibility: tabs and navigation

Yes, plugins can take this further than a theme:

- FreeCAD workbenches are add-ons that define related commands and toolbars. [FreeCAD Addon docs](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Addon.md)
- [FreeCAD-Ribbon](https://github.com/APEbbers/FreeCAD-Ribbon) replaces standard toolbars with a customizable ribbon, supports custom panels and panel/button ordering, lets users choose workbenches and apply a stylesheet. Its README documents restart-based installation and recovery steps for restoring classic toolbars after removal. It is GPL-3.0.
- [NeoRibbon](https://github.com/robdevtech/NeoRibbon) says it supports FreeCAD 1.1+ and maps the active workbench toolbars into ribbon-style sections. Its README clarifies that it is not one tab per toolbar and that the workbench selector moves into the ribbon. It says the add-on is not yet in the official Addon Index, so distribution currently means a custom repository/manual path and a restart.
- The [ModernUI workbench](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/ModernUI_Workbench.md) describes one ribbon tab per workbench, but the documentation warns about issues when adding other workbenches and an awkward uninstall path. It is not the low-risk starting point for a polished installer.
- Navigation behavior can also be implemented in an add-on. The pinned `freecad-fusion` add-on in this project applies FreeCAD's Revit navigation style, adds drag-to-orbit NaviCube behavior, and registers commands. See the pinned source: [`InitGui.py`](https://github.com/arxdsilva/freecad-fusion/blob/332ba07bdcaca194e5a3010d1fc0a365eeaefcf1/InitGui.py), [`navicube_drag.py`](https://github.com/arxdsilva/freecad-fusion/blob/332ba07bdcaca194e5a3010d1fc0a365eeaefcf1/freecad_fusion/navicube_drag.py), and [`presets.py`](https://github.com/arxdsilva/freecad-fusion/blob/332ba07bdcaca194e5a3010d1fc0a365eeaefcf1/freecad_fusion/presets.py).)

**Practical conclusion:** navigation can live in an add-on inside Frontdoor's isolated profile, but available ribbon add-ons do not provide the task-tab model we want. The product UI target is a Frontdoor-owned workbench; navigation remains a separate module. Do not treat a ribbon add-on as a production UI dependency.

### Local candidate smoke observation

On 2026-11-06, FreeCAD-Ribbon was copied from commit `bbaf5d5126d48eaf2bca9252984d4eb287b86172` into a disposable profile and launched with FreeCAD 1.1.1 Linux AppImage. The app stayed open and the screenshot showed the extension loading a ribbon-like strip of grouped toolbars. On this build the screenshot did not show Fusion-style command-category tabs; the active workbench remained a selector at the left. The default layout is visibly dense and clips many labels. The profile showed the FreeCAD first-run theme dialog and CAD navigation because this ribbon-only test did not install the theme or navigation add-on. This is an add-on smoke observation, not a Windows validation or a user-acceptance result.

FreeCAD-Ribbon is useful as a layout prototype because it replaces toolbars with configurable panels. It does not create task-category tabs and will not be the product UI dependency. Its package is GPL-3.0-or-later; do not bundle it for the MVP. NeoRibbon is also not a fit: its documented active-workbench sections do not create Fusion-style task tabs.

### Workbench-tab prototype and task-based UI target

On the disposable FreeCAD 1.1.1 profile, a curated FreeCAD-Ribbon configuration rendered panel headings but retained FreeCAD workbench tabs (`Assembly`, `CAM`, `Part`, `Part Design`, `Sketcher`, `TechDraw`). It reduces visible workbench clutter but does **not** create Fusion's task-category tabs. The product decision is to build a Frontdoor-owned workbench with task tabs and command groups.

For a new-user Fusion profile, do not expose every installed workbench by default. The six workbenches in the prototype are evidence of what the add-on displays, not the target navigation. The product target is a `Design` workspace with task tabs `Solid`, `Surface`, `Mesh`, `Sheet Metal`, and `Tools`, plus `Manufacture` and `Drawing` workspaces when supported. Specialized FreeCAD workbenches remain available through Full FreeCAD. Autodesk describes the Design tabs as task and data categories within a workspace; our layout should follow that task-oriented structure while mapping to available FreeCAD commands. The FreeCAD first-run Welcome panel still occupies the modeling area and offers its own theme choice, so preselecting Frontdoor defaults and handling first-start onboarding remain unresolved.

An earlier test run used a profile that had saved a `672 × 480` window with `Maximized=0`. A fresh profile and a separate full-ribbon run both opened maximized after setting `Maximized=1`; Frontdoor preserves later saved window-state choices.

The test also reproduced FreeCAD 1.1's first-start setup surface: it offers language, units, navigation style, and a Light/Dark theme choice. The theme preference is stored at `BaseApp/Preferences/MainWindow/Theme`; FreeCAD's own preference pack uses this setting. Frontdoor can set `FreeCAD Dark` in its isolated Fusion profile before launch, so the theme is preselected without asking the user to choose it. The setup surface itself may still appear, with its `Done` control; replacing or hiding that panel has not been confirmed. See [FreeCAD's built-in Classic preference pack](https://github.com/FreeCAD/FreeCAD/blob/main/src/Gui/PreferencePacks/FreeCAD%20Classic/FreeCAD%20Classic.cfg) and [FreeCAD 1.1 release notes](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Release_notes_1.0.md).

The first custom `Inspect` panel config emitted warnings because it supplied `Std_Measure` and `Std_UnitsCalculator` as icon resource names. These are command IDs, not icon resources. The evaluation config now leaves those icon names unset so the add-on can resolve icons from command actions; a fresh GUI launch is still needed to verify that the warnings disappear.

## Sources

- Autodesk, [UserInterfaceThemes enumerator](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_UserInterfaceThemes.htm): theme names and semantics.
- Autodesk, [Fusion interface (desktop)](https://help.autodesk.com/cloudhelp/ENU/Fusion-GetStarted/files/GS-THE-FUSION-INTERFACE.htm): named interface regions and their roles.
- Autodesk, [Fusion workspaces](https://help.autodesk.com/cloudhelp/ENU/Fusion-GetStarted/files/GS-WORKSPACES.htm): workspace and task-tab organization.
- Autodesk, [Fusion UI customization](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/UserInterface_UM.htm): Design workspace tabs and panels.
- Autodesk, [September 2025 product update](https://www.autodesk.com/products/fusion-360/blog/september-2025-product-update-whats-new/): describes Dark Blue, Match Device Theme, and setting the canvas environment separately from the UI theme.
- FreeCAD, [FreeCAD-themes](https://github.com/FreeCAD/FreeCAD-themes): included theme packs and installation/selection instructions.
- OpenTheme, [repository README](https://github.com/obelisk79/opentheme): theme scope, compatibility notes, optional preferences pack, and warning.
- FreeCAD, [Addon documentation](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Addon.md): workbenches and toolbars as extension points.
- APEbbers, [FreeCAD-Ribbon](https://github.com/APEbbers/FreeCAD-Ribbon): ribbon features, customization, installation, GPL-3.0 license, and recovery caveats.
- robdevtech, [NeoRibbon](https://github.com/robdevtech/NeoRibbon): 1.1+ compatibility claim, active-workbench ribbon model, custom repository installation, and reversibility.
- FreeCAD, [ModernUI workbench documentation](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/ModernUI_Workbench.md): documented per-workbench tabs and limitations.

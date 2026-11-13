"""Register Frontdoor's task-based workbench with FreeCAD."""

import os
import sys
import FreeCAD as App
import FreeCADGui as Gui


_addon_dir = None
_profile = os.environ.get("FREECAD_USER_HOME")
_launch_ready_written = False
if _profile:
    _candidate = os.path.join(_profile, "Mod", "FrontdoorUI")
    if os.path.isfile(os.path.join(_candidate, "task_surface.py")):
        _addon_dir = os.path.realpath(_candidate)
if _addon_dir is None:
    try:
        _candidate = os.path.join(App.getUserAppDataDir(), "Mod", "FrontdoorUI")
        if os.path.isfile(os.path.join(_candidate, "task_surface.py")):
            _addon_dir = os.path.realpath(_candidate)
    except Exception:
        pass
if _addon_dir is None:
    for _entry in sys.path:
        if _entry and os.path.basename(_entry) == "FrontdoorUI":
            if os.path.isfile(os.path.join(_entry, "task_surface.py")):
                _addon_dir = os.path.realpath(_entry)
                break
if _addon_dir and _addon_dir not in sys.path:
    sys.path.insert(0, _addon_dir)


if _addon_dir:
    try:
        class FrontdoorWorkbench(Workbench):
            MenuText = "Frontdoor"
            ToolTip = "Fusion-friendly, task-based modeling tools"

            def Initialize(self):
                # Register native commands before TaskSurface snapshots Gui.listCommands().
                # Importing these providers leaves Frontdoor active and avoids
                # forcing the user through another workbench just to load tools.
                for provider in ("SketcherGui", "PartDesignGui"):
                    try:
                        __import__(provider)
                    except Exception as exc:
                        App.Console.PrintError(
                            "[Frontdoor] Could not load %s commands: %s\n" % (provider, exc)
                        )
                import task_surface

                self._task_surface = task_surface
                task_surface.register_workbench(self)

            def Activated(self):
                global _launch_ready_written
                import task_surface

                task_surface.show()
                launch_token = os.environ.get("FRONTDOOR_LAUNCH_TOKEN")
                if launch_token and not _launch_ready_written:
                    try:
                        from startup_status import write_launch_ready_marker

                        version = ".".join(str(part) for part in App.Version()[:3])
                        write_launch_ready_marker(
                            _profile or App.getUserAppDataDir(),
                            launch_token,
                            process_id=os.getpid(),
                            freecad_version=version,
                        )
                        _launch_ready_written = True
                    except Exception as exc:
                        App.Console.PrintWarning(
                            "[Frontdoor] Could not confirm launch readiness: %s\n" % exc
                        )

            def Deactivated(self):
                import task_surface

                task_surface.hide()

            def GetClassName(self):
                return "Gui::PythonWorkbench"

        Gui.addWorkbench(FrontdoorWorkbench())
        App.Console.PrintMessage("[Frontdoor] Task-based workbench registered.\n")
    except Exception as exc:
        App.Console.PrintError("[Frontdoor] Could not register workbench: %s\n" % exc)
else:
    App.Console.PrintError("[Frontdoor] Could not find the installed workbench files.\n")

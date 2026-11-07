"""Manage isolated Linux GUI smoke runs without touching ordinary FreeCAD."""

from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import json
import os
import re
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from .errors import FrontdoorError
from .paths import data_root

_PRODUCT = "FreeCAD Fusion Frontdoor"
_SMOKE_ROOT = "smoke-tests"


def _root() -> Path:
    return data_root() / _SMOKE_ROOT


def _profile_environment(profile: Path, profile_name: str, *, frontdoor_ui: bool) -> dict[str, str]:
    profile.mkdir(parents=True, exist_ok=False)
    (profile / "temp").mkdir()
    home = profile / "home"
    config = home / ".config"
    share = home / ".local" / "share"
    cache = home / ".cache"
    for directory in (home, config, share, cache, profile / "Mod"):
        directory.mkdir(parents=True, exist_ok=True)
    owner = profile / ".frontdoor-profile.json"
    owner.write_text(
        json.dumps({"product": _PRODUCT, "profile": profile_name, "kind": "smoke-test"}, indent=2),
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment.update(
        {
            "FREECAD_USER_HOME": str(profile.resolve()),
            "FREECAD_USER_DATA": str(profile.resolve()),
            "FREECAD_USER_TEMP": str((profile / "temp").resolve()),
            "HOME": str(home.resolve()),
            "XDG_CONFIG_HOME": str(config.resolve()),
            "XDG_DATA_HOME": str(share.resolve()),
            "XDG_CACHE_HOME": str(cache.resolve()),
        }
    )
    if frontdoor_ui:
        from .theme import ensure_default_theme
        from .ui_addon import ensure_default_workbench, install_frontdoor_ui
        from .window_state import ensure_initial_maximized

        install_frontdoor_ui(profile)
        ensure_default_workbench(profile)
        ensure_default_theme(profile)
        ensure_initial_maximized(profile)
    return environment


def _install_startup_probe(
    profile: Path,
    report_path: Path,
    exercise_new_design: bool = False,
    exercise_create_sketch: bool = False,
    exercise_sketch_geometry: bool = False,
    exercise_pocket: bool = False,
    exercise_dressups: bool = False,
) -> None:
    task_surface = profile / "Mod" / "FrontdoorUI" / "task_surface.py"
    if not task_surface.is_file():
        raise FrontdoorError(f"Frontdoor UI files were not staged in the smoke profile: {profile}")
    source = task_surface.read_text(encoding="utf-8")
    anchor = "    _dock.raise_()\n"
    if source.count(anchor) != 1:
        raise FrontdoorError("Could not install the probe at the Frontdoor task-surface activation point.")
    probe = '''    # Temporary probe added only in a disposable smoke profile.
    if __REPORT_PATH__ and not globals().get("_fdsmoke_probe_scheduled"):
        globals()["_fdsmoke_probe_scheduled"] = True
        from PySide import QtCore as _fdsmoke_core
        def _fdsmoke_probe_commands():
            import json as _fdsmoke_json
            import os as _fdsmoke_os
            import tempfile as _fdsmoke_tempfile
            _fdsmoke_ids = ("Sketcher_NewSketch", "PartDesign_NewSketch", "PartDesign_Pad", "PartDesign_Pocket", "PartDesign_Fillet", "PartDesign_Chamfer")
            _fdsmoke_modal_events = []
            def _fdsmoke_auto_accept_modal():
                _dialog = QtWidgets.QApplication.activeModalWidget()
                if _dialog is None:
                    return
                _event = {
                    "title": _dialog.windowTitle(),
                    "labels": [label.text() for label in _dialog.findChildren(QtWidgets.QLabel)],
                }
                if _event not in _fdsmoke_modal_events:
                    _fdsmoke_modal_events.append(_event)
                _ok = next((button for button in _dialog.findChildren(QtWidgets.QAbstractButton)
                            if button.text().replace("&", "").strip().casefold() in ("ok", "yes", "accept")), None)
                if _ok:
                    _ok.click()
                elif hasattr(_dialog, "accept"):
                    _dialog.accept()
            _fdsmoke_modal_timer = QtCore.QTimer()
            _fdsmoke_modal_timer.timeout.connect(_fdsmoke_auto_accept_modal)
            _fdsmoke_modal_timer.start(250)
            _fdsmoke_observations = {"before": {name: name in set(Gui.listCommands()) for name in _fdsmoke_ids}}
            _fdsmoke_imports = {}
            for _fdsmoke_module in ("SketcherGui", "PartDesignGui"):
                try:
                    __import__(_fdsmoke_module)
                    _fdsmoke_imports[_fdsmoke_module] = "loaded"
                except Exception as _fdsmoke_error:
                    _fdsmoke_imports[_fdsmoke_module] = str(_fdsmoke_error)
                _fdsmoke_commands = set(Gui.listCommands())
                _fdsmoke_observations["after_import_" + _fdsmoke_module] = {name: name in _fdsmoke_commands for name in _fdsmoke_ids}
            _fdsmoke_workbenches = {}
            if not all(_fdsmoke_observations["after_import_PartDesignGui"].values()):
                for _fdsmoke_workbench in ("PartDesignWorkbench", "SketcherWorkbench"):
                    try:
                        Gui.activateWorkbench(_fdsmoke_workbench)
                        _fdsmoke_workbenches[_fdsmoke_workbench] = "activated"
                    except Exception as _fdsmoke_error:
                        _fdsmoke_workbenches[_fdsmoke_workbench] = str(_fdsmoke_error)
                    _fdsmoke_commands = set(Gui.listCommands())
                    _fdsmoke_observations["after_activate_" + _fdsmoke_workbench] = {name: name in _fdsmoke_commands for name in _fdsmoke_ids}
            try:
                Gui.activateWorkbench("FrontdoorWorkbench")
                _fdsmoke_workbenches["FrontdoorWorkbench"] = "restored"
            except Exception as _fdsmoke_error:
                _fdsmoke_workbenches["FrontdoorWorkbench"] = str(_fdsmoke_error)
            _fdsmoke_commands = set(Gui.listCommands())
            _fdsmoke_dock = _dock
            _fdsmoke_status = _fdsmoke_dock.findChild(QtWidgets.QLabel, "commandHint") if _fdsmoke_dock else None
            def _fdsmoke_action_state():
                _states = {}
                if _fdsmoke_dock:
                    for _button in _fdsmoke_dock.findChildren(QtWidgets.QToolButton):
                        _command = _button.property("commandId")
                        if _command:
                            _states[str(_command)] = {"visible": _button.isVisibleTo(_fdsmoke_dock), "enabled": _button.isEnabled()}
                return _states
            _fdsmoke_initial_actions = _fdsmoke_action_state()
            _fdsmoke_new_design_created = False
            if __EXERCISE_NEW_DESIGN__ and _fdsmoke_dock:
                _new_button = next((button for button in _fdsmoke_dock.findChildren(QtWidgets.QToolButton)
                                    if button.property("commandId") == "Std_New"), None)
                if _new_button:
                    _new_button.click()
                    _fdsmoke_dock.refresh_state()
                    _fdsmoke_new_design_created = App.ActiveDocument is not None
            _fdsmoke_create_sketch_invoked = False
            _fdsmoke_sketch_dialog = {}
            _fdsmoke_workbench_after_sketch = None
            _fdsmoke_workbench_after_restore = None
            _fdsmoke_restore_error = None
            if __EXERCISE_CREATE_SKETCH__ and _fdsmoke_dock:
                _sketch_button = next((button for button in _fdsmoke_dock.findChildren(QtWidgets.QToolButton)
                                       if button.property("commandId") == "PartDesign_NewSketch"), None)
                if _sketch_button and _sketch_button.isEnabled():
                    def _fdsmoke_confirm_xy_plane():
                        _dialog = QtWidgets.QApplication.activeModalWidget()
                        if _dialog is None:
                            _fdsmoke_sketch_dialog["found"] = False
                            return
                        _radios = _dialog.findChildren(QtWidgets.QRadioButton)
                        _fdsmoke_sketch_dialog.update({
                            "found": True,
                            "title": _dialog.windowTitle(),
                            "planes": {radio.text(): radio.isChecked() for radio in _radios},
                            "labels": [label.text() for label in _dialog.findChildren(QtWidgets.QLabel)],
                        })
                        _ok = next((button for button in _dialog.findChildren(QtWidgets.QPushButton)
                                    if button.text().replace("&", "").strip().casefold() == "ok"), None)
                        if _ok:
                            _ok.click()
                            _fdsmoke_sketch_dialog["accepted"] = True
                        elif hasattr(_dialog, "accept"):
                            _dialog.accept()
                            _fdsmoke_sketch_dialog["accepted"] = True
                    QtCore.QTimer.singleShot(750, _fdsmoke_confirm_xy_plane)
                    _sketch_button.click()
                    _fdsmoke_create_sketch_invoked = True
                    _fdsmoke_dock.refresh_state()
                    try:
                        _fdsmoke_workbench_after_sketch = Gui.activeWorkbench().name()
                    except Exception:
                        _fdsmoke_workbench_after_sketch = "unknown"
                    if _fdsmoke_workbench_after_sketch != "FrontdoorWorkbench":
                        try:
                            Gui.activateWorkbench("FrontdoorWorkbench")
                            _fdsmoke_workbench_after_restore = Gui.activeWorkbench().name()
                        except Exception as _fdsmoke_error:
                            _fdsmoke_restore_error = str(_fdsmoke_error)
            _fdsmoke_geometry = {}
            if __EXERCISE_SKETCH_GEOMETRY__ and App.ActiveDocument:
                try:
                    import Part as _fdsmoke_part
                    _sketch = next(obj for obj in App.ActiveDocument.Objects if obj.TypeId == "Sketcher::SketchObject")
                    _points = ((0, 0), (20, 0), (20, 20), (0, 20))
                    for _index, (_x, _y) in enumerate(_points):
                        _nx, _ny = _points[(_index + 1) % len(_points)]
                        _sketch.addGeometry(
                            _fdsmoke_part.LineSegment(App.Vector(_x, _y, 0), App.Vector(_nx, _ny, 0)),
                            False,
                        )
                    App.ActiveDocument.recompute()
                    _fdsmoke_geometry = {
                        "geometry_count": len(_sketch.Geometry),
                        "wire_count": len(_sketch.Shape.Wires),
                        "shape_valid": _sketch.Shape.isValid(),
                        "area_mm2": _sketch.Shape.Area,
                    }
                    Gui.activeDocument().resetEdit()
                    Gui.Selection.clearSelection()
                    Gui.Selection.addSelection(_sketch)
                    _fdsmoke_dock.refresh_state()
                    _fdsmoke_geometry["pad_enabled"] = _fdsmoke_dock.buttons["PartDesign_Pad"].isEnabled()
                    if _fdsmoke_geometry["pad_enabled"]:
                        _fdsmoke_dock.buttons["PartDesign_Pad"].click()
                        QtWidgets.QApplication.processEvents()
                        _fdsmoke_geometry["pad_command_started"] = True
                        _body = next(obj for obj in App.ActiveDocument.Objects if obj.TypeId == "PartDesign::Body")
                        _shape = _body.Shape
                        _tip = _body.Tip
                        _tip_length = getattr(_tip, "Length", None) if _tip else None
                        if hasattr(_tip_length, "Value"):
                            _tip_length = float(_tip_length.Value)
                        _fdsmoke_geometry.update({
                            "body_tip": _tip.Name if _tip else None,
                            "body_valid": _shape.isValid(),
                            "body_solid_count": len(_shape.Solids),
                            "body_volume_mm3": _shape.Volume,
                            "tip_length_mm": _tip_length,
                            "workbench_after_pad": Gui.activeWorkbench().name(),
                        })
                        if __EXERCISE_POCKET__:
                            try:
                                Gui.activeDocument().resetEdit()
                                App.ActiveDocument.recompute()
                                _fdsmoke_geometry["pad_edit_closed"] = Gui.activeDocument().getInEdit() is None
                                _tip_shape = _body.Tip.Shape
                                _top_face_index = max(
                                    (index for index, face in enumerate(_tip_shape.Faces, 1)
                                     if abs(face.BoundBox.ZMin - 10.0) < 1e-6
                                     and abs(face.BoundBox.ZMax - 10.0) < 1e-6),
                                    key=lambda index: _tip_shape.Faces[index - 1].Area,
                                )
                                Gui.Selection.clearSelection()
                                Gui.Selection.addSelection(_body, "Face%d" % _top_face_index)
                                _fdsmoke_dock.refresh_state()
                                _fdsmoke_dock.buttons["PartDesign_NewSketch"].click()
                                QtWidgets.QApplication.processEvents()
                                _pocket_sketch = next(
                                    obj for obj in App.ActiveDocument.Objects
                                    if obj.TypeId == "Sketcher::SketchObject" and obj != _sketch
                                )
                                _inverse = _pocket_sketch.Placement.inverse()
                                _global_points = ((5, 5, 10), (15, 5, 10), (15, 15, 10), (5, 15, 10))
                                _local_points = [
                                    _inverse.multVec(App.Vector(_x, _y, _z)) for _x, _y, _z in _global_points
                                ]
                                for _index, _point in enumerate(_local_points):
                                    _next = _local_points[(_index + 1) % len(_local_points)]
                                    _pocket_sketch.addGeometry(
                                        _fdsmoke_part.LineSegment(
                                            App.Vector(_point.x, _point.y, 0),
                                            App.Vector(_next.x, _next.y, 0),
                                        ),
                                        False,
                                    )
                                App.ActiveDocument.recompute()
                                _fdsmoke_geometry["pocket_sketch"] = {
                                    "support": str(_pocket_sketch.AttachmentSupport),
                                    "geometry_count": len(_pocket_sketch.Geometry),
                                    "wire_count": len(_pocket_sketch.Shape.Wires),
                                    "shape_valid": _pocket_sketch.Shape.isValid(),
                                }
                                Gui.activeDocument().resetEdit()
                                Gui.Selection.clearSelection()
                                Gui.Selection.addSelection(_pocket_sketch)
                                _fdsmoke_dock.refresh_state()
                                _fdsmoke_geometry["pocket_enabled"] = _fdsmoke_dock.buttons["PartDesign_Pocket"].isEnabled()
                                if _fdsmoke_geometry["pocket_enabled"]:
                                    _fdsmoke_dock.buttons["PartDesign_Pocket"].click()
                                    QtWidgets.QApplication.processEvents()
                                    App.ActiveDocument.recompute()
                                    _body_shape = _body.Shape
                                    _fdsmoke_geometry["pocket"] = {
                                        "tip": _body.Tip.Name if _body.Tip else None,
                                        "valid": _body_shape.isValid(),
                                        "solid_count": len(_body_shape.Solids),
                                        "volume_mm3": _body_shape.Volume,
                                        "length_mm": float(_body.Tip.Length.Value),
                                        "workbench": Gui.activeWorkbench().name(),
                                    }
                                    Gui.activeDocument().resetEdit()
                                    App.ActiveDocument.recompute()
                                    _fdsmoke_geometry["pocket"]["edit_closed"] = Gui.activeDocument().getInEdit() is None
                                    _fdsmoke_geometry["pocket"]["final_volume_mm3"] = _body.Shape.Volume
                                    if __EXERCISE_DRESSUPS__:
                                        _dressup_report = {}
                                        _fdsmoke_geometry["dressups"] = _dressup_report
                                        for _feature_command, _label in (
                                            ("PartDesign_Fillet", "fillet"),
                                            ("PartDesign_Chamfer", "chamfer"),
                                        ):
                                            try:
                                                _branch = App.ActiveDocument.copyObject(_body, True)
                                                App.ActiveDocument.recompute()
                                                _body.ViewObject.Visibility = False
                                                _branch.ViewObject.Visibility = True
                                                Gui.activeDocument().activeView().setActiveObject("pdbody", _branch)
                                                _edge_index = max(
                                                    range(1, len(_branch.Shape.Edges) + 1),
                                                    key=lambda index: _branch.Shape.Edges[index - 1].Length,
                                                )
                                                Gui.Selection.clearSelection()
                                                Gui.Selection.addSelection(_branch.Tip, "Edge%d" % _edge_index)
                                                _fdsmoke_dock.refresh_state()
                                                _dressup_report[_label + "_enabled"] = _fdsmoke_dock.buttons[_feature_command].isEnabled()
                                                if not _dressup_report[_label + "_enabled"]:
                                                    continue
                                                _fdsmoke_dock.buttons[_feature_command].click()
                                                QtWidgets.QApplication.processEvents()
                                                App.ActiveDocument.recompute()
                                                _branch_shape = _branch.Shape
                                                _dressup_report[_label] = {
                                                    "tip": _branch.Tip.Name if _branch.Tip else None,
                                                    "valid": _branch_shape.isValid(),
                                                    "solid_count": len(_branch_shape.Solids),
                                                    "volume_mm3": _branch_shape.Volume,
                                                    "workbench": Gui.activeWorkbench().name(),
                                                }
                                                Gui.activeDocument().resetEdit()
                                                App.ActiveDocument.recompute()
                                                _dressup_report[_label]["edit_closed"] = Gui.activeDocument().getInEdit() is None
                                                _dressup_report[_label]["final_valid"] = _branch.Shape.isValid()
                                                _dressup_report[_label]["final_solid_count"] = len(_branch.Shape.Solids)
                                                _dressup_report[_label]["final_volume_mm3"] = _branch.Shape.Volume
                                                _branch.ViewObject.Visibility = False
                                                _body.ViewObject.Visibility = True
                                            except Exception as _feature_error:
                                                _dressup_report[_label + "_error"] = str(_feature_error)
                                else:
                                    _fdsmoke_geometry["pocket_started"] = False
                            except Exception as _fdsmoke_error:
                                _fdsmoke_geometry["pocket_error"] = str(_fdsmoke_error)
                    else:
                        _fdsmoke_geometry["pad_command_started"] = False
                except Exception as _fdsmoke_error:
                    _fdsmoke_geometry["error"] = str(_fdsmoke_error)
            _fdsmoke_actions = _fdsmoke_action_state()
            _fdsmoke_objects = [
                {"name": obj.Name, "type": obj.TypeId}
                for obj in (App.ActiveDocument.Objects if App.ActiveDocument else [])
            ]
            _fdsmoke_dialogs = [
                {"title": widget.windowTitle(), "object_name": widget.objectName(), "class": type(widget).__name__}
                for widget in QtWidgets.QApplication.topLevelWidgets()
                if widget.isVisible() and isinstance(widget, QtWidgets.QDialog)
            ]
            try:
                _fdsmoke_active = Gui.activeWorkbench().name()
            except Exception:
                _fdsmoke_active = "unknown"
            try:
                _fdsmoke_in_edit = Gui.activeDocument().getInEdit()
                if hasattr(_fdsmoke_in_edit, "Name"):
                    _fdsmoke_in_edit = str(_fdsmoke_in_edit.Name)
                elif _fdsmoke_in_edit is not None:
                    _fdsmoke_in_edit = str(_fdsmoke_in_edit)
            except Exception as _fdsmoke_error:
                _fdsmoke_in_edit = "unavailable: " + str(_fdsmoke_error)
            _fdsmoke_main_window = Gui.getMainWindow()
            _fdsmoke_task_docks = [
                {"title": dock.windowTitle(), "object_name": dock.objectName(),
                 "visible": dock.isVisible(),
                 "labels": [label.text() for label in dock.findChildren(QtWidgets.QLabel) if label.isVisible()]}
                for dock in _fdsmoke_main_window.findChildren(QtWidgets.QDockWidget)
                if "task" in (dock.windowTitle() + " " + dock.objectName()).casefold()
            ]
            _fdsmoke_report = {"dock_found": _fdsmoke_dock is not None,
                               "active_workbench": _fdsmoke_active,
                               "active_edit_object": _fdsmoke_in_edit,
                               "sketch_geometry": _fdsmoke_geometry,
                               "auto_accepted_dialogs": _fdsmoke_modal_events,
                               "task_docks": _fdsmoke_task_docks,
                               "native_imports": _fdsmoke_imports,
                               "workbench_activation": _fdsmoke_workbenches,
                               "observations": _fdsmoke_observations,
                               "status": _fdsmoke_status.text() if _fdsmoke_status else None,
                               "commands_after_return": {name: name in _fdsmoke_commands for name in _fdsmoke_ids},
                               "initial_actions": _fdsmoke_initial_actions,
                               "new_design_created": _fdsmoke_new_design_created,
                               "create_sketch_invoked": _fdsmoke_create_sketch_invoked,
                               "sketch_plane_dialog": _fdsmoke_sketch_dialog,
                               "workbench_after_sketch": _fdsmoke_workbench_after_sketch,
                               "workbench_after_restore": _fdsmoke_workbench_after_restore,
                               "restore_error": _fdsmoke_restore_error,
                               "document_objects_after_create_sketch": _fdsmoke_objects,
                               "visible_task_labels": [
                                   label.text()
                                   for label in _fdsmoke_dock.findChildren(QtWidgets.QLabel)
                                   if _fdsmoke_dock.isVisible() and label.isVisible()
                               ],
                               "visible_dialogs": _fdsmoke_dialogs,
                               "actions": _fdsmoke_actions}
            _fdsmoke_fd, _fdsmoke_temp = _fdsmoke_tempfile.mkstemp(prefix="frontdoor-probe.", dir=_fdsmoke_os.path.dirname(__REPORT_PATH__))
            with _fdsmoke_os.fdopen(_fdsmoke_fd, "w", encoding="utf-8") as _fdsmoke_stream:
                _fdsmoke_json.dump(_fdsmoke_report, _fdsmoke_stream, indent=2)
            _fdsmoke_os.replace(_fdsmoke_temp, __REPORT_PATH__)
            _fdsmoke_modal_timer.stop()
        _fdsmoke_core.QTimer.singleShot(0, _fdsmoke_probe_commands)
'''.replace("__REPORT_PATH__", repr(str(report_path)))
    probe = probe.replace("__EXERCISE_NEW_DESIGN__", repr(exercise_new_design))
    probe = probe.replace("__EXERCISE_CREATE_SKETCH__", repr(exercise_create_sketch))
    probe = probe.replace("__EXERCISE_SKETCH_GEOMETRY__", repr(exercise_sketch_geometry))
    probe = probe.replace("__EXERCISE_POCKET__", repr(exercise_pocket))
    probe = probe.replace("__EXERCISE_DRESSUPS__", repr(exercise_dressups))
    task_surface.write_text(source.replace(anchor, anchor + probe, 1), encoding="utf-8")


def _profile_processes(profile: Path, executable_name: str) -> list[int]:
    """Find FreeCAD-family processes carrying this exact profile marker."""
    expected = f"FREECAD_USER_HOME={profile.resolve()}".encode()
    found: list[int] = []
    proc = Path("/proc")
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        try:
            environment = (entry / "environ").read_bytes().split(b"\0")
            if expected not in environment:
                continue
            command = (entry / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace").casefold()
        except (OSError, PermissionError):
            continue
        if any(token in command for token in ("freecad", "apprun", executable_name.casefold())):
            found.append(pid)
    return sorted(found)


def _x_windows() -> dict[int, list[int]]:
    if not os.environ.get("DISPLAY"):
        raise FrontdoorError("No X11 DISPLAY is available; the smoke runner needs the desktop session.")
    try:
        root = subprocess.run(
            ["xprop", "-root", "_NET_CLIENT_LIST"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout
    except (FileNotFoundError, subprocess.SubprocessError) as exc:
        raise FrontdoorError("Could not read the X11 window list with xprop.") from exc
    windows = re.findall(r"0x[0-9a-fA-F]+", root)
    by_pid: dict[int, list[int]] = {}
    for window in windows:
        try:
            result = subprocess.run(
                ["xprop", "-id", window, "_NET_WM_PID"],
                check=False,
                capture_output=True,
                text=True,
                timeout=3,
            )
        except (FileNotFoundError, subprocess.SubprocessError):
            continue
        match = re.search(r"_NET_WM_PID\(CARDINAL\)\s*=\s*(\d+)", result.stdout)
        if match:
            by_pid.setdefault(int(match.group(1)), []).append(int(window, 16))
    return by_pid


class _XClientData(ctypes.Union):
    _fields_ = [("b", ctypes.c_char * 20), ("s", ctypes.c_short * 10), ("l", ctypes.c_long * 5)]


class _XClientMessage(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int),
        ("serial", ctypes.c_ulong),
        ("send_event", ctypes.c_int),
        ("display", ctypes.c_void_p),
        ("window", ctypes.c_ulong),
        ("message_type", ctypes.c_ulong),
        ("format", ctypes.c_int),
        ("data", _XClientData),
    ]


class _XEvent(ctypes.Union):
    _fields_ = [("xclient", _XClientMessage), ("padding", ctypes.c_long * 24)]


def _request_window_close(window_ids: list[int]) -> None:
    if not window_ids:
        return
    library_path = ctypes.util.find_library("X11")
    if not library_path:
        raise FrontdoorError("Xlib is unavailable; cannot request a graceful window close.")
    x11 = ctypes.CDLL(library_path)
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
    x11.XInternAtom.restype = ctypes.c_ulong
    x11.XSendEvent.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_long, ctypes.POINTER(_XEvent)]
    x11.XSendEvent.restype = ctypes.c_int
    x11.XFlush.argtypes = [ctypes.c_void_p]
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    display = x11.XOpenDisplay(None)
    if not display:
        raise FrontdoorError("Could not connect to the X11 desktop to close smoke-test windows.")
    try:
        protocols = x11.XInternAtom(display, b"WM_PROTOCOLS", 0)
        delete_window = x11.XInternAtom(display, b"WM_DELETE_WINDOW", 0)
        for window_id in window_ids:
            event = _XEvent()
            event.xclient.type = 33  # ClientMessage
            event.xclient.serial = 0
            event.xclient.send_event = 1
            event.xclient.display = display
            event.xclient.window = window_id
            event.xclient.message_type = protocols
            event.xclient.format = 32
            event.xclient.data.l[0] = delete_window
            event.xclient.data.l[1] = 0
            x11.XSendEvent(display, window_id, 0, 0, ctypes.byref(event))
        x11.XFlush(display)
    finally:
        x11.XCloseDisplay(display)


def _wait_for_window(profile: Path, executable_name: str, timeout: float) -> tuple[int, list[int]]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        pids = _profile_processes(profile, executable_name)
        windows = _x_windows()
        for pid in pids:
            if pid in windows:
                return pid, windows[pid]
        time.sleep(0.5)
    raise FrontdoorError(f"No FreeCAD window appeared for the isolated profile {profile} within {timeout:g}s.")


def _wait_for_exit(profile: Path, executable_name: str, timeout: float) -> list[int]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        pids = _profile_processes(profile, executable_name)
        if not pids:
            return []
        time.sleep(0.25)
    return _profile_processes(profile, executable_name)


def _wait_for_probe(path: Path, profile: Path, executable_name: str, timeout: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass
        error_path = path.with_suffix(path.suffix + ".error")
        if error_path.is_file():
            raise FrontdoorError(f"The Frontdoor probe failed: {error_path.read_text(encoding='utf-8')}")
        if not _profile_processes(profile, executable_name):
            raise FrontdoorError(f"FreeCAD exited before the Frontdoor probe completed for {profile}.")
        time.sleep(0.5)
    raise FrontdoorError(f"The Frontdoor startup probe did not write its report within {timeout:g}s.")


def _close_instance(instance: dict[str, Any], executable_name: str) -> None:
    profile = Path(instance["profile"])
    if not profile.is_dir():
        return
    owner_path = profile / ".frontdoor-profile.json"
    try:
        owner = json.loads(owner_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FrontdoorError(f"Cannot verify smoke-profile ownership at {profile}; leaving processes untouched.") from exc
    if owner.get("product") != _PRODUCT or owner.get("kind") != "smoke-test":
        raise FrontdoorError(f"Refusing to close processes for a profile not owned by the smoke runner: {profile}")

    owned = _profile_processes(profile, executable_name)
    if not owned:
        print(f"Already closed: {profile}")
        return
    windows = _x_windows()
    owned_windows = [window for pid in owned for window in windows.get(pid, [])]
    if owned_windows:
        _request_window_close(owned_windows)
        print(f"Requested graceful close for {len(owned_windows)} window(s): {profile}")
    remaining = _wait_for_exit(profile, executable_name, 12)
    if remaining:
        print(f"Graceful close timed out; sending SIGTERM only to owned PIDs {remaining}")
        for pid in remaining:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        remaining = _wait_for_exit(profile, executable_name, 5)
    if remaining:
        print(f"SIGTERM timed out; force-closing owned PIDs {remaining}")
        for pid in remaining:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        remaining = _wait_for_exit(profile, executable_name, 5)
    if remaining:
        raise FrontdoorError(f"Could not confirm smoke process exit for {profile}; remaining PIDs: {remaining}")
    print(f"Closed and confirmed: {profile}")


def open_run(
    executable: Path,
    count: int = 3,
    window_timeout: float = 120,
    *,
    frontdoor_ui: bool = False,
    probe: bool = False,
    exercise_new_design: bool = False,
    exercise_create_sketch: bool = False,
    exercise_sketch_geometry: bool = False,
    exercise_pocket: bool = False,
    exercise_dressups: bool = False,
) -> str:
    if os.name != "posix" or sys.platform != "linux":
        raise FrontdoorError("The local smoke-run manager currently supports Linux/X11 only.")
    executable = executable.expanduser().resolve()
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise FrontdoorError(f"FreeCAD executable was not found or is not executable: {executable}")
    if count < 1 or count > 3:
        raise FrontdoorError("Choose between one and three smoke instances.")
    if probe and not frontdoor_ui:
        raise FrontdoorError("The command-availability probe requires --frontdoor-ui.")
    if exercise_new_design and not probe:
        raise FrontdoorError("The New Design exercise requires --probe.")
    if exercise_create_sketch and not exercise_new_design:
        raise FrontdoorError("The Create Sketch exercise requires --exercise-new-design.")
    if exercise_sketch_geometry and not exercise_create_sketch:
        raise FrontdoorError("The sketch-geometry exercise requires --exercise-create-sketch.")
    if exercise_pocket and not exercise_sketch_geometry:
        raise FrontdoorError("The Pocket exercise requires --exercise-sketch-geometry.")
    if exercise_dressups and not exercise_pocket:
        raise FrontdoorError("The Fillet/Chamfer exercise requires --exercise-pocket.")
    if not os.environ.get("DISPLAY"):
        raise FrontdoorError("Run this command inside the active X11 desktop session (DISPLAY is not set).")

    root = _root()
    root.mkdir(parents=True, exist_ok=True)
    executable_name = executable.name
    for run_file in root.glob("*/run.json"):
        try:
            existing = json.loads(run_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if any(_profile_processes(Path(item["profile"]), executable_name) for item in existing.get("instances", [])):
            raise FrontdoorError(f"A prior smoke run is still open ({existing.get('run_id')}). Close it with `frontdoor-smoke close --all` first.")

    run_id = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    run_dir = root / run_id
    run_dir.mkdir()
    instances: list[dict[str, Any]] = []
    run_file = run_dir / "run.json"
    state: dict[str, Any] = {"run_id": run_id, "executable": str(executable), "instances": instances}
    try:
        for index in range(1, count + 1):
            profile_name = f"smoke-{run_id}-{index}"
            profile = run_dir / profile_name
            environment = _profile_environment(profile, profile_name, frontdoor_ui=frontdoor_ui)
            if probe:
                probe_path = run_dir / f"{profile_name}-probe.json"
                _install_startup_probe(
                    profile,
                    probe_path,
                    exercise_new_design,
                    exercise_create_sketch,
                    exercise_sketch_geometry,
                    exercise_pocket,
                    exercise_dressups,
                )
            process = subprocess.Popen(
                [str(executable)],
                cwd=str(executable.parent),
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            instance: dict[str, Any] = {
                "profile": str(profile),
                "profile_name": profile_name,
                "launcher_pid": process.pid,
                "process_group": process.pid,
                "window_pid": None,
                "window_ids": [],
                "probe": str(run_dir / f"{profile_name}-probe.json") if probe else None,
            }
            instances.append(instance)
            run_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
            window_pid, window_ids = _wait_for_window(profile, executable_name, window_timeout)
            instance["window_pid"] = window_pid
            instance["window_ids"] = window_ids
            run_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
            print(f"Opened instance {index}/{count}: PID {window_pid}, window {', '.join(hex(w) for w in window_ids)}")
            if probe:
                report = _wait_for_probe(Path(instance["probe"]), profile, executable_name, window_timeout)
                print(json.dumps(report, indent=2))
                if not report.get("dock_found"):
                    raise FrontdoorError("FreeCAD started, but the Frontdoor task surface did not load.")
    except Exception:
        run_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        close_run(run_id)
        raise
    (root / "latest.json").write_text(json.dumps({"run_id": run_id}), encoding="utf-8")
    print(f"Run {run_id} is ready with {count} visible FreeCAD window(s).")
    return run_id


def close_run(run_id: str | None = None, close_all: bool = False) -> None:
    root = _root()
    if close_all:
        run_files = sorted(root.glob("*/run.json"))
    else:
        if run_id is None:
            try:
                run_id = json.loads((root / "latest.json").read_text(encoding="utf-8"))["run_id"]
            except (OSError, KeyError, json.JSONDecodeError) as exc:
                raise FrontdoorError("No latest smoke run is recorded; specify --run-id.") from exc
        run_files = [root / run_id / "run.json"]
    if not run_files:
        print("No smoke runs are recorded.")
        return
    failures: list[str] = []
    for run_file in run_files:
        try:
            state = json.loads(run_file.read_text(encoding="utf-8"))
            executable_name = Path(state["executable"]).name
            for instance in state.get("instances", []):
                _close_instance(instance, executable_name)
        except (OSError, KeyError, json.JSONDecodeError, FrontdoorError) as exc:
            failures.append(f"{run_file.parent.name}: {exc}")
    if failures:
        raise FrontdoorError("Smoke cleanup incomplete:\n" + "\n".join(failures))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="frontdoor-smoke", description="Open and clean up isolated Linux FreeCAD smoke runs.")
    subparsers = parser.add_subparsers(dest="action", required=True)
    open_parser = subparsers.add_parser("open", help="Open one to three isolated FreeCAD smoke windows")
    open_parser.add_argument("--freecad", required=True, type=Path, help="Path to the FreeCAD AppImage or executable")
    open_parser.add_argument("--count", type=int, default=3, help="Number of windows (1-3; default: 3)")
    open_parser.add_argument("--window-timeout", type=float, default=120, help="Seconds to wait for each GUI window")
    open_parser.add_argument("--frontdoor-ui", action="store_true", help="Install the current Frontdoor UI into each disposable profile")
    open_parser.add_argument("--probe", action="store_true", help="Record native command availability and task-surface state after startup")
    open_parser.add_argument("--exercise-new-design", action="store_true", help="Click New Design and record the updated action states")
    open_parser.add_argument("--exercise-create-sketch", action="store_true", help="Click Create Sketch after New Design and record the resulting UI state")
    open_parser.add_argument("--exercise-sketch-geometry", action="store_true", help="Draw a deterministic rectangle in the active sketch, exit edit, and start Pad")
    open_parser.add_argument("--exercise-pocket", action="store_true", help="Continue the deterministic sketch/Pad exercise with a top-face Pocket")
    open_parser.add_argument("--exercise-dressups", action="store_true", help="Test Fillet and Chamfer on separate deep copies of the Pocket result")
    close_parser = subparsers.add_parser("close", help="Gracefully close recorded smoke windows")
    close_parser.add_argument("--run-id", help="Specific run ID; defaults to the most recent run")
    close_parser.add_argument("--all", action="store_true", help="Close all recorded smoke runs")
    subparsers.add_parser("status", help="List recorded smoke runs and owned processes")
    args = parser.parse_args(argv)
    try:
        if args.action == "open":
            open_run(
                args.freecad,
                args.count,
                args.window_timeout,
                frontdoor_ui=args.frontdoor_ui,
                probe=args.probe,
                exercise_new_design=args.exercise_new_design,
                exercise_create_sketch=args.exercise_create_sketch,
                exercise_sketch_geometry=args.exercise_sketch_geometry,
                exercise_pocket=args.exercise_pocket,
                exercise_dressups=args.exercise_dressups,
            )
        elif args.action == "close":
            close_run(args.run_id, args.all)
        else:
            for run_file in sorted(_root().glob("*/run.json")):
                state = json.loads(run_file.read_text(encoding="utf-8"))
                print(f"{state['run_id']}: {sum(bool(_profile_processes(Path(i['profile']), Path(state['executable']).name)) for i in state['instances'])}/{len(state['instances'])} instance(s) running")
                for instance in state.get("instances", []):
                    probe_path = instance.get("probe")
                    if probe_path and Path(probe_path).is_file():
                        print(Path(probe_path).read_text(encoding="utf-8"))
    except (FrontdoorError, OSError, ValueError) as exc:
        print(f"Smoke run failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

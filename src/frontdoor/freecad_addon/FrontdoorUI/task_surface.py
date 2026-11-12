"""Small native-Qt task surface that dispatches to FreeCAD's own commands."""

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets


_dock = None
_timer = None
_toolbar_visibility = {}
_toolbar_managed = False
_native_toolbars_override = False
_frontdoor_active = False
_commands = {
    "New Design": "Std_New",
    "Create Sketch": "PartDesign_NewSketch",
    "Pad": "PartDesign_Pad",
    "Pocket": "PartDesign_Pocket",
    "Fillet": "PartDesign_Fillet",
    "Chamfer": "PartDesign_Chamfer",
}


class TaskSurface(QtWidgets.QDockWidget):
    def __init__(self, parent):
        super().__init__("Frontdoor Design", parent)
        self.setObjectName("FrontdoorDesignTaskSurface")
        self.setAllowedAreas(QtCore.Qt.DockWidgetArea.TopDockWidgetArea)
        self.setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.setTitleBarWidget(QtWidgets.QWidget(self))
        self.setMinimumHeight(132)

        root = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(root)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        heading = QtWidgets.QHBoxLayout()
        brand = QtWidgets.QLabel("DESIGN")
        brand.setObjectName("workspaceLabel")
        heading.addWidget(brand)
        heading.addSpacing(8)
        heading.addWidget(QtWidgets.QLabel("/"))
        heading.addSpacing(8)
        active_task = QtWidgets.QLabel("SOLID")
        active_task.setObjectName("activeTaskLabel")
        heading.addWidget(active_task)
        heading.addStretch(1)
        layout.addLayout(heading)

        self.tabs = QtWidgets.QTabWidget(root)
        self.tabs.setObjectName("frontdoorTaskTabs")
        self.tabs.setDocumentMode(True)
        try:
            self.available_commands = set(Gui.listCommands())
        except Exception:
            self.available_commands = None
        self.solid_page = QtWidgets.QWidget(self.tabs)
        self.action_row = QtWidgets.QHBoxLayout(self.solid_page)
        self.action_row.setContentsMargins(4, 6, 4, 0)
        self.action_row.setSpacing(10)
        self.create_group, self.create_layout = self._group("Create")
        self.modify_group, self.modify_layout = self._group("Modify")
        self.action_row.addWidget(self.create_group)
        self.action_row.addWidget(self.modify_group)
        self.action_row.addStretch(1)
        self.tabs.addTab(self.solid_page, "Solid")
        layout.addWidget(self.tabs)

        self.status = QtWidgets.QLabel()
        self.status.setObjectName("commandHint")
        layout.addWidget(self.status)
        self.setWidget(root)
        self.setStyleSheet(
            "QDockWidget { background: #252a31; color: #e8edf2; }"
            "QWidget { background: #252a31; color: #e8edf2; }"
            "QLabel#workspaceLabel { color: #9ca9b7; font-size: 10px; font-weight: 700; letter-spacing: 1px; }"
            "QLabel#activeTaskLabel { color: #ffffff; font-size: 12px; font-weight: 700; }"
            "QLabel#commandHint { color: #b8c2cc; font-size: 10px; }"
            "QTabWidget::pane { border: 0; border-top: 1px solid #404852; }"
            "QTabBar::tab { background: #30363e; color: #bdc6cf; padding: 7px 16px; margin-right: 3px; border: 0; }"
            "QTabBar::tab:selected { background: #145fa9; color: #ffffff; font-weight: 600; }"
            "QToolButton { background: #343b44; border: 1px solid #48515d; border-radius: 3px; padding: 7px 12px; min-width: 78px; min-height: 30px; color: #f1f4f7; }"
            "QToolButton:hover:enabled { background: #414b56; border-color: #9ca9b7; }"
            "QToolButton:focus { border: 2px solid #91caff; }"
            "QToolButton#primaryAction { background: #145fa9; border-color: #145fa9; color: #ffffff; font-weight: 600; padding: 8px 16px; min-width: 112px; min-height: 34px; }"
            "QToolButton#primaryAction:hover:enabled { background: #0f4e8f; border-color: #0f4e8f; }"
            "QToolButton:disabled { color: #74808c; background: #2c3239; border-color: #3b424a; }"
        )
        self.primary_button = None
        self.primary_command = None
        self.secondary_buttons = {}
        self.buttons = {}
        self._rendered_state = None
        self.refresh_state()

    def _group(self, title):
        group = QtWidgets.QGroupBox(title)
        row = QtWidgets.QHBoxLayout(group)
        row.setContentsMargins(8, 10, 8, 7)
        row.setSpacing(6)
        group.hide()
        return group, row

    def _make_button(self, command, primary=False):
        label = next(label for label, command_id in _commands.items() if command_id == command)
        button = QtWidgets.QToolButton(self.solid_page)
        button.setText(label)
        button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextOnly)
        button.setProperty("commandId", command)
        button.setToolTip(self._tooltip(label))
        if primary:
            button.setObjectName("primaryAction")
            button.setAccessibleName(label)
        button.clicked.connect(lambda checked=False, command=command: self._run(command))
        self.buttons[command] = button
        return button

    def _clear_buttons(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _render_actions(self, primary, secondary, modifying):
        state = (primary, tuple(secondary), bool(modifying))
        if state == self._rendered_state:
            return
        self._clear_buttons(self.create_layout)
        self._clear_buttons(self.modify_layout)
        self.buttons = {}
        self.primary_button = None
        self.primary_command = primary
        self.secondary_buttons = {}

        if primary:
            button = self._make_button(primary, primary=True)
            self.primary_button = button
            self.create_layout.addWidget(button)
            self.create_group.show()
        else:
            self.create_group.hide()

        for command in secondary:
            if self.available_commands is not None and command not in self.available_commands:
                continue
            button = self._make_button(command)
            if command in (_commands["Fillet"], _commands["Chamfer"]):
                self.modify_layout.addWidget(button)
            else:
                self.create_layout.addWidget(button)
            self.secondary_buttons[command] = button

        self.modify_group.setVisible(bool(modifying and self.modify_layout.count()))
        if primary and primary not in self.buttons:
            self._rendered_state = None
            return
        self._rendered_state = state

    @staticmethod
    def _tooltip(label):
        descriptions = {
            "Create Sketch": "Start a native sketch on the selected plane or face, or on the body's XY plane.",
            "Pad": "Extrude a selected sketch using FreeCAD Part Design.",
            "Pocket": "Cut into a body from a selected sketch.",
            "Fillet": "Round selected edges in the active Part Design body.",
            "Chamfer": "Bevel selected edges in the active Part Design body.",
        }
        return descriptions.get(label, "Create a new FreeCAD design.")

    def _run(self, command):
        try:
            available = set(Gui.listCommands())
        except Exception:
            available = None
        if available is not None and command not in available:
            QtWidgets.QMessageBox.information(
                self,
                "Command unavailable",
                "This FreeCAD build has not loaded the native command yet. "
                "Switch to Part Design or Sketcher once, then return to Frontdoor.",
            )
            return
        try:
            if command == "PartDesign_NewSketch":
                document = App.ActiveDocument
                gui_document = Gui.activeDocument()
                active_view = gui_document.activeView()
                body = None
                try:
                    body = active_view.getActiveObject("pdbody")
                except Exception:
                    pass
                if body is None:
                    bodies = [obj for obj in document.Objects if obj.TypeId == "PartDesign::Body"]
                    body = bodies[0] if bodies else document.addObject("PartDesign::Body", "Body")
                    active_view.setActiveObject("pdbody", body)

                if not Gui.Selection.getSelectionEx():
                    Gui.Selection.clearSelection()
                    xy_plane = next(
                        (feature for feature in body.Origin.OriginFeatures
                         if getattr(feature, "Role", "") == "XY_Plane"),
                        None,
                    )
                    if xy_plane is None:
                        raise RuntimeError("The active Part Design body has no XY origin plane.")
                    Gui.Selection.addSelection(xy_plane)
            Gui.runCommand(command)
            if command in {
                "PartDesign_NewSketch",
                "PartDesign_Pad",
                "PartDesign_Pocket",
                "PartDesign_Fillet",
                "PartDesign_Chamfer",
            }:
                # Native Part Design commands switch workbenches while opening
                # their edit tasks. Keep the task active and restore Frontdoor.
                try:
                    if Gui.activeWorkbench().name() != "FrontdoorWorkbench":
                        Gui.activateWorkbench("FrontdoorWorkbench")
                except Exception as exc:
                    App.Console.PrintWarning(
                        "[Frontdoor] Could not restore the Frontdoor workbench: %s\n" % exc
                    )
        except Exception as exc:
            App.Console.PrintError("[Frontdoor] %s failed: %s\n" % (command, exc))
            QtWidgets.QMessageBox.warning(self, "Could not start command", str(exc))
        self.refresh_state()

    def refresh_state(self):
        has_document = App.ActiveDocument is not None
        try:
            selection = Gui.Selection.getSelectionEx() if has_document else []
            gui_document = Gui.activeDocument() if has_document else None
            in_edit = gui_document.getInEdit() if gui_document else None
        except Exception:
            selection = []
            in_edit = None

        edit_object = getattr(in_edit, "Object", None) or in_edit
        editing_sketch = getattr(edit_object, "TypeId", "") == "Sketcher::SketchObject"
        self._sync_native_task_panel(in_edit)
        _sync_native_toolbars(editing_sketch)
        selected_sketches = [
            item.Object for item in selection
            if getattr(item.Object, "TypeId", "") == "Sketcher::SketchObject"
        ]
        closed_sketches = [sketch for sketch in selected_sketches if self._has_closed_profile(sketch)]
        selected_edges = any(self._item_has_body_edge(item) for item in selection)

        new_design = _commands["New Design"]
        create_sketch = _commands["Create Sketch"]
        pad = _commands["Pad"]
        pocket = _commands["Pocket"]
        fillet = _commands["Fillet"]
        chamfer = _commands["Chamfer"]
        if not has_document:
            primary, secondary, modifying = new_design, (), False
            hint = "Start a design here. Next, create a sketch."
        elif editing_sketch:
            primary, secondary, modifying = None, (), False
            hint = "Draw a closed profile, then finish the sketch to continue."
        elif closed_sketches:
            primary, secondary, modifying = pad, (pocket, new_design), False
            hint = "Create a solid from the closed sketch, or choose another sketch operation."
        elif selected_edges and has_valid_solid:
            primary, secondary, modifying = create_sketch, (new_design, fillet, chamfer), True
            hint = "Selected solid edges · choose Fillet or Chamfer to modify them."
        else:
            primary, secondary, modifying = create_sketch, (new_design,), False
            hint = "Create a sketch on a plane, then draw a closed profile to begin."

        commands = (primary,) + tuple(secondary) if primary else tuple(secondary)
        missing = [
            next(label for label, command in _commands.items() if command == command_id)
            for command_id in commands
            if self.available_commands is not None and command_id not in self.available_commands
        ]
        if missing:
            hint = "This FreeCAD build does not provide: " + ", ".join(missing)
            if primary is not None and self.available_commands is not None and primary not in self.available_commands:
                primary = None
        secondary = tuple(
            command for command in secondary
            if self.available_commands is None or command in self.available_commands
        )
        self._render_actions(primary, secondary, modifying)
        self.status.setText(hint)

    def _sync_native_task_panel(self, in_edit):
        main_window = self.parentWidget()
        if main_window is None:
            return
        for dock in main_window.findChildren(QtWidgets.QDockWidget):
            if dock is self:
                continue
            title = dock.windowTitle().strip().casefold()
            object_name = dock.objectName().strip().casefold()
            if title == "tasks" or object_name in {"taskdock", "tasksdock"}:
                dock.setVisible(in_edit is not None)

    @staticmethod
    def _has_closed_profile(sketch):
        try:
            wires = list(sketch.Shape.Wires)
            return bool(wires) and all(wire.isClosed() for wire in wires)
        except Exception:
            return False

    @classmethod
    def _item_has_body_edge(cls, item):
        if not any(str(name).startswith("Edge") for name in getattr(item, "SubElementNames", ())):
            return False
        try:
            obj = item.Object
            body = obj if getattr(obj, "TypeId", "") == "PartDesign::Body" else obj.getParentGeoFeatureGroup()
            return cls._body_has_valid_solid(body)
        except Exception:
            return False

    @staticmethod
    def _body_has_valid_solid(body):
        if body is None or getattr(body, "TypeId", "") != "PartDesign::Body":
            return False
        try:
            shape = body.Shape
            return not shape.isNull() and shape.isValid() and len(shape.Solids) == 1
        except Exception:
            return False


def register_workbench(workbench):
    workbench.appendMenu("Frontdoor", ["Frontdoor_NewDesign", "Frontdoor_NativeToolbars"])
    Gui.addCommand("Frontdoor_NewDesign", _NewDesignCommand())
    Gui.addCommand("Frontdoor_NativeToolbars", _NativeToolbarsCommand())


class _NewDesignCommand:
    def GetResources(self):
        return {"MenuText": "New Design", "ToolTip": "Create a new FreeCAD design document"}

    def IsActive(self):
        return True

    def Activated(self):
        Gui.runCommand("Std_New")


class _NativeToolbarsCommand:
    def GetResources(self):
        return {
            "MenuText": "Toggle Native Toolbars",
            "ToolTip": "Temporarily show or hide FreeCAD's standard toolbars while idle",
        }

    def IsActive(self):
        return _frontdoor_active and not _is_modeling_task_active()

    def Activated(self):
        global _native_toolbars_override
        _native_toolbars_override = not _native_toolbars_override
        _sync_native_toolbars(_is_modeling_task_active())


def _main_window_toolbars():
    main_window = Gui.getMainWindow()
    return [
        toolbar
        for toolbar in main_window.findChildren(QtWidgets.QToolBar)
        if toolbar.parentWidget() is main_window
    ]


def _capture_toolbar_visibility():
    global _toolbar_managed
    for toolbar in _main_window_toolbars():
        if toolbar not in _toolbar_visibility:
            # isHidden() reflects the toolbar's own visibility flag even when
            # its parent window is not currently visible.
            _toolbar_visibility[toolbar] = not toolbar.isHidden()
    _toolbar_managed = True


def _is_modeling_task_active():
    try:
        gui_document = Gui.activeDocument()
        return bool(gui_document and gui_document.getInEdit())
    except Exception:
        return False


def _is_focused_sketcher_toolbar(toolbar):
    title = toolbar.windowTitle().strip().casefold()
    return title in {
        "edit mode",
        "geometries",
        "constraints",
    }


def _sync_native_toolbars(editing_sketch=False):
    _capture_toolbar_visibility()
    toolbars = _main_window_toolbars()
    if editing_sketch:
        # The sketch editor's command bars provide geometry and constraint
        # tools. Keep them available while the remaining duplicate bars stay
        # out of the task-focused layout.
        for toolbar in toolbars:
            toolbar.setVisible(_is_focused_sketcher_toolbar(toolbar))
        return
    if not _frontdoor_active:
        return
    if _native_toolbars_override:
        for toolbar in toolbars:
            toolbar.setVisible(_toolbar_visibility.get(toolbar, True))
        return
    for toolbar in toolbars:
        toolbar.hide()


def _restore_native_toolbars():
    global _toolbar_managed, _native_toolbars_override
    if not _toolbar_managed:
        return
    for toolbar, was_visible in list(_toolbar_visibility.items()):
        try:
            toolbar.setVisible(was_visible)
        except RuntimeError:
            # A workbench may have destroyed an add-on toolbar on shutdown.
            pass
    _toolbar_visibility.clear()
    _toolbar_managed = False
    _native_toolbars_override = False


def show():
    global _dock, _timer, _frontdoor_active
    _frontdoor_active = True
    main_window = Gui.getMainWindow()
    if _dock is None:
        _dock = TaskSurface(main_window)
        main_window.addDockWidget(QtCore.Qt.DockWidgetArea.TopDockWidgetArea, _dock)
    _dock.show()
    _dock.raise_()
    gui_document = Gui.activeDocument()
    in_edit = gui_document.getInEdit() if gui_document else None
    edit_object = getattr(in_edit, "Object", None) or in_edit
    _sync_native_toolbars(
        getattr(edit_object, "TypeId", "") == "Sketcher::SketchObject"
    )
    if _timer is None:
        _timer = QtCore.QTimer(_dock)
        _timer.timeout.connect(_dock.refresh_state)
    if not _timer.isActive():
        _timer.start(350)


def hide():
    global _frontdoor_active
    _frontdoor_active = False
    if _dock is not None:
        _dock.hide()
    if _is_modeling_task_active():
        # Native Part Design commands briefly switch workbenches while opening
        # their edit task. Wait for the command handler's return to Frontdoor
        # before deciding whether the original toolbar layout should be restored.
        QtCore.QTimer.singleShot(300, _restore_after_workbench_switch)
    else:
        _restore_native_toolbars()
        if _timer is not None:
            _timer.stop()


def _restore_after_workbench_switch():
    try:
        if Gui.activeWorkbench().name() == "FrontdoorWorkbench":
            return
    except Exception:
        pass
    _restore_native_toolbars()
    if _timer is not None:
        _timer.stop()

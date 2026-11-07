"""Small native-Qt task surface that dispatches to FreeCAD's own commands."""

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets


_dock = None
_timer = None
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
        new_design = QtWidgets.QToolButton(root)
        new_design.setText("New Design")
        new_design.setProperty("commandId", _commands["New Design"])
        new_design.clicked.connect(lambda checked=False: self._run(_commands["New Design"]))
        heading.addWidget(new_design)
        heading.addWidget(QtWidgets.QLabel("Frontdoor prototype"))
        layout.addLayout(heading)

        self.tabs = QtWidgets.QTabWidget(root)
        self.tabs.setObjectName("frontdoorTaskTabs")
        self.tabs.setDocumentMode(True)
        try:
            self.available_commands = set(Gui.listCommands())
        except Exception:
            self.available_commands = None
        self.solid_page = QtWidgets.QWidget(self.tabs)
        row = QtWidgets.QHBoxLayout(self.solid_page)
        row.setContentsMargins(4, 6, 4, 0)
        row.setSpacing(10)

        row.addWidget(self._group("Create", ("Create Sketch", "Pad", "Pocket")))
        row.addWidget(self._group("Modify", ("Fillet", "Chamfer")))
        row.addStretch(1)
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
            "QTabBar::tab:selected { background: #1677d2; color: #ffffff; font-weight: 600; }"
            "QToolButton { background: #343b44; border: 1px solid #48515d; border-radius: 4px; padding: 7px 12px; min-width: 78px; color: #f1f4f7; }"
            "QToolButton:hover:enabled { background: #414b56; border-color: #748291; }"
            "QToolButton:disabled { color: #74808c; background: #2c3239; border-color: #3b424a; }"
        )
        self.buttons = {}
        for button in root.findChildren(QtWidgets.QToolButton):
            self.buttons[button.property("commandId")] = button
        self.refresh_state()

    def _group(self, title, labels):
        group = QtWidgets.QGroupBox(title)
        row = QtWidgets.QHBoxLayout(group)
        row.setContentsMargins(8, 12, 8, 8)
        row.setSpacing(6)
        for label in labels:
            command = _commands[label]
            if self.available_commands is not None and command not in self.available_commands:
                continue
            button = QtWidgets.QToolButton(group)
            button.setText(label)
            button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextOnly)
            button.setProperty("commandId", command)
            button.setToolTip(self._tooltip(label))
            button.clicked.connect(lambda checked=False, command=command: self._run(command))
            row.addWidget(button)
        if row.count() == 0:
            group.hide()
        return group

    @staticmethod
    def _tooltip(label):
        descriptions = {
            "Create Sketch": "Start a native FreeCAD sketch and choose a plane.",
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
        selection = Gui.Selection.getSelectionEx() if has_document else []
        selected_sketch = any(
            getattr(item.Object, "TypeId", "") == "Sketcher::SketchObject"
            for item in selection
        )
        has_selection = bool(selection)
        for command, button in self.buttons.items():
            command_available = self.available_commands is None or command in self.available_commands
            if command == "Std_New":
                button.setEnabled(command_available)
            elif command == "PartDesign_NewSketch":
                button.setEnabled(command_available and has_document)
            elif command in ("PartDesign_Pad", "PartDesign_Pocket"):
                button.setEnabled(command_available and has_document and selected_sketch)
            else:
                button.setEnabled(command_available and has_document and has_selection)

        if not has_document:
            hint = "Create a design to start sketching."
        elif selected_sketch:
            hint = "Sketch selected · Pad or Pocket is ready."
        elif has_selection:
            hint = "Selection ready · choose Fillet or Chamfer when edges are selected."
        else:
            hint = "Create a sketch on a plane, then draw a closed profile to begin."
        missing = [
            label
            for label in ("Create Sketch", "Pad", "Pocket", "Fillet", "Chamfer")
            if self.available_commands is not None and _commands[label] not in self.available_commands
        ]
        if missing:
            hint = "Unavailable in this FreeCAD build: " + ", ".join(missing)
        self.status.setText(hint)


def register_workbench(workbench):
    workbench.appendMenu("Frontdoor", ["Frontdoor_NewDesign"])
    Gui.addCommand("Frontdoor_NewDesign", _NewDesignCommand())


class _NewDesignCommand:
    def GetResources(self):
        return {"MenuText": "New Design", "ToolTip": "Create a new FreeCAD design document"}

    def IsActive(self):
        return True

    def Activated(self):
        Gui.runCommand("Std_New")


def show():
    global _dock, _timer
    main_window = Gui.getMainWindow()
    if _dock is None:
        _dock = TaskSurface(main_window)
        main_window.addDockWidget(QtCore.Qt.DockWidgetArea.TopDockWidgetArea, _dock)
    _dock.show()
    _dock.raise_()
    if _timer is None:
        _timer = QtCore.QTimer(_dock)
        _timer.timeout.connect(_dock.refresh_state)
        _timer.start(350)


def hide():
    if _dock is not None:
        _dock.hide()

from __future__ import annotations

import os
import uuid
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .models import ReleaseAsset, SetupResult
from .addon import ADDON_COMMIT
from .errors import FrontdoorError
from .performance import append_startup_measurement
from .freecad_addon.FrontdoorUI.startup_status import (
    launch_ready_marker,
    read_launch_ready_marker,
)
from .launcher import launch_freecad
from .paths import fusion_addon_ready, install_root, managed_executable, managed_version, profile_root
from .release import latest_windows_release
from .setup import install_managed_copy
from .workers import TaskWorker


STYLESHEET = """
QMainWindow, QWidget#root { background: #11151a; color: #edf1f4; }
QFrame#topbar { background: #171c22; border-bottom: 1px solid #303842; }
QFrame#surface { background: #1b2128; border: 1px solid #343d47; border-radius: 12px; }
QFrame#inset { background: #202730; border: 1px solid #38434e; border-radius: 9px; }
QLabel { color: #edf1f4; }
QLabel#muted { color: #a9b3bd; }
QLabel#quiet { color: #8995a0; }
QLabel#eyebrow { color: #ff9a70; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
QLabel#headline { font-size: 29px; font-weight: 700; }
QLabel#section { font-size: 15px; font-weight: 650; }
QLabel#logo { color: #ff8754; font-size: 21px; font-weight: 800; }
QPushButton { min-height: 42px; padding: 0 15px; border: 1px solid #46515c; border-radius: 7px; background: #252d36; color: #f1f4f6; font-weight: 650; }
QPushButton:hover { background: #303a45; border-color: #65717e; }
QPushButton:disabled { color: #727e89; background: #20262d; border-color: #343d46; }
QPushButton#primary { background: #fa8150; color: #1d1714; border: 0; }
QPushButton#primary:hover { background: #ff9a70; }
QPushButton#quietButton { background: transparent; border-color: transparent; color: #bac4cc; }
QPushButton#quietButton:hover { background: #252d36; }
QProgressBar { min-height: 8px; max-height: 8px; border: 0; border-radius: 4px; background: #303842; }
QProgressBar::chunk { border-radius: 4px; background: #ff8754; }
"""


def _bytes(value: int) -> str:
    gib = value / (1024**3)
    return f"{gib:.1f} GB" if gib >= 1 else f"{value / (1024**2):.0f} MB"


class MainWindow(QMainWindow):
    LAUNCH_READY_TIMEOUT_MS = 90_000

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FreeCAD Fusion Frontdoor")
        self.setMinimumSize(880, 660)
        self.resize(1060, 760)
        self._release: ReleaseAsset | None = None
        self._worker: TaskWorker | None = None
        self._closing = False
        self._executable = managed_executable()
        self._is_windows = os.name == "nt"
        self._build_ui()
        self._show_ready()
        self._refresh_release()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("topbar")
        top_layout = QHBoxLayout(topbar)
        top_layout.setContentsMargins(28, 14, 28, 14)
        logo = QLabel("F")
        logo.setObjectName("logo")
        logo.setFixedWidth(28)
        wordmark = QLabel("FREECAD  /  FRONTDOOR")
        wordmark.setStyleSheet("font-size: 12px; font-weight: 750; letter-spacing: 1px;")
        top_layout.addWidget(logo)
        top_layout.addWidget(wordmark)
        top_layout.addStretch(1)
        self.platform_badge = QLabel("WINDOWS SETUP")
        self.platform_badge.setObjectName("muted")
        self.platform_badge.setStyleSheet("font-size: 11px; font-weight: 650; letter-spacing: 0.7px;")
        top_layout.addWidget(self.platform_badge)
        layout.addWidget(topbar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(42, 32, 42, 32)
        content_layout.setSpacing(20)
        content_layout.addWidget(self._label("A FAMILIAR WAY INTO FREECAD", "eyebrow"))
        content_layout.addWidget(self._label("Start with the tools you already know.", "headline"))
        subtitle = self._label(
            "Set up a separate FreeCAD copy with Fusion-style navigation. Your existing FreeCAD setup stays on its own."
        )
        subtitle.setObjectName("muted")
        subtitle.setWordWrap(True)
        content_layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("surface")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 22, 24, 22)
        card_layout.setSpacing(17)
        card_layout.addWidget(self._label("Your separate workspace", "section"))

        self.version_label = QLabel("Checking the latest stable FreeCAD release…")
        self.version_label.setObjectName("muted")
        card_layout.addWidget(self.version_label)

        locations = QFrame()
        locations.setObjectName("inset")
        locations_layout = QVBoxLayout(locations)
        locations_layout.setContentsMargins(15, 13, 15, 13)
        locations_layout.setSpacing(7)
        locations_layout.addWidget(self._label("APP LOCATION", "eyebrow"))
        self.install_path_label = QLabel(str(install_root()))
        self.install_path_label.setWordWrap(True)
        self.install_path_label.setTextInteractionFlags(
            self.install_path_label.textInteractionFlags() | Qt.TextInteractionFlag.TextSelectableByMouse
        )
        locations_layout.addWidget(self.install_path_label)
        self.profile_path_label = QLabel(f"Fusion profile  ·  {profile_root('fusion')}")
        self.profile_path_label.setObjectName("muted")
        self.profile_path_label.setWordWrap(True)
        self.profile_path_label.setTextInteractionFlags(
            self.profile_path_label.textInteractionFlags() | Qt.TextInteractionFlag.TextSelectableByMouse
        )
        locations_layout.addWidget(self.profile_path_label)
        self.full_profile_path_label = QLabel(f"Full FreeCAD profile  ·  {profile_root('full')}")
        self.full_profile_path_label.setObjectName("muted")
        self.full_profile_path_label.setWordWrap(True)
        self.full_profile_path_label.setTextInteractionFlags(
            self.full_profile_path_label.textInteractionFlags() | Qt.TextInteractionFlag.TextSelectableByMouse
        )
        locations_layout.addWidget(self.full_profile_path_label)
        locations_layout.addWidget(self._label("Fusion and Full FreeCAD use separate settings profiles.", "muted"))
        card_layout.addWidget(locations)

        self.status_label = QLabel("Waiting for release details…")
        self.status_label.setObjectName("muted")
        self.status_label.setWordWrap(True)
        card_layout.addWidget(self.status_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.hide()
        card_layout.addWidget(self.progress)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        self.setup_button = QPushButton("Set up separate FreeCAD")
        self.setup_button.setObjectName("primary")
        self.setup_button.clicked.connect(self._start_setup)
        actions.addWidget(self.setup_button)
        self.fusion_button = QPushButton("Launch Fusion mode")
        self.fusion_button.clicked.connect(lambda: self._launch("fusion"))
        actions.addWidget(self.fusion_button)
        self.full_button = QPushButton("Launch Full FreeCAD")
        self.full_button.clicked.connect(lambda: self._launch("full"))
        actions.addWidget(self.full_button)
        card_layout.addLayout(actions)
        content_layout.addWidget(card)

        safety = QFrame()
        safety.setObjectName("inset")
        safety_layout = QVBoxLayout(safety)
        safety_layout.setContentsMargins(17, 14, 17, 14)
        safety_layout.setSpacing(6)
        safety_layout.addWidget(self._label("What this setup changes", "section"))
        details = self._label(
            "Downloads the official FreeCAD Windows installer, checks its SHA-256 and publisher signature, "
            "then installs the Fusion add-on into a dedicated profile. It does not edit your existing FreeCAD settings."
        )
        details.setObjectName("muted")
        details.setWordWrap(True)
        safety_layout.addWidget(details)
        source = QLabel(
            f'Community add-on pinned to a fixed revision. '
            f'<a href="https://github.com/arxdsilva/freecad-fusion/commit/{ADDON_COMMIT}">Review source</a> · '
            f'<a href="https://github.com/arxdsilva/freecad-fusion/blob/{ADDON_COMMIT}/README.md#using-and-undoing-it">Undo instructions</a>. '
            'Windows behavior still needs confirmation.'
        )
        source.setObjectName("muted")
        source.setOpenExternalLinks(True)
        source.setStyleSheet("QLabel { color: #a9b3bd; } a { color: #ff9a70; }")
        safety_layout.addWidget(source)
        content_layout.addWidget(safety)
        content_layout.addStretch(1)

        footer = QHBoxLayout()
        footer.addWidget(self._label("Independent community project · Not affiliated with Autodesk", "quiet"))
        footer.addStretch(1)
        self.refresh_button = QPushButton("Refresh release info")
        self.refresh_button.setObjectName("quietButton")
        self.refresh_button.clicked.connect(self._refresh_release)
        footer.addWidget(self.refresh_button)
        content_layout.addLayout(footer)
        layout.addWidget(content, 1)
        self.setCentralWidget(root)

        if not self._is_windows:
            self.platform_badge.setText("WINDOWS TARGET · SETUP DISABLED HERE")
            self.status_label.setText("This host is not Windows. You can inspect the app, but installer and profile behavior need a Windows run.")
            self.setup_button.setEnabled(False)
            self.setup_button.setToolTip("Windows-only operation")
            self.fusion_button.setEnabled(False)
            self.full_button.setEnabled(False)

    @staticmethod
    def _label(text: str, object_name: str | None = None) -> QLabel:
        label = QLabel(text)
        if object_name:
            label.setObjectName(object_name)
        return label

    def _show_ready(self) -> None:
        self._executable = managed_executable()
        if self._executable is not None:
            self.setup_button.setText("Repair / refresh Fusion mode")
            self.fusion_button.setEnabled(self._is_windows and fusion_addon_ready())
            self.full_button.setEnabled(self._is_windows)
            if fusion_addon_ready():
                self.status_label.setText(f"FreeCAD {managed_version() or ''} is ready at {self._executable}")
            else:
                self.setup_button.setText("Finish Fusion mode setup")
                self.status_label.setText("The separate FreeCAD copy exists; finish setup to add Fusion mode.")
        else:
            self.setup_button.setText("Set up separate FreeCAD")
            self.fusion_button.setEnabled(False)
            self.full_button.setEnabled(False)

    def _set_worker(self, worker: TaskWorker, success_callback) -> None:
        self._worker = worker
        worker.progress.connect(self._on_progress)
        worker.succeeded.connect(success_callback)
        worker.failed.connect(self._on_error)
        worker.finished.connect(self._on_worker_finished)
        worker.start()

    def _on_worker_finished(self) -> None:
        if self._worker:
            self._worker.deleteLater()
        self._worker = None
        self.refresh_button.setEnabled(True)
        if self._is_windows:
            self.setup_button.setEnabled(self._release is not None)
        self.progress.hide()

    def _on_progress(self, message: str, percentage: int) -> None:
        self.status_label.setText(message)
        self.progress.setValue(max(0, min(percentage, 100)))

    def _on_error(self, message: str) -> None:
        self.status_label.setText("Setup stopped. Your existing FreeCAD settings were not changed.")
        QMessageBox.critical(self, "FreeCAD setup could not finish", message)

    def _refresh_release(self) -> None:
        self.refresh_button.setEnabled(False)
        self.setup_button.setEnabled(False)
        self.progress.show()
        self.progress.setRange(0, 0)
        self.status_label.setText("Checking official FreeCAD release information…")

        def loaded(asset: ReleaseAsset) -> None:
            self._release = asset
            self.version_label.setText(
                f"Latest stable: FreeCAD {asset.version}  ·  Windows x64  ·  installer {_bytes(asset.size)}"
            )
            self.progress.setRange(0, 100)
            self.progress.hide()
            self.status_label.setText(
                "Release details loaded. Setup and launch are available on Windows."
                if self._is_windows
                else "Release details loaded from the official feed. Setup and launch require Windows."
            )
            self.setup_button.setEnabled(self._is_windows)

        worker = TaskWorker(lambda progress: latest_windows_release(progress))
        self._set_worker(worker, loaded)

    def _start_setup(self) -> None:
        if not self._is_windows or self._release is None:
            return
        existing_version = managed_version()
        if self._executable and existing_version == self._release.version:
            action = f"Keep the app-managed FreeCAD {existing_version} copy and refresh its pinned Fusion add-on."
        elif self._executable and existing_version:
            action = (
                f"Download FreeCAD {self._release.version} ({_bytes(self._release.size)}) from the official release, "
                f"verify its SHA-256 and Windows publisher signature, then update this app-managed {existing_version} copy."
            )
        else:
            action = (
                f"Download FreeCAD {self._release.version} ({_bytes(self._release.size)}) from the official release, "
                "verify its SHA-256 and Windows publisher signature, then install it for your Windows user."
            )
        message = (
            f"{action}\n\nInstall location:\n{install_root()}\n\n"
            f"Fusion profile:\n{profile_root('fusion')}\n\n"
            f"Full FreeCAD profile:\n{profile_root('full')}\n\n"
            f"Add-on source: github.com/arxdsilva/freecad-fusion @ {ADDON_COMMIT}\n\n"
            "Expected installer publisher: FreeCAD Project Association AISBL. The installer must have a valid Authenticode signature.\n\n"
            "Then install the pinned Fusion add-on only in this app's separate profile. Its Windows behavior is "
            "not validated yet. No admin rights or "
            "changes to your existing FreeCAD profile are intended. Continue?"
        )
        answer = QMessageBox.question(
            self,
            "Set up a separate FreeCAD copy?",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.setup_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.show()
        worker = TaskWorker(lambda progress: install_managed_copy(self._release, progress))
        self._set_worker(worker, self._setup_complete)

    def _setup_complete(self, result: SetupResult) -> None:
        self._executable = result.executable
        self.status_label.setText(
            f"FreeCAD {result.version} is installed. The Fusion add-on is in its isolated profile."
        )
        self.fusion_button.setEnabled(True)
        self.full_button.setEnabled(True)
        self.setup_button.setText("Repair / refresh Fusion mode")
        QMessageBox.information(
            self,
            "Setup complete",
            "The separate FreeCAD copy and Fusion profile are ready. The first FreeCAD launch is the point "
            "where Windows behavior can be confirmed.",
        )

    def _launch(self, profile: str) -> None:
        executable = self._executable or managed_executable()
        if executable is None:
            QMessageBox.warning(self, "FreeCAD is not installed", "Set up the separate FreeCAD copy first.")
            return
        if profile == "fusion" and not fusion_addon_ready():
            QMessageBox.warning(self, "Fusion mode is not ready", "Run setup again to install the Fusion add-on.")
            return
        launch_token = uuid.uuid4().hex if profile == "fusion" else None
        try:
            process = launch_freecad(executable, profile, launch_token=launch_token)
        except FrontdoorError as exc:
            QMessageBox.critical(self, "Could not launch FreeCAD", str(exc))
            return
        self.status_label.setText(
            "Waiting for Frontdoor to confirm it loaded…"
            if launch_token
            else "Starting Full FreeCAD…"
        )
        QTimer.singleShot(
            500,
            lambda: self._check_launch(process, profile, launch_token, elapsed_ms=500),
        )

    def _check_launch(self, process, profile: str, launch_token: str | None, *, elapsed_ms: int) -> None:
        if self._closing:
            return
        if launch_token:
            marker = launch_ready_marker(profile_root(profile), launch_token)
            ready = read_launch_ready_marker(profile_root(profile), launch_token)
            if ready:
                marker.unlink(missing_ok=True)
                performance_log = os.environ.get("FRONTDOOR_PERF_LOG")
                if performance_log and profile == "fusion":
                    try:
                        append_startup_measurement(
                            performance_log,
                            profile=profile,
                            ready=ready,
                        )
                    except (OSError, ValueError):
                        pass
                self.status_label.setText(
                    f"Frontdoor workbench loaded · FreeCAD {ready['freecad_version']}"
                )
                return

        exit_code = process.poll()
        if profile == "full":
            if exit_code is None:
                self.status_label.setText(
                    "Full FreeCAD is running. This clean profile has no Frontdoor readiness signal; check its window."
                )
            elif exit_code == 0:
                self.status_label.setText(
                    "The Full FreeCAD launcher handed off successfully; GUI readiness is unconfirmed. Check its window."
                )
            else:
                self.status_label.setText(f"Full FreeCAD exited with status {exit_code}.")
                QMessageBox.warning(
                    self,
                    "Full FreeCAD did not start",
                    f"The FreeCAD process exited with status {exit_code}. Check the FreeCAD logs and try again.",
                )
            return

        if exit_code not in (None, 0):
            self.status_label.setText(f"FreeCAD exited with status {exit_code} before Frontdoor confirmed startup.")
            QMessageBox.warning(
                self,
                "Frontdoor did not start",
                f"FreeCAD exited with status {exit_code} before Frontdoor became ready. "
                "You can still try Launch Full FreeCAD or inspect the FreeCAD log.",
            )
            return

        if elapsed_ms < self.LAUNCH_READY_TIMEOUT_MS:
            self.status_label.setText("FreeCAD is starting; waiting for the Frontdoor workbench…")
            QTimer.singleShot(
                1000,
                lambda: self._check_launch(
                    process, profile, launch_token, elapsed_ms=elapsed_ms + 1000
                ),
            )
            return

        self.status_label.setText("Frontdoor did not confirm startup. The clean Full FreeCAD profile remains available.")
        QMessageBox.warning(
            self,
            "Frontdoor did not confirm startup",
            "The app did not receive an in-process ready signal from Frontdoor within 90 seconds. "
            "The FreeCAD window may still be opening. Check it before retrying; Launch Full FreeCAD is the recovery option.",
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._worker and self._worker.isRunning():
            QMessageBox.information(
                self,
                "Setup is still running",
                "Wait for the current download or setup step to finish, then close the app.",
            )
            event.ignore()
            return
        self._closing = True
        event.accept()

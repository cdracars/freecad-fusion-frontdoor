from __future__ import annotations

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from .window import MainWindow, STYLESHEET


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("FreeCAD Fusion Frontdoor")
    app.setOrganizationName("FreeCAD Fusion Frontdoor")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

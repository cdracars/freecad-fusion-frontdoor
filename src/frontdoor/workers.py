from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QThread, Signal


class TaskWorker(QThread):
    progress = Signal(str, int)
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, task: Callable[[Callable[[str, int], None]], Any]) -> None:
        super().__init__()
        self._task = task

    def run(self) -> None:
        try:
            result = self._task(self.progress.emit)
        except Exception as exc:
            logging.exception("Frontdoor task failed")
            self.failed.emit(str(exc))
        else:
            self.succeeded.emit(result)

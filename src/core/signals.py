from PyQt6.QtCore import QObject, pyqtSignal
from pathlib import Path


class AppSignals(QObject):
    """Bridges watcher-thread callbacks onto the Qt UI thread."""

    prn_started = pyqtSignal(Path)  # a report began printing -> show loading
    prn_ready = pyqtSignal(Path)    # the .PRN finished writing -> render it

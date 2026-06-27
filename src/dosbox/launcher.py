import subprocess
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

from ..logger import get_logger

logger = get_logger(__name__)


def launch_dosbox(dosbox_exe: Path, dosbox_conf: Path) -> subprocess.Popen:
    """Launch DOSBox-X as a child process so we own its lifecycle (see CLAUDE.md)."""
    process = subprocess.Popen([str(dosbox_exe), '-conf', str(dosbox_conf)])
    logger.info("DOSBox-X launched (pid=%s)", process.pid)
    return process


class DOSBoxMonitor(QThread):
    """Waits for DOSBox-X to exit, then signals the app to shut down."""

    dosbox_closed = pyqtSignal()

    def __init__(self, process: subprocess.Popen):
        super().__init__()
        self._process = process

    def run(self):
        self._process.wait()  # block until DOSBox-X exits
        logger.info("DOSBox-X closed (exit code=%s)", self._process.returncode)
        self.dosbox_closed.emit()

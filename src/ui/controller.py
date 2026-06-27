import os
import tempfile
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

from ..settings import Settings, FontConfig
from ..logger import get_logger
from ..report.parser import parse_prn
from ..report.generator import generate_pdf
from ..report.naming import report_filename
from .preview_window import PreviewWindow

logger = get_logger(__name__)


class PdfWorker(QThread):
    """Parses a .PRN and generates its PDF off the UI thread."""

    finished_ok = pyqtSignal(object, Path, str)  # (window, temp_pdf, suggested_name)
    failed = pyqtSignal(object, str)              # (window, message)

    def __init__(self, prn_path: Path, window: PreviewWindow, fonts: FontConfig):
        super().__init__()
        self._prn_path = prn_path
        self._window = window
        self._fonts = fonts

    def run(self):
        try:
            fd, temp_name = tempfile.mkstemp(suffix='.pdf')
            os.close(fd)
            temp_pdf = Path(temp_name)
            lines = parse_prn(str(self._prn_path))
            generate_pdf(lines, str(temp_pdf), self._fonts)
            suggested_name = report_filename(lines) or ""
            logger.info("Generated PDF for %s (%d lines) -> %s", self._prn_path, len(lines), temp_pdf)
        except Exception as exc:  # surface the failure in the window
            logger.error("Failed to generate PDF for %s", self._prn_path, exc_info=True)
            self.failed.emit(self._window, str(exc))
            return
        self.finished_ok.emit(self._window, temp_pdf, suggested_name)


class ReportController:
    """Owns the report windows: one new window per printed report.

    ``on_started`` opens a loading window as soon as the DOS program starts
    printing; ``on_ready`` generates the PDF and loads it into that window.
    Bursts are strictly sequential, so the window opened by the last
    ``on_started`` is the one the next ``on_ready`` fills.
    """

    def __init__(self, settings: Settings):
        self._settings = settings
        self._windows: set[PreviewWindow] = set()
        self._workers: set[PdfWorker] = set()
        self._pending: PreviewWindow | None = None

    def on_started(self, prn_path: Path):
        logger.info("Report started: %s", prn_path)
        window = PreviewWindow(self._settings.icon_file, self._settings.output_base)
        window.closed.connect(self._on_window_closed)
        self._windows.add(window)
        self._pending = window

        window.showNormal()
        window.raise_()
        window.activateWindow()

    def on_ready(self, prn_path: Path):
        window = self._pending
        self._pending = None
        if window is None or window not in self._windows:
            logger.warning("Report ready with no pending window: %s", prn_path)
            return

        worker = PdfWorker(prn_path, window, self._settings.fonts)
        worker.finished_ok.connect(self._on_pdf_ready)
        worker.failed.connect(self._on_pdf_failed)
        worker.finished.connect(lambda: self._workers.discard(worker))
        self._workers.add(worker)
        worker.start()

    def _on_pdf_ready(self, window: PreviewWindow, temp_pdf: Path, suggested_name: str):
        if window in self._windows:
            window.load_pdf(temp_pdf, suggested_name)
        elif temp_pdf.exists():
            temp_pdf.unlink()  # window closed while generating

    def _on_pdf_failed(self, window: PreviewWindow, message: str):
        if window in self._windows:
            window.show_error(message)

    def _on_window_closed(self, window: PreviewWindow):
        self._windows.discard(window)
        logger.info("Report window closed")

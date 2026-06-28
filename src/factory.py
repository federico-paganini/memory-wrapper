"""Composition root: builds Settings, sets up logging, validates (fail fast),
launches DOSBox-X and wires the PRN watcher to the report controller."""
import sys
import ctypes
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon

from settings import load_settings, SettingsError
from logger import setup_logging, get_logger
from core.signals import AppSignals
from dosbox.launcher import launch_dosbox, DOSBoxMonitor
from dosbox.watcher import PRNWatcher
from ui.controller import ReportController


class MemoryWrapperApp:
    """Holds the assembled runtime and runs the Qt event loop."""

    def __init__(self, qapp, dosbox_process, watcher, monitor, controller, signals):
        self._qapp = qapp
        self._dosbox_process = dosbox_process
        self._watcher = watcher
        # Held only to own their lifetime for the duration of the run.
        self._monitor = monitor
        self._controller = controller
        self._signals = signals

    def run(self) -> int:
        try:
            return self._qapp.exec()
        finally:
            self._watcher.stop()
            self._dosbox_process.terminate()  # just in case


def create_app() -> MemoryWrapperApp:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('memory.wrapper.app')

    settings = load_settings()
    setup_logging(
        settings.log_dir, settings.log_level,
        settings.log_max_bytes, settings.log_backup_count,
    )
    logger = get_logger(__name__)

    qapp = QApplication(sys.argv)
    qapp.setWindowIcon(QIcon(str(settings.icon_file)))
    qapp.setQuitOnLastWindowClosed(False)

    # Fail fast and loud: surface missing resources before launching anything.
    try:
        settings.validate()
    except SettingsError as exc:
        logger.critical("Startup validation failed:\n%s", exc)
        QMessageBox.critical(None, "Memory Wrapper", f"No se puede iniciar:\n\n{exc}")
        sys.exit(1)

    logger.info(
        "Settings OK (base_dir=%s, quiet_period=%ss)",
        settings.base_dir, settings.quiet_period,
    )

    dosbox_process = launch_dosbox(settings.dosbox_exe, settings.dosbox_conf)
    monitor = DOSBoxMonitor(dosbox_process)
    monitor.dosbox_closed.connect(qapp.quit)  # DOSBox closed -> shut everything down
    monitor.start()

    controller = ReportController(settings)
    signals = AppSignals()
    signals.prn_started.connect(controller.on_started)
    signals.prn_ready.connect(controller.on_ready)

    watcher = PRNWatcher(
        str(settings.program_dir),
        on_started=signals.prn_started.emit,
        on_ready=signals.prn_ready.emit,
        quiet_period=settings.quiet_period,
    )
    watcher.start()

    return MemoryWrapperApp(qapp, dosbox_process, watcher, monitor, controller, signals)

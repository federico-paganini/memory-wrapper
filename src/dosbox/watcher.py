import time
import threading
from pathlib import Path
from collections.abc import Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from ..logger import get_logger

logger = get_logger(__name__)


class PRNHandler(FileSystemEventHandler):
    """Detects .PRN writes via a write-inactivity debounce.

    The emulated printer writes the file incrementally, often pausing mid-job
    (between pages, or while the DOS program computes). Sampling the size until
    it repeats can mistake such a pause for the end of the write and yield a
    truncated report. Instead two callbacks bracket the write:

    - ``on_started`` fires on the first write of a burst (idle -> writing), so
      the UI can show a loading state while the DOS program is still printing.
    - ``on_ready`` fires once the file has stayed silent for ``quiet_period``
      seconds, i.e. the write has finished.
    """

    def __init__(
        self,
        on_started: Callable[[Path], None],
        on_ready: Callable[[Path], None],
        quiet_period: float = 1.5,
    ):
        self._on_started = on_started
        self._on_ready = on_ready
        self._quiet_period = quiet_period
        self._start_time = time.time()
        self._lock = threading.Lock()
        self._timers: dict[str, threading.Timer] = {}

    def on_modified(self, event: FileModifiedEvent):
        if event.is_directory or not event.src_path.upper().endswith('.PRN'):
            return

        path = Path(event.src_path)

        # Ignore the .PRN left over from a previous session: it is only relevant
        # once this run's DOS program rewrites it (mtime moves past start time).
        try:
            if path.stat().st_mtime <= self._start_time:
                return
        except OSError:
            return  # file vanished mid-event (e.g. being replaced)

        self._schedule(path)

    def _schedule(self, path: Path):
        """(Re)start the debounce timer; announce the start of a new burst."""
        src_path = str(path)
        with self._lock:
            existing = self._timers.get(src_path)
            if existing is not None:
                existing.cancel()
            else:
                # idle -> writing: a new report has started printing.
                logger.info("PRN write started: %s", path)
                self._on_started(path)
            timer = threading.Timer(self._quiet_period, self._on_quiet, args=(path,))
            self._timers[src_path] = timer
            timer.start()

    def _on_quiet(self, path: Path):
        """Fired once the file has been silent for ``quiet_period``: it is done."""
        with self._lock:
            self._timers.pop(str(path), None)
        try:
            size = path.stat().st_size
        except OSError:
            size = -1
        logger.info("PRN ready: %s (%d bytes)", path, size)
        self._on_ready(path)

    def cancel_pending(self):
        """Cancel any in-flight debounce timers (called on shutdown)."""
        with self._lock:
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()


class PRNWatcher:
    def __init__(
        self,
        watch_path: str,
        on_started: Callable[[Path], None],
        on_ready: Callable[[Path], None],
        quiet_period: float = 1.5,
    ):
        self._watch_path = watch_path
        self._handler = PRNHandler(on_started, on_ready, quiet_period)
        self._observer = Observer()

    def start(self):
        self._observer.schedule(self._handler, self._watch_path, recursive=False)
        self._observer.start()
        logger.info("Watching %s for .PRN files", self._watch_path)

    def stop(self):
        self._observer.stop()
        self._observer.join()
        self._handler.cancel_pending()

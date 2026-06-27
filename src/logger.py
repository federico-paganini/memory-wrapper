import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logging(log_dir: Path, level: str, max_bytes: int, backup_count: int) -> None:
    """Configure root logging from injected settings. Call once at startup."""
    log_dir.mkdir(parents=True, exist_ok=True)

    handlers: list[logging.Handler] = [
        RotatingFileHandler(
            filename=log_dir / "app.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        ),
    ]
    # The build is windowed (console=False): sys.stderr is None and a bare
    # StreamHandler would crash. Only log to console when one exists (dev).
    if sys.stderr is not None:
        handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=True,  # called once in the app; lets logging be reconfigured cleanly
    )

    # No console in a windowed build, so an uncaught exception would vanish.
    # Route it to the log instead of losing it.
    def _log_uncaught(exc_type, exc, tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc, tb)
            return
        logging.getLogger(__name__).critical("Uncaught exception", exc_info=(exc_type, exc, tb))

    sys.excepthook = _log_uncaught

    logging.getLogger(__name__).info("Logging initialized (level=%s, dir=%s)", level.upper(), log_dir)


def get_logger(name: str = __name__) -> logging.Logger:
    return logging.getLogger(name)

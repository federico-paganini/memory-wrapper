"""Tests for logging setup."""
import sys
import logging

import pytest

from logger import setup_logging, get_logger


def test_creates_log_file_and_writes(tmp_path):
    log_dir = tmp_path / 'logs'
    setup_logging(log_dir, 'INFO', 1024, 2)
    get_logger('test').info("hello-marker")

    log_file = log_dir / 'app.log'
    assert log_file.exists()
    assert 'hello-marker' in log_file.read_text(encoding='utf-8')


def test_log_dir_is_created(tmp_path):
    log_dir = tmp_path / 'nested' / 'logs'
    assert not log_dir.exists()
    setup_logging(log_dir, 'INFO', 1024, 2)
    assert log_dir.exists()


def test_level_filtering(tmp_path):
    log_dir = tmp_path / 'logs'
    setup_logging(log_dir, 'WARNING', 1024, 2)
    logger = get_logger('test')
    logger.info("should-not-appear")
    logger.warning("should-appear")

    content = (log_dir / 'app.log').read_text(encoding='utf-8')
    assert 'should-appear' in content
    assert 'should-not-appear' not in content


def test_no_stream_handler_when_stderr_is_none(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, 'stderr', None)
    setup_logging(tmp_path / 'logs', 'INFO', 1024, 2)
    stream_handlers = [
        h for h in logging.getLogger().handlers
        if isinstance(h, logging.StreamHandler)
        and not isinstance(h, logging.handlers.RotatingFileHandler)
    ]
    assert stream_handlers == []


def test_stream_handler_present_with_stderr(tmp_path):
    setup_logging(tmp_path / 'logs', 'INFO', 1024, 2)
    stream_handlers = [
        h for h in logging.getLogger().handlers
        if type(h) is logging.StreamHandler
    ]
    assert len(stream_handlers) == 1


def test_excepthook_logs_uncaught(tmp_path):
    setup_logging(tmp_path / 'logs', 'INFO', 1024, 2)
    assert sys.excepthook is not sys.__excepthook__

    try:
        raise ValueError("boom-marker")
    except ValueError:
        sys.excepthook(*sys.exc_info())

    content = (tmp_path / 'logs' / 'app.log').read_text(encoding='utf-8')
    assert 'boom-marker' in content
    assert 'CRITICAL' in content


def test_invalid_level_falls_back_to_info(tmp_path):
    # getattr fallback path: a bogus level must not crash and defaults to INFO.
    setup_logging(tmp_path / 'logs', 'NONSENSE', 1024, 2)
    assert logging.getLogger().level == logging.INFO

"""Tests for the write-inactivity debounce in PRNHandler.

The debounce relies on wall-clock timers, so these use a short quiet_period and
control ``_start_time`` explicitly (instead of relying on filesystem mtime
granularity) to stay deterministic.
"""
import time
from pathlib import Path

import pytest

from src.dosbox.watcher import PRNHandler

QUIET = 0.25


class FakeEvent:
    def __init__(self, src_path: str):
        self.src_path = src_path
        self.is_directory = False


@pytest.fixture
def prn(tmp_path):
    path = tmp_path / 'CONT.PRN'
    path.write_bytes(b'')
    return path


def make_handler(start_time: float = 0.0):
    """Build a handler. Default start_time=0 (epoch) so any real file passes the
    stale-file gate; pass a future value to exercise the gate itself."""
    started: list[Path] = []
    ready: list[Path] = []
    handler = PRNHandler(started.append, ready.append, quiet_period=QUIET)
    handler._start_time = start_time
    return handler, started, ready


def write(handler, path: Path, data: bytes):
    with open(path, 'ab') as f:
        f.write(data)
    handler.on_modified(FakeEvent(str(path)))


def test_ready_fires_after_quiet_period(prn):
    handler, started, ready = make_handler()
    write(handler, prn, b'data\n')
    assert ready == []  # not yet
    time.sleep(QUIET + 0.15)
    assert len(started) == 1
    assert len(ready) == 1


def test_mid_write_pause_does_not_truncate(prn):
    handler, started, ready = make_handler()
    write(handler, prn, b'line 1\n')
    time.sleep(QUIET * 0.5)
    write(handler, prn, b'line 2\n')
    time.sleep(QUIET * 0.5)
    write(handler, prn, b'line 3\n')
    assert ready == []  # a pause shorter than quiet_period must not fire
    time.sleep(QUIET + 0.15)
    assert len(started) == 1
    assert len(ready) == 1


def test_started_fires_once_per_burst(prn):
    handler, started, ready = make_handler()
    write(handler, prn, b'a')
    write(handler, prn, b'b')
    write(handler, prn, b'c')
    assert len(started) == 1  # one burst -> one start
    time.sleep(QUIET + 0.15)
    assert len(ready) == 1


def test_sequential_bursts_open_separate_reports(prn):
    handler, started, ready = make_handler()
    write(handler, prn, b'report A\n')
    time.sleep(QUIET + 0.15)
    write(handler, prn, b'report B\n')
    time.sleep(QUIET + 0.15)
    assert len(started) == 2
    assert len(ready) == 2


def test_cancel_pending_stops_inflight_timer(prn):
    handler, started, ready = make_handler()
    write(handler, prn, b'half')
    handler.cancel_pending()
    time.sleep(QUIET + 0.15)
    assert ready == []  # cancelled before firing


def test_stale_file_before_start_is_ignored(prn):
    # A file whose mtime predates the handler's start must be ignored.
    handler, started, ready = make_handler(start_time=time.time() + 100)
    handler.on_modified(FakeEvent(str(prn)))
    time.sleep(QUIET + 0.15)
    assert started == []
    assert ready == []


def test_non_prn_file_is_ignored(prn):
    handler, started, ready = make_handler()
    other = prn.parent / 'data.txt'
    other.write_bytes(b'x')
    handler.on_modified(FakeEvent(str(other)))
    time.sleep(QUIET + 0.15)
    assert started == []
    assert ready == []

"""Tests for base-path resolution (dev vs frozen)."""
import sys
from pathlib import Path

from src.core.utils import get_base_path


def test_dev_base_path_is_repo_root(monkeypatch):
    monkeypatch.setattr(sys, 'frozen', False, raising=False)
    base = get_base_path()
    # In dev it resolves to the repo root, which holds src/ and pyproject.toml.
    assert (base / 'src').is_dir()
    assert (base / 'pyproject.toml').exists()


def test_frozen_base_path_is_executable_dir(monkeypatch, tmp_path):
    fake_exe = tmp_path / 'MemoryWrapper.exe'
    fake_exe.write_bytes(b'')
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, 'executable', str(fake_exe))
    assert get_base_path() == tmp_path

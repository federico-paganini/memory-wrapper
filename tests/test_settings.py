"""Tests for settings construction, validation and env overrides."""
from pathlib import Path

import pytest

from src.settings import Settings, FontConfig, SettingsError, load_settings, _env_float


def make_settings(tmp_path: Path, **overrides) -> Settings:
    """Build a Settings whose required paths all exist under tmp_path."""
    for name in ('dosbox.exe', 'dosbox-x.conf', 'Icon.png', 'consola.ttf', 'consolab.ttf'):
        (tmp_path / name).write_bytes(b'x')
    program = tmp_path / 'program'
    program.mkdir()

    base = dict(
        base_dir=tmp_path,
        program_dir=program,
        assets_dir=tmp_path,
        icon_file=tmp_path / 'Icon.png',
        dosbox_exe=tmp_path / 'dosbox.exe',
        dosbox_conf=tmp_path / 'dosbox-x.conf',
        fonts=FontConfig(
            regular=tmp_path / 'consola.ttf',
            bold=tmp_path / 'consolab.ttf',
            size_normal=12, size_condensed=10, size_wide=18,
        ),
        quiet_period=1.5,
        log_dir=tmp_path / 'logs',
        log_level='INFO',
        log_max_bytes=1024,
        log_backup_count=3,
        output_base=tmp_path / 'out',
    )
    base.update(overrides)
    return Settings(**base)


def test_validate_passes_when_all_present(tmp_path):
    make_settings(tmp_path).validate()  # must not raise


def test_validate_lists_all_missing(tmp_path):
    s = make_settings(tmp_path, dosbox_exe=tmp_path / 'nope.exe',
                      icon_file=tmp_path / 'missing.png')
    with pytest.raises(SettingsError) as exc:
        s.validate()
    message = str(exc.value)
    assert 'nope.exe' in message
    assert 'missing.png' in message
    # the present ones must not be reported
    assert 'consola.ttf' not in message


def test_validate_reports_missing_font(tmp_path):
    s = make_settings(tmp_path, fonts=FontConfig(
        regular=tmp_path / 'absent.ttf', bold=tmp_path / 'consolab.ttf',
        size_normal=12, size_condensed=10, size_wide=18,
    ))
    with pytest.raises(SettingsError, match='absent.ttf'):
        s.validate()


# --- load_settings env overrides ------------------------------------------------

def test_load_settings_defaults(monkeypatch):
    monkeypatch.delenv('MEMORY_WRAPPER_QUIET_PERIOD', raising=False)
    monkeypatch.delenv('MEMORY_WRAPPER_LOG_LEVEL', raising=False)
    s = load_settings()
    assert s.quiet_period == 1.5
    assert s.log_level == 'INFO'
    assert s.fonts.size_normal == 12


def test_load_settings_env_overrides(monkeypatch):
    monkeypatch.setenv('MEMORY_WRAPPER_QUIET_PERIOD', '2.5')
    monkeypatch.setenv('MEMORY_WRAPPER_LOG_LEVEL', 'debug')
    s = load_settings()
    assert s.quiet_period == 2.5
    assert s.log_level == 'DEBUG'  # upper-cased


def test_load_settings_log_dir_uses_localappdata(monkeypatch):
    monkeypatch.setenv('LOCALAPPDATA', '/tmp/fake-appdata')
    s = load_settings()
    assert s.log_dir == Path('/tmp/fake-appdata') / 'MemoryWrapper' / 'logs'


# --- _env_float -----------------------------------------------------------------

def test_env_float_default_when_unset(monkeypatch):
    monkeypatch.delenv('X_FLOAT', raising=False)
    assert _env_float('X_FLOAT', 1.5) == 1.5


def test_env_float_parses_value(monkeypatch):
    monkeypatch.setenv('X_FLOAT', '3.25')
    assert _env_float('X_FLOAT', 1.5) == 3.25


def test_env_float_falls_back_on_garbage(monkeypatch):
    monkeypatch.setenv('X_FLOAT', 'not-a-number')
    assert _env_float('X_FLOAT', 1.5) == 1.5

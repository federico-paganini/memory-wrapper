import os
from dataclasses import dataclass
from pathlib import Path

from .core.utils import get_base_path


class SettingsError(Exception):
    """Raised when required runtime resources are missing (fail fast at startup)."""


@dataclass(frozen=True)
class FontConfig:
    """Fonts and per-ESC/P-state sizes used to render the report PDF."""

    regular: Path
    bold: Path
    size_normal: int
    size_condensed: int
    size_wide: int


@dataclass(frozen=True)
class Settings:
    """Centralized application configuration.

    All knobs live here (no .env): paths are derived from the base dir, a couple
    of field-tunable values accept an environment override. Built once via
    ``load_settings`` and injected from the factory.
    """

    base_dir: Path
    program_dir: Path
    icon_file: Path
    dosbox_exe: Path
    dosbox_conf: Path

    fonts: FontConfig

    quiet_period: float

    log_dir: Path
    log_level: str
    log_max_bytes: int
    log_backup_count: int

    output_base: Path

    def validate(self) -> None:
        """Ensure every required file/dir exists; raise listing all that don't."""
        required = {
            'DOSBox-X executable': self.dosbox_exe,
            'DOSBox-X config': self.dosbox_conf,
            'DOS program directory': self.program_dir,
            'application icon': self.icon_file,
            'regular font': self.fonts.regular,
            'bold font': self.fonts.bold,
        }
        missing = [f"  - {name}: {path}" for name, path in required.items() if not path.exists()]
        if missing:
            raise SettingsError("Missing required files:\n" + "\n".join(missing))


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def load_settings() -> Settings:
    base = get_base_path()

    local_appdata = os.environ.get('LOCALAPPDATA')
    log_root = Path(local_appdata) if local_appdata else Path.home()

    return Settings(
        base_dir=base,
        program_dir=base / 'legacy' / 'program',
        icon_file=base / 'assets' / 'Icon.png',
        dosbox_exe=base / 'dosbox' / 'dosbox-x.exe',
        dosbox_conf=base / 'legacy' / 'dosbox-x.conf',
        fonts=FontConfig(
            regular=Path('C:/Windows/Fonts/consola.ttf'),
            bold=Path('C:/Windows/Fonts/consolab.ttf'),
            size_normal=12,
            size_condensed=10,
            size_wide=18,
        ),
        quiet_period=_env_float('MEMORY_WRAPPER_QUIET_PERIOD', 1.5),
        log_dir=log_root / 'MemoryWrapper' / 'logs',
        log_level=os.environ.get('MEMORY_WRAPPER_LOG_LEVEL', 'INFO').upper(),
        log_max_bytes=5 * 1024 * 1024,
        log_backup_count=5,
        output_base=Path.home() / 'Desktop' / 'Memory Docs',
    )

import sys
from pathlib import Path


def get_base_path() -> Path:
    """Resuelve la ruta base tanto en desarrollo como compilado."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent.parent
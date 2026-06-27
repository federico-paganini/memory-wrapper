import sys
from pathlib import Path


def get_base_path() -> Path:
    """Base dir where legacy/, dosbox/ and assets/ live (dev and frozen builds)."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    # src/core/utils.py -> repo root
    return Path(__file__).resolve().parents[2]
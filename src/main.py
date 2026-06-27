"""Entry point.

Dev:    python -m src.main   (or: python src/main.py)
Frozen: bundled by PyInstaller (see MemoryWrapper.spec)
"""
import sys
from pathlib import Path

# Make the `src` package importable whether launched as a module, as a script,
# or frozen by PyInstaller — a relative import in __main__ would fail when frozen.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import create_app  # noqa: E402

if __name__ == '__main__':
    sys.exit(create_app().run())

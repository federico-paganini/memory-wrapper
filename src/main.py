"""Entry point. Run: python src/main.py  (bundled by PyInstaller for the build)."""
import sys

from factory import create_app

if __name__ == '__main__':
    sys.exit(create_app().run())

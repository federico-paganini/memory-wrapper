# Memory Wrapper

Windows desktop wrapper around a legacy DOS accounting program (**Memory Contab**,
`contab.exe`). It runs the DOS program inside DOSBox-X, captures its printer output,
and turns each printed report into a modern PDF the user can preview and archive — all
without the user ever touching DOSBox or a real printer.

> **Platform:** Windows only. The app relies on Win32 APIs (`ctypes.windll`,
> `os.startfile`) and Windows system fonts.

---

## How it works

```
┌────────────┐   prints    ┌─────────────┐   .PRN file   ┌──────────────┐
│ contab.exe │ ──────────► │  DOSBox-X   │ ────────────► │  PRNWatcher  │
│  (DOS)     │  (LPT1)     │ (emulator)  │  (on disk)    │  (watchdog)  │
└────────────┘             └─────────────┘               └──────┬───────┘
                                                                │ stable file
                                                                ▼
                              ┌──────────────┐   Line[]   ┌───────────┐
                              │ pdf_generator│ ◄───────── │ prn_parser│
                              │   (fpdf2)    │            │  (ESC/P)  │
                              └──────┬───────┘            └───────────┘
                                     │ temp .pdf
                                     ▼
                              ┌──────────────┐  "Save"   ~/Desktop/Memory Docs/
                              │ PreviewWindow│ ────────► <year>/<month>/Reporte dd-mm-yyyy.pdf
                              │   (PyQt6)    │
                              └──────────────┘
```

1. **Launch** — `main.py` starts DOSBox-X with `legacy/dosbox-x.conf`, which mounts the
   program directory and auto-runs `contab.exe`.
2. **Capture** — when the operator prints a report inside the DOS program, DOSBox writes
   a `.PRN` file (raw ESC/P printer stream) into `legacy/program/`.
3. **Detect** — `PRNWatcher` (watchdog) sees the new/changed `.PRN`, waits until it is
   fully written, and signals the UI thread.
4. **Parse** — `report/parser.py` decodes the ESC/P control codes (bold, double-width,
   condensed) into a list of `Line` objects made of styled `Segment`s.
5. **Render** — `report/generator.py` lays the lines out into a landscape PDF using the
   Consolas monospaced font.
6. **Preview & save** — `PreviewWindow` renders the PDF (PyMuPDF) and lets the operator
   save it to `Desktop/Memory Docs/<year>/<month>/`.

When DOSBox-X is closed, the wrapper shuts down with it.

---

## Project layout

```
src/
  __init__.py         → create_app(): composition root (builds settings, logging, wiring)
  main.py             → entry point (python -m src.main)
  settings.py         → centralized config (paths, fonts/sizes, quiet_period, logging)
  logger.py           → logging setup (rotating file + console)
  core/
    signals.py        → Qt signal bridge (watcher thread → UI thread)
    utils.py          → base-path resolution (dev vs PyInstaller-frozen)
  dosbox/
    launcher.py       → launches DOSBox-X and monitors its lifecycle
    watcher.py        → watchdog observer; debounced detection of a finished .PRN
  report/
    parser.py         → ESC/P byte stream → Line[] / Segment[] (style-aware)
    generator.py      → Line[] → landscape PDF (fpdf2)
  ui/
    controller.py     → one preview window per report; off-thread PDF worker
    preview_window.py → PDF preview with loading state, save-to-archive
    styles.py         → Qt stylesheet snippets

tests/                → pytest suite, mirrors the src/ layout

legacy/
  dosbox-x.conf       → DOSBox-X configuration (autoexec mounts + runs contab.exe)
  program/            → DOS program + real client data — NOT in this repo (gitignored)

installer/setup.iss   → Inno Setup script
MemoryWrapper.spec    → PyInstaller build spec
assets/               → application icon
```

---

## Requirements

- **Windows** 10/11
- **Python** 3.12 (`>=3.12,<3.13`)
- **Poetry** for dependency management
- **DOSBox-X** installed (the installer expects it under `C:\DOSBox-X`)
- **Consolas** font (`consola.ttf`, `consolab.ttf`) — ships with Windows

Python dependencies (see `pyproject.toml`): `watchdog`, `pyqt6`, `fpdf2`, `pymupdf`,
`pillow`; dev: `pyinstaller`, `pytest`.

---

## Development

```bash
poetry install
poetry run python -m src.main   # full run; needs DOSBox-X + the DOS program (see note)
poetry run pytest               # run the test suite
```

> **Note:** a full end-to-end run needs DOSBox-X reachable at `dosbox/dosbox-x.exe`
> (relative to the repo root) and the DOS program under `legacy/program/` — **neither is
> included in this repository**. The parser, PDF generator, settings and watcher are
> covered by the test suite and run without DOSBox.

---

## Build & installer

**1. Build the executable** (PyInstaller):

```bash
poetry run pyinstaller MemoryWrapper.spec
```

Produces `dist/MemoryWrapper.exe`.

**2. Build the installer** (Inno Setup, on Windows):

Compile `installer/setup.iss`. It bundles `MemoryWrapper.exe`, the `assets`, the DOS
program under `legacy/program`, the DOSBox-X configuration, and a copy of DOSBox-X taken
from `C:\DOSBox-X`. Output: `installer/Output/MemoryWrapper_Installer.exe`, installing to
`C:\MemoryWrapper`.

---

## Output

Saved reports land in:

```
%USERPROFILE%\Desktop\Memory Docs\<year>\<month-in-spanish>\Reporte <dd-mm-yyyy>.pdf
```

---

## Known limitations

- Windows-only by design.
- Font paths and the DOSBox-X source path are currently hardcoded.

---

## License

MIT — see [LICENSE](LICENSE).

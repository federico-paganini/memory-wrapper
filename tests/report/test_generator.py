"""Tests for PDF generation. Requires fpdf2 and a system TrueType font."""
from pathlib import Path

import pytest

from src.settings import FontConfig
from src.report.parser import Line, Segment
from src.report.generator import generate_pdf, _get_font_size, _get_line_height


def _find_ttf() -> Path | None:
    for root in ('/usr/share/fonts', '/usr/local/share/fonts'):
        base = Path(root)
        if base.exists():
            for ttf in base.rglob('*.ttf'):
                return ttf
    return None


_TTF = _find_ttf()
requires_font = pytest.mark.skipif(_TTF is None, reason="no system .ttf font available")


@pytest.fixture
def fonts() -> FontConfig:
    return FontConfig(
        regular=_TTF, bold=_TTF,
        size_normal=12, size_condensed=10, size_wide=18,
    )


# --- pure helpers (no font needed) ---------------------------------------------

def test_get_font_size_by_state(fonts=None):
    fc = FontConfig(regular=Path('x'), bold=Path('x'),
                    size_normal=12, size_condensed=10, size_wide=18)
    assert _get_font_size(Segment(text='a'), fc) == 12
    assert _get_font_size(Segment(text='a', condensed=True), fc) == 10
    assert _get_font_size(Segment(text='a', wide=True), fc) == 18
    # condensed takes precedence over wide
    assert _get_font_size(Segment(text='a', wide=True, condensed=True), fc) == 10


def test_line_height_empty_line():
    fc = FontConfig(regular=Path('x'), bold=Path('x'),
                    size_normal=12, size_condensed=10, size_wide=18)
    assert _get_line_height(Line(segments=[]), fc) == 4


# --- full PDF generation (needs a font) ----------------------------------------

@requires_font
def test_generates_valid_pdf(tmp_path, fonts):
    lines = [
        Line(segments=[Segment(text='Title', bold=True)]),
        Line(segments=[]),
        Line(segments=[Segment(text='body', condensed=True)]),
    ]
    out = tmp_path / 'out.pdf'
    generate_pdf(lines, str(out), fonts)

    assert out.exists()
    data = out.read_bytes()
    assert data.startswith(b'%PDF')
    assert len(data) > 500


@requires_font
def test_generates_pdf_for_empty_document(tmp_path, fonts):
    out = tmp_path / 'empty.pdf'
    generate_pdf([], str(out), fonts)
    assert out.exists()
    assert out.read_bytes().startswith(b'%PDF')

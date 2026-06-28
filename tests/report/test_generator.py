"""Tests for PDF generation. Requires fpdf2 and a system TrueType font."""
from pathlib import Path

import pytest

from settings import FontConfig
from report.parser import Line, Segment
from report.generator import generate_pdf, _get_font_size


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
        size_normal=10, size_condensed=8, size_wide=11,
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


import re  # noqa: E402


def _page_count(data: bytes) -> int:
    return len(re.findall(rb'/Type\s*/Page[^s]', data))


def _media_box(data: bytes) -> tuple[float, float]:
    m = re.search(rb'/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]', data)
    assert m, "no MediaBox in PDF"
    return float(m.group(1)), float(m.group(2))


@requires_font
def test_pages_are_a4_portrait(tmp_path, fonts):
    out = tmp_path / 'p.pdf'
    generate_pdf([Line(segments=[Segment(text='X')])], str(out), fonts)
    w, h = _media_box(out.read_bytes())
    assert w < h  # portrait: width < height


@requires_font
def test_leading_form_feed_does_not_create_blank_page(tmp_path, fonts):
    lines = [Line(page_break=True), Line(segments=[Segment(text='X')])]
    out = tmp_path / 'lead.pdf'
    generate_pdf(lines, str(out), fonts)
    assert _page_count(out.read_bytes()) == 1


@requires_font
def test_trailing_form_feed_does_not_create_blank_page(tmp_path, fonts):
    lines = [Line(segments=[Segment(text='X')]), Line(page_break=True)]
    out = tmp_path / 'trail.pdf'
    generate_pdf(lines, str(out), fonts)
    assert _page_count(out.read_bytes()) == 1


@requires_font
def test_mid_form_feed_creates_new_page(tmp_path, fonts):
    lines = [
        Line(segments=[Segment(text='A')]),
        Line(page_break=True),
        Line(segments=[Segment(text='B')]),
    ]
    out = tmp_path / 'mid.pdf'
    generate_pdf(lines, str(out), fonts)
    assert _page_count(out.read_bytes()) == 2


@requires_font
def test_full_prn_page_fits_one_a4_page(tmp_path, fonts):
    # A typical PRN page (~64 lines) must fit on a single A4 page so the report's
    # own pagination stays aligned with the PDF's.
    lines = [Line(segments=[Segment(text=f'row {i}')]) for i in range(64)]
    out = tmp_path / 'page.pdf'
    generate_pdf(lines, str(out), fonts)
    assert _page_count(out.read_bytes()) == 1

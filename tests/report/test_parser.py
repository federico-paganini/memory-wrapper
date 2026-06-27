"""Exhaustive tests for the ESC/P -> Line/Segment parser."""
from pathlib import Path

import pytest

from src.report.parser import parse_prn, Line, Segment


def parse_bytes(tmp_path: Path, data: bytes) -> list[Line]:
    prn = tmp_path / 'CONT.PRN'
    prn.write_bytes(data)
    return parse_prn(str(prn))


# --- plain text & line handling -------------------------------------------------

def test_plain_single_line(tmp_path):
    lines = parse_bytes(tmp_path, b'HELLO\n')
    assert len(lines) == 1
    assert lines[0].plain_text() == 'HELLO'
    seg = lines[0].segments[0]
    assert (seg.bold, seg.wide, seg.condensed) == (False, False, False)


def test_no_trailing_newline_still_flushes(tmp_path):
    lines = parse_bytes(tmp_path, b'ABC')
    assert len(lines) == 1
    assert lines[0].plain_text() == 'ABC'


def test_cr_is_ignored(tmp_path):
    lines = parse_bytes(tmp_path, b'A\rB\n')
    assert len(lines) == 1
    assert lines[0].plain_text() == 'AB'


def test_form_feed_is_ignored(tmp_path):
    lines = parse_bytes(tmp_path, b'A\x0cB\n')
    assert len(lines) == 1
    assert lines[0].plain_text() == 'AB'


def test_multiple_lines(tmp_path):
    lines = parse_bytes(tmp_path, b'one\ntwo\nthree\n')
    assert [l.plain_text() for l in lines] == ['one', 'two', 'three']


# --- bold (ESC E / ESC F) -------------------------------------------------------

def test_bold_on_off_splits_segments(tmp_path):
    lines = parse_bytes(tmp_path, b'a\x1bEb\x1bFc\n')
    segs = lines[0].segments
    assert [(s.text, s.bold) for s in segs] == [('a', False), ('b', True), ('c', False)]


def test_bold_persists_across_text(tmp_path):
    lines = parse_bytes(tmp_path, b'\x1bEBOLD\n')
    assert lines[0].segments[0].bold is True
    assert lines[0].plain_text() == 'BOLD'


# --- double-width (ESC W n) -----------------------------------------------------

def test_wide_on_and_off(tmp_path):
    # ESC W 0x01 -> wide on ; ESC W 0x00 -> wide off
    lines = parse_bytes(tmp_path, b'\x1bW\x01A\x1bW\x00B\n')
    segs = lines[0].segments
    assert [(s.text, s.wide) for s in segs] == [('A', True), ('B', False)]


# --- condensed (SI 0x0F / DC2 0x12) --------------------------------------------

def test_condensed_on_off(tmp_path):
    lines = parse_bytes(tmp_path, b'\x0fA\x12B\n')
    segs = lines[0].segments
    assert [(s.text, s.condensed) for s in segs] == [('A', True), ('B', False)]


# --- reset (ESC @) --------------------------------------------------------------

def test_reset_clears_all_styles(tmp_path):
    lines = parse_bytes(tmp_path, b'\x1bE\x1bW\x01X\x1b@Y\n')
    segs = lines[0].segments
    x = next(s for s in segs if s.text == 'X')
    y = next(s for s in segs if s.text == 'Y')
    assert (x.bold, x.wide) == (True, True)
    assert (y.bold, y.wide, y.condensed) == (False, False, False)


# --- escape sequences that are skipped -----------------------------------------

def test_esc_c_consumes_one_param_byte(tmp_path):
    # ESC C <n> sets page length; parser must skip all three bytes, not print <n>.
    lines = parse_bytes(tmp_path, b'A\x1bC\x18B\n')
    assert lines[0].plain_text() == 'AB'


def test_unknown_escape_sequence_skips_two_bytes(tmp_path):
    lines = parse_bytes(tmp_path, b'A\x1bZB\n')
    assert lines[0].plain_text() == 'AB'


# --- CP437 decoding -------------------------------------------------------------

def test_cp437_decoding(tmp_path):
    # 0x82 -> 'é', 0xA4 -> 'ñ' in CP437
    lines = parse_bytes(tmp_path, b'\x82\xa4\n')
    assert lines[0].plain_text() == 'éñ'


# --- empty-line collapsing ------------------------------------------------------

def test_consecutive_empty_lines_collapse_to_one(tmp_path):
    lines = parse_bytes(tmp_path, b'A\n\n\n\nB\n')
    texts = [l.plain_text() for l in lines]
    assert texts == ['A', '', 'B']
    assert lines[1].is_empty()


def test_whitespace_only_line_is_empty(tmp_path):
    lines = parse_bytes(tmp_path, b'   \n')
    assert lines[0].is_empty()


# --- Line / Segment helpers -----------------------------------------------------

def test_line_is_empty_and_plain_text():
    line = Line(segments=[Segment(text='  '), Segment(text='x')])
    assert not line.is_empty()
    assert line.plain_text() == '  x'

    blank = Line(segments=[Segment(text='   ')])
    assert blank.is_empty()


def test_empty_input_produces_no_lines(tmp_path):
    assert parse_bytes(tmp_path, b'') == []

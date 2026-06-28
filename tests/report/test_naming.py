"""Tests for deriving an export filename from a report header."""
from report.parser import Line, Segment
from report.naming import report_filename


def _lines(*texts: str) -> list[Line]:
    return [Line(segments=[Segment(text=t)]) for t in texts]


def test_estado_de_resultados_period_range():
    lines = _lines(
        "ESTADO DE RESULTADOS                   CAJA GENERAL",
        "   en el periodo 01/9/25 a 31/09/25",
        "Hoja Nro 1 - 23/09/12 12:48:00",
    )
    assert report_filename(lines) == "Estado de Resultados 01-09-2025 a 31-09-2025"


def test_balance_single_date():
    lines = _lines(
        "BALANCE                                CAJA GENERAL",
        "   al 30/09/25",
        "Hoja Nro 1 - 23/09/12 11:42:00",
    )
    assert report_filename(lines) == "Balance al 30-09-2025"


def test_mayor_analitico_single_digit_year():
    lines = _lines(
        "MAYOR ANALITICO                        CAJA GENERAL",
        "   en el periodo 01/05/6 a 31/05/6",
    )
    assert report_filename(lines) == "Mayor Analitico 01-05-2006 a 31-05-2006"


def test_pads_day_and_month():
    lines = _lines("BALANCE   X", "al 1/01/24")
    assert report_filename(lines) == "Balance al 01-01-2024"


def test_titlecase_keeps_connectors_lowercase():
    lines = _lines("ESTADO DE RESULTADOS   X", "al 01/01/25")
    assert report_filename(lines) == "Estado de Resultados al 01-01-2025"


def test_two_digit_year_pivot_to_1900s():
    lines = _lines("MAYOR   X", "en el periodo 01/01/92 a 31/12/92")
    assert report_filename(lines) == "Mayor 01-01-1992 a 31-12-1992"


def test_unparseable_period_returns_none():
    assert report_filename(_lines("ALGO RARO   X", "sin fecha aca")) is None


def test_too_few_lines_returns_none():
    assert report_filename(_lines("BALANCE   X")) is None
    assert report_filename([]) is None


def test_illegal_chars_are_sanitized():
    name = report_filename(_lines('BAL/AN:CE*?   X', 'al 01/01/25'))
    assert name is not None
    assert not any(c in name for c in '\\/:*?"<>|')


def test_two_digit_year_pivot_boundary():
    assert report_filename(_lines('X   Y', 'al 01/01/69')) == 'X al 01-01-2069'
    assert report_filename(_lines('X   Y', 'al 01/01/70')) == 'X al 01-01-1970'

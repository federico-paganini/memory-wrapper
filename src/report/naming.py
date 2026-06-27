import re

from .parser import Line

# Spanish connector words kept lowercase in title-cased report names.
_SMALL_WORDS = {'de', 'del', 'la', 'las', 'el', 'los', 'y', 'e', 'en', 'a', 'por', 'con', 'o', 'u'}
_ILLEGAL = re.compile(r'[\\/:*?"<>|]')


def report_filename(lines: list[Line]) -> str | None:
    """Derive a filename stem from a report's header.

    The header's first non-empty line is "<TYPE>   <COMPANY>" and the second is
    the period — either "en el periodo <from> a <to>" or "al <date>". Returns a
    stem such as ``Estado de Resultados 01-09-2025 a 31-09-2025`` or
    ``Balance al 30-09-2025``; returns None if the header does not match (the
    caller then falls back to a date-based name).
    """
    texts = [t for t in (line.plain_text().rstrip() for line in lines) if t.strip()]
    if len(texts) < 2:
        return None

    report_type = re.split(r'\s{2,}', texts[0].strip())[0].strip()
    period = _parse_period(texts[1])
    if not report_type or not period:
        return None

    return _sanitize(f"{_titlecase(report_type)} {period}")


def _parse_period(text: str) -> str | None:
    t = text.strip()
    m = re.search(
        r'per[ií]odo\s+(\d{1,2}/\d{1,2}/\d{1,4})\s+a\s+(\d{1,2}/\d{1,2}/\d{1,4})', t, re.I
    )
    if m:
        return f"{_norm_date(m.group(1))} a {_norm_date(m.group(2))}"
    m = re.search(r'\bal\s+(\d{1,2}/\d{1,2}/\d{1,4})', t, re.I)
    if m:
        return f"al {_norm_date(m.group(1))}"
    return None


def _norm_date(s: str) -> str:
    """'01/9/25' -> '01-09-2025' (pads parts, expands 1-2 digit years)."""
    day, month, year = (int(x) for x in s.split('/'))
    if year < 100:
        year += 2000 if year < 70 else 1900
    return f"{day:02d}-{month:02d}-{year:04d}"


def _titlecase(s: str) -> str:
    words = s.lower().split()
    return ' '.join(
        word if i and word in _SMALL_WORDS else word.capitalize()
        for i, word in enumerate(words)
    )


def _sanitize(name: str) -> str:
    return _ILLEGAL.sub('', name).strip()

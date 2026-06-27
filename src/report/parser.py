from dataclasses import dataclass, field


@dataclass
class Segment:
    text: str
    bold: bool = False
    wide: bool = False
    condensed: bool = False


@dataclass
class Line:
    segments: list[Segment] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not any(s.text.strip() for s in self.segments)

    def plain_text(self) -> str:
        return ''.join(s.text for s in self.segments)


def _collapse_empty_lines(lines: list[Line]) -> list[Line]:
    result = []
    prev_empty = False
    for line in lines:
        is_empty = line.is_empty()
        if is_empty:
            if not prev_empty:
                result.append(line)
            prev_empty = True
        else:
            result.append(line)
            prev_empty = False
    return result


def parse_prn(filepath: str) -> list[Line]:
    with open(filepath, 'rb') as f:
        content = f.read()

    lines = []
    bold = False
    wide = False
    condensed = False
    current_text = bytearray()
    current_segments: list[Segment] = []

    def flush_segment():
        if current_text:
            current_segments.append(Segment(
                text=current_text.decode('cp437'),
                bold=bold,
                wide=wide,
                condensed=condensed
            ))
            current_text.clear()

    def flush_line():
        flush_segment()
        lines.append(Line(segments=list(current_segments)))
        current_segments.clear()

    i = 0
    while i < len(content):
        b = content[i]

        if b == 0x1B:
            next_b = content[i + 1] if i + 1 < len(content) else None

            if next_b == ord('@'):
                flush_segment()
                bold = wide = condensed = False
                i += 2

            elif next_b == ord('E'):
                flush_segment()
                bold = True
                i += 2

            elif next_b == ord('F'):
                flush_segment()
                bold = False
                i += 2

            elif next_b == ord('W'):
                flush_segment()
                wide = content[i + 2] == 0x01
                i += 3

            elif next_b == ord('C'):
                i += 3

            else:
                i += 2

        elif b == 0x0F:
            flush_segment()
            condensed = True
            i += 1

        elif b == 0x12:
            flush_segment()
            condensed = False
            i += 1

        elif b == 0x0C:                  # Form feed — ignorar
            i += 1

        elif b == 0x0D:                  # CR — ignorar
            i += 1

        elif b == 0x0A:                  # LF — fin de línea
            flush_line()
            i += 1

        else:
            current_text.append(b)
            i += 1

    if current_text or current_segments:
        flush_line()

    return _collapse_empty_lines(lines)
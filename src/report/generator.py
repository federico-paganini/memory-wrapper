from fpdf import FPDF

from report.parser import Line
from settings import FontConfig

# Report pages render on A4 landscape (matches the wide dot-matrix layout) and
# paginate automatically when a page fills up; form-feeds force a new page.
PAGE_ORIENTATION = 'L'
PAGE_FORMAT = 'A4'
PAGE_MARGIN = 10


def _get_font_size(segment, fonts: FontConfig) -> int:
    if segment.condensed:
        return fonts.size_condensed
    if segment.wide:
        return fonts.size_wide
    return fonts.size_normal


def _get_line_height(line: Line, fonts: FontConfig) -> int:
    sizes = [_get_font_size(s, fonts) for s in line.segments if s.text]
    return max(sizes) // 2 if sizes else 4


def generate_pdf(lines: list[Line], output_path: str, fonts: FontConfig) -> None:
    pdf = FPDF(orientation=PAGE_ORIENTATION, unit='mm', format=PAGE_FORMAT)
    pdf.set_margins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
    pdf.set_auto_page_break(auto=True, margin=PAGE_MARGIN)

    pdf.add_font('Consolas', style='', fname=str(fonts.regular))
    pdf.add_font('Consolas', style='B', fname=str(fonts.bold))

    pdf.add_page()
    pdf.set_font('Consolas', style='', size=fonts.size_normal)

    for line in lines:
        if line.page_break:
            pdf.add_page()
            continue

        if line.is_empty():
            pdf.ln(4)
            continue

        line_height = _get_line_height(line, fonts)
        last_idx = len(line.segments) - 1

        for idx, segment in enumerate(line.segments):
            if not segment.text:
                continue

            style = 'B' if segment.bold else ''
            size = _get_font_size(segment, fonts)

            pdf.set_font('Consolas', style=style, size=size)
            pdf.cell(
                w=0 if idx == last_idx else pdf.get_string_width(segment.text),
                h=line_height,
                text=segment.text,
                new_x='RIGHT',
                new_y='TOP',
            )

        pdf.ln(line_height)

    pdf.output(output_path)

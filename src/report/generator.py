from fpdf import FPDF

from .parser import Line
from ..settings import FontConfig


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
    # Total content height -> single continuous page.
    total_height = sum(
        4 if line.is_empty() else _get_line_height(line, fonts)
        for line in lines
    ) + 20  # extra margin

    pdf = FPDF(orientation='L', unit='mm', format=(total_height, 297))
    pdf.set_margins(10, 10, 10)
    pdf.set_auto_page_break(auto=False)

    pdf.add_font('Consolas', style='', fname=str(fonts.regular))
    pdf.add_font('Consolas', style='B', fname=str(fonts.bold))

    pdf.add_page()
    pdf.set_font('Consolas', style='', size=fonts.size_normal)

    for line in lines:
        if line.is_empty():
            pdf.ln(4)
            continue

        line_height = _get_line_height(line, fonts)

        for segment in line.segments:
            if not segment.text:
                continue

            style = 'B' if segment.bold else ''
            size = _get_font_size(segment, fonts)

            pdf.set_font('Consolas', style=style, size=size)
            pdf.cell(
                w=0 if segment == line.segments[-1] else pdf.get_string_width(segment.text),
                h=line_height,
                text=segment.text,
                new_x='RIGHT',
                new_y='TOP',
            )

        pdf.ln(line_height)

    pdf.output(output_path)

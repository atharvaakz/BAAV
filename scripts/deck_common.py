"""Build the 10-minute presentation (.pptx) from model numbers and charts, with speaker notes."""
import json, pathlib
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

ROOT = pathlib.Path(__file__).resolve().parents[1]
N = json.loads((ROOT / "data/processed/numbers.json").read_text())
CH = ROOT / "reports/charts/deck"
OUT = ROOT / "reports/ProjectBaav_Group27_Presentation.pptx"
D, G, P, I = N["DLF"], N["GPL"], N["PML"], N["Inputs"]
BG, INK, MUTE, ACC, OCH, RUST, RULE = "F7F5F0", "1F2A30", "6B7780", "2F5D62", "C08A3E", "8C4A3C", "D8D4CA"
HEAD, BODY, MONO = "Cambria", "Calibri", "Consolas"


def rgb(h):
    return RGBColor.from_string(h)


def pc(x, d=1):
    return f"{x*100:.{d}f}%"


def rs(x):
    return f"₹{x:,.0f}"


prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]


def tb(slide, x, y, w, h, text, size=14, color=INK, font=BODY, bold=False, align=PP_ALIGN.LEFT, italic=False, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.02); tf.margin_top = tf.margin_bottom = Inches(0.02)
    lines = text if isinstance(text, list) else [text]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        segs = ln if isinstance(ln, list) else [(ln, bold, color)]
        for seg in segs:
            t, b, c = seg
            r = p.add_run(); r.text = t; r.font.size = Pt(size); r.font.name = font; r.font.bold = b
            r.font.color.rgb = rgb(c); r.font.italic = italic
        p.space_after = Pt(size * 0.35)
    return box


def rule(slide, x, y, w, color=RULE, h=0.012):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = rgb(color); s.line.fill.background(); s.shadow.inherit = False


def base(module, title, num, sheet=None):
    s = prs.slides.add_slide(BLANK)
    bg = s.background.fill; bg.solid(); bg.fore_color.rgb = rgb(BG)
    tb(s, 0.6, 0.38, 9, 0.3, module.upper(), 10, MUTE, BODY, True)
    tb(s, 0.6, 0.66, 12.1, 1.0, title, 26, INK, HEAD, True)
    rule(s, 0.6, 1.55, 12.13)
    tb(s, 12.2, 7.02, 0.6, 0.3, str(num), 10, MUTE, BODY, align=PP_ALIGN.RIGHT)
    if sheet:
        tb(s, 0.6, 7.02, 9, 0.3, f"Workbook › {sheet}", 9, MUTE, MONO)
    return s


def method(slide, text, y=6.25, h=0.62):
    """'How we did it' strip — shows the working, not just the result."""
    r = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(y), Inches(12.13), Inches(h))
    r.fill.solid(); r.fill.fore_color.rgb = rgb("EEEBE3"); r.line.fill.background(); r.shadow.inherit = False
    tb(slide, 0.75, y + 0.06, 1.3, h - 0.1, "HOW", 9, ACC, BODY, True)
    tb(slide, 1.45, y + 0.05, 11.2, h - 0.08, text, 10.5, INK, MONO)


def pic(slide, name, x, y, w=None, h=None):
    kw = {}
    if w: kw["width"] = Inches(w)
    if h: kw["height"] = Inches(h)
    return slide.shapes.add_picture(str(CH / f"{name}.png"), Inches(x), Inches(y), **kw)


def table(slide, x, y, w, rows, colw=None, size=11, h_row=0.34, first_bold=True):
    nr, nc = len(rows), len(rows[0])
    t = slide.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(h_row * nr)).table
    for j in range(nc):
        if colw:
            t.columns[j].width = Inches(colw[j])
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = t.cell(i, j); c.text = ""
            c.fill.solid(); c.fill.fore_color.rgb = rgb(ACC if i == 0 else ("FFFFFF" if i % 2 else "F1EFE9"))
            p = c.text_frame.paragraphs[0]; r = p.add_run(); r.text = str(v)
            r.font.size = Pt(size); r.font.name = BODY; r.font.color.rgb = rgb("FFFFFF" if i == 0 else INK)
            r.font.bold = (i == 0) or (j == 0 and first_bold)
            p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.RIGHT
            c.margin_left = c.margin_right = Inches(0.06); c.margin_top = c.margin_bottom = Inches(0.02)
    return t


def below(shape, gap=0.1):
    return (shape.top + shape.height) / 914400 + gap


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text



"""Generate the project report (.docx) from model numbers. Re-run after any model change."""
import json, pathlib, re
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = pathlib.Path(__file__).resolve().parents[1]
N = json.loads((ROOT / "data/processed/numbers.json").read_text())
CH = ROOT / "reports/charts"
OUT = ROOT / "reports/ProjectBaav_Group27_Report.docx"
D, G, P = N["DLF"], N["GPL"], N["PML"]
I = N["Inputs"]


def pc(x, d=1):
    return f"{x*100:.{d}f}%"


def cr(x):
    return f"−₹{abs(x):,.0f} cr" if x < 0 else f"₹{x:,.0f} cr"


def rs(x):
    return f"₹{x:,.0f}"


def xx(x, d=1):
    return f"{x:.{d}f}x"


doc = Document()
sec = doc.sections[0]
sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
sec.left_margin = sec.right_margin = Cm(1.9)
sec.top_margin, sec.bottom_margin = Cm(1.7), Cm(1.6)
st = doc.styles["Normal"]
st.font.name = "Georgia"; st.font.size = Pt(9.5)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Georgia")
st.paragraph_format.space_after = Pt(5); st.paragraph_format.line_spacing = 1.12
INK = RGBColor(0x11, 0x14, 0x18); ACC = RGBColor(0xD9, 0x48, 0x1C); MUTE = RGBColor(0x6E, 0x73, 0x7A)
for lvl, size in [(1, 15), (2, 11), (3, 10)]:
    h = doc.styles[f"Heading {lvl}"]
    h.font.name = "Arial"; h.font.size = Pt(size); h.font.color.rgb = INK; h.font.bold = lvl > 1
    h.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    h.paragraph_format.space_before = Pt(12 if lvl == 1 else 8); h.paragraph_format.space_after = Pt(4)

# page numbers in footer
fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
run = fp.add_run(); f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin")
it = OxmlElement("w:instrText"); it.text = "PAGE"; f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "end")
run._r.extend([f1, it, f2]); run.font.size = Pt(8); run.font.color.rgb = MUTE
hp = sec.header.paragraphs[0]; hr = hp.add_run("Paying for the Future  /  Indian Real Estate  /  Group 27")
hr.font.size = Pt(8); hr.font.color.rgb = MUTE; hr.font.name = "Courier New"


def para(text, bold_lead=None, italic=False, size=None, after=None):
    p = doc.add_paragraph()
    if bold_lead:
        r = p.add_run(bold_lead + " "); r.bold = True
    r = p.add_run(text); r.italic = italic
    if size:
        r.font.size = Pt(size)
    if after is not None:
        p.paragraph_format.space_after = Pt(after)
    return p


def bullets(items):
    for t in items:
        p = doc.add_paragraph(style="List Bullet")
        if isinstance(t, tuple):
            r = p.add_run(t[0] + " "); r.bold = True; p.add_run(t[1])
        else:
            p.add_run(t)
        p.paragraph_format.space_after = Pt(2)


def module_tag(text):
    p = doc.add_paragraph(); r = p.add_run(text); r.font.size = Pt(7.5); r.font.color.rgb = MUTE; r.font.name = "Courier New"
    p.paragraph_format.space_after = Pt(0)


def shade(cell, hexcol):
    tcPr = cell._tc.get_or_add_tcPr(); s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), hexcol); tcPr.append(s)


def table(headers, rows_, widths=None, note=None, size=8.5):
    t = doc.add_table(rows=1, cols=len(headers)); t.style = "Light List"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]; c.text = ""; r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(size)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF); r.font.name = "Arial"; shade(c, "111418")
    for row in rows_:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""; r = cells[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(size); r.font.name = "Arial"
            sv = str(v)
            if i > 0 and len(sv) < 22 and re.match(r"^[\s₹+\-−(]*[\d.,]", sv):
                cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if widths:
        t.autofit = False
        for i, w in enumerate(widths):
            t.columns[i].width = Cm(w)
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    if note:
        p = doc.add_paragraph(); r = p.add_run(note); r.italic = True; r.font.size = Pt(8); r.font.color.rgb = MUTE
    else:
        doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def fig(name, caption, width=16.5):
    doc.add_picture(str(CH / f"{name}.png"), width=Cm(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph(); m = re.match(r"^(Figure \\d+)\\s+—\\s+(.*)$", caption)
    if m:
        r0 = p.add_run(m.group(1) + ".  "); r0.font.size = Pt(8); r0.font.color.rgb = ACC; r0.font.name = "Courier New"; caption = m.group(2)
    r = p.add_run(caption); r.font.size = Pt(8); r.font.color.rgb = MUTE; r.font.name = "Arial"




def bridge(text):
    """Short 'what we did and why' note at the start of each section."""
    p = doc.add_paragraph(); p.paragraph_format.left_indent = Cm(0.4); p.paragraph_format.space_after = Pt(6)
    r0 = p.add_run("Approach — "); r0.font.size = Pt(8); r0.font.color.rgb = ACC; r0.font.name = "Courier New"
    r_ = p.add_run(text); r_.font.size = Pt(9); r_.font.color.rgb = INK; r_.font.name = "Arial"


def callout(title, lines, fill="F4F5F6"):
    t = doc.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.rows[0].cells[0]; shade(c, fill); c.width = Cm(16.5)
    p = c.paragraphs[0]; r = p.add_run(title); r.bold = True; r.font.color.rgb = ACC; r.font.size = Pt(10)
    for ln in lines:
        p = c.add_paragraph(); r = p.add_run(ln); r.font.size = Pt(9.5); p.paragraph_format.space_after = Pt(2)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def cover(title, subtitle, kicker, headers, rows, authors, submitted, note):
    p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(90)
    r = p.add_run("ECON F355 / Business Analysis & Valuation  ·  Sector report / 31 October 2026"); r.font.size = Pt(8.5); r.font.color.rgb = INK; r.font.name = "Courier New"
    p = doc.add_paragraph(); r = p.add_run("■"); r.font.size = Pt(28); r.font.color.rgb = ACC
    p = doc.add_paragraph(); r = p.add_run(title); r.font.name = "Arial"; r.font.size = Pt(40); r.font.color.rgb = INK
    p = doc.add_paragraph(); r = p.add_run(subtitle); r.font.size = Pt(14); r.font.color.rgb = INK; r.font.name = "Georgia"
    doc.add_paragraph()
    table(headers, rows, [5.0, 3.8, 3.9, 3.8], size=9)
    para(f"{submitted} · {authors}", size=10)
    para(note, size=8.5, italic=True)
    doc.add_page_break()


def references(refs):
    for ref in refs:
        p = doc.add_paragraph(ref, style="List Number"); p.paragraph_format.space_after = Pt(2)
        for r in p.runs:
            r.font.size = Pt(9)

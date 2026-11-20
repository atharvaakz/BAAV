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
sec.left_margin = sec.right_margin = Cm(2.2)
sec.top_margin, sec.bottom_margin = Cm(2.0), Cm(2.0)
st = doc.styles["Normal"]
st.font.name = "Calibri"; st.font.size = Pt(11)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
st.paragraph_format.space_after = Pt(5); st.paragraph_format.line_spacing = 1.12
INK = RGBColor(0x1F, 0x2A, 0x30); ACC = RGBColor(0x2F, 0x5D, 0x62); MUTE = RGBColor(0x6B, 0x77, 0x80)
for lvl, size in [(1, 15), (2, 12), (3, 10.5)]:
    h = doc.styles[f"Heading {lvl}"]
    h.font.name = "Cambria"; h.font.size = Pt(size); h.font.color.rgb = ACC if lvl < 3 else INK; h.font.bold = True
    h.element.rPr.rFonts.set(qn("w:eastAsia"), "Cambria")
    h.paragraph_format.space_before = Pt(12 if lvl == 1 else 8); h.paragraph_format.space_after = Pt(4)

# page numbers in footer
fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
run = fp.add_run(); f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin")
it = OxmlElement("w:instrText"); it.text = "PAGE"; f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "end")
run._r.extend([f1, it, f2]); run.font.size = Pt(8); run.font.color.rgb = MUTE
hp = sec.header.paragraphs[0]; hr = hp.add_run("ECON F355 · Business Analysis & Valuation · Group 27 · Indian Real Estate")
hr.font.size = Pt(8); hr.font.color.rgb = MUTE


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
    p = doc.add_paragraph(); r = p.add_run(text.upper()); r.font.size = Pt(7.5); r.font.color.rgb = MUTE; r.bold = True
    p.paragraph_format.space_after = Pt(0)


def shade(cell, hexcol):
    tcPr = cell._tc.get_or_add_tcPr(); s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), hexcol); tcPr.append(s)


def table(headers, rows_, widths=None, note=None, size=8.5):
    t = doc.add_table(rows=1, cols=len(headers)); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]; c.text = ""; r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(size)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF); shade(c, "2F5D62")
    for row in rows_:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""; r = cells[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(size)
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
    p = doc.add_paragraph(); r = p.add_run(caption); r.italic = True; r.font.size = Pt(8.5); r.font.color.rgb = MUTE
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER



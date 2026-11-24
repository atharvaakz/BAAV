"""Standalone AI-use acknowledgement for the ECON F355 project (disclosed-assisted mode)."""
import pathlib
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/AI_Use_Acknowledgement.docx"
INK, SIG, MUTE = RGBColor(0x11, 0x14, 0x18), RGBColor(0xD9, 0x48, 0x1C), RGBColor(0x6E, 0x73, 0x7A)
doc = Document()
s = doc.sections[0]; s.left_margin = s.right_margin = Cm(2.2); s.top_margin = s.bottom_margin = Cm(2.0)
st = doc.styles["Normal"]; st.font.name = "Georgia"; st.font.size = Pt(10.5); st.element.rPr.rFonts.set(qn("w:eastAsia"), "Georgia")
st.paragraph_format.space_after = Pt(6); st.paragraph_format.line_spacing = 1.2
for lvl, size in [(1, 14), (2, 11)]:
    h = doc.styles[f"Heading {lvl}"]; h.font.name = "Arial"; h.font.size = Pt(size); h.font.color.rgb = INK; h.font.bold = lvl == 2
    h.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial"); h.paragraph_format.space_before = Pt(12); h.paragraph_format.space_after = Pt(4)


def shade(cell, hexcol):
    tcPr = cell._tc.get_or_add_tcPr(); e = OxmlElement("w:shd"); e.set(qn("w:val"), "clear"); e.set(qn("w:color"), "auto"); e.set(qn("w:fill"), hexcol); tcPr.append(e)


def para(text, size=None, italic=False, color=None, bold_lead=None):
    p = doc.add_paragraph()
    if bold_lead:
        r = p.add_run(bold_lead + " "); r.bold = True
    r = p.add_run(text); r.italic = italic
    if size: r.font.size = Pt(size)
    if color: r.font.color.rgb = color
    return p


def table(headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers)); t.style = "Table Grid"
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]; c.text = ""; r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(9); r.font.name = "Arial"
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF); shade(c, "111418")
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""; r = cells[i].paragraphs[0].add_run(v); r.font.size = Pt(9); r.font.name = "Arial"
            if "[" in v: r.font.color.rgb = SIG
    for row in t.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Cm(w)
    doc.add_paragraph()


p = doc.add_paragraph(); r = p.add_run("ECON F355 / Business Analysis & Valuation  ·  Group 27"); r.font.name = "Courier New"; r.font.size = Pt(8.5)
doc.add_heading("Acknowledgement of AI use", 1)
para("Project: Paying for the Future — valuation of DLF, Godrej Properties and Phoenix Mills. "
     "Group 27: Saatvik Nagpal, Atharvaa Khanzode. Submitted to Prof. Mohit Kumar, BITS Pilani, K K Birla Goa Campus.", size=9.5, color=MUTE)

doc.add_heading("Summary", 2)
para("We used a generative AI assistant, Claude (Anthropic), throughout this project, as the course permits. It was used through Claude Code, "
     "an environment in which the assistant writes and runs code, collects public data, builds files and drafts text on instruction. "
     "Its contribution was substantial: much of the code, the Excel model, the charts and the first drafts of the report, presentation and viva notes were "
     "produced by the assistant. We set the questions and the scope, made the analytical choices listed below, checked the numbers and sources, "
     "and are responsible for everything submitted. We can explain every figure and method in the report.")

doc.add_heading("What the AI assistant did", 2)
table(["Area", "AI assistant's role", "Our role and checks"],
      [["Data collection", "Wrote scripts to download prices, financial statements and macro series (Yahoo Finance, FRED, Damodaran); searched for and extracted company filings, transcripts and industry reports.",
        "[Describe: which sources you chose or verified, e.g. checked FY26 figures against the DLF and Godrej annual reports.]"],
       ["Excel model and code", "Built the formula-driven workbook (62 sheets) and the Python scripts for the DCF replica, Monte Carlo, event studies and charts.",
        "[Describe: which sheets you reviewed or rebuilt by hand; assumptions you changed, e.g. growth paths, terminal growth, peer set.]"],
       ["Analysis and methods", "Proposed methods from the course and textbooks (DuPont, EVA, two cost-of-capital versions, reverse DCF, NAV, event studies) and implemented them.",
        "[Describe: methods you selected or rejected, and why.]"],
       ["Writing", "Drafted the report, presentation text, speaker notes and viva pack; revised wording for clarity on request.",
        "[Describe: sections you rewrote, the argument and conclusions you decided on.]"],
       ["Design", "Researched presentation and report design and produced the layout, charts and diagrams.", "[Describe: design decisions you made or changed.]"],
       ["Review", "Ran an 'equity research professor' style review and added the valuation summary, sensitivity grid and catalysts table.", "[Describe: which suggestions you accepted.]"]],
      [3.0, 7.0, 6.6])

doc.add_heading("Decisions that were ours", 2)
for t in ["Choice of sector and companies (one per business model: DLF, Godrej Properties, Phoenix Mills).",
          "The research question and the twelve hypotheses tested.",
          "The data cutoff of 31 October 2026, with prices taken at the 30 October close.",
          "[Add further decisions: e.g. weights in the valuation summary, rating bands, which cost-of-capital version to treat as the base case.]"]:
    p = doc.add_paragraph(style="List Bullet"); r = p.add_run(t)
    if "[" in t: r.font.color.rgb = SIG

doc.add_heading("Use of the Turnitin AI-writing report", 2)
para("We submitted a draft of the report (the Word version) to Turnitin. Its AI-writing indicator flagged 28% of the text as likely AI-generated "
     "(submission of 21 November 2026). This was expected, since the assistant drafted much of the text, and it is consistent with this disclosure.")
para("We used the report as a prompt to review our own work, not as a score to reduce. We read the highlighted passages to check that each claim is ours to "
     "defend and supported by the model. We did not rewrite flagged passages to change the score, and we did not use paraphrasing or 'humanising' tools. "
     "Turnitin itself states that its indicator can misidentify text and should not be the sole basis for decisions about a student's work.")
para("[Optional: add one or two sentences on what you personally took from the report, e.g. which sections you went back to and checked.]", color=SIG)

doc.add_heading("Verification and process evidence", 2)
for t in ["Every number in the report and presentation is generated from the Excel model; a check script confirms the workbook has no formula errors and that no data after 31 October 2026 is used.",
          "DLF's and Godrej's FY26 figures were tied to their audited annual reports (equity, assets, inventory, profit and operating cash flow match exactly).",
          "The full history of the work, with dated commits, is in the project repository (github.com/atharvaakz/BAAV) and is available on request.",
          "We are happy to walk through any part of the model or the report in the viva."]:
    doc.add_paragraph(t, style="List Bullet")

doc.add_heading("Declaration", 2)
para("We confirm that this statement accurately describes how AI was used in this project and that we take responsibility for the submitted work.")
for nm in ["Saatvik Nagpal", "Atharvaa Khanzode"]:
    para(f"{nm}          Signature: ____________________          Date: ____________")
doc.save(OUT); print("saved", OUT)

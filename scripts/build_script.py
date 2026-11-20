"""Presenter script: slide titles, on-slide read-aloud text and speaker notes, in order, with timing guide."""
import pathlib
from pptx import Presentation
from docx import Document
from docx.shared import Pt, RGBColor

ROOT = pathlib.Path(__file__).resolve().parents[1]
prs = Presentation(ROOT / "reports/ProjectBaav_Group27_Presentation.pptx")
doc = Document()
st = doc.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(11)
doc.add_heading("Presenter script — Group 27", 0)
doc.add_paragraph("Main deck: slides 1–13, about ten minutes (roughly 45–50 seconds per step slide; title and close are quick). "
                  "Slides 14 onward are backup for questions. Suggested split: one presenter takes slides 1–7, the other slides 8–13.")
for i, s in enumerate(prs.slides, 1):
    texts = [sh.text_frame.text.strip() for sh in s.shapes if sh.has_text_frame and sh.text_frame.text.strip()]
    title = next((t for t in texts if len(t) > 15 and not t[:1].isdigit() and "Workbook" not in t and t.upper() != t), texts[0] if texts else "")
    if i == 14:
        doc.add_page_break(); doc.add_heading("Backup slides (for questions)", 1)
    doc.add_heading(f"Slide {i}: {title}", 2)
    note = s.notes_slide.notes_text_frame.text.strip() if s.has_notes_slide else ""
    if note:
        p = doc.add_paragraph(); r = p.add_run("Say: "); r.bold = True; p.add_run(note)
    panel = [t for t in texts if t.startswith(("WHAT WE DID", "WHAT WE FOUND", "SO WHAT"))]
out = ROOT / "reports/Presenter_Script.docx"
doc.save(out); print("saved", out)

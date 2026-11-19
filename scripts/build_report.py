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
    return f"₹{x:,.0f} cr"


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


# ---------------------------------------------------------------- title page
for _ in range(5):
    doc.add_paragraph()
p = doc.add_paragraph(); r = p.add_run("Paying for the Future"); r.font.name = "Cambria"; r.font.size = Pt(28); r.bold = True; r.font.color.rgb = INK
p = doc.add_paragraph(); r = p.add_run("Business analysis and valuation of DLF, Godrej Properties and Phoenix Mills"); r.font.size = Pt(14); r.font.color.rgb = ACC
doc.add_paragraph()
para("ECON F355 — Business Analysis & Valuation · End-semester project report", size=11)
para("Submitted to Prof. Mohit Kumar · BITS Pilani, K K Birla Goa Campus", size=11)
para("Group 27: Saatvik Nagpal · Atharvaa Khanzode", size=11)
para(f"Pricing date: {I['Valuation date']} · Financial data FY23–FY26 (years ending 31 March) · ₹ crore unless stated", size=9, italic=True)
doc.add_page_break()

# ---------------------------------------------------------------- executive summary
doc.add_heading("Executive summary", 1)
para(f"We analyse three listed real-estate companies with deliberately different business models: DLF, a Gurugram-focused "
     f"luxury developer that also owns 66.66% of a large office-and-retail rental platform (DCCDL); Godrej Properties, a "
     f"high-growth national developer that is building land and inventory faster than it recognises revenue; and Phoenix "
     f"Mills, a mall-led rental (annuity) business. The analysis follows the course sequence — strategy, accounting quality, "
     f"recasting, financial analysis, cost of capital, intrinsic valuation and relative valuation — and every number is "
     f"produced by formulas in our Excel model.")
bullets([
    ("Accounting changes the picture.", f"Reported profits mix three very different things. For DLF, {pc(D['JV/associate share of PAT'][3],0)} of FY26 profit is its share of DCCDL rental income and a further large slice is treasury interest; core development EBIT was only {cr(D['RC Core operating EBIT'][3])}. Godrej's core EBIT is negative ({cr(G['RC Core operating EBIT'][3])}) because revenue is recognised only on completion while overheads hit the P&L immediately, and {cr(G['RC Interest capitalised (cash paid − P&L cost)'][3])} of interest was capitalised into inventory in FY26."),
    ("Returns are modest; growth is funded by customers.", f"Average ROE in FY26 was {pc(D['DP ROE (3-step product)'][2])} (DLF), {pc(G['DP ROE (3-step product)'][2])} (Godrej) and {pc(P['DP ROE (3-step product)'][2])} (Phoenix) — below each firm's cost of equity. Customer advances now equal {xx(D['Customer advances / revenue (x)'][3])} DLF's annual revenue and {xx(G['Customer advances / revenue (x)'][3])} Godrej's, which is why DLF's invested capital fell even as bookings rose."),
    ("Cost of capital.", f"Using a rupee risk-free rate of {pc(I['Rupee risk-free rate = G-Sec − default spread'],2)} and an India equity risk premium of {pc(I['India total ERP = mature ERP + CRP'],2)}, the cost of equity is {pc(D['W Cost of equity (CAPM)'])} for DLF, {pc(G['W Cost of equity (CAPM)'])} for Godrej and {pc(P['W Cost of equity (CAPM)'])} for Phoenix; WACC is {pc(D['W WACC'])}, {pc(G['W WACC'])} and {pc(P['W WACC'])}."),
    ("Intrinsic value is well below price.", f"A 10-year FCFF model gives {rs(D['DCF']['Intrinsic value per share (Rs)'])} for DLF (price {rs(D['DCF']['Current market price (Rs)'])}), {rs(G['DCF']['Intrinsic value per share (Rs)'])} for Godrej ({rs(G['DCF']['Current market price (Rs)'])}) and {rs(P['DCF']['Intrinsic value per share (Rs)'])} for Phoenix ({rs(P['DCF']['Current market price (Rs)'])}). A reverse DCF shows today's prices imply discount rates of only {pc(D['implied WACC'])}, {pc(G['implied WACC'])} and {pc(P['implied WACC'])}."),
    ("Relative value tells a different story.", f"Against five listed peers, Godrej trades at {xx(N['RelVal'][1][12])} earnings and {xx(N['RelVal'][1][13],2)} book versus peer medians of {xx(N['RelStats']['Median'][0])} and {xx(N['RelStats']['Median'][1],2)}; DLF sits inside the peer range; Phoenix is the most expensive on every multiple."),
    ("Conclusion.", "The sector as a whole is priced for a long runway of growth that standard CAPM discount rates do not justify. Within the sector, Godrej Properties is the relatively cheapest, DLF is fairly priced relative to peers but expensive intrinsically, and Phoenix Mills carries the richest valuation. Ranking: Godrej Properties > DLF > Phoenix Mills."),
])

# ---------------------------------------------------------------- 1 scope
doc.add_heading("1. Scope, data and workflow", 1)
module_tag("Module 1 · framework for business analysis and valuation")
para("Real estate is a useful test of the course's tools because the gap between accounting profit and economic value is "
     "unusually wide: projects take four to six years, cash arrives before revenue, land is carried at historical cost and "
     "large parts of the business sit inside joint ventures. Our three companies cover the main models in the Indian sector:")
table(["", "DLF", "Godrej Properties", "Phoenix Mills"],
      [["Model", "Luxury development + rental JV", "National development, JV/JDA + outright land", "Mall-led rental annuity"],
       ["Revenue FY26", cr(D['DCF']['Shares outstanding (crore)'] * 0 + N['RelVal'][0][8]), cr(N['RelVal'][1][8]), cr(N['RelVal'][2][8])],
       ["PAT to owners FY26", cr(N['RelVal'][0][6]), cr(N['RelVal'][1][6]), cr(N['RelVal'][2][6])],
       ["Market cap", cr(N['RelVal'][0][3]), cr(N['RelVal'][1][3]), cr(N['RelVal'][2][3])],
       ["Net debt FY26", cr(N['RelVal'][0][4]), cr(N['RelVal'][1][4]), cr(N['RelVal'][2][4])]],
      [3.2, 4.2, 4.6, 4.2], "Source: company consolidated statements via Yahoo Finance; prices are the latest NSE close in our dataset.")
para("Data. Consolidated income statements, balance sheets and cash-flow statements for FY23–FY26 were downloaded for the "
     "three companies and five listed peers (Oberoi Realty, Prestige Estates, Brigade Enterprises, Sobha, Lodha/Macrotech) "
     "and mapped into one standard layout. Monthly and weekly prices for all eight stocks, the Nifty 50, the Nifty Realty index "
     "and four listed REITs were used for beta estimation. The 10-year G-Sec yield comes from the OECD series published on "
     "FRED, and country risk inputs, the mature-market premium and the rating–spread table come from Damodaran's January 2026 "
     "datasets.", after=4)
para("Workflow. The model is built in the order the course teaches: raw statements → recast (operating vs financing vs "
     "non-operating) → ratios and DuPont → regression and bottom-up betas → WACC → growth estimation → FCFF DCF, DDM → "
     "relative valuation → football field. Blue cells in the workbook are hard inputs with a stated source; everything else "
     "is a formula, so changing any assumption flows through to the final value.")

# ---------------------------------------------------------------- 2 strategy
doc.add_heading("2. Industry and strategy analysis", 1)
module_tag("Module 2 · strategy and competitive analysis (TB1 Ch-2)")
para("Since RERA (2016) and GST, Indian residential real estate has consolidated toward large, branded, well-capitalised "
     "developers. Buyers now pay for projects in instalments into escrowed accounts, which favours developers whose brand "
     "makes buyers comfortable paying early. Office and retail rental assets have become institutional, with REITs and "
     "sovereign funds (GIC, CPPIB) as long-term owners. These two trends explain most of what follows.")
doc.add_heading("Porter's five forces", 3)
table(["Force", "Assessment", "Why it matters for our three firms"],
      [["Threat of entry", "Low–moderate", "Land, approvals and RERA compliance need capital and track record; brand trust now decides who can pre-sell. Entry is easier through JDAs, which Godrej uses."],
       ["Supplier power", "High (land)", "Landowners in prime micro-markets have strong bargaining power; construction inputs (cement, steel, labour) are competitive but cyclical. DLF's legacy Gurugram land bank is a structural advantage."],
       ["Buyer power", "Moderate", "Home buyers are price-sensitive in mid-income segments but less so in luxury (DLF). Mall tenants (Phoenix) have limited alternatives in a city's top mall, giving the landlord pricing power."],
       ["Substitutes", "Moderate", "Renting instead of buying, resale homes, and for investors, REITs and gold. For malls, e-commerce is the long-term substitute; experiential retail limits it."],
       ["Rivalry", "High but consolidating", "Many local developers compete on price, but share is shifting to listed national players (Lodha, Prestige, Godrej, DLF)."]],
      [2.6, 2.4, 11.5])
doc.add_heading("Generic strategy, BCG and SPACE", 3)
para("DLF follows a focused differentiation strategy — a small number of very large luxury launches in one region, priced at "
     "a premium and pre-sold fast. Godrej Properties competes on brand-led breadth: projects in all major cities, sourced "
     "through joint ventures and outright purchases, with volume as the objective. Phoenix pursues differentiation through "
     "location and tenant mix: a few dominant malls per city, operated rather than sold.", after=3)
table(["Business unit", "Market growth", "Relative share", "BCG position"],
      [["DLF — Gurugram luxury residential", "High", "High", "Star"],
       ["DLF — DCCDL offices & malls (rental)", "Moderate", "High", "Cash cow"],
       ["DLF — other regions / plotted", "Moderate", "Low", "Question mark"],
       ["Godrej — MMR, NCR, Pune, Bengaluru residential", "High", "Medium–high", "Star"],
       ["Godrej — new cities, plotted development", "High", "Low", "Question mark"],
       ["Phoenix — operating malls", "Moderate", "High", "Cash cow"],
       ["Phoenix — offices", "Moderate", "Low", "Question mark"],
       ["Phoenix — hotels / residential", "Low", "Low", "Dog (non-core)"]],
      [7.0, 2.8, 2.8, 3.9])
para("On a SPACE assessment, DLF sits in the aggressive quadrant (strong financial position — net cash — and an attractive "
     "industry), Godrej in the competitive quadrant (strong competitive advantage and growth, but weaker financial strength as "
     "leverage and negative operating cash flow rise), and Phoenix in the conservative-to-aggressive boundary (financially "
     "strong, stable environment, slower growth).")
doc.add_heading("Value chain", 3)
para("For a developer, value is created at three points: land acquisition (buying cheaply or through revenue-sharing JDAs), "
     "approvals and design (time-to-launch drives IRR), and sales (pre-selling converts customers into the cheapest source of "
     "financing). Construction is largely outsourced. For Phoenix, the value chain is leasing, tenant curation and mall "
     "operations; revenue-share clauses mean Phoenix earns more when its tenants sell more, which links rent to consumption "
     "growth. This difference is why we model the developers with high sales-to-capital ratios and Phoenix with a low one.")

doc.add_heading("PESTEL and SWOT", 3)
table(["Factor", "Key point for Indian real estate", "Most exposed"],
      [["Political", "State-level approvals and land policy; affordable-housing incentives; infrastructure push (metros, expressways) re-rates micro-markets", "Godrej (multi-state)"],
       ["Economic", "Home-loan rates track RBI policy; G-Sec at 7.4% raises discount rates; consumption growth drives mall rents", "All; Phoenix via consumption"],
       ["Social", "Urbanisation, nuclear families and preference for branded, RERA-registered projects; experiential retail", "DLF luxury, Phoenix"],
       ["Technological", "Digital sales and site tracking; e-commerce as a long-run substitute for physical retail", "Phoenix"],
       ["Environmental", "Green-building norms, water and construction-dust restrictions (NCR construction bans delay projects)", "DLF, Godrej in NCR"],
       ["Legal", "RERA escrow and delivery timelines; Ind AS 115 revenue timing; stamp-duty changes", "Developers"]],
      [2.4, 10.4, 3.7], size=8)
table(["", "DLF", "Godrej Properties", "Phoenix Mills"],
      [["Strengths", "Low-cost legacy land bank; net cash; luxury brand; rental platform with GIC", "Group brand; national reach; fast booking growth; JV sourcing", "Dominant malls in top cities; recurring rent; partners CPPIB and GIC"],
       ["Weaknesses", "Concentrated in Gurugram; core margin fell in FY26", "Negative operating cash flow; rising debt; core EBIT negative", "Capital-intensive; low dividend; minority leakage (~21% of PAT)"],
       ["Opportunities", "Monetising land bank; more rental assets in DCCDL", "Conversion of bookings to revenue; new cities", "New malls in CWIP; offices; rent escalations"],
       ["Threats", "Luxury demand cycle; regulatory delays in NCR", "Land prices; execution across many projects", "E-commerce; slowdown in discretionary spending"]],
      [2.4, 4.6, 4.8, 4.7], "SWOT summary (qualitative; evidence from the ratios in Section 5).", size=8)

# ---------------------------------------------------------------- 3 accounting analysis
doc.add_heading("3. Accounting analysis: where reported numbers mislead", 1)
module_tag("Module 3 · accounting analysis — policies, flexibility and red flags (TB1 Ch-3)")
para("We reviewed the accounting policies that most affect these companies and checked each against the numbers.")
table(["Policy / issue", "Effect on reported numbers", "Evidence in our data", "How we adjust"],
      [["Revenue on completion (Ind AS 115)", "Revenue lags bookings by years; margins swing with the project mix delivered", f"Godrej: customer advances {xx(G['Customer advances / revenue (x)'][3])} revenue; core margin {pc(G['Core EBIT margin'][3])}", "Forecast revenue converging to bookings; value on cash-generating capacity"],
       ["Borrowing costs capitalised (Ind AS 23)", "Interest moves into inventory and hits COGS later; P&L interest cover looks inflated", f"Godrej FY26: interest paid {cr(G['W Interest paid (cash, incl. capitalised) FY26'])} vs P&L finance cost far smaller; P&L cover {G['Interest coverage: EBIT / P&L finance cost (x)'][3]:.0f}x vs cash cover {G['Cash interest coverage: EBIT / interest paid (x)'][3]:.1f}x", "Use cash interest for coverage and synthetic rating"],
       ["Joint ventures equity-accounted (Ind AS 111)", "JV revenue, debt and assets are off the consolidated statements; only a one-line profit share appears", f"DLF: DCCDL share {cr(D['RC Share of JV/associate profit (post-tax)'][3])}, {pc(D['JV/associate share of PAT'][3],0)} of PAT; 'tax & JV burden' >1 ({D['DP Tax & JV burden'][2]:.2f})", "Value DCCDL separately; exclude from operating EBIT"],
       ["Investment property at cost (Ind AS 40)", "Mall and office assets carried at depreciated cost, far below market value", f"Phoenix P/B {xx(N['RelVal'][2][13],1)}", "Do not rely on P/B for Phoenix; use cash-flow valuation"],
       ["RERA escrow (70% of collections)", "Part of cash is not freely available", f"DLF restricted cash {cr(D['RC Restricted cash (kept operating)'][3])}", "Treat as operating, not as surplus cash"],
       ["Treasury and exceptional income", "Interest on surplus funds and one-off gains inflate EBIT", f"Godrej exceptional/other gains FY26 large enough to turn core EBIT negative", "Strip from core EBIT; add liquid assets separately"]],
      [3.4, 4.2, 4.8, 4.1], size=8)
para(f"Earnings quality. Accruals are low for DLF and Phoenix: cash flow from operations exceeded PAT in FY26 ({xx(D['CFO / PAT (x)'][3],2)} and {xx(P['CFO / PAT (x)'][3],2)}). Godrej is the exception — operating cash flow has been negative every year (CFO/PAT {xx(G['CFO / PAT (x)'][3],2)} in FY26) because it is buying land and building inventory "
     f"(inventory rose to {pc(G['Inventory / total assets'][3],0)} of total assets). This is a growth-phase pattern rather than evidence of manipulation, but it means Godrej's reported profit is not yet backed by cash, so its value depends heavily on future execution.")

# ---------------------------------------------------------------- 4 recast
doc.add_heading("4. Recasting the statements", 1)
module_tag("Module 4 · implementing accounting analysis — recasting (TB1 Ch-4/5)")
para("Following the Palepu–Healy approach, each balance sheet was split into net operating assets (what the business needs "
     "to operate), net financial obligations (debt less liquid investments) and non-operating JV investments. The income "
     "statement was split the same way, giving a core operating EBIT and NOPAT that excludes treasury income, exceptional "
     "items and JV profits.")
table(["FY26 (₹ cr)", "DLF", "Godrej", "Phoenix"],
      [["EBIT incl. other income", f"{D['RC EBIT incl. other income'][3]:,.0f}", f"{G['RC EBIT incl. other income'][3]:,.0f}", f"{P['RC EBIT incl. other income'][3]:,.0f}"],
       ["Core operating EBIT", f"{D['RC Core operating EBIT'][3]:,.0f}", f"{G['RC Core operating EBIT'][3]:,.0f}", f"{P['RC Core operating EBIT'][3]:,.0f}"],
       ["NOPAT (t = 25.17%)", f"{D['RC NOPAT = core EBIT × (1 − t)'][3]:,.0f}", f"{G['RC NOPAT = core EBIT × (1 − t)'][3]:,.0f}", f"{P['RC NOPAT = core EBIT × (1 − t)'][3]:,.0f}"],
       ["Share of JV/associate profit", f"{D['RC Share of JV/associate profit (post-tax)'][3]:,.0f}", f"{G['RC Share of JV/associate profit (post-tax)'][3]:,.0f}", f"{P['RC Share of JV/associate profit (post-tax)'][3]:,.0f}"],
       ["Cash & liquid investments", f"{D['RC Cash & liquid investments'][3]:,.0f}", f"{G['RC Cash & liquid investments'][3]:,.0f}", f"{P['RC Cash & liquid investments'][3]:,.0f}"],
       ["Net financial obligations", f"{D['RC Net financial obligations (NFO)'][3]:,.0f}", f"{G['RC Net financial obligations (NFO)'][3]:,.0f}", f"{P['RC Net financial obligations (NFO)'][3]:,.0f}"],
       ["Net operating assets (invested capital)", f"{D['RC Net operating assets = invested capital'][3]:,.0f}", f"{G['RC Net operating assets = invested capital'][3]:,.0f}", f"{P['RC Net operating assets = invested capital'][3]:,.0f}"],
       ["Customer advances & other op. liabilities", f"{D['RC Customer advances & other op. liabilities (derived)'][3]:,.0f}", f"{G['RC Customer advances & other op. liabilities (derived)'][3]:,.0f}", f"{P['RC Customer advances & other op. liabilities (derived)'][3]:,.0f}"]],
      [6.5, 3.2, 3.2, 3.2])
para(f"Two results stand out. DLF's invested capital fell from {cr(D['RC Net operating assets = invested capital'][0])} in FY23 to "
     f"{cr(D['RC Net operating assets = invested capital'][3])} in FY26 even though bookings grew, because customer advances "
     f"({cr(D['RC Customer advances & other op. liabilities (derived)'][3])}) now fund construction. Godrej's invested capital "
     f"doubled over the same period to {cr(G['RC Net operating assets = invested capital'][3])}, reflecting land purchases.")

# ---------------------------------------------------------------- 5 financial analysis
doc.add_heading("5. Financial analysis", 1)
module_tag("Module 5 · ratio analysis, cash-flow analysis, EVA (TB1 Ch-5)")
rows5 = []
for lab, key, f in [("Revenue CAGR FY23–26", "Revenue CAGR FY23→FY26", "pct1"), ("Core EBIT margin FY26", "Core EBIT margin", "pctL"),
                    ("ROE (avg) FY26", "Return on equity (avg)", "pctL"), ("ROIC (avg) FY26", "ROIC = NOPAT / avg invested capital", "pctL"),
                    ("Inventory days FY26", "Inventory days (on cost of revenue)", "numL"), ("Receivable days FY26", "Receivable days", "numL"),
                    ("Current ratio FY26", "Current ratio (x)", "xL"), ("Net debt / equity FY26", "Net debt / equity (x)", "xL"),
                    ("Cash interest cover FY26", "Cash interest coverage: EBIT / interest paid (x)", "xL"), ("CFO / PAT FY26", "CFO / PAT (x)", "xL"),
                    ("Dividend payout FY26", "Dividend payout", "pctL")]:
    vals = []
    for d in (D, G, P):
        v = d[key] if f == "pct1" else d[key][3]
        vals.append(pc(v) if f.startswith("pct") else (f"{v:,.0f}" if f == "numL" else xx(v, 2)))
    rows5.append([lab] + vals)
table(["Ratio", "DLF", "Godrej", "Phoenix"], rows5, [6.5, 3.2, 3.2, 3.2],
      "Average balances used where a flow is divided by a stock. Full 38-ratio set with FY23–FY26 history in the 'Ratios' sheet.")
fig("re_signature", "Figure 1 — The real-estate signature: very long inventory cycles, growing customer advances and diverging cash conversion.")
para(f"Efficiency ratios that look alarming in other industries are normal here: DLF holds about {D['Inventory days (on cost of revenue)'][3]:,.0f} "
     f"days of inventory and Godrej about {G['Inventory days (on cost of revenue)'][3]:,.0f}, because land and work-in-progress take years to become "
     f"revenue. The useful question is how inventory is financed. DLF and Godrej finance it largely with customer advances; Godrej also "
     f"uses debt (net debt/equity {xx(G['Net debt / equity (x)'][3],2)}), while DLF is net cash ({xx(D['Net debt / equity (x)'][3],2)}).")
doc.add_heading("DuPont analysis", 2)
fig("dupont", "Figure 2 — Three-step DuPont, FY24–FY26 (average assets and equity).")
para(f"The three companies earn similar ROEs (about 10–11% in FY26) in completely different ways. DLF has a very high net margin "
     f"({pc(D['DP Net profit margin'][2])}) but a very low asset turnover ({D['DP Asset turnover'][2]:.2f}x) and little leverage ({D['DP Equity multiplier'][2]:.2f}x). "
     f"Godrej has a lower margin but the highest leverage ({G['DP Equity multiplier'][2]:.2f}x), and its asset turnover fell to {G['DP Asset turnover'][2]:.2f}x "
     f"as inventory grew faster than revenue. Phoenix has the highest turnover ({P['DP Asset turnover'][2]:.2f}x), which is expected for an operating rental business.")
para(f"The extended five-step version exposes the JV effect directly. DLF's 'tax and JV burden' ratio is {D['DP Tax & JV burden'][2]:.2f} — above one — "
     f"because its DCCDL profit share is added after the tax line. Attribution of the change in ROE between FY24 and FY26 shows that for DLF "
     f"{pc(D['ROEattr' + 'from margin'],1)} of the {pc(D['ROEattr' + 'total = ΔROE'],1)} increase came from margin and {pc(D['ROEattr' + 'from leverage'],1)} from leverage; for Godrej, "
     f"a {pc(G['ROEattr' + 'from margin'],1)} margin gain was partly offset by a {pc(G['ROEattr' + 'from asset turnover'],1)} turnover drag.")
para(f"Separating operating from financing activity (Palepu's decomposition) is more revealing still. DLF's return on net operating assets "
     f"was {pc(D['DP Return on net operating assets (RNOA)'][2])} and Godrej's was {pc(G['DP Return on net operating assets (RNOA)'][2])}: almost all of Godrej's ROE "
     f"(non-operating contribution {pc(G['DP Non-operating (JV, exceptional) contribution'][2])}) came from treasury income, exceptional gains and JV-related items rather than "
     f"from completed projects. Phoenix is the only firm whose ROE is almost entirely operating (RNOA {pc(P['DP Return on net operating assets (RNOA)'][2])}).")
doc.add_heading("Economic value added, distress and the balanced scorecard", 2)
para(f"EVA (NOPAT − WACC × opening invested capital) was negative for all three in every year: FY26 EVA was {cr(D['EVA = NOPAT − WACC × opening NOA'][2])} for DLF, "
     f"{cr(G['EVA = NOPAT − WACC × opening NOA'][2])} for Godrej and {cr(P['EVA = NOPAT − WACC × opening NOA'][2])} for Phoenix. On recognised accounting returns, none of them "
     f"yet earns its cost of capital; the market's valuation therefore rests on future projects, not on current returns. Phoenix is closest to "
     f"breaking even on EVA (spread {pc(P['EVA spread = ROIC − WACC'][2])}).")
para("Cash value added (CVA) gives a cash-based version of the same test: operating cash flow less capex less a capital charge on invested capital. "
     f"On FY26 figures DLF's free cash flow ({cr(D['Free cash flow = CFO − capex'][3])}) comfortably exceeds its capital charge — CVA is positive even though EVA is negative — "
     f"because customer advances turn accounting profit into early cash. Godrej's free cash flow was {cr(G['Free cash flow = CFO − capex'][3])}, so CVA is deeply negative; "
     f"Phoenix's free cash flow of {cr(P['Free cash flow = CFO − capex'][3])} does not yet cover its capital charge. Comparing EVA with CVA shows how much of each company's "
     "value story depends on the timing of cash rather than on profit.")
fig("altman", "Figure 3 — Altman Z (manufacturing weights) misclassifies an asset-heavy developer; the emerging-market Z'' does not.", 15.5)
para(f"Godrej's original Altman Z fell to {G['Z'][3]:.2f} in FY26, inside the 'distress' zone, while its Z'' score was {G['Zpp'][3]:.2f} (grey zone). The original model "
     f"rewards sales/total assets, which is structurally low for developers, and uses market value of equity, which is volatile. Z'' drops the turnover term and is "
     f"the better screen here; on it, DLF ({D['Zpp'][3]:.2f}) and Phoenix ({P['Zpp'][3]:.2f}) are comfortably safe.")
table(["Perspective", "DLF", "Godrej Properties", "Phoenix Mills"],
      [["Financial", f"Net cash; ROE {pc(D['Return on equity (avg)'][3])}", f"Leverage rising; CFO negative", f"ROIC {pc(P['ROIC = NOPAT / avg invested capital'][3])}; stable"],
       ["Customer", "Luxury buyers pre-pay; advances 2.9x revenue", "Brand drives bookings ahead of revenue", "Footfall and tenant sales drive revenue share"],
       ["Internal process", "Execution of large launches on time", "Land-to-launch speed across cities", "Leasing, tenant mix, occupancy"],
       ["Learning & growth", "Rental platform with GIC", "Scaling project management", "New-city mall pipeline in CWIP"]],
      [3.0, 4.4, 4.6, 4.5], "Balanced scorecard: the non-financial drivers behind the ratios above.", size=8)

# ---------------------------------------------------------------- 6 cost of capital
doc.add_heading("6. Cost of capital", 1)
module_tag("Module 6 · hurdle rate — risk-free rate, ERP, CRP, regression and bottom-up beta, Kd, WACC (TB2 Ch-2)")
para(f"Risk-free rate. The 10-year G-Sec yielded {pc(I['India 10-yr G-Sec yield'],2)} (October 2026). Because the Indian government's own bonds carry default risk, "
     f"we subtract the sovereign default spread for a Baa3 rating ({pc(I['India sovereign default spread (Baa3)'],2)}) to get a rupee risk-free rate of "
     f"{pc(I['Rupee risk-free rate = G-Sec − default spread'],2)}. Equity risk premium. We add India's country risk premium ({pc(I['India country risk premium (CRP)'],2)}) to the mature-market "
     f"implied premium ({pc(I['Mature market ERP'],2)}) for a total of {pc(I['India total ERP = mature ERP + CRP'],2)}. Terminal growth is capped at {pc(I['Terminal growth rate (nominal, Rs)'],1)}, "
     f"close to the rupee risk-free rate, since no firm can grow faster than the economy forever.")
fig("beta_scatter", "Figure 4 — Regression betas: 60 monthly returns against the Nifty 50 (Apr 2021 – Oct 2026 window in the dataset).")
bm = N["Beta_Monthly"]
dl, gp, ph = bm["DLF Ltd"], bm["Godrej Propert"], bm["Phoenix Mills"]
para(f"Regression beta. DLF's raw beta is {dl['Raw beta (SLOPE)']:.2f} (standard error {dl['Std error of beta']:.2f}, R² {dl['R-squared']:.2f}); Godrej's is {gp['Raw beta (SLOPE)']:.2f} "
     f"(SE {gp['Std error of beta']:.2f}); Phoenix's is {ph['Raw beta (SLOPE)']:.2f} (SE {ph['Std error of beta']:.2f}, R² {ph['R-squared']:.2f}). The 95% confidence interval for Godrej runs from "
     f"{gp['95% CI low']:.2f} to {gp['95% CI high']:.2f} — wide enough to move the cost of equity by about four percentage points. Weekly betas over three years gave similar values, so "
     f"the result is not an artefact of the return interval.")
fig("bottomup_beta", "Figure 5 — Bottom-up beta: unlevering eight listed developers at their market debt-to-equity.", 13.5)
para(f"Bottom-up beta. To reduce estimation error, we unlevered all eight developers' betas using Hamada's formula at their own market D/E and took the median: "
     f"{N['BU_median']:.2f}. Averaging eight estimates cuts the standard error to roughly {N['BU_se']:.2f}. Relevered at each firm's D/E this gives "
     f"{D['W Beta used']:.2f} for DLF and {G['W Beta used']:.2f} for Godrej. For Phoenix we did not use the developer median, because a rental business carries less "
     f"operating risk. We tested India's listed REITs as alternative comparables, but their betas ({N['Beta_REIT']['Nexus Select T']['Raw beta (SLOPE)']:.2f} for the mall REIT) have R² below 12% — "
     f"REIT units trade like illiquid bonds — so they are unreliable. We therefore use Phoenix's own Blume-adjusted beta of {P['W Beta used']:.2f}.")
para("Cost of debt. Synthetic ratings are based on cash interest paid rather than the P&L finance cost, because capitalised interest otherwise flatters coverage. "
     f"DLF's coverage of {D['W Interest coverage ratio (cash basis)']:.1f}x maps to {D['W Synthetic rating']}, Godrej's {G['W Interest coverage ratio (cash basis)']:.1f}x to {G['W Synthetic rating']} and Phoenix's "
     f"{P['W Interest coverage ratio (cash basis)']:.1f}x to {P['W Synthetic rating']}.")
table(["", "DLF", "Godrej", "Phoenix"],
      [["Beta used", f"{D['W Beta used']:.2f}", f"{G['W Beta used']:.2f}", f"{P['W Beta used']:.2f}"],
       ["Cost of equity", pc(D['W Cost of equity (CAPM)']), pc(G['W Cost of equity (CAPM)']), pc(P['W Cost of equity (CAPM)'])],
       ["Synthetic rating / pre-tax Kd", f"{D['W Synthetic rating']} / {pc(D['W Pre-tax Kd used'])}", f"{G['W Synthetic rating']} / {pc(G['W Pre-tax Kd used'])}", f"{P['W Synthetic rating']} / {pc(P['W Pre-tax Kd used'])}"],
       ["Debt / (debt + equity), market", pc(D['W D / V']), pc(G['W D / V']), pc(P['W D / V'])],
       ["WACC", pc(D['W WACC']), pc(G['W WACC']), pc(P['W WACC'])]], [6.0, 3.4, 3.4, 3.4])

# ---------------------------------------------------------------- 7 intrinsic valuation
doc.add_heading("7. Intrinsic valuation", 1)
module_tag("Module 7 · growth estimation, FCFF DCF, DDM; limitations (TB2 Ch-6)")
doc.add_heading("Growth estimation", 3)
para(f"Historical growth was strong — revenue CAGR FY23–26 of {pc(D['Revenue CAGR FY23→FY26'])} (DLF), {pc(G['Revenue CAGR FY23→FY26'])} (Godrej) and {pc(P['Revenue CAGR FY23→FY26'])} (Phoenix) — "
     f"but fundamental growth (reinvestment rate × ROIC) is unusable for developers: DLF's reinvestment rate is negative because customer advances shrink its invested "
     f"capital, and Godrej's is meaningless while its ROIC is near zero. Phoenix's fundamental growth averaged about {pc(sum(P['Fundamental growth = RR × ROIC'])/3)}, close to its revenue growth. We "
     f"therefore set revenue growth from the business pipeline (bookings already made but not yet recognised) and tie reinvestment to growth through a "
     f"sales-to-capital ratio, so growth in the model is always paid for.")
doc.add_heading("FCFF model design", 3)
bullets([("Two phases.", "Five years of explicit growth, then five years in which growth fades linearly to the terminal rate."),
         ("Margins.", "Core EBIT margin moves from the FY26 level to a target by year 5 and is then held."),
         ("Reinvestment.", "Reinvestment = change in revenue ÷ sales-to-capital; in the terminal year reinvestment = g ÷ RONIC × NOPAT."),
         ("Discount rates.", "WACC for years 1–5; it then moves to a stable WACC in which beta converges to 1.0, as Damodaran recommends for mature firms; mid-year discounting."),
         ("Bridge.", "Add liquid investments and JV investments, subtract all debt (including leases) and the minority share (Phoenix's platform partners own about 21% of profits).")])
table(["Assumption", "DLF", "Godrej", "Phoenix"],
      [["Revenue growth FY27–31", " / ".join(pc(g, 0) for g in D['DCF growth']), " / ".join(pc(g, 0) for g in G['DCF growth']), " / ".join(pc(g, 0) for g in P['DCF growth'])],
       ["Core EBIT margin FY26 → target", f"{pc(D['Core EBIT margin'][3],0)} → {pc(D['DCF margin'],0)}", f"{pc(G['Core EBIT margin'][3],0)} → {pc(G['DCF margin'],0)}", f"{pc(P['Core EBIT margin'][3],0)} → {pc(P['DCF margin'],0)}"],
       ["Sales-to-capital", f"{D['DCF s2c']:.1f}", f"{G['DCF s2c']:.1f}", f"{P['DCF s2c']:.1f}"],
       ["WACC (years 1–5 → stable)", f"{pc(D['W WACC'])} → {pc(D['DCF stableWACC'])}", f"{pc(G['W WACC'])} → {pc(G['DCF stableWACC'])}", f"{pc(P['W WACC'])} → {pc(P['DCF stableWACC'])}"]],
      [5.0, 3.8, 3.8, 3.8], size=8)
para("Why these numbers. DLF's growth reflects luxury projects already sold in Gurugram that will be recognised on completion over FY27–30; its target margin of 40% reflects "
     "the high-ticket mix. Godrej's revenue converges toward its booking run-rate, which is several times current revenue, and its margin normalises to 22% as "
     "overheads are spread over more completed projects. Phoenix grows with the ramp-up of malls opened in FY24–25 and the projects already in CWIP; its margin "
     "is already about 55%. Developers need little new capital per rupee of revenue (inventory and land are already on the balance sheet), while malls need a lot.")
fig("dcf_paths", "Figure 6 — Forecast revenue and margin paths used in the FCFF models (FY26 actual in colour).")
table(["Valuation bridge (₹ cr)", "DLF", "Godrej", "Phoenix"],
      [[k, *[f"{d['DCF'][k]:,.0f}" if abs(d['DCF'][k]) > 50 else (pc(d['DCF'][k]) if abs(d['DCF'][k]) < 1.5 else f"{d['DCF'][k]:,.2f}") for d in (D, G, P)]]
       for k in ["PV of FCFF FY27–FY36", "PV of terminal value", "Value of operating assets", "Terminal value as % of operating value",
                 "Add: cash & liquid investments (FY26)", "Add: JV / associate investments", "Less: total debt incl. leases",
                 "Less: minority interest (proportional)", "Equity value to owners", "Intrinsic value per share (Rs)", "Current market price (Rs)"]],
      [6.5, 3.2, 3.2, 3.2])
para(f"DLF's DCCDL stake is valued separately by capitalising its share of DCCDL's profit ({cr(D['DCCDL']['jv_pat'])}) at the cost of equity less growth, giving "
     f"{cr(D['DCCDL']['value'])} — close to its book value of {cr(D['DCCDL']['book'])}, which is a useful cross-check.")
doc.add_heading("Sensitivity and reverse DCF", 3)
gA = D["gridA"]
para(f"Shifting WACC by ±2 percentage points and terminal growth by ±1 point moves DLF's value between {rs(D['gridA_min'])} and {rs(D['gridA_max'])}; Godrej's between "
     f"{rs(G['gridA_min'])} and {rs(G['gridA_max'])}; Phoenix's between {rs(P['gridA_min'])} and {rs(P['gridA_max'])}. No reasonable combination reaches the market price. "
     f"Because value is linear in the target margin, we can also solve exactly for the margin the market price requires: {pc(D['implied margin'],0)} for DLF, "
     f"{pc(G['implied margin'],0)} for Godrej and {pc(P['implied margin'],0)} for Phoenix. Margins above 100% are impossible, so the gap is not about margins. Solving instead "
     f"for the discount rate shows that today's prices are consistent with our cash flows only at a WACC of roughly {pc(D['implied WACC'])} (DLF), {pc(G['implied WACC'])} (Godrej) "
     f"and {pc(P['implied WACC'])} (Phoenix) — in Phoenix's case, about the government bond yield.")
fig("implied_wacc", "Figure 7 — The discount rate implied by market prices versus our CAPM-based WACC.", 12.5)
doc.add_heading("Dividend discount model", 3)
para(f"A two-stage DDM, with payout gliding to the stable level implied by g/ROE, gives {rs(D['DDM']['DDM value per share (Rs)'])} for DLF and {rs(P['DDM']['DDM value per share (Rs)'])} for Phoenix. "
     f"Godrej pays no dividend, so the DDM cannot be applied. Both values are far below price because these firms pay out only {pc(D['Dividend payout'][3],0)} and {pc(P['Dividend payout'][3],0)} "
     f"of earnings and reinvest the rest; DDM undervalues firms whose value lies in reinvestment, which is a known limitation of the model.")

# ---------------------------------------------------------------- 8 relative valuation
doc.add_heading("8. Relative valuation", 1)
module_tag("Module 8 · four-step relative valuation; P/E, PEG, P/B, P/S (TB2 Ch-7, 8)")
para("Step 1 — comparables: five listed developers of similar scale. Step 2 — standardise: all multiples use FY26 consolidated figures and the same price date. "
     "Step 3 — distribution: we use the median and inter-quartile range because the distribution is skewed (Sobha's P/E is above 70x). Step 4 — control for differences: "
     "we regress P/B on ROE across all eight firms.")
rvrows = []
for r in N["RelVal"]:
    rvrows.append([r[0], f"{r[12]:.1f}", f"{r[13]:.2f}", f"{r[14]:.1f}", f"{r[15]:.1f}", (f"{r[16]:.2f}" if isinstance(r[16], (int, float)) else "n.m."), pc(r[11])])
med = N["RelStats"]["Median"]
rvrows.append(["Peer median (5 peers)", f"{med[0]:.1f}", f"{med[1]:.2f}", f"{med[2]:.1f}", f"{med[3]:.1f}", f"{med[4]:.2f}", ""])
table(["Company", "P/E", "P/B", "P/S", "EV/EBITDA", "PEG", "ROE"], rvrows, [4.6, 1.8, 1.8, 1.8, 2.2, 1.8, 1.8])
fig("pb_roe", "Figure 8 — Controlling for profitability: P/B against ROE across eight developers.", 12.5)
reg = N["Reg"]
para(f"The regression (P/B = {reg['a']:.2f} + {reg['b']:.1f} × ROE) has an R² of only {reg['r2']:.2f}: ROE explains little of the variation in P/B, largely because Phoenix's "
     f"book value is understated by cost-based accounting for investment property and because developers' current ROE says little about their land banks. We therefore "
     f"treat the regression as a cross-check rather than a primary estimate. Implied values at peer medians:")
ri = N["RelImplied"]
table(["Implied value (₹/share)", "P/E median", "P/E IQR", "P/B median", "EV/EBITDA median", "P/B on ROE"],
      [[k, f"{v[0]:,.0f}", f"{v[1]:,.0f}–{v[2]:,.0f}", f"{v[3]:,.0f}", f"{v[6]:,.0f}", f"{v[8]:,.0f}"] for k, v in ri.items()],
      [4.6, 2.4, 3.0, 2.4, 2.8, 2.4])
para("EV/EBITDA understates DLF because its EBITDA excludes the DCCDL profit share, and P/S is distorted for all developers by revenue-recognition timing; we place "
     "most weight on P/E and P/B.")

# ---------------------------------------------------------------- 9 synthesis
doc.add_heading("9. Synthesis and recommendation", 1)
fig("football_field", "Figure 9 — Football field: intrinsic and relative value ranges against the market price.")
para("Two conclusions follow from the football field. First, intrinsic and relative valuation disagree sharply. Relative valuation compares each company with "
     "peers that are themselves priced at high multiples, so it cannot detect a sector-wide premium; the DCF and reverse DCF show that such a premium exists — "
     "investors are discounting real-estate cash flows at rates close to the government bond yield, which implies they expect growth well beyond our ten-year horizon "
     "or treat land banks as valuable options. Second, within the sector the ranking is clear:")
bullets([("Godrej Properties — relatively undervalued.", f"Cheapest on P/E and P/B; peer-median P/E implies {rs(ri['Godrej Properties'][0])} against a price of {rs(G['DCF']['Current market price (Rs)'])}. Risk: negative operating cash flow and rising leverage; value depends on converting bookings into cash."),
         ("DLF — fairly valued against peers, expensive intrinsically.", f"Inside the peer P/E range ({rs(ri['DLF Ltd'][1])}–{rs(ri['DLF Ltd'][2])}); strongest balance sheet; but the DCF ({rs(D['DCF']['Intrinsic value per share (Rs)'])}) requires a discount rate of about {pc(D['implied WACC'])} to justify the price."),
         ("Phoenix Mills — richly valued.", f"Most expensive on every multiple and the lowest implied discount rate ({pc(P['implied WACC'])}); a high-quality annuity business, but the price already assumes many years of rental growth.")])
doc.add_heading("Limitations", 2)
bullets(["Four years of statements from one aggregated source; key figures should be reconciled to annual reports before relying on them.",
         "Bookings, land-bank and occupancy data (the main value drivers for developers) are disclosed in investor presentations, not in the statements we used; a NAV approach would capture them better.",
         "Beta estimates have wide confidence intervals; a one-standard-error change in Godrej's beta moves its cost of equity by about two percentage points.",
         "Accounting book values (cost-based investment property, capitalised interest) limit the usefulness of P/B and ROE comparisons.",
         "The growth and margin paths are judgements; the sensitivity tables and reverse DCF show how much each matters."])

# ---------------------------------------------------------------- references
doc.add_heading("References", 1)
for ref in ["Palepu, K., Healy, P. & Bernard, V. Business Analysis & Valuation: Using Financial Statements (3rd ed.). Cengage.",
            "Damodaran, A. Damodaran on Valuation (2nd ed.). Wiley.",
            "Damodaran, A. The Dark Side of Valuation (2nd ed.). Pearson, 2010.",
            "Damodaran Online datasets (January 2026): country risk premiums (ctryprem.xlsx); ratings, interest coverage and default spreads.",
            "OECD Main Economic Indicators, long-term government bond yield for India (INDIRLTLT01STM), via FRED, Federal Reserve Bank of St. Louis.",
            "Yahoo Finance: consolidated financial statements and NSE price histories for the companies analysed.",
            "Altman, E. (1968). Financial ratios, discriminant analysis and the prediction of corporate bankruptcy. Journal of Finance, 23(4); Altman, E. (2005). An emerging market credit scoring system for corporate bonds. Emerging Markets Review, 6(4).",
            "Blume, M. (1971). On the assessment of risk. Journal of Finance, 26(1).",
            "Hamada, R. (1972). The effect of the firm's capital structure on the systematic risk of common stocks. Journal of Finance, 27(2).",
            "Real Estate (Regulation and Development) Act, 2016; Ind AS 115, Ind AS 23, Ind AS 40, Ind AS 111."]:
    p = doc.add_paragraph(ref, style="List Number"); p.paragraph_format.space_after = Pt(2)
    for r in p.runs:
        r.font.size = Pt(9)

doc.add_heading("Appendix — model map", 2)
table(["Workbook sheet", "Course module", "Content"],
      [["Inputs", "6", "Risk-free rate, ERP, CRP, tax, terminal growth, rating table"], ["Data_*", "1", "Standardised statements, 8 companies"],
       ["Recast", "3–4", "Operating / financing / JV split, NOPAT, capitalised interest"], ["Ratios, DuPont, AltmanZ, Growth_EVA", "5", "38 ratios, 3- and 5-step DuPont, Palepu split, Z/Z'', EVA"],
       ["Beta_Monthly, Beta_Weekly, Beta_REIT, BottomUp_Beta, WACC", "6", "Regression statistics, bottom-up beta, synthetic rating, WACC"],
       ["DCF_DLF, DCF_GPL, DCF_PML, DDM", "7", "10-year FCFF, two sensitivity grids, reverse DCF, implied WACC, DDM"],
       ["RelVal, Summary", "8", "Peer multiples, P/B–ROE regression, football field"]], [6.5, 2.2, 7.8], size=8)
doc.add_heading("Appendix — formulas used, step by step", 2)
table(["Step", "Formula", "Module"],
      [["Core EBIT", "PBT + finance cost − interest income − exceptional items", "4"],
       ["NOPAT", "Core EBIT × (1 − 25.17%)", "4"],
       ["Invested capital (NOA)", "Equity + minority + debt − cash & liquid investments − JV investments", "4"],
       ["3-step DuPont", "ROE = PAT/Revenue × Revenue/avg Assets × avg Assets/avg Equity", "5"],
       ["5-step DuPont", "ROE = (PAT/PBT) × (PBT/EBIT) × (EBIT/Revenue) × ATO × EM × owners' share", "5"],
       ["Palepu split", "ROE = RNOA + (RNOA − NBC) × NFL  (+ non-operating residual)", "5"],
       ["EVA", "NOPAT − WACC × opening invested capital", "5"],
       ["Altman Z''", "3.25 + 6.56·WC/TA + 3.26·RE/TA + 6.72·EBIT/TA + 1.05·BVE/TL", "5"],
       ["Rupee risk-free rate", "10-yr G-Sec − sovereign default spread", "6"],
       ["Regression beta", "SLOPE(R_stock, R_Nifty); SE = STEYX / (σ_m·√(n−1))", "6"],
       ["Blume adjustment", "0.67 × raw β + 0.33", "6"],
       ["Unlever / relever", "β_u = β_L / (1 + (1 − t)·D/E);  β_L = β_u·(1 + (1 − t)·D/E)", "6"],
       ["Cost of equity", "Ke = Rf + β × (mature ERP + CRP)", "6"],
       ["Cost of debt", "Kd = Rf + country default spread + company spread (from cash interest coverage)", "6"],
       ["WACC", "E/V·Ke + D/V·Kd·(1 − t)", "6"],
       ["Reinvestment", "ΔRevenue ÷ sales-to-capital; terminal: g ÷ RONIC × NOPAT", "7"],
       ["FCFF", "NOPAT − reinvestment", "7"],
       ["Terminal value", "FCFF(n+1) ÷ (stable WACC − g)", "7"],
       ["Reverse DCF (margin)", "target margin = (implied firm value + PV reinvestment − PV base-margin NOPAT) ÷ PV per unit margin", "7"],
       ["Two-stage DDM", "Σ DPS_t/(1+Ke)^t + [EPS₆ × (1 − g/ROE)]/(Ke − g)/(1+Ke)⁵", "7"],
       ["Implied price from multiple", "peer median multiple × company's own denominator ÷ shares", "8"],
       ["Controlled multiple", "P/B = a + b × ROE (cross-sectional regression, n = 8)", "8"]],
      [3.6, 11.0, 1.9], size=8)
OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print("saved", OUT)

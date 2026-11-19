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


n = 0
# 1 ------------------------------------------------------------------ title
n += 1
s = prs.slides.add_slide(BLANK); s.background.fill.solid(); s.background.fill.fore_color.rgb = rgb(BG)
rule(s, 0.6, 2.2, 0.9, ACC, 0.06)
tb(s, 0.6, 2.45, 11, 1.1, "Paying for the Future", 48, INK, HEAD, True)
tb(s, 0.6, 3.5, 11, 0.6, "Business analysis and valuation of DLF, Godrej Properties and Phoenix Mills", 20, ACC, BODY)
tb(s, 0.6, 5.4, 8, 1.0, ["ECON F355 · Business Analysis & Valuation · Prof. Mohit Kumar", "Group 27 · Saatvik Nagpal · Atharvaa Khanzode"], 13, MUTE)
for i, (k, c) in enumerate([("DLF", ACC), ("GPL", OCH), ("PML", RUST)]):
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(10.3 + i * 0.85), Inches(5.45), Inches(0.7), Inches(0.7))
    r.fill.solid(); r.fill.fore_color.rgb = rgb(c); r.line.fill.background(); r.shadow.inherit = False
    tb(s, 10.3 + i * 0.85, 6.2, 0.7, 0.3, k, 9, MUTE, BODY, True, PP_ALIGN.CENTER)
notes(s, "Good evening. We valued three Indian real-estate companies that represent the three business models in the sector: DLF, a luxury developer with a big rental joint venture; Godrej Properties, a fast-growing national developer; and Phoenix Mills, a mall owner. The title is the conclusion: investors are paying today for growth that is many years away.")

# 2 ------------------------------------------------------------------ question & workflow
n += 1
s = base("Scope · Module 1", "Three business models, one question: is the price justified by the cash?", n, "Index")
cards = [("DLF", ACC, "Luxury developer", f"Gurugram-focused; owns 66.66% of DCCDL rental JV (GIC 33.34%). Net cash.", f"Mcap ₹{N['RelVal'][0][3]/1000:,.0f}k cr"),
         ("Godrej Properties", OCH, "National developer", "Brand-led growth across MMR, NCR, Pune, Bengaluru; land + inventory build-up.", f"Mcap ₹{N['RelVal'][1][3]/1000:,.0f}k cr"),
         ("Phoenix Mills", RUST, "Mall-led annuity", "Dominant city malls; platforms with CPPIB and GIC; offices, hotels.", f"Mcap ₹{N['RelVal'][2][3]/1000:,.0f}k cr")]
for i, (nm, c, sub, desc, mc) in enumerate(cards):
    x = 0.6 + i * 4.1
    rule(s, x, 1.85, 3.85, c, 0.05)
    tb(s, x, 1.98, 3.85, 0.45, nm, 18, INK, HEAD, True)
    tb(s, x, 2.42, 3.85, 0.35, sub, 12, c, BODY, True)
    tb(s, x, 2.78, 3.85, 0.9, desc, 12, INK)
    tb(s, x, 3.62, 3.85, 0.35, mc, 11, MUTE, MONO)
steps = [("Data", "1"), ("Strategy", "2"), ("Accounting\nquality", "3"), ("Recast", "4"), ("Ratios ·\nDuPont · EVA", "5"),
         ("Beta ·\nWACC", "6"), ("DCF · DDM", "7"), ("Multiples", "8")]
for i, (t, m) in enumerate(steps):
    x = 0.6 + i * 1.53
    r = s.shapes.add_shape(MSO_SHAPE.CHEVRON if i else MSO_SHAPE.PENTAGON, Inches(x), Inches(4.35), Inches(1.5), Inches(0.95))
    r.fill.solid(); r.fill.fore_color.rgb = rgb("E4E8E6" if i % 2 else "D5DEDC"); r.line.fill.background(); r.shadow.inherit = False
    tb(s, x + 0.2, 4.43, 1.15, 0.8, t, 10.5, INK, BODY, True, PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    tb(s, x + 0.2, 5.35, 1.15, 0.3, f"Module {m}", 9, MUTE, BODY, False, PP_ALIGN.CENTER)
method(s, "8 companies × FY23–FY26 statements → 1 standard layout · 60 monthly + 156 weekly returns · G-Sec (FRED/OECD) · Damodaran Jan-2026 ERP/CRP/spreads · every output is a live Excel formula")
notes(s, "Our workflow follows the course modules left to right. We built one workbook where blue cells are sourced inputs and everything else is a formula, so any assumption can be changed live during Q&A. Data: four years of consolidated statements for our three firms plus five peers, five years of monthly prices, the 10-year G-Sec from FRED and Damodaran's January 2026 country-risk data.")

# 3 ------------------------------------------------------------------ strategy
n += 1
s = base("Module 2 · Strategy and competitive analysis", "RERA rewards brands that can pre-sell; malls reward location", n)
table(s, 0.6, 1.85, 6.4, [["Force", "Level", "Driver"],
                          ["Entry", "Low–mod", "Land, approvals, RERA capital"],
                          ["Suppliers", "High", "Landowners in prime micro-markets"],
                          ["Buyers", "Moderate", "Price-sensitive mid-income; not luxury"],
                          ["Substitutes", "Moderate", "Renting, resale; e-commerce for malls"],
                          ["Rivalry", "High ↓", "Fragmented but consolidating"]], [1.4, 1.1, 3.9], 11)
table(s, 7.3, 1.85, 5.43, [["Business unit", "BCG"],
                           ["DLF Gurugram luxury", "Star"], ["DLF DCCDL rental", "Cash cow"],
                           ["Godrej core 4 cities", "Star"], ["Godrej new cities", "Question mark"],
                           ["Phoenix malls", "Cash cow"], ["Phoenix offices", "Question mark"]], [3.6, 1.83], 11)
tb(s, 0.6, 4.25, 12, 1.8, [[("Generic strategy  ", True, ACC), ("DLF: focused differentiation (few, very large luxury launches).  Godrej: brand-led breadth.  Phoenix: location-based differentiation.", False, INK)],
                           [("SPACE  ", True, ACC), ("DLF aggressive (net cash, attractive industry) · Godrej competitive (strong position, weak cash flow) · Phoenix conservative–aggressive.", False, INK)],
                           [("Value chain  ", True, ACC), ("Developers create value at land, approvals and pre-sales; Phoenix at leasing and tenant mix → drives our sales-to-capital choice (2.0 vs 0.5).", False, INK)]], 12.5)
method(s, "Porter 5 forces · BCG by SBU (not by company) · SPACE quadrant · value chain → each conclusion is reused later as a DCF input")
notes(s, "Strategy matters for valuation through two channels. First, after RERA, buyers pay in instalments into escrow, so brands that can pre-sell get customer money as their cheapest financing — that becomes the customer-advances story. Second, the value chain tells us how much capital each rupee of growth needs: developers already carry land and inventory, malls must be built. That is why our sales-to-capital ratio is 2.0 for developers and 0.5 for Phoenix.")

# 4 ------------------------------------------------------------------ accounting
n += 1
s = base("Module 3 · Accounting analysis", "Four accounting rules make reported profit misleading here", n, "Recast, Ratios")
items = [("Ind AS 115", "Revenue only on completion", f"Godrej advances = {G['Customer advances / revenue (x)'][3]:.1f}× revenue"),
         ("Ind AS 23", "Interest capitalised into inventory", f"Godrej P&L cover {G['Interest coverage: EBIT / P&L finance cost (x)'][3]:.0f}× vs cash cover {G['Cash interest coverage: EBIT / interest paid (x)'][3]:.1f}×"),
         ("Ind AS 111", "JVs shown as one line", f"DLF: {pc(D['JV/associate share of PAT'][3],0)} of PAT is DCCDL share"),
         ("Ind AS 40", "Malls at depreciated cost", f"Phoenix P/B {N['RelVal'][2][13]:.1f}× — book value understated")]
for i, (k, a, b) in enumerate(items):
    y = 1.9 + i * 1.0
    tb(s, 0.6, y, 2.0, 0.5, k, 20, ACC, HEAD, True)
    tb(s, 2.7, y + 0.04, 4.6, 0.5, a, 15, INK)
    tb(s, 7.4, y + 0.04, 5.3, 0.5, b, 15, INK, BODY, True)
    rule(s, 0.6, y + 0.78, 12.13)
method(s, f"Red-flag screen: CFO/PAT, accruals ratio = (PAT − CFO)/avg assets, cash vs P&L interest · Godrej CFO/PAT = {G['CFO / PAT (x)'][3]:.2f} (growth-phase land buying, not manipulation)")
notes(s, "Before any ratio, we asked which accounting rules distort these companies. Revenue is recognised only when a project completes, so Godrej's customer advances are almost eight times its revenue. Interest is capitalised into inventory, so Godrej's P&L interest cover looks like 45 times, but on cash interest it is about 2 times — we use the cash figure for the credit rating. DLF's rental JV appears as a single line, yet it is 41% of profit. And Phoenix's malls are carried at cost, so its book value means little.")

# 5 ------------------------------------------------------------------ recast
n += 1
s = base("Module 4 · Recasting the statements", "Strip out treasury, exceptional and JV income — core profit looks very different", n, "Recast")
pic(s, "profit_mix", 0.6, 1.75, w=7.6)
tb(s, 8.5, 1.9, 4.2, 4.2, [[("DLF  ", True, ACC), (f"core NOPAT only ₹{D['RC NOPAT = core EBIT × (1 − t)'][3]:,.0f} cr; invested capital fell to ₹{D['RC Net operating assets = invested capital'][3]:,.0f} cr because customers fund construction.", False, INK)],
                           [("Godrej  ", True, OCH), (f"core EBIT ₹{G['RC Core operating EBIT'][3]:,.0f} cr — all FY26 profit came from treasury and exceptional items.", False, INK)],
                           [("Phoenix  ", True, RUST), (f"profit is genuinely operating; 21% leaks to minority partners.", False, INK)]], 13.5)
method(s, "Core EBIT = PBT + finance cost − interest income − exceptional items · NOPAT = core EBIT × (1 − 25.17%) · NOA = equity + MI + debt − liquid assets − JV investments · restricted (RERA) cash kept operating")
notes(s, "Recasting follows Palepu: separate operating, financing and non-operating items. The bars show FY26 profit split into core operations, the JV share, and treasury plus exceptional items. Godrej is the striking case: its core operations lost money after tax; reported profit came from interest income and one-off gains. That is not wrong accounting, it is timing — but it tells us valuation must rely on future project cash flows.")

# 6 ------------------------------------------------------------------ ratios
n += 1
s = base("Module 5 · Financial analysis", "Five-year inventory cycles are normal; who funds them is what matters", n, "Ratios")
pic(s, "re_signature", 0.6, 1.75, w=12.1)
tb(s, 0.6, 5.35, 12.1, 0.8, f"DLF is net cash (net debt/equity {D['Net debt / equity (x)'][3]:.2f}×) and CFO is {D['CFO / PAT (x)'][3]:.1f}× PAT; Godrej funds land with advances and debt (net debt/equity {G['Net debt / equity (x)'][3]:.2f}×, CFO negative every year); Phoenix converts {pc(P['CFO / revenue'][3],0)} of revenue into operating cash.", 13)
method(s, "38 ratios × 4 years × 3 firms, average balances where flow ÷ stock · inventory days on cost of revenue · advances = CL − current debt − payables")
notes(s, "We computed 38 ratios. Three tell the real-estate story. Inventory days of 1,800 to 5,600 would be alarming elsewhere but are normal for land plus construction. Customer advances relative to revenue show who funds that inventory. And cash flow over profit shows the outcome: DLF and Phoenix generate more cash than profit; Godrej is still burning cash as it buys land.")

# 7 ------------------------------------------------------------------ dupont
n += 1
s = base("Module 5 · DuPont, Palepu split, EVA", "Similar ROE (~10%), three different engines — and none beats its cost of equity", n, "DuPont, Growth_EVA")
pic(s, "dupont", 0.6, 1.72, w=12.1)
table(s, 0.6, 5.05, 12.13, [["FY26", "ROE", "RNOA (operating)", "Non-operating part", "JV & tax burden", "EVA (₹ cr)"],
                            ["DLF", pc(D['DP ROE (3-step product)'][2]), pc(D['DP Return on net operating assets (RNOA)'][2]), pc(D['DP Non-operating (JV, exceptional) contribution'][2]), f"{D['DP Tax & JV burden'][2]:.2f}", f"{D['EVA = NOPAT − WACC × opening NOA'][2]:,.0f}"],
                            ["Godrej", pc(G['DP ROE (3-step product)'][2]), pc(G['DP Return on net operating assets (RNOA)'][2]), pc(G['DP Non-operating (JV, exceptional) contribution'][2]), f"{G['DP Tax & JV burden'][2]:.2f}", f"{G['EVA = NOPAT − WACC × opening NOA'][2]:,.0f}"],
                            ["Phoenix", pc(P['DP ROE (3-step product)'][2]), pc(P['DP Return on net operating assets (RNOA)'][2]), pc(P['DP Non-operating (JV, exceptional) contribution'][2]), f"{P['DP Tax & JV burden'][2]:.2f}", f"{P['EVA = NOPAT − WACC × opening NOA'][2]:,.0f}"]],
      [1.6, 1.7, 2.3, 2.4, 2.1, 2.03], 11, 0.28)
method(s, "ROE = NPM × ATO × EM  →  5-step adds tax/JV and interest burden  →  Palepu: ROE = RNOA + (RNOA − NBC) × NFL  ·  EVA = NOPAT − WACC × opening NOA", y=6.32, h=0.55)
notes(s, "All three earn about 10 to 11 percent ROE but in different ways: DLF through very high margins, Godrej through leverage, Phoenix through turnover. The five-step version shows DLF's tax-and-JV burden above 1, because JV profit enters below tax. The Palepu split shows almost all of Godrej's ROE is non-operating. EVA is negative for all three: on current accounting returns, none earns its cost of capital — so today's value rests on future projects.")

# 8 ------------------------------------------------------------------ beta
n += 1
s = base("Module 6 · Hurdle rate", "Betas of 1.1–2.2; bottom-up median of eight developers cuts the noise", n, "Beta_Monthly, BottomUp_Beta, WACC")
pic(s, "beta_scatter", 0.6, 1.72, w=7.4)
pic(s, "bottomup_beta", 0.6, 4.05, w=5.6)
table(s, 8.3, 1.85, 4.43, [["", "DLF", "GPL", "PML"],
                           ["Beta used", f"{D['W Beta used']:.2f}", f"{G['W Beta used']:.2f}", f"{P['W Beta used']:.2f}"],
                           ["Ke", pc(D['W Cost of equity (CAPM)']), pc(G['W Cost of equity (CAPM)']), pc(P['W Cost of equity (CAPM)'])],
                           ["Rating", D['W Synthetic rating'], G['W Synthetic rating'], P['W Synthetic rating']],
                           ["Kd pre-tax", pc(D['W Pre-tax Kd used']), pc(G['W Pre-tax Kd used']), pc(P['W Pre-tax Kd used'])],
                           ["D/V", pc(D['W D / V']), pc(G['W D / V']), pc(P['W D / V'])],
                           ["WACC", pc(D['W WACC']), pc(G['W WACC']), pc(P['W WACC'])]], [1.35, 1.03, 1.03, 1.02], 11, 0.32)
tb(s, 6.5, 4.4, 6.2, 1.7, [f"Rf = G-Sec {pc(I['India 10-yr G-Sec yield'],2)} − default spread {pc(I['India sovereign default spread (Baa3)'],2)} = {pc(I['Rupee risk-free rate = G-Sec − default spread'],2)}",
                           f"ERP = mature {pc(I['Mature market ERP'],2)} + India CRP {pc(I['India country risk premium (CRP)'],2)} = {pc(I['India total ERP = mature ERP + CRP'],2)}",
                           "Phoenix uses own Blume β: REIT betas had R² < 12%"], 12)
method(s, "β = SLOPE(R_i, R_Nifty) · SE, t-stat, 95% CI, R² · Blume 0.67β+0.33 · Hamada unlever at market D/E → median → relever · Kd from cash interest cover → Damodaran synthetic rating")
notes(s, "We estimated regression betas on 60 monthly returns and checked them on 156 weekly returns. Godrej's confidence interval is wide, so we used the bottom-up method: unlever eight developers, take the median of 1.41, relever at each firm's debt. For Phoenix, a rental business, developer betas are wrong; we tested India's REITs, but their R-squared is under 12 percent, so we used Phoenix's own Blume-adjusted beta. The risk-free rate removes India's default spread from the G-Sec, and the ERP adds the country risk premium.")

# 9 ------------------------------------------------------------------ DCF design
n += 1
s = base("Module 7 · Intrinsic valuation — design", "Growth must be paid for: reinvestment = Δrevenue ÷ sales-to-capital", n, "DCF_DLF, DCF_GPL, DCF_PML")
pic(s, "dcf_paths", 0.6, 1.72, w=12.1)
table(s, 0.6, 4.85, 12.13, [["Assumption", "DLF", "Godrej", "Phoenix"],
                            ["Growth FY27–31 (then fades to 5.5%)", " · ".join(pc(g, 0) for g in D['DCF growth']), " · ".join(pc(g, 0) for g in G['DCF growth']), " · ".join(pc(g, 0) for g in P['DCF growth'])],
                            ["Core EBIT margin FY26 → target", f"{pc(D['Core EBIT margin'][3],0)} → {pc(D['DCF margin'],0)}", f"{pc(G['Core EBIT margin'][3],0)} → {pc(G['DCF margin'],0)}", f"{pc(P['Core EBIT margin'][3],0)} → {pc(P['DCF margin'],0)}"],
                            ["Sales-to-capital · WACC → stable (β→1)", f"{D['DCF s2c']:.1f} · {pc(D['W WACC'])} → {pc(D['DCF stableWACC'])}", f"{G['DCF s2c']:.1f} · {pc(G['W WACC'])} → {pc(G['DCF stableWACC'])}", f"{P['DCF s2c']:.1f} · {pc(P['W WACC'])} → {pc(P['DCF stableWACC'])}"]],
      [3.8, 2.8, 2.8, 2.73], 11, 0.3)
method(s, "10 years: 5 explicit + 5 fade · FCFF = NOPAT − reinvestment · terminal reinvestment = g/RONIC · beta → 1 in stable phase · mid-year discounting", y=6.25)
notes(s, "Our DCF corrects the most common error in past projects: growing cash flows without paying for growth. Reinvestment equals the change in revenue divided by sales-to-capital, and in the terminal year g over return on new capital. Growth for the developers comes from bookings already made but not yet recognised. After year five, growth fades to 5.5 percent and beta moves to 1, so the discount rate falls to a stable level.")

# 10 ----------------------------------------------------------------- DCF result
n += 1
s = base("Module 7 · Results, sensitivity, reverse DCF", "No sensible input reaches today's price — the market is discounting at ~8–12%", n, "DCF_* (grids, reverse DCF), DDM")
table(s, 0.6, 1.85, 6.3, [["₹ per share", "DLF", "Godrej", "Phoenix"],
                          ["DCF value", rs(D['DCF']['Intrinsic value per share (Rs)']), rs(G['DCF']['Intrinsic value per share (Rs)']), rs(P['DCF']['Intrinsic value per share (Rs)'])],
                          ["WACC ±2%, g ±1%", f"{rs(D['gridA_min'])}–{D['gridA_max']:,.0f}", f"{rs(G['gridA_min'])}–{G['gridA_max']:,.0f}", f"{rs(P['gridA_min'])}–{P['gridA_max']:,.0f}"],
                          ["DDM", rs(D['DDM']['DDM value per share (Rs)']), "n.a.", rs(P['DDM']['DDM value per share (Rs)'])],
                          ["Market price", rs(D['DCF']['Current market price (Rs)']), rs(G['DCF']['Current market price (Rs)']), rs(P['DCF']['Current market price (Rs)'])],
                          ["TV % of value", pc(D['DCF']['Terminal value as % of operating value'],0), pc(G['DCF']['Terminal value as % of operating value'],0), pc(P['DCF']['Terminal value as % of operating value'],0)],
                          ["Implied margin", pc(D['implied margin'],0), pc(G['implied margin'],0), pc(P['implied margin'],0)]], [1.9, 1.45, 1.45, 1.5], 11.5, 0.36)
pp = pic(s, "implied_wacc", 7.1, 1.75, w=5.6)
tb(s, 7.1, below(pp), 5.6, 1.4, "Value is linear in the target margin, so the reverse DCF is solved exactly. Required margins above 100% are impossible → the gap is the discount rate, not profitability.", 12, INK)
method(s, "Grid A: WACC shift × g (explicit compounding per cell) · Grid B: margin × S/C · reverse DCF: margin = (firm value implied by price + PV reinvestment − PV base NOPAT) ÷ PV per unit margin · DCCDL stake = JV PAT×(1+g)/(Ke−g)")
notes(s, "Our base values are well below price. The sensitivity grids show no reasonable WACC or growth closes the gap. So we reversed the model. First we solved for the margin the price needs: above 100 percent for DLF and Phoenix — impossible. Then we solved for the discount rate: the market is effectively using about 11 percent for DLF, 12 for Godrej and under 8 for Phoenix, close to the government bond yield. The DDM is even lower because these firms reinvest most earnings; Godrej pays no dividend, so DDM does not apply.")

# 11 ----------------------------------------------------------------- relative
n += 1
s = base("Module 8 · Relative valuation", "Against peers, Godrej is cheapest and Phoenix is the most expensive", n, "RelVal")
rows = [["", "P/E", "P/B", "EV/EBITDA", "ROE"]]
for r in N["RelVal"]:
    rows.append([r[0].replace(" Ltd", "").replace(" (Macrotech)", ""), f"{r[12]:.1f}", f"{r[13]:.2f}", f"{r[15]:.1f}", pc(r[11])])
med = N["RelStats"]["Median"]
rows.append(["Peer median", f"{med[0]:.1f}", f"{med[1]:.2f}", f"{med[3]:.1f}", ""])
table(s, 0.6, 1.8, 6.0, rows, [2.2, 0.9, 0.9, 1.1, 0.9], 11, 0.37)
pp = pic(s, "pb_roe", 6.9, 1.72, h=3.2)
reg = N["Reg"]
tb(s, 6.9, below(pp), 5.8, 1.1, f"Step 4 controls for profitability: R² is only {reg['r2']:.2f} — cost-based book values (Phoenix) and land banks break the P/B–ROE link, so the regression is a cross-check, not the anchor.", 12)
method(s, "Four steps: comparables → standardise (FY26, same price date) → distribution (median, IQR; Sobha P/E > 70x skews mean) → control for differences (P/B = a + b·ROE, n = 8)")
notes(s, "Relative valuation follows the four steps from Damodaran. Godrej trades at about 31 times earnings and 3 times book, below the peer medians of 35 and 3.7. DLF is inside the peer range. Phoenix is the most expensive on every multiple. When we control for ROE, the regression explains little — Phoenix's malls are at historical cost, so its book value is understated — so we use it only as a check.")

# 12 ----------------------------------------------------------------- synthesis
n += 1
s = base("Synthesis · Modules 7–8", "The sector is priced for growth; within it, Godrej > DLF > Phoenix", n, "Summary")
pp = pic(s, "football_field", 0.6, 1.72, h=3.6)
ri = N["RelImplied"]
tb(s, 0.6, below(pp), 12.1, 0.8, [[("Godrej · relatively undervalued  ", True, OCH), (f"peer P/E implies {rs(ri['Godrej Properties'][0])} vs {rs(G['DCF']['Current market price (Rs)'])}; risk = cash burn.   ", False, INK),
                             ("DLF · fair vs peers, rich intrinsically  ", True, ACC), ("strongest balance sheet.   ", False, INK),
                             ("Phoenix · richly valued  ", True, RUST), ("quality annuity, priced like a bond.", False, INK)]], 12.5)
method(s, "Relative value cannot see a sector-wide premium; intrinsic value can · triangulate: DCF range, P/E and P/B IQR, EV/EBITDA, P/B–ROE, DDM, market price", y=6.3, h=0.55)
notes(s, "Putting it together. Intrinsic and relative value disagree, and that disagreement is the finding: relative valuation compares each stock with peers that are also expensive, so it cannot detect a sector-wide premium. Within the sector, Godrej is the relatively cheapest but carries execution and cash risk; DLF is fairly valued against peers with the best balance sheet; Phoenix is a high-quality business whose price already assumes many years of rental growth.")

# 13 ----------------------------------------------------------------- limitations
n += 1
s = base("Limitations · CLO3", "What would change our answer", n)
tb(s, 0.6, 1.9, 6.0, 4.2, [[("Data  ", True, ACC), ("four years from one aggregated source; bookings, land bank and occupancy sit in investor presentations, not statements.", False, INK)],
                           [("Method  ", True, ACC), ("NAV / sum-of-parts would value land banks directly; land banks also behave like real options (contingent-claim view).", False, INK)],
                           [("Estimation  ", True, ACC), (f"Godrej beta 95% CI {N['Beta_Monthly']['Godrej Propert']['95% CI low']:.2f}–{N['Beta_Monthly']['Godrej Propert']['95% CI high']:.2f}; one SE moves Ke ~{N['Beta_Monthly']['Godrej Propert']['Std error of beta']*I['India total ERP = mature ERP + CRP']*100:.1f} pp.", False, INK)],
                           [("Accounting  ", True, ACC), ("cost-based investment property and capitalised interest limit P/B and ROE comparisons.", False, INK)]], 14)
tb(s, 7.1, 1.9, 5.6, 3.6, [[("Next steps", True, INK)], "Reconcile key lines to annual reports", "Add a NAV model from project-level disclosures",
                           "Value DCCDL with its own cash flows", "Track bookings vs revenue each quarter"], 14)
tb(s, 7.1, 5.3, 5.6, 0.6, "Thank you — questions welcome.", 18, ACC, HEAD, True)
notes(s, "Finally, the limits. Our data does not include bookings, land bank or occupancy, which a NAV model would use. Land banks also act like options — the right to develop when prices are favourable — which may explain part of the premium. Beta estimates are noisy. With more time we would reconcile key numbers to annual reports and build a NAV model. Thank you.")

prs.save(OUT)
print("saved", OUT, "slides:", n)

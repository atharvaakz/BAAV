"""Presentation v3 — a guided walk-through of the project.

Structure (see docs/PRESENTATION_DESIGN_BRIEF.md): question (SCQA) → road map → hypotheses → six steps, each slide
= one sentence title (the finding) + one chart (the evidence) + a read-aloud panel (what we did / what we found) →
conclusion → limits. Detailed tables sit in a backup section for questions. Every number comes from the model.
"""
import pathlib
exec(open(pathlib.Path(__file__).resolve().parent / "deck_common.py").read())
MC, SC = N["MC"], N["SC"]; imp, scn = SC["implied"], SC["scenarios"]
RV = {r[0]: r for r in N["RelVal"]}; med = N["RelStats"]["Median"]
CAP, LC, RB, RF, HS, IB = N["Cap"], N["LongCycle"], N["RollingBeta"], N["RateFactor"], N["Housing"], N["Industry"]
E, IV, LQ, NAV, DLY = N["EV"], N["IVC"], N["LITQ"], N["NAV"], N["Delay"]
price = {c: N[c]["DCF"]["Current market price (Rs)"] for c in ("DLF", "GPL", "PML")}
vA = {c: N[c]["DCF"]["Intrinsic value per share (Rs)"] for c in ("DLF", "GPL", "PML")}
vB = {c: N[c]["lensB"]["vps"] for c in ("DLF", "GPL", "PML")}
BKMED = {r[0]: r[1] for r in N["Brokers"] if r[0] in ("DLF Ltd", "Godrej Properties", "Phoenix Mills")}
COL = {"DLF": NAVY, "GPL": ACC, "PML": RUST}
cr = lambda x: f"₹{x:,.0f} cr"
GLO = min(imp[c]["terminal_g"] for c in ("DLF", "GPL", "PML")); GHI = max(imp[c]["terminal_g"] for c in ("DLF", "GPL", "PML"))
OUT = ROOT / "reports/ProjectBaav_Group27_Presentation.pptx"
from pptx.oxml.ns import qn as _qn
from lxml import etree as _et

STEPS = [("01", "Understand the business"), ("02", "Clean the accounts"), ("03", "Measure performance"),
         ("04", "Set the hurdle rate"), ("05", "Value it three ways"), ("06", "Test it through time")]
GRID_X, GRID_W = 0.6, 12.13


def bar(s, x, y, w, h, color):
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    r.fill.solid(); r.fill.fore_color.rgb = rgb(color); r.line.fill.background(); r.shadow.inherit = False
    return r


def tracker(s, cur):
    """Signposting, Swiss style: six numbered labels on a hairline; the current step carries the signal colour."""
    w = GRID_W / 6
    bar(s, GRID_X, 0.62, GRID_W, 0.008, RULE)
    for i, (k, lab) in enumerate(STEPS):
        on, done = (i + 1) == cur, (i + 1) < cur
        x = GRID_X + i * w
        if on:
            bar(s, x, 0.585, w - 0.08, 0.05, ACC)
        tb(s, x, 0.3, 0.42, 0.26, k, 9, ACC if on else (INK if done else "A7ABB0"), MONO, on)
        tb(s, x + 0.36, 0.3, w - 0.45, 0.26, lab, 9, INK if (on or done) else "A7ABB0", BODY, on)


def slide(title, cur=None, sheet=None, kicker=None):
    s = prs.slides.add_slide(BLANK)
    bg = s.background.fill; bg.solid(); bg.fore_color.rgb = rgb(BG)
    if cur:
        tracker(s, cur)
    elif kicker:
        tb(s, GRID_X, 0.3, 9, 0.3, kicker, 10, ACC, MONO, False)
        bar(s, GRID_X, 0.62, GRID_W, 0.008, RULE)
    tb(s, GRID_X, 0.78, 12.1, 0.9, title, 25 if len(title) <= 58 else (22 if len(title) <= 70 else 20), INK, HEAD, False)
    num = len(prs.slides)
    bar(s, GRID_X, 7.0, GRID_W, 0.008, RULE)
    tb(s, 12.13, 7.06, 0.6, 0.3, f"{num:02d}", 9, INK, MONO, align=PP_ALIGN.RIGHT)
    if sheet:
        tb(s, GRID_X, 7.06, 10, 0.3, f"Workbook / {sheet}", 8.5, MUTE, MONO)
    return s


def story(s, did, found, sowhat=None, x=9.05, y=1.75, w=3.68, h=4.6):
    """Read-aloud column: no box — a vertical hairline separates it from the evidence, labels are numbered."""
    bar(s, x - 0.22, y, 0.008, h, INK)
    blocks = [("What we did", did, MUTE), ("What we found", found, INK)] + ([("So what", sowhat, ACC)] if sowhat else [])
    import math
    def need(txt, fs):
        cpl = (w - 0.1) * 72 / (fs * 0.52)
        return 0.3 + math.ceil(len(txt) / cpl) * fs * 1.3 / 72 + 0.14
    fs = 13.5
    while sum(need(tx, fs) for _, tx, _ in blocks) > h and fs > 11:
        fs -= 0.5
    yy = y
    for i, (lab, txt, c) in enumerate(blocks):
        hh = need(txt, fs)
        tb(s, x, yy, w, 0.26, [[(f"{i + 1:02d}  ", False, ACC), (lab, True, INK)]], 10, INK, MONO)
        tb(s, x, yy + 0.3, w, hh - 0.3, txt, fs, INK if c != ACC else ACC, BODY, c == ACC)
        yy += hh


def source(s, text, y=6.55):
    tb(s, GRID_X, y, 12.1, 0.4, text, 8.5, MUTE, BODY)


def leftalign(tbl):
    for _r in tbl.rows:
        for _c in _r.cells:
            _c.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT


def card(s, x, y, w, h, big, small, color=ACC, bigsize=26):
    bar(s, x, y, w, 0.02, INK)
    tb(s, x, y + 0.08, w, h * 0.5, big, bigsize, color, HEAD)
    tb(s, x, y + h * 0.55, w, h * 0.45, small, 11, INK)


# ---------- diagram primitives: boxes, arrows, mind maps ----------
def box(s, x, y, w, h, text, fill="FFFFFF", line=INK, color=INK, size=11, bold=False, font=None, lw=0.75):
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill:
        r.fill.solid(); r.fill.fore_color.rgb = rgb(fill)
    else:
        r.fill.background()
    if line:
        r.line.color.rgb = rgb(line); r.line.width = Pt(lw)
    else:
        r.line.fill.background()
    r.shadow.inherit = False
    tf = r.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.06); tf.margin_top = tf.margin_bottom = Inches(0.03)
    lines = text if isinstance(text, list) else [text]
    for i, ln in enumerate(lines):
        p_ = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p_.alignment = PP_ALIGN.CENTER
        r_ = p_.add_run(); r_.text = ln; r_.font.size = Pt(size if i == 0 else size - 1.5); r_.font.name = font or (HEAD if (bold and i == 0) else BODY)
        r_.font.color.rgb = rgb(color if i == 0 else (MUTE if color == INK else color))
    return r


def arrow(s, x1, y1, x2, y2, color=INK, w=1.0):
    c = s.shapes.add_connector(1, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = rgb(color); c.line.width = Pt(w)
    ln = c.line._get_or_add_ln()
    tail = _et.SubElement(ln, _qn("a:tailEnd")); tail.set("type", "triangle"); tail.set("w", "med"); tail.set("len", "med")
    return c


def flow(s, x, y, w, h, items, gap=0.32, hi=None, size=10.5):
    """Left-to-right flowchart strip: equal boxes joined by arrows; item `hi` carries the signal colour."""
    n = len(items); bw = (w - gap * (n - 1)) / n
    for i, it in enumerate(items):
        bx = x + i * (bw + gap)
        on = hi is not None and (i == hi or (isinstance(hi, (list, tuple)) and i in hi))
        box(s, bx, y, bw, h, it, fill=(ACC if on else "FFFFFF"), line=(ACC if on else INK), color=("FFFFFF" if on else INK), size=size, bold=True)
        if i < n - 1:
            arrow(s, bx + bw + 0.03, y + h / 2, bx + bw + gap - 0.03, y + h / 2)


# ===================================================================== 1 TITLE  (Swiss: big flush-left type, grid, one signal colour)
s = prs.slides.add_slide(BLANK); s.background.fill.solid(); s.background.fill.fore_color.rgb = rgb(BG)
tb(s, GRID_X, 0.5, 6, 0.3, "ECON F355  /  Business Analysis & Valuation", 10, INK, MONO)
tb(s, 7.0, 0.5, 5.73, 0.3, "Group 27  /  October 2026", 10, INK, MONO, align=PP_ALIGN.RIGHT)
bar(s, GRID_X, 0.86, GRID_W, 0.012, INK)
bar(s, GRID_X, 2.05, 0.42, 0.42, ACC)
tb(s, GRID_X, 2.6, 12, 1.4, "Paying for", 64, INK, HEAD)
tb(s, GRID_X, 3.65, 12, 1.4, "the Future", 64, INK, HEAD)
tb(s, GRID_X, 4.95, 8.5, 0.8, "What the market is pricing into DLF, Godrej Properties and Phoenix Mills", 20, INK, SERIF)
bar(s, GRID_X, 6.25, GRID_W, 0.008, INK)
tb(s, GRID_X, 6.38, 6, 0.6, ["Saatvik Nagpal  ·  Atharvaa Khanzode", "Prof. Mohit Kumar  ·  BITS Pilani, K K Birla Goa Campus"], 11, INK, BODY)
for i, (k, nm) in enumerate([("DLF", "DLF"), ("GPL", "Godrej"), ("PML", "Phoenix")]):
    x = 9.3 + i * 1.15
    bar(s, x, 6.42, 0.18, 0.18, COL[k]); tb(s, x + 0.25, 6.38, 0.9, 0.3, nm, 10, INK, BODY)
notes(s, "Good evening. We valued three Indian real-estate companies that represent the sector's three business models: DLF, which sells luxury homes and owns offices; "
         "Godrej Properties, which builds housing across many cities; and Phoenix Mills, which owns and runs malls. Over the next ten minutes we will walk you through "
         "the question we asked, how we went about answering it, and what we concluded.")

# ===================================================================== 2 THE QUESTION (SCQA)
s = slide("The question we set out to answer", kicker="00 / Where we started", sheet="Summary")
pe = {k: RV[n_][12] for k, n_ in [("DLF", "DLF Ltd"), ("GPL", "Godrej Properties"), ("PML", "Phoenix Mills")]}
BLK = [("Situation", "Real estate is one of India's largest sectors. We chose one company for each business model: luxury homes and offices (DLF), "
                     "housing across many cities (Godrej) and shopping malls (Phoenix)."),
       ("Complication", f"The shares trade at {pe['DLF']:.0f}, {pe['GPL']:.0f} and {pe['PML']:.0f} times earnings, well above the market. Yet developers book revenue only "
                        "when a project is finished, so their reported profits lag their sales by years."),
       ("Question", "Can today's share prices be justified by the cash these businesses will generate? And if not, what does an investor have to believe to pay them?"),
       ("Our short answer", f"The prices assume all three grow with India's economy for ever, about {GLO:.0%}–{GHI:.0%} a year. "
                            "Godrej is the cheapest of the three; Phoenix is the most fully priced.")]
for i, (lab, txt) in enumerate(BLK):
    x = GRID_X + i * 3.06
    last = i == 3
    bar(s, x, 1.9, 2.86, 0.03 if not last else 0.08, ACC if last else INK)
    tb(s, x, 2.05, 2.86, 0.3, [[(f"{chr(65 + i)}  ", False, ACC), (lab, True, INK)]], 12, INK, MONO)
    tb(s, x, 2.5, 2.8, 3.5, txt, 15, ACC if last else INK, BODY, last)
    if i < 3:
        arrow(s, x + 2.88, 2.12, x + 3.04, 2.12, MUTE, 0.75)
source(s, "Structure: situation, complication, question, answer (Minto). Multiples from the RelVal sheet; implied growth from the reverse DCF.")
notes(s, "We framed the project as one question. These companies trade at very high multiples of earnings, but their accounting makes earnings look small because revenue arrives only on completion. "
         "So we asked whether the cash these businesses will generate can justify today's prices, and if not, what you have to believe to pay them. "
         "Our short answer is on the right: the prices only work if the companies grow with the Indian economy for ever. We will now show how we got there.")

# ===================================================================== 2b MIND MAP — what drives value in this sector
s = slide("What drives value in Indian real estate: the map we worked from", kicker="00 / The landscape", sheet="Concept_Map")
cx, cy, cw, ch = 5.17, 3.55, 3.0, 1.0
box(s, cx, cy, cw, ch, ["Equity value", "of a developer or landlord"], fill=INK, line=INK, color="FFFFFF", size=16, bold=True)
NODES = [("Land bank", "bought years ago, held at cost", 0.6, 1.85), ("Pre-sales & advances", "customers fund construction", 4.67, 1.85),
         ("Rental assets", "offices and malls, valued on yield", 8.73, 1.85),
         ("Cost of capital", "beta, bond yield, risk premium", 0.6, 5.35), ("Regulation (RERA)", "escrow, disclosure, delivery", 4.67, 5.35),
         ("Cycle & credit", "rates, NBFC funding, demand", 8.73, 5.35)]
for lab, sub, x, y in NODES:
    box(s, x, y, 4.0, 0.95, [lab, sub], fill="FFFFFF", line=INK, size=14, bold=True)
    nx, ny = x + 2.0, (y + 0.95 if y < cy else y)
    tx, ty = cx + cw / 2 + (nx - (cx + cw / 2)) * 0.35, (cy if y < cy else cy + ch)
    arrow(s, nx, ny, tx, ty, ACC, 1.25)
tb(s, 0.6, 3.6, 4.2, 0.9, "Each branch is tested in one of our six steps.", 12, MUTE, SERIF)
tb(s, 8.6, 3.6, 4.1, 0.9, "Accounting hides three of them: land, advances and rental assets.", 12, MUTE, SERIF, align=PP_ALIGN.RIGHT)
notes(s, "Before modelling, we mapped what drives value in this sector. Six things matter: the land bank, which sits in the books at old cost; pre-sales and customer advances, which fund construction; "
         "rental assets such as offices and malls, valued on their yield; the cost of capital; regulation, especially RERA's escrow and disclosure rules; and the property and credit cycle. "
         "The accounts hide three of these, which is why cleaning the accounts was such an important step.")

# ===================================================================== 3 HOW WE WENT ABOUT IT  (numbered flowchart)
s = slide("How we went about it: six steps, following the course", kicker="00 / Our approach", sheet="Index, Concept_Map")
DESC = ["Twenty years of prices, industry data, strategy (Porter, BCG, SWOT)", "Recast statements: separate operating profit from JV, treasury and one-off income",
        "Ratios, DuPont, EVA and distress scores against peers and the industry", "Cost of capital: betas, risk-free rate and equity risk premium, two versions",
        "DCF, relative multiples, and the practitioner's NAV method", "Event studies, survivors vs failures, company filings and guidance"]
MODS = ["Module 2", "Modules 3–4", "Module 5", "Module 6", "Modules 7–8", "Extension"]
bw, gap = 1.75, 0.326
for i, ((k, lab), d, m) in enumerate(zip(STEPS, DESC, MODS)):
    x = GRID_X + i * (bw + gap)
    tb(s, x, 1.85, bw, 0.6, k, 30, ACC, MONO)
    box(s, x, 2.55, bw, 0.95, lab, fill=INK if i == 4 else "FFFFFF", line=INK, color="FFFFFF" if i == 4 else INK, size=12.5, bold=True)
    if i < 5:
        arrow(s, x + bw + 0.03, 3.02, x + bw + gap - 0.03, 3.02)
    tb(s, x, 3.65, bw, 1.4, d, 11.5, INK)
    tb(s, x, 4.95, bw, 0.3, m, 9.5, MUTE, MONO)
bar(s, GRID_X, 5.45, GRID_W, 0.008, INK)
tb(s, GRID_X, 5.55, 12.1, 0.9, [[("Before building anything, we wrote down twelve hypotheses ", True, ACC),
                             ("about how these companies are priced, so the analysis could prove us wrong. We collected statements for 13 developers, prices back to 2007 "
                              "and house prices back to 2009, and checked our data against the companies' audited annual reports.", False, INK)]], 13.5)
notes(s, "This is our road map, and the strip at the top of each following slide shows where we are on it. We followed the order of the course: understand the business, clean up the accounts, "
         "measure performance, set the hurdle rate, value the companies three different ways, and finally test our conclusions against what has actually happened in the market over time. "
         "Before modelling we wrote down twelve hypotheses, so the analysis could prove us wrong rather than simply confirm what we expected.")

# ===================================================================== 4 HYPOTHESES
s = slide("What we expected before we started, and what the data said", kicker="00 / Hypotheses", sheet="Index")
GROUPS = [("How the price is set", [("H1", "Prices embed growth beyond a normal long-run rate", "Supported"), ("H7", "Book value understates the real capital", "Supported"),
                                    ("H8", "Phoenix is priced for growth, not yield", "Supported"), ("H9", "Brokers reach the price only with land and growth premia", "Supported")]),
          ("Risk", [("H2", "Big developers are riskier than the industry average", "Supported"), ("H3", "Beta changes through the cycle", "Supported"),
                    ("H4", "Rising interest rates hurt developers", "Weak")]),
          ("How the business works", [("H5", "Realty shares follow house prices", "Rejected"), ("H6", "Customer advances fund growth", "Supported (DLF)")]),
          ("How the market reacts", [("H10", "Deals and launches move prices; profit surprises do not", "Supported"), ("H11", "Shocks pass; failed delivery is permanent", "Supported"),
                                     ("H12", "Companies sell new shares after price run-ups", "Supported")])]
x0, y0 = 0.6, 1.75
cols = [(0.6, GROUPS[0]), (0.6, GROUPS[1]), (6.75, GROUPS[2]), (6.75, GROUPS[3])]
yy = {0.6: 1.75, 6.75: 1.75}
for x, (g, items) in cols:
    y = yy[x]
    bar(s, x, y, 5.9, 0.02, INK); tb(s, x, y + 0.06, 5.9, 0.3, g, 11, INK, HEAD); y += 0.42
    for h, t, res in items:
        clr = {"Supported": INK, "Rejected": ACC, "Weak": MUTE}.get(res.split(" ")[0], INK)
        mk = bar(s, x, y + 0.1, 0.14, 0.14, clr)
        if res.startswith("Weak"):
            mk.fill.background(); mk.line.color.rgb = rgb(MUTE)
        tb(s, x + 0.25, y, 0.6, 0.35, h, 12, INK, MONO); tb(s, x + 0.85, y + 0.02, 3.75, 0.5, t, 12, INK)
        tb(s, x + 4.7, y + 0.02, 1.3, 0.35, res, 11, clr, BODY, res.startswith("Rejected")); y += 0.5
    yy[x] = y + 0.12
source(s, "■ supported   □ weak   ■ rejected (in red). Ten supported, one weak, one rejected; the evidence for each is on the step slides that follow and in the report (section 1).", y=6.55)
notes(s, "These are the twelve hypotheses, grouped by theme. Ten held up, one had only weak support, and one was rejected: we expected realty shares to follow house prices, and they do not. "
         "We will point to the evidence for each as we go through the steps.")

# ===================================================================== 5 STEP 1 — BUSINESS AND CYCLE
s = slide(f"Step 1: this is a boom-and-bust sector; DLF is still below its 2008 peak", 1, "LongCycle, Housing, Industry_Data")
pic(s, "long_cycle", 0.6, 1.7, w=8.05)
story(s, "We collected share prices back to 2007, house prices back to 2009 and housing sales for India's top seven cities, and mapped each company's strategy.",
      f"Share prices swing far more than house prices. DLF has returned only {pc(LC['DLF'][2])} a year since its 2007 listing, and Phoenix fell 90% in 2008. "
      f"House prices grew {pc(HS['Real house-price CAGR'])} a year after inflation, and the shares do not track them (H5 rejected).",
      "Any valuation has to allow for the cycle; recent years flatter the sector.")
source(s, "Dividend-adjusted monthly prices; BIS house-price indices; ANAROCK housing data. Strategy tables (Porter, BCG, SWOT) are in the backup section and report section 2.")
notes(s, "Step one was to understand the business and the cycle. We went back as far as the data allowed. The picture is a sector of booms and busts: DLF listed at the top of the 2007 boom "
         "and is still below that peak nineteen years later. House prices, by contrast, grew slowly and steadily, and the shares do not move with them, so we rejected our fifth hypothesis. Alongside the numbers we applied the strategy frameworks from the course: Porter's five forces, BCG by business unit and a SWOT for each firm. The key point was that after RERA, buyers pay in instalments into escrow, so brands that buyers trust get cheap financing from their customers.")

# ===================================================================== 6 STEP 2 — ACCOUNTS
s = slide("Step 2: once we strip out one-offs, core profit looks very different", 2, "Recast, Quarterly")
flow(s, GRID_X, 1.8, 8.0, 0.72, ["Reported profit", "less treasury income", "less one-off gains", "less JV share", "Core operating profit"], gap=0.28, hi=4, size=10.5)
pic(s, "profit_mix", 0.9, 2.75, h=3.65)
story(s, "We rebuilt each income statement and balance sheet, separating operating profit from joint-venture income, interest earned on cash and one-off gains.",
      f"Godrej's core operations lost money in FY26; its profit came from treasury income and one-off gains. About {pc(D['JV/associate share of PAT'][3],0)} of DLF's profit is its share of "
      "the office joint venture. Only Phoenix's profit is mostly operating.",
      "We value the operating business and the joint venture separately, so nothing is counted twice.")
source(s, "Accounting rules behind this: revenue on completion (Ind AS 115), interest added to inventory (Ind AS 23), JVs as one line (Ind AS 111), property at cost (Ind AS 40).")
notes(s, "Step two was cleaning the accounts. Four accounting rules distort this sector, so we recast each company's statements. The chart shows what FY26 profit was really made of. "
         "Godrej's core business lost money, and its profit came from interest income and one-off gains. About two-fifths of DLF's profit is its share of the rental joint venture. Only Phoenix earns its profit from operations.")

# ===================================================================== 7 STEP 3 — PERFORMANCE
s = slide("Step 3: the same 10–11% return on equity, from three different engines", 3, "Ratios, DuPont, Growth_EVA, AltmanZ")
pic(s, "dupont_deck", 0.9, 1.7, h=4.6)
story(s, "We computed about fifty ratios over four years, broke return on equity into its parts (DuPont), and measured economic profit (EVA) and distress risk.",
      f"DLF earns through high margins, Godrej through borrowing, Phoenix through using its assets hard. EVA is negative for all three: on current accounting returns, "
      f"none covers its cost of capital. Godrej's distress score is in the grey zone ({G['Zpp'][3]:.1f}).",
      "Value has to come from future growth, which is why the valuation steps matter so much.")
source(s, "DuPont 3-step and 5-step; Palepu's split into operating and financing returns; Altman Z'' for emerging markets; Damodaran India industry benchmarks.")
notes(s, "Step three measured performance. All three earn about 10 to 11 percent on equity, but in different ways: DLF through margins, Godrej through leverage, Phoenix through asset turnover. "
         "Economic profit is negative for all three, which tells us that the share prices are not paying for today's returns. They must be paying for growth.")

# ===================================================================== 8 STEP 4 — HURDLE RATE
s = slide("Step 4: the choice of beta moves the cost of capital by four to five points", 4, "Beta_*, RollingBeta, BottomUp_Beta, WACC")
flow(s, GRID_X, 1.8, 8.0, 0.72, ["10-yr G-Sec", "less default spread", "plus beta × risk premium", "Cost of equity", "with debt after tax", "WACC"], gap=0.22, hi=5, size=9.5)
pic(s, "rolling_beta", 0.6, 2.75, w=8.0)
story(s, f"We estimated betas three ways (regression on monthly returns, a median of {len(N['BU'])} developers, and Damodaran's industry figure) and built the cost of capital from the "
         f"government bond yield, adjusted for India's default risk.",
      f"Beta is unstable: Phoenix's has ranged from 0.5 to 1.9. Our base case gives a cost of capital of {pc(D['W WACC'])} (DLF), {pc(G['W WACC'])} (Godrej) and "
      f"{pc(P['W WACC'])} (Phoenix). The industry beta gives rates four to five points lower.",
      "We report both versions instead of picking the one that suits the answer.")
source(s, f"Risk-free rate {pc(I['Rupee risk-free rate = G-Sec − default spread'],2)} = 10-year G-Sec less default spread; equity risk premium {pc(I['India total ERP = mature ERP + CRP'],2)} (Damodaran, implied).")
notes(s, "Step four set the hurdle rate. This is where analysts disagree most, so we did it carefully. Betas move a lot over time, as the chart shows. "
         "Our base case uses the median beta of twelve large developers; the alternative uses Damodaran's industry beta, which is lower. The two differ by four to five points, so we carry both through the valuation. For the risk-free rate we took the ten-year government bond yield and removed India's default spread, and we used Damodaran's implied equity risk premium because twenty years of Indian market history gave an estimate too noisy to rely on.")

# ===================================================================== 9 STEP 5a — DCF
s = slide("Step 5: the prices only work if these firms grow with India for ever", 5, "DCF_DLF, DCF_GPL, DCF_PML, Scenarios_Implied")
flow(s, GRID_X, 1.8, 8.0, 0.72, ["Revenue path", "× margin = NOPAT", "less reinvestment", "Free cash flow", "discount at WACC", "Equity per share"], gap=0.22, hi=3, size=9.5)
pic(s, "implied_growth", 0.75, 2.75, h=3.6)
story(s, "We built a ten-year cash-flow model for each company, where growth has to be paid for by reinvestment, then ran it backwards to find the growth rate the share price needs.",
      f"Our DCF values are {rs(vA['DLF'])}, {rs(vA['GPL'])} and {rs(vA['PML'])} a share, against prices of {rs(price['DLF'])}, {rs(price['GPL'])} and {rs(price['PML'])}. "
      f"To justify the prices, cash flows must grow {GLO:.0%}–{GHI:.0%} a year for ever, against the 5.5% we allow.",
      f"In 10,000 simulations, value beats price {pc(MC['GPL']['A']['prob_above_price'],0)} of the time for Godrej and almost never for the other two.")
source(s, "Free cash flow to the firm; 5 explicit + 5 fade years; beta moves to 1 in the stable phase; mid-year discounting. Model assumptions and the Monte Carlo are in the backup section.")
notes(s, "Step five valued the companies, first with a discounted cash-flow model. We made growth pay for itself: to grow revenue, a company has to reinvest. "
         "Our values sit well below the share prices. Rather than stop there, we asked what the price is assuming. Running the model backwards, the prices need cash flows to grow 9 to 12 percent a year for ever, "
         "roughly India's nominal growth rate. We allow 5.5 percent. That is the central finding of the project. We also stress-tested the model with bear and bull cases and ten thousand simulations; even the bull case does not reach the price for DLF or Phoenix.")

# ===================================================================== 10 STEP 5b — CROSS-CHECKS
s = slide("Step 5: peers, the brokers' NAV method and our DCF agree on the ranking", 5, "RelVal, NAV_SOTP, Broker_Views, CapRates")
pic(s, "practitioner_vs_textbook", 0.6, 1.75, w=8.05)
story(s, "We compared each company with ten listed peers on P/E and P/B, rebuilt the brokers' net-asset-value method from company disclosures, and collected broker targets.",
      f"Godrej trades slightly below the peer median; Phoenix at the top of the range. On the NAV method DLF's identifiable assets are worth {rs(NAV['dlf_nav_ps'])} a share; "
      f"the rest of the price is the market's value for its land. Broker targets sit 10–50% above the prices.",
      "Brokers get closer to the price by using lower discount rates and paying for land and growth.")
source(s, f"Peer median P/E {med[0]:.0f}x, P/B {med[1]:.1f}x. NAV: DCCDL at a 7.5% cap rate, pipeline margin, net cash. Broker medians: DLF ₹{BKMED['DLF Ltd']:,.0f}, Godrej ₹{BKMED['Godrej Properties']:,.0f}, Phoenix ₹{BKMED['Phoenix Mills']:,.0f}.")
notes(s, "We then checked the DCF two other ways. Against ten listed peers, Godrej sits just below the median and Phoenix at the top. We also rebuilt the net-asset-value method that brokers use. "
         "It gets closer to the price only by using lower discount rates and by giving value to land beyond any visible project pipeline. All three methods rank the companies the same way.")

# ===================================================================== 11 STEP 6 — THROUGH TIME
s = slide("Step 6: shocks pass quickly; deals move prices, profit surprises barely do", 6, "Event_Study, Survivorship, Delay_Cost")
pic(s, "event_macro", 0.6, 1.75, w=8.05)
story(s, "We measured how the shares reacted to 17 shocks (demonetisation, RERA, IL&FS, COVID, rate decisions) and 12 company announcements, using daily prices since 2007. "
         "We also compared today's survivors with developers that failed.",
      f"Shocks cost 9–16% in three days but reversed within a year. Asset sales to GIC and CPPIB earned {pc(E['by_kind']['monetisation']['ann'])} on average. "
      f"Failed developers lost {pc(-E['survivorship']['total']['failed'],0)} since 2008.",
      f"Delivery is the lasting risk: each year of delay costs DLF about ₹{DLY['mgmt_ps']:.0f} a share.")
source(s, "Market-model event study (abnormal return vs Nifty, estimated over the prior year); results-day study of 180 announcements; nine survivors vs six failed developers.")
notes(s, "Our final step tested the story against history. We looked at how the shares reacted to big shocks and to company news. The shocks hit hard but were reversed within a year. "
         "What moved prices lastingly was deal news, such as GIC buying into DLF's office arm, while earnings surprises explained almost nothing. "
         "Comparing survivors with developers that failed showed that delivery, not the macro cycle, is what destroys value permanently. Method in one line: for each event we estimated how the stock normally moves with the market over the previous year, and measured the part of the move on the event days that the market does not explain.")

# ===================================================================== 12 CONCLUSION
s = slide("What we concluded: Godrej preferred, DLF neutral, Phoenix least preferred", kicker="07 / Conclusion", sheet="Summary")
pic(s, "conclusion_methods", 0.6, 1.8, w=8.05)
story(s, "We put the main methods side by side, each shown as a percentage of today's share price: two DCF versions, peer multiples, the brokers' NAV method and broker targets.",
      "No DCF reaches today's prices; broker targets do, and for Godrej so do the NAV method and peer multiples. Godrej comes closest on every method. DLF has the strongest balance sheet but is priced for long-run growth. "
      "Phoenix owns excellent malls at a 3% yield and is the most fully priced.",
      "To own these shares you must believe they grow with India for ever, or that the right discount rate is close to the bond yield.")
source(s, "Ranking from relative valuation, simulation odds and the practitioner cross-check; intrinsic values under both cost-of-capital versions in the backup section.")
notes(s, "This chart brings every method together. The methods disagree, and the disagreement is informative: comparing with peers cannot see a sector-wide premium, because the peers are expensive too, "
         "while the cash-flow model can. Our ranking is Godrej first, DLF second, Phoenix third. To own any of them at today's prices you have to believe in growth with India for ever, "
         "or accept a discount rate close to the government bond yield. Each of those is defensible, but none leaves a margin of safety, which is why we rank rather than recommend buying any of them outright.")

# ===================================================================== 13 LIMITS
s = slide("What could change our answer, and what we would watch", kicker="08 / Limits")
tb(s, 0.6, 1.85, 6.4, 4.4, [[("Data. ", True, ACC), ("Four years of statements, tied to DLF's and Godrej's audited reports; Phoenix's filings we could not retrieve.", False, INK)],
                            [("Cost of capital. ", True, ACC), ("Two defensible versions, four to five points apart. We show both.", False, INK)],
                            [("Terminal value. ", True, ACC), ("Most of the value sits beyond year ten, so the long-run growth rule matters more than any forecast.", False, INK)],
                            [("Accounting. ", True, ACC), (f"Land is held at about ₹{NAV['dlf_book_psf']:,.0f} per sq ft in DLF's books against roughly ₹{NAV['dlf_psf']:,.0f} implied by the market.", False, INK)],
                            [("Cycle. ", True, ACC), ("The RBI raised rates to 5.50% in October and unsold stock is rising again.", False, INK)]], 14)
bar(s, 7.4, 1.85, 5.33, 0.03, INK)
tb(s, 7.4, 1.95, 5.0, 3.1, [[("What we would watch", True, ACC)], "Godrej: bookings turning into collections", "DLF: second-half launches against guidance",
                            "Phoenix: rent growth in the new malls", "DLF: any sale of its office stake", "The sector: interest rates and unsold inventory"], 14)
bar(s, 7.4, 5.35, 0.3, 0.3, ACC)
tb(s, 7.85, 5.28, 5.0, 0.6, "Thank you. We are happy to take questions.", 20, INK, HEAD)
notes(s, "To close, these are the main things that could change our answer, and the indicators we would watch. Thank you; we are happy to take questions.")

# ===================================================================== BACKUP
s = slide("Backup", kicker="09 / For questions")
tb(s, 0.6, 2.0, 12, 3.5, ["Strategy: Porter, BCG, SPACE, value chain", "Financial analysis: key ratios", "Cost of capital: betas and WACC under both versions",
                          "DCF assumptions and the Monte Carlo", "Relative valuation and cap rates", "NAV bridge", "Survivors and REIT yields",
                          "The industry in numbers", "What Indian research says"], 16, INK)
notes(s, "Backup slides for questions.")

s = slide("Backup: strategy — RERA rewards brands that can pre-sell; malls reward location", kicker="Backup / Step 1")
_s1 = table(s, 0.6, 1.85, 6.3, [["Force", "Level", "Driver"], ["Entry", "Low–mod", "Land, approvals, RERA, brand trust"], ["Suppliers", "High", "Owners of prime land"],
                          ["Buyers", "Moderate", "Mid-income price-sensitive; luxury not"], ["Substitutes", "Moderate", "Renting, REITs; e-commerce for malls"],
                          ["Rivalry", "High, falling", "Fragmented, consolidating to listed"]], [1.3, 1.2, 3.8], 12)
_s2 = table(s, 7.2, 1.85, 5.53, [["Business unit", "BCG", "Porter"], ["DLF luxury housing", "Star", "Focus-differentiation"], ["DLF DCCDL rental", "Cash cow", "Location"],
                           ["Godrej core cities", "Star", "Brand breadth"], ["Godrej new cities", "Question mark", "Land-led"], ["Phoenix malls", "Cash cow", "Location, tenant mix"]], [2.5, 1.45, 1.58], 12)
tb(s, 0.6, 4.4, 12.1, 1.8, [[("SPACE: ", True, ACC), ("DLF aggressive · Godrej competitive · Phoenix conservative to aggressive", False, INK)],
                            [("Value chain: ", True, ACC), ("developers create value at land, approvals and pre-sales; Phoenix at leasing", False, INK)],
                            [("Blind spots: ", True, ACC), ("DLF treats luxury demand as permanent · Godrej treats bookings as cash · Phoenix assumes rents compound with GDP for ever", False, INK)]], 14)
leftalign(_s1); leftalign(_s2)
notes(s, "Backup: strategy frameworks.")

s = slide("Backup: financial analysis — key ratios, FY26", kicker="Backup / Step 3", sheet="Ratios, DuPont, AltmanZ, Growth_EVA")
table(s, 0.6, 1.85, 12.13, [["FY26", "DLF", "Godrej", "Phoenix"],
                            ["Return on net operating assets", pc(D['DP Return on net operating assets (RNOA)'][2], 1), pc(G['DP Return on net operating assets (RNOA)'][2], 1), pc(P['DP Return on net operating assets (RNOA)'][2], 1)],
                            ["Net profit margin", pc(D['DP Net profit margin'][2], 1), pc(G['DP Net profit margin'][2], 1), pc(P['DP Net profit margin'][2], 1)],
                            ["Asset turnover (x)", f"{D['DP Asset turnover'][2]:.2f}", f"{G['DP Asset turnover'][2]:.2f}", f"{P['DP Asset turnover'][2]:.2f}"],
                            ["Equity multiplier (x)", f"{D['DP Equity multiplier'][2]:.2f}", f"{G['DP Equity multiplier'][2]:.2f}", f"{P['DP Equity multiplier'][2]:.2f}"],
                            ["EVA (₹ cr)", f"{D['EVA = NOPAT − WACC × opening NOA'][2]:,.0f}", f"{G['EVA = NOPAT − WACC × opening NOA'][2]:,.0f}", f"{P['EVA = NOPAT − WACC × opening NOA'][2]:,.0f}"],
                            ["Operating cash flow / profit (x)", f"{D['CFO / PAT (x)'][3]:.2f}", f"{G['CFO / PAT (x)'][3]:.2f}", f"{P['CFO / PAT (x)'][3]:.2f}"],
                            ["Altman Z'' (emerging markets)", f"{D['Zpp'][3]:.1f}", f"{G['Zpp'][3]:.1f}", f"{P['Zpp'][3]:.1f}"],
                            ["Inventory days", f"{D['Inventory days (on cost of revenue)'][3]:,.0f}", f"{G['Inventory days (on cost of revenue)'][3]:,.0f}", f"{P['Inventory days (on cost of revenue)'][3]:,.0f}"],
                            ["Customer advances / revenue (x)", f"{D['Customer advances / revenue (x)'][3]:.1f}", f"{G['Customer advances / revenue (x)'][3]:.1f}", f"{P['Customer advances / revenue (x)'][3]:.1f}"]],
      [5.2, 2.31, 2.31, 2.31], 13, 0.42)
notes(s, "Backup: ratio table.")

s = slide("Backup: cost of capital under both versions", kicker="Backup / Step 4", sheet="Beta_*, BottomUp_Beta, WACC")
table(s, 0.6, 1.85, 12.13, [["", "DLF", "Godrej", "Phoenix"],
                            ["Regression beta (60 months)", f"{N['Beta_Monthly']['DLF Ltd']['Raw beta (SLOPE)']:.2f}", f"{N['Beta_Monthly']['Godrej Propert']['Raw beta (SLOPE)']:.2f}", f"{N['Beta_Monthly']['Phoenix Mills']['Raw beta (SLOPE)']:.2f}"],
                            ["Base-case beta (median of large developers)", f"{D['W Beta used']:.2f}", f"{G['W Beta used']:.2f}", f"{P['W Beta used']:.2f}"],
                            ["Alternative beta (Damodaran industry)", f"{D['W_B']['beta']:.2f}", f"{G['W_B']['beta']:.2f}", f"{P['W_B']['beta']:.2f}"],
                            ["Cost of capital, base case", pc(D['W WACC']), pc(G['W WACC']), pc(P['W WACC'])],
                            ["Cost of capital, alternative", pc(D['W_B']['wacc']), pc(G['W_B']['wacc']), pc(P['W_B']['wacc'])],
                            ["Synthetic credit rating (cash interest cover)", D['W Synthetic rating'], G['W Synthetic rating'], P['W Synthetic rating']],
                            ["DCF value per share, base / alternative (₹)", f"{vA['DLF']:,.0f} / {vB['DLF']:,.0f}", f"{vA['GPL']:,.0f} / {vB['GPL']:,.0f}", f"{vA['PML']:,.0f} / {vB['PML']:,.0f}"]],
      [5.2, 2.31, 2.31, 2.31], 13, 0.45)
source(s, f"Rates: about {pc(-RF['DLF'][2],0)} fall in DLF per +100bp in bond yields, t ≈ {RF['DLF'][4]:.1f} (weak). Historical equity premium 2005–26 too noisy to use; implied premium used.", y=5.9)
notes(s, "Backup: the two cost-of-capital versions and what each does to value.")

s = slide("Backup: DCF assumptions and 10,000 simulations", kicker="Backup / Step 5", sheet="DCF_*, MonteCarlo")
pic(s, "monte_carlo", 0.6, 1.7, w=12.1)
table(s, 0.6, 4.85, 12.13, [["Assumption", "DLF", "Godrej", "Phoenix"],
                            ["Growth FY27–31 (then fades to 5.5%)", " · ".join(pc(g, 0) for g in D['DCF growth']), " · ".join(pc(g, 0) for g in G['DCF growth']), " · ".join(pc(g, 0) for g in P['DCF growth'])],
                            ["Core margin FY26 → target", f"{pc(D['Core EBIT margin'][3],0)} → {pc(D['DCF margin'],0)}", f"{pc(G['Core EBIT margin'][3],0)} → {pc(G['DCF margin'],0)}", f"{pc(P['Core EBIT margin'][3],0)} → {pc(P['DCF margin'],0)}"],
                            ["Sales-to-capital · stable cost of capital", f"{D['DCF s2c']:.1f} · {pc(D['DCF stableWACC'])}", f"{G['DCF s2c']:.1f} · {pc(G['DCF stableWACC'])}", f"{P['DCF s2c']:.1f} · {pc(P['DCF stableWACC'])}"]],
      [3.8, 2.8, 2.8, 2.73], 12, 0.33)
notes(s, "Backup: model assumptions and the simulation.")

s = slide("Backup: relative valuation and cap rates", kicker="Backup / Step 5", sheet="RelVal, CapRates")
rows = [["", "P/E", "P/B", "EV/EBITDA", "ROE"]]
for nm in ["DLF Ltd", "Godrej Properties", "Phoenix Mills"]:
    r_ = RV[nm]; rows.append([nm.replace(" Ltd", ""), f"{r_[12]:.1f}", f"{r_[13]:.2f}", f"{r_[15]:.1f}", pc(r_[11])])
rows.append([f"Peer median (n = {N['n_peers']})", f"{med[0]:.1f}", f"{med[1]:.2f}", f"{med[3]:.1f}", ""])
table(s, 0.6, 1.85, 5.9, rows, [2.4, 0.85, 0.85, 1.0, 0.8], 13, 0.45)
pic(s, "cap_rates", 6.8, 1.75, w=5.9)
tb(s, 0.6, 4.6, 6.0, 1.5, f"Phoenix's EBITDA yield is {pc(CAP['yield'])}, against {pc(CAP['reit_median'])} for listed REITs and the G-Sec above both: investors pay for growth.", 14)
notes(s, "Backup: peers and cap rates.")

s = slide("Backup: rebuilding the brokers' NAV from public data", kicker="Backup / Step 5", sheet="NAV_SOTP")
pic(s, "nav_bridge", 0.6, 1.7, w=12.1)
source(s, f"DLF: identifiable NAV {rs(NAV['dlf_nav_ps'])}/share; residual land implied at ~₹{NAV['dlf_psf']:,.0f}/sq ft vs book ~₹{NAV['dlf_book_psf']:,.0f}. Phoenix: price {pc(NAV['pml_prem'],0)} above NAV.", y=6.2)
notes(s, "Backup: the NAV bridge.")

s = slide("Backup: survivors vs failed developers; REIT yields vs the bond yield", kicker="Backup / Step 6", sheet="Survivorship, REIT_Spread")
pic(s, "survivors_reit", 0.6, 1.7, w=12.1)
source(s, f"REIT yield {pc(E['reit']['latest_median'])} vs G-Sec {pc(E['reit']['latest_gsec'])}. Pre-sale financing saves Godrej about ₹{LQ['save_gpl']:,.0f} cr a year (Dutta et al.; upper bound).", y=6.2)
notes(s, "Backup: survivorship and REITs.")

s = slide("Backup: the industry in numbers, and where our three stand", kicker="Backup / Step 1", sheet="Industry_Data, Industry_vs_Company")
pic(s, "industry_cycle", 0.6, 1.7, w=12.1)
source(s, f"About 6.3 lakh homes stuck or delayed (≈{IV['stuck_yrs']:.1f} years of sales). Godrej share of top-7 sales value {pc(IV['sh_gpl_prev'])} → {pc(IV['sh_gpl'])}; deliveries 121–123% of guidance.", y=6.2)
notes(s, "Backup: industry data.")

s = slide("Backup: what Indian research says, and what we used", kicker="Backup / Research", sheet="Literature")
rows = [["Study", "Finding", "What we used"],
        ["Tandel, Gandhi, Nanda & Agnihotri (2025)", "RERA disclosure cut litigated-home prices 4–6%", "Trust is priced: flight to quality"],
        ["Gandhi, Tandel, Tabarrok et al. (2019)", "Litigation adds ~20% to completion time", f"Delay priced: ≈ ₹{LQ['lit_gpl']:.0f}/share for Godrej"],
        ["Dutta, Green et al. (2021, IIMB)", "Pre-sales replace 16–18% loans with 8–10% buyer money", f"Advances save Godrej ≈ ₹{LQ['save_gpl']:,.0f} cr a year"],
        ["Brueckner & Sridhar (2012)", "Floor-area limits make central land scarce", "Scarcity value in DLF and Phoenix land"],
        ["Singh & Nadkarni (2017, RBI)", "Rates drive share prices; credit drives house prices", "Why H5 is rejected"],
        ["Walia et al. (2023)", "REITs behave like bonds", "REIT yields below the G-Sec"]]
_t = table(s, 0.6, 1.85, 12.13, rows, colw=[3.8, 4.4, 3.93], size=13, h_row=0.55)
for _r in _t.rows:
    for _c in _r.cells:
        _c.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT
notes(s, "Backup: research we drew on.")

prs.save(OUT); print("saved", OUT, "slides", len(prs.slides))

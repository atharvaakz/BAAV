"""Project report v2 — investment-memo structure, all modules, every number from the model."""
import pathlib
exec(open(pathlib.Path(__file__).resolve().parent / "report_common.py").read())
import re as _re
_fig0, _FIGN = fig, [0]
def fig(name, caption, width=16.5):
    _FIGN[0] += 1
    _fig0(name, _re.sub(r"^Figure \d+", f"Figure {_FIGN[0]}", caption), width)
from docx.enum.text import WD_BREAK

MC, SC, A2 = N["MC"], N["SC"], N["A2"]
import openpyxl as _ox
_wbx = _ox.load_workbook(ROOT / "models/excel/_recalc/BAV_RealEstate_Model.xlsx", data_only=True, read_only=True)
NSHEETS = len(_wbx.sheetnames)
def _find(sheet, label, k=0, col=2):
    ws = _wbx[sheet]; hits = [r for r in ws.iter_rows(values_only=True) if r and r[0] == label]
    return hits[k][col - 1]
AEG = {c: _find("ResidualIncome", "AEG value (10-yr, no terminal) per share (₹)", i) for i, c in enumerate(["DLF", "GPL", "PML"])}
FPE = {c: _find("ResidualIncome", "Implied forward P/E = price ÷ E₁ vs 1/Ke", i) for i, c in enumerate(["DLF", "GPL", "PML"])}
NAIVE = {c: _find(f"DCF_{c}", "Our forecast ÷ naive trend (FY31)", 0, 7) for c in ["DLF", "GPL", "PML"]}
RV = {r[0]: r for r in N["RelVal"]}
RI_ = {"DLF Ltd": "DLF", "Godrej Properties": "GPL", "Phoenix Mills": "PML"}
med = N["RelStats"]["Median"]; q1 = N["RelStats"]["25th percentile"]; q3 = N["RelStats"]["75th percentile"]
LC, RB, RF, HE, HS, IB, CAP, RO = N["LongCycle"], N["RollingBeta"], N["RateFactor"], N["HistERP"], N["Housing"], N["Industry"], N["Cap"], N["RO"]
bm = N["Beta_Monthly"]; dl, gp, ph = bm["DLF Ltd"], bm["Godrej Propert"], bm["Phoenix Mills"]
imp = SC["implied"]; scn = SC["scenarios"]
price = {c: N[c]["DCF"]["Current market price (Rs)"] for c in ("DLF", "GPL", "PML")}
vA = {c: N[c]["DCF"]["Intrinsic value per share (Rs)"] for c in ("DLF", "GPL", "PML")}
vB = {c: N[c]["lensB"]["vps"] for c in ("DLF", "GPL", "PML")}


def callout(title, lines, fill="E6EEEE"):
    t = doc.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.rows[0].cells[0]; shade(c, fill); c.width = Cm(16.5)
    p = c.paragraphs[0]; r = p.add_run(title); r.bold = True; r.font.color.rgb = ACC; r.font.size = Pt(10)
    for ln in lines:
        p = c.add_paragraph(); r = p.add_run(ln); r.font.size = Pt(9.5); p.paragraph_format.space_after = Pt(2)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


# ================================================================ COVER
p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(90)
r = p.add_run("ECON F355 · BUSINESS ANALYSIS & VALUATION · END-SEMESTER PROJECT"); r.font.size = Pt(9); r.bold = True; r.font.color.rgb = MUTE
p = doc.add_paragraph(); r = p.add_run("Paying for the Future"); r.font.name = "Cambria"; r.font.size = Pt(34); r.bold = True; r.font.color.rgb = INK
p = doc.add_paragraph(); r = p.add_run("What Indian real-estate equities are really priced on — DLF, Godrej Properties and Phoenix Mills"); r.font.size = Pt(14); r.font.color.rgb = ACC
doc.add_paragraph()
table(["", "DLF", "Godrej Properties", "Phoenix Mills"],
      [["Business model", "Luxury developer + 66.66% of DCCDL rental JV", "National developer, land-led growth", "Mall-led rental annuity"],
       ["Price (₹)", rs(price['DLF']), rs(price['GPL']), rs(price['PML'])],
       ["DCF value, lens A / lens B (₹)", f"{vA['DLF']:,.0f} / {vB['DLF']:,.0f}", f"{vA['GPL']:,.0f} / {vB['GPL']:,.0f}", f"{vA['PML']:,.0f} / {vB['PML']:,.0f}"],
       ["Perpetual growth the price implies", pc(imp['DLF']['terminal_g']), pc(imp['GPL']['terminal_g']), pc(imp['PML']['terminal_g'])],
       ["Versus peers (P/E, P/B)", "Above median, inside IQR", "At the median", "Top of the range"],
       ["Relative ranking", "2", "1", "3"]], [5.0, 3.8, 3.9, 3.8], size=9)
para("Submitted to Prof. Mohit Kumar · BITS Pilani, K K Birla Goa Campus · Group 27: Saatvik Nagpal, Atharvaa Khanzode", size=10)
para(f"Pricing date {I['Valuation date']}. Financial statements FY23–FY26 and Q1–Q2 FY27; market data from 2007. ₹ crore unless stated. "
     f"All figures trace to the accompanying Excel model ({NSHEETS} sheets, live formulas).", size=8.5, italic=True)
doc.add_page_break()

# ================================================================ EXEC SUMMARY
doc.add_heading("Executive summary", 1)
para("Real estate is the sector where accounting profit and economic value drift furthest apart. Revenue is booked years after a flat is sold, "
     "land sits on the balance sheet at what it cost decades ago, and much of the profit of the largest developer arrives as a one-line share of "
     "a joint venture. We set out to separate what these three companies earn from what their share prices assume, using every framework in the course.")
bullets([
    ("The reported numbers flatter in different ways.", f"For DLF, {pc(D['JV/associate share of PAT'][3],0)} of FY26 profit is its share of joint-venture income, mainly the DCCDL rental platform, and treasury income adds a large slice; core development EBIT was {cr(D['RC Core operating EBIT'][3])}. "
     f"Godrej's core operations lost money ({cr(G['RC Core operating EBIT'][3])} before tax) while it capitalised {cr(G['RC Interest capitalised (cash paid − P&L cost)'][3])} of interest into inventory. Phoenix is the only one whose profit is genuinely operating."),
    ("None of them yet earns its cost of capital on recognised profit.", f"FY26 ROE was {pc(D['DP ROE (3-step product)'][2])}, {pc(G['DP ROE (3-step product)'][2])} and {pc(P['DP ROE (3-step product)'][2])}; EVA was negative for all three in every year."),
    ("Cost of capital is the swing factor — so we show two lenses.", f"Lens A uses a bottom-up beta from {len(N['BU'])} large developers (WACC {pc(D['W WACC'])}, {pc(G['W WACC'])}, {pc(P['W WACC'])}). "
     f"Lens B uses Damodaran's India industry beta across 156 developers (WACC {pc(D['W_B']['wacc'])}, {pc(G['W_B']['wacc'])}, {pc(P['W_B']['wacc'])}). Large, liquid developers are far more market-sensitive than the industry average, which is diluted by thinly traded small caps."),
    ("Intrinsic value sits well below price under either lens.", f"DCF values are {rs(vA['DLF'])} / {rs(vB['DLF'])} for DLF, {rs(vA['GPL'])} / {rs(vB['GPL'])} for Godrej and {rs(vA['PML'])} / {rs(vB['PML'])} for Phoenix against prices of {rs(price['DLF'])}, {rs(price['GPL'])} and {rs(price['PML'])}. "
     f"In 10,000 Monte Carlo draws the probability that value exceeds price is {pc(MC['DLF']['A']['prob_above_price'],1)} for DLF, {pc(MC['GPL']['A']['prob_above_price'],0)} for Godrej and {pc(MC['PML']['A']['prob_above_price'],0)} for Phoenix."),
    ("The gap is about the long run, not the next five years.", f"Holding our discount rates, today's prices imply perpetual growth of {pc(imp['DLF']['terminal_g'])}, {pc(imp['GPL']['terminal_g'])} and {pc(imp['PML']['terminal_g'])} — roughly India's long-run nominal GDP growth, double the {pc(I['Terminal growth rate (nominal, Rs)'])} we allow under the textbook rule that growth cannot exceed the risk-free rate forever. "
     "The market is pricing these firms as perpetual claims on Indian growth."),
    ("The practitioner view agrees on the ranking.", f"Rebuilding the sell-side's NAV method from company disclosures, DLF's identifiable assets are worth {rs(N['NAV']['dlf_nav_ps'])} a share — close to our DCF — so {pc(N['NAV']['dlf_land']/N['NAV']['dlf_mcap'],0)} of its market value is land beyond the visible pipeline. "
     f"Phoenix trades at {pc(N['NAV']['pml_prem'],0)} above our sum-of-the-parts NAV. Godrej is the one stock a practitioner multiple values above its price ({rs(N['NAV']['gpl_emb_ps'])} on 12x embedded profit; broker consensus about ₹2,300)."),
    ("Against peers, the ranking is clear.", f"Godrej sits at the peer median — the cheapest of our three — at {xx(RV['Godrej Properties'][12])} earnings and {xx(RV['Godrej Properties'][13],2)} book; DLF at {xx(RV['DLF Ltd'][12])} and {xx(RV['DLF Ltd'][13],2)}; Phoenix at {xx(RV['Phoenix Mills'][12])} and {xx(RV['Phoenix Mills'][13],2)} — against peer medians of {xx(med[0])} and {xx(med[1],2)} across {N['n_peers']} listed developers. "
     f"DLF sits above the median but inside the inter-quartile range; Phoenix has the highest P/B in the set. Phoenix's EBITDA yield of {pc(CAP['yield'])} is less than half the {pc(CAP['reit_median'])} cash yield on listed REITs."),
])
callout("Our view", [f"1. Godrej Properties — the cheapest of the three relative to peers and the only one the practitioner method values above price; the risk is that land buying keeps statutory cash flow negative.",
                     f"2. DLF — fairly priced against peers with the strongest balance sheet, but only a long-run growth view justifies the price.",
                     f"3. Phoenix Mills — a high-quality annuity priced like one that will compound at the rate of the economy for ever."])

# ================================================================ 1 QUESTION & HYPOTHESES
doc.add_heading("1. The question, and what we tested", 1)
module_tag("Module 1 · framework for business analysis and valuation")
para("A valuation is only as good as the questions it answers. Before building the model we wrote down hypotheses about Indian real estate that "
     "the analysis could confirm or reject. Their results run through the report and are summarised here.")
H = [["H1", "Prices embed growth well beyond a textbook terminal rate", f"Implied perpetual g {pc(imp['DLF']['terminal_g'],0)}–{pc(imp['PML']['terminal_g'],0)} vs 5.5% cap", "Supported"],
     ["H2", "Large developers are riskier (higher β) than the industry average", f"β {dl['Raw beta (SLOPE)']:.2f}–{gp['Raw beta (SLOPE)']:.2f} vs industry {IB['Levered beta (industry avg)'][0]:.2f}", "Supported"],
     ["H3", "Beta is unstable through the cycle", f"Rolling 36-month β spans {min(v[0] for v in RB.values()):.1f}–{max(v[1] for v in RB.values()):.1f} across firms", "Supported"],
     ["H4", "Developers are hurt by rising long-term rates", f"≈ {pc(RF['DLF'][2],0)} per +100bp, t ≈ {RF['DLF'][4]:.1f}", "Weak evidence"],
     ["H5", "Realty stocks follow house prices", f"Correlation of annual changes {HS['Correlation: realty YoY vs house-price YoY (same quarter)']:.2f}", "Rejected"],
     ["H6", "Customer advances fund growth (negative reinvestment)", "DLF invested capital fell 28% FY23–26", "Supported (DLF)"],
     ["H7", "Book value understates economic capital", f"Justified P/B {N['DLF']['RI']['Justified P/B on current ROE — lens A']:.2f} vs market {RV['DLF Ltd'][13]:.2f} (DLF)", "Supported"],
     ["H8", "Phoenix is priced as a growth asset, not a yield asset", f"EBITDA yield {pc(CAP['yield'])} vs REITs {pc(CAP['reit_median'])}", "Supported"],
     ["H9", "Sell-side NAVs reach price only via land and growth premia", f"DLF residual land {pc(N['NAV']['dlf_land']/N['NAV']['dlf_mcap'],0)} of mcap; Phoenix premium {pc(N['NAV']['pml_prem'],0)}", "Supported"],
     ["H10", "Deal and launch news moves prices; profit surprises barely do", f"Monetisation CAR {pc(N['EV']['by_kind']['monetisation']['ann'])} (t {N['EV']['by_kind']['monetisation']['t_cs']:.1f}); EPS surprise R² ≤ {max(v['r2'] for v in N['EV']['earnings'].values()):.2f}", "Supported"],
     ["H11", "Macro shocks are temporary for strong developers; delivery failure is permanent", f"Shock CARs −9% to −16% reversed within a year; failed developers {pc(N['EV']['survivorship']['total']['failed'],0)}", "Supported"],
     ["H12", "Developers issue equity after run-ups (market timing)", f"Run-up {pc(N['EV']['by_kind']['equity issue']['run'])}, 60-day drift {pc(N['EV']['by_kind']['equity issue']['drift'])}", "Supported (small n)"]]
table(["#", "Hypothesis", "Evidence", "Result"], H, [1.0, 7.0, 6.0, 2.5], size=8.5)

doc.add_heading("Data and workflow", 2)
para(f"We assembled the longest consistent record we could reach: consolidated statements for FY23–FY26 and the five latest quarters (to September 2026) for "
     f"the three companies and {N['n_peers']} listed peers; monthly prices since listing (DLF and Phoenix from 2007; the Sensex from 1997); BIS residential "
     "property prices for India (2009–2026); the 10-year G-Sec (IMF series to 2010, OECD from 2011); Damodaran's January 2026 country-risk and India industry "
     "datasets; and distributions of four listed REITs. Each source is identified on the input sheets of the model.")
table(["Layer", "What", "Span"],
      [["Fundamentals", f"3 targets + {N['n_peers']} peers, P&L, balance sheet, cash flow", "FY23–FY26; quarters to Sep-26"],
       ["Prices", "Monthly/weekly/daily, dividend-adjusted", "2007–2026 (Sensex 1997–)"],
       ["Macro", "10-yr G-Sec, 3-m rate, CPI, INR, GDP, household credit", "1960s–2026 (series vary)"],
       ["Real estate", "BIS house prices (nominal, real), REIT distributions", "2009–2026"],
       ["Cost of capital", "Damodaran ERP, CRP, rating spreads; India industry betas, margins, multiples", "Jan-2026"]], [3.2, 9.3, 4.0], size=8.5)
para("The model follows the course order — strategy, accounting analysis, recasting, financial analysis, cost of capital, intrinsic and relative valuation — "
     "and a Python replica of the DCF (verified to reproduce the spreadsheet to the rupee) drives the scenario and Monte Carlo work.")

# ================================================================ 2 SECTOR
doc.add_heading("2. The sector: two decades of boom and bust", 1)
module_tag("Module 2 · strategy and competitive analysis · real-estate cycle")
fig("long_cycle", "Figure 1 — Twenty years of Indian real-estate equity: total-return index and drawdowns.", 13)
lc = LC
para(f"The record is humbling. DLF listed in July 2007 near the top of the last boom; nineteen years later its dividend-adjusted return is "
     f"{pc(lc['DLF'][2])} a year and the stock is still {pc(-lc['DLF'][4],0)} below its December 2007 peak, after falling {pc(-lc['DLF'][3],0)}. "
     f"Phoenix fell {pc(-lc['Phoenix Mills'][3],0)} in 2008, took until 2017 to recover, and has compounded at {pc(lc['Phoenix Mills'][2])} a year since listing. "
     f"The Nifty Realty index has returned {pc(lc['Nifty Realty'][2])} a year since 2010 with a {pc(-lc['Nifty Realty'][3],0)} drawdown, against {pc(lc['Nifty 50'][2])} for the Nifty 50. "
     "Anyone valuing these stocks off the last three years of data is looking at one half of a cycle.")
fig("housing", "Figure 2 — House prices compound slowly; realty equities swing violently and do not track them quarter by quarter.", 12.5)
para(f"Physical prices behave very differently. BIS data show Indian house prices rising {pc(HS['Nominal house-price CAGR'])} a year in nominal terms since 2009 "
     f"but only {pc(HS['Real house-price CAGR'])} in real terms; in the latest quarter real prices were {pc(HS['Latest real YoY'])} year on year. "
     f"The correlation between annual changes in house prices and in the realty index is {HS['Correlation: realty YoY vs house-price YoY (same quarter)']:.2f}: "
     "equities move on expectations, rates and bookings momentum, and overshoot the physical market in both directions. Hypothesis H5 is rejected.")
para("Where are we now? The latest data read as late-cycle. Anarock's top-seven-city sales rose only 3% in Q3 2026 after falling 6% in Q2 (PropEquity's wider count fell 6%), "
     "while launches rose 18% and unsold inventory 12% to about 6.3 lakh units; prices are still up about 7%. On 7 October 2026 the RBI raised the repo rate to 5.50% and moved to "
     "'calibrated tightening', and the 10-year G-Sec is near multi-year highs. Supply outrunning sales, and rates turning up, is the combination that preceded past corrections in Figure 1.")
doc.add_heading("Industry structure", 2)
table(["Force", "Level", "Why it matters here"],
      [["Threat of entry", "Low–moderate", "Land, approvals, RERA escrow and brand trust decide who can pre-sell; joint development agreements lower the bar (Godrej's route)."],
       ["Supplier power", "High (land)", "Owners of prime land capture much of the value; construction inputs are competitive. DLF's legacy Gurugram land is a cost advantage no entrant can buy."],
       ["Buyer power", "Moderate", "Mid-income buyers are price-sensitive; luxury buyers less so. Tenants in a city's dominant mall have few alternatives."],
       ["Substitutes", "Moderate", "Renting, resale stock, REITs and gold for investors; e-commerce for malls."],
       ["Rivalry", "High, consolidating", "Thousands of local builders, but RERA and funding costs push share toward listed national developers."]],
      [2.8, 2.6, 11.1], size=8.5)
table(["Business unit", "Growth", "Share", "BCG", "Strategy (Porter)"],
      [["DLF — Gurugram luxury housing", "High", "High", "Star", "Focused differentiation"],
       ["DLF — DCCDL offices & malls", "Moderate", "High", "Cash cow", "Differentiation (location)"],
       ["Godrej — core four cities", "High", "Med–high", "Star", "Brand-led breadth"],
       ["Godrej — new cities, plotted", "High", "Low", "Question mark", "Land-led expansion"],
       ["Phoenix — operating malls", "Moderate", "High", "Cash cow", "Location & tenant mix"],
       ["Phoenix — offices, hotels, residential", "Low–mod", "Low", "Question mark / dog", "Non-core"]], [5.6, 1.8, 1.8, 3.0, 4.3], size=8.5)
para("SPACE places DLF in the aggressive quadrant (net cash, attractive industry), Godrej in the competitive quadrant (strong position, weak financial strength) "
     "and Phoenix on the conservative–aggressive border (financially strong, stable, slower growth). In the value chain, developers create value at land "
     "acquisition, approvals and pre-sales — construction is largely outsourced — while Phoenix creates it in leasing and tenant curation, with revenue-share "
     "rents tying its income to tenant sales.")
table(["", "DLF", "Godrej Properties", "Phoenix Mills"],
      [["Strengths", "Low-cost land; net cash; luxury brand; GIC partnership", "Group brand; national reach; JV sourcing", "Dominant city malls; recurring rent; CPPIB and GIC partners"],
       ["Weaknesses", "Gurugram concentration; core margin fell in FY26", "Negative operating cash flow; rising debt", "Capital-intensive; ~21% of profit to minorities"],
       ["Opportunities", "Monetise land bank; grow DCCDL", "Convert sales to revenue; new cities", "Malls already in CWIP; offices"],
       ["Threats", "Luxury cycle; NCR construction bans", "Land prices; execution across many sites", "E-commerce; discretionary slowdown"],
       ["Blind spot", "Treating luxury demand as structural", "Assuming bookings equal cash", "Assuming rents compound with GDP for ever"]],
      [2.6, 4.6, 4.6, 4.7], "SWOT plus a blind-spot row: the assumption each management team (and its investors) is most likely to over-trust.", size=8)
para("Customer segments differ sharply. DLF sells to high-net-worth buyers and non-resident Indians for whom a Gurugram apartment is partly an investment; "
     "Godrej sells to salaried, mortgage-financed buyers across cities, so its demand is rate-sensitive; Phoenix's customers are tenants whose sales depend on "
     "urban discretionary spending. Customer lifetime value is highest for Phoenix (tenants renew leases repeatedly) and lowest for developers, whose buyers rarely buy twice.")

# ================================================================ 3 ACCOUNTING
doc.add_heading("3. Accounting analysis: where the numbers mislead", 1)
module_tag("Module 3 · accounting policies, flexibility and red flags")
table(["Policy", "Effect", "Evidence", "Our adjustment"],
      [["Revenue on completion (Ind AS 115)", "Revenue lags sales by years; margins follow the mix delivered", f"Godrej advances {xx(G['Customer advances / revenue (x)'][3])} revenue; DLF quarterly revenue swings ₹1,260–2,720 cr", "Forecast recognised revenue converging to sales; use cash measures"],
       ["Borrowing costs capitalised (Ind AS 23)", "Interest parked in inventory; P&L cover inflated", f"Godrej P&L cover {G['Interest coverage: EBIT / P&L finance cost (x)'][3]:.0f}x vs cash cover {G['Cash interest coverage: EBIT / interest paid (x)'][3]:.1f}x", "Rate credit on cash interest"],
       ["JVs equity-accounted (Ind AS 111)", "JV debt and assets invisible; one-line profit share", f"DLF: tax-and-JV burden {D['DP Tax & JV burden'][2]:.2f} (> 1)", "Strip from EBIT; value DCCDL separately"],
       ["Investment property at cost (Ind AS 40)", "Malls at depreciated cost", f"Phoenix P/B {xx(RV['Phoenix Mills'][13])}", "Use cash-flow and cap-rate valuation"],
       ["RERA escrow", "Part of cash is ring-fenced", f"DLF restricted cash {cr(D['RC Restricted cash (kept operating)'][3])}", "Treat as operating, not surplus"],
       ["Treasury, JV stake sales, fair-value gains (Ind AS 109)", "Inflates EBIT; largely non-cash", "Godrej: gains on JV divestments and re-measurement on taking control of a JV turn its core loss into profit", "Exclude from core EBIT; note it recurs in a JV-heavy model"]],
      [3.5, 4.0, 5.0, 4.0], size=8)
para(f"Earnings quality is good at DLF and Phoenix — operating cash flow was {xx(D['CFO / PAT (x)'][3],2)} and {xx(P['CFO / PAT (x)'][3],2)} profit in FY26 — and apparently poor at Godrej, "
     f"where statutory operating cash flow has been negative every year (accruals ratio {pc(G['Accruals ratio = (PAT − CFO) / avg assets'][3])} of assets) as inventory rose to {pc(G['Inventory / total assets'][3],0)} of assets. "
     f"Classification matters: land is inventory, so land purchases sit inside operating cash flow. Management's pre-land operating cash flow was ₹7,830 cr in FY26; the gap of about "
     f"₹{N['KPI']['Godrej: management OCF − statutory CFO = land & BD spend proxy'][1]:,.0f} cr is reinvestment in land. Godrej generates cash from sold projects and spends all of it, and more, on growth. Quarterly data make the timing problem vivid: DLF's trailing-twelve-month "
     f"P/E is {N['DLF']['ttm_pe']:.1f}x against {xx(RV['DLF Ltd'][12])} on FY26, and its quarterly net margin has ranged from 28% to over 100% as projects complete.")

# ================================================================ 4 RECAST
doc.add_heading("4. Recasting the statements", 1)
module_tag("Module 4 · operating, financing and non-operating split (TB1 Ch-4/5)")
fig("profit_mix", "Figure 3 — What FY26 profit is actually made of.", 12)
table(["FY26 (₹ cr)", "DLF", "Godrej", "Phoenix"],
      [[k.replace("RC ", "").replace(" = core EBIT × (1 − t)", " (t = 25.17%)"), *[f"{d[k][3]:,.0f}" for d in (D, G, P)]] for k in
       ["RC EBIT incl. other income", "RC Core operating EBIT", "RC NOPAT = core EBIT × (1 − t)", "RC Share of JV/associate profit (post-tax)",
        "RC Cash & liquid investments", "RC Net financial obligations (NFO)", "RC Net operating assets = invested capital",
        "RC Customer advances & other op. liabilities (derived)"]], [7.0, 3.1, 3.1, 3.1], size=8.5)
para(f"DLF's invested capital fell from {cr(D['RC Net operating assets = invested capital'][0])} to {cr(D['RC Net operating assets = invested capital'][3])} over FY23–26 "
     f"while customer advances rose to {cr(D['RC Customer advances & other op. liabilities (derived)'][3])}: buyers are financing construction (H6). Godrej's invested capital doubled to "
     f"{cr(G['RC Net operating assets = invested capital'][3])} as it bought land.")

# ================================================================ 5 FINANCIAL ANALYSIS
doc.add_heading("5. Financial analysis", 1)
module_tag("Module 5 · ratios, cash flow, DuPont, EVA/CVA, distress, balanced scorecard")
rows5 = []
for lab, key, kind in [("Revenue CAGR FY23–26", "Revenue CAGR FY23→FY26", "g"), ("EBITDA margin (incl. other income)", "EBITDA margin (incl. other income)", "p"),
                       ("Core EBIT margin", "Core EBIT margin", "p"), ("Net profit margin", "Net profit margin (owners)", "p"),
                       ("ROE (average equity)", "Return on equity (avg)", "p"), ("ROIC (average NOA)", "ROIC = NOPAT / avg invested capital", "p"),
                       ("Self-sustained growth (ROE × retention)", "Self-sustained growth = ROE × retention", "p"), ("Inventory days", "Inventory days (on cost of revenue)", "n"),
                       ("Receivable / payable days", None, "rp"), ("Current / quick ratio", None, "cq"),
                       ("Net debt / equity", "Net debt / equity (x)", "x"), ("Cash interest cover", "Cash interest coverage: EBIT / interest paid (x)", "x"),
                       ("CFO / PAT", "CFO / PAT (x)", "x"), ("CFO / total debt", "CFO / total debt (x)", "x"), ("Dividend payout", "Dividend payout", "p")]:
    vals = []
    for d in (D, G, P):
        if kind == "g": vals.append(pc(d[key]))
        elif kind == "rp": vals.append(f"{d['Receivable days'][3]:.0f} / {d['Payable days'][3]:.0f}")
        elif kind == "cq": vals.append(f"{d['Current ratio (x)'][3]:.2f} / {d['Quick ratio (x)'][3]:.2f}")
        else:
            v = d[key][3]
            vals.append("n.m." if isinstance(v, str) else (pc(v) if kind == "p" else (f"{v:,.0f}" if kind == "n" else xx(v, 2))))
    rows5.append([lab] + vals)
table(["FY26", "DLF", "Godrej", "Phoenix"], rows5, [6.6, 3.2, 3.2, 3.2], "Selected from 50 ratios × 4 years in the 'Ratios' sheet; average balances where a flow meets a stock.", size=8.5)
fig("re_signature", "Figure 4 — The real-estate signature: long inventory cycles, customer-funded inventory, diverging cash conversion.", 13)
fig("industry_bench", "Figure 5 — Against Damodaran's India industry data (156 listed developers).", 13)
para(f"Against the industry, all three earn above-average ROE ({pc(IB['ROE'][0])} for the industry) and much higher margins. DLF and Phoenix trade above the industry's aggregate "
     f"trailing P/E of {IB['Trailing P/E (aggregate)'][0]:.0f}x; Godrej trades below it. The industry is reinvesting {IB['Reinvestment rate'][0]:.1f}x its after-tax operating income — a land-buying phase that "
     "Godrej exemplifies.")
doc.add_heading("DuPont: three engines, one ROE", 2)
fig("dupont", "Figure 6 — Three-step DuPont, FY24–FY26.", 13)
para(f"The three companies reach similar ROEs in opposite ways: DLF through margin ({pc(D['DP Net profit margin'][2])}) with turnover of only {D['DP Asset turnover'][2]:.2f}x; "
     f"Godrej through leverage (equity multiplier {G['DP Equity multiplier'][2]:.2f}x) while its turnover fell to {G['DP Asset turnover'][2]:.2f}x; Phoenix through turnover ({P['DP Asset turnover'][2]:.2f}x). "
     f"The five-step version shows DLF's tax-and-JV burden above one ({D['DP Tax & JV burden'][2]:.2f}) because JV profit enters after tax. Between FY24 and FY26, "
     f"{pc(D['ROEattr' + 'from margin'],1)} of DLF's {pc(D['ROEattr' + 'total = ΔROE'],1)} rise in ROE came from margin; Godrej's {pc(G['ROEattr' + 'from margin'],1)} margin gain was partly offset by a {pc(G['ROEattr' + 'from asset turnover'],1)} turnover drag.")
para(f"Palepu's split of ROE into operating return and financing is the most revealing view. Godrej's return on net operating assets was {pc(G['DP Return on net operating assets (RNOA)'][2])}; "
     f"{pc(G['DP Non-operating (JV, exceptional) contribution'][2])} of its ROE came from non-operating items. DLF's RNOA was {pc(D['DP Return on net operating assets (RNOA)'][2])}, and Phoenix's "
     f"{pc(P['DP Return on net operating assets (RNOA)'][2])} — almost all of its ROE.")
doc.add_heading("EVA, CVA, distress and the scorecard", 2)
para(f"EVA was negative throughout — FY26: {cr(D['EVA = NOPAT − WACC × opening NOA'][2])} (DLF), {cr(G['EVA = NOPAT − WACC × opening NOA'][2])} (Godrej), {cr(P['EVA = NOPAT − WACC × opening NOA'][2])} (Phoenix). "
     f"Cash value added tells a different story for DLF: free cash flow of {cr(D['Free cash flow = CFO − capex'][3])} exceeds its capital charge because customers pay early. "
     f"Godrej's statutory free cash flow, after land purchases, was {cr(G['Free cash flow = CFO − capex'][3])}. Godrej's original Altman Z fell to {G['Z'][3]:.2f} ('distress'), but the emerging-market Z'' — which drops the "
     f"sales/assets term that penalises any developer — is {G['Zpp'][3]:.2f} (grey); DLF ({D['Zpp'][3]:.2f}) and Phoenix ({P['Zpp'][3]:.2f}) are safe.")
table(["Perspective", "DLF", "Godrej", "Phoenix"],
      [["Financial", "Net cash; EVA < 0, CVA > 0", "Leverage up; pre-land OCF ₹7,830 cr, all reinvested", f"ROIC {pc(P['ROIC = NOPAT / avg invested capital'][3])}; closest to EVA break-even"],
       ["Customer", "Luxury buyers pre-pay", "Brand pulls sales ahead of revenue", "Footfall and tenant sales"],
       ["Internal process", "Delivering large launches on time", "Land-to-launch speed", "Leasing, occupancy, tenant mix"],
       ["Learning & growth", "Rental platform with GIC", "Project management at scale", "New-city malls in CWIP"]], [3.0, 4.4, 4.5, 4.6], "Balanced scorecard.", size=8)

# ================================================================ 6 COST OF CAPITAL
doc.add_heading("6. Cost of capital: the decision that decides the answer", 1)
module_tag("Module 6 · risk-free rate, ERP, CRP; regression, bottom-up and industry beta; Kd; WACC; multi-factor check")
para(f"Risk-free rate. The 10-year G-Sec yields {pc(I['India 10-yr G-Sec yield'],2)}. It contains India's sovereign default spread ({pc(I['India sovereign default spread (Baa3)'],2)}), which we remove to get a rupee "
     f"risk-free rate of {pc(I['Rupee risk-free rate = G-Sec − default spread'],2)}. Equity risk premium. Damodaran's implied mature-market premium ({pc(I['Mature market ERP'],2)}) plus India's country "
     f"risk premium ({pc(I['India country risk premium (CRP)'],2)}) gives {pc(I['India total ERP = mature ERP + CRP'],2)}. History agrees, loosely: over 2005–2026 the Sensex beat the G-Sec by "
     f"{pc(HE['Geometric excess (total)'])} a year geometrically, but with a standard error of {pc(HE['Standard error of arithmetic mean'])} — too noisy to estimate a premium from, which is why we use the implied figure.")
fig("beta_scatter", "Figure 7 — Regression betas, 60 monthly returns against the Nifty 50.", 12.5)
para(f"Regression beta. DLF {dl['Raw beta (SLOPE)']:.2f} (SE {dl['Std error of beta']:.2f}, R² {dl['R-squared']:.2f}), Godrej {gp['Raw beta (SLOPE)']:.2f} (SE {gp['Std error of beta']:.2f}), Phoenix {ph['Raw beta (SLOPE)']:.2f} "
     f"(SE {ph['Std error of beta']:.2f}). Godrej's 95% interval of {gp['95% CI low']:.2f}–{gp['95% CI high']:.2f} alone moves its cost of equity by about seven points.")
fig("rolling_beta", "Figure 8 — Beta drifts: rolling 36-month beta, 2010–2026.", 13)
para(f"Beta is not a constant (H3). Phoenix's rolling beta has ranged from {RB['Phoenix'][0]:.2f} to {RB['Phoenix'][1]:.2f}, Godrej's from {RB['Godrej'][0]:.2f} to {RB['Godrej'][1]:.2f}. "
     f"A single five-year regression is one draw from a moving target. Bottom-up beta. Unlevering {len(N['BU'])} large developers at market D/E and taking the median gives "
     f"{N['BU_median']:.2f}, relevered to {D['W Beta used']:.2f} for DLF and {G['W Beta used']:.2f} for Godrej. For Phoenix — a rental business — developer betas overstate risk; listed REITs "
     f"have betas of 0.1–0.4 with R² below 12%, so we use Phoenix's own Blume-adjusted beta ({P['W Beta used']:.2f}).")
para(f"Industry lens. Damodaran's India dataset gives an unlevered beta of {IB['Unlevered beta, cash-corrected'][0]:.2f} for 156 developers and {IB['Unlevered beta, cash-corrected'][1]:.2f} "
     f"for real-estate operators. These averages are dragged down by thinly traded small caps, whose prices react to the market with a lag (H2). We carry them as lens B "
     f"rather than discard them, because they show how sensitive the answer is. A Dimson (1979) test confirms the bias: adding last month's market return raises the median peer beta "
     f"from 1.47 to 1.59, and lifts small caps such as Puravankara (1.69 → 2.43) and Anant Raj (1.66 → 2.27) far more than DLF (1.70 → 1.72). For Phoenix, lens B implies a cost of equity of {pc(P['W_B']['ke'])} — below the G-Sec — so we treat it as an upper bound.")
fig("rate_factor", "Figure 9 — Rate sensitivity from a two-factor model (market + change in the 10-year G-Sec), 2012–2026.", 11)
para(f"Beyond CAPM. A two-factor model adds the monthly change in the G-Sec. Developers lose about {pc(-RF['DLF'][2],0)}–{pc(-RF['Godrej'][2],0)} per +100bp after controlling for the market, "
     f"but with t-statistics of only {RF['DLF'][4]:.1f} to {RF['Godrej'][4]:.1f}; Phoenix shows no rate exposure. Rate risk is real but noisy (H4), so CAPM remains our base.")
table(["", "DLF", "Godrej", "Phoenix"],
      [["Lens A beta / Ke", f"{D['W Beta used']:.2f} / {pc(D['W Cost of equity (CAPM)'])}", f"{G['W Beta used']:.2f} / {pc(G['W Cost of equity (CAPM)'])}", f"{P['W Beta used']:.2f} / {pc(P['W Cost of equity (CAPM)'])}"],
       ["Lens B beta / Ke", f"{D['W_B']['beta']:.2f} / {pc(D['W_B']['ke'])}", f"{G['W_B']['beta']:.2f} / {pc(G['W_B']['ke'])}", f"{P['W_B']['beta']:.2f} / {pc(P['W_B']['ke'])}"],
       ["Synthetic rating (cash cover) / pre-tax Kd", f"{D['W Synthetic rating']} / {pc(D['W Pre-tax Kd used'])}", f"{G['W Synthetic rating']} / {pc(G['W Pre-tax Kd used'])}", f"{P['W Synthetic rating']} / {pc(P['W Pre-tax Kd used'])}"],
       ["Debt / capital (market)", pc(D['W D / V']), pc(G['W D / V']), pc(P['W D / V'])],
       ["WACC lens A / lens B", f"{pc(D['W WACC'])} / {pc(D['W_B']['wacc'])}", f"{pc(G['W WACC'])} / {pc(G['W_B']['wacc'])}", f"{pc(P['W WACC'])} / {pc(P['W_B']['wacc'])}"],
       ["Damodaran industry WACC (₹)", pc(IB['Cost of capital (local currency)'][0]), pc(IB['Cost of capital (local currency)'][0]), pc(IB['Cost of capital (local currency)'][1])]], [6.2, 3.4, 3.4, 3.4], size=8.5)

# ================================================================ 7 INTRINSIC
doc.add_heading("7. Intrinsic valuation", 1)
module_tag("Module 7 · growth estimation, FCFF, FCFE, APV, EVA, residual income, DDM, real options, scenarios")
para(f"Growth. Historical revenue growth was {pc(D['Revenue CAGR FY23→FY26'])} (DLF), {pc(G['Revenue CAGR FY23→FY26'])} (Godrej) and {pc(P['Revenue CAGR FY23→FY26'])} (Phoenix). Fundamental growth "
     "(reinvestment rate × ROIC) fails for developers — DLF's reinvestment is negative because advances shrink its capital, and Godrej's ROIC is near zero — so growth "
     "comes from sales already made but not yet recognised, visible in customer advances, and reinvestment is tied to growth through a sales-to-capital ratio.")
table(["Assumption", "DLF", "Godrej", "Phoenix"],
      [["Revenue growth FY27–31 (then fades to 5.5%)", " / ".join(pc(g, 0) for g in D['DCF growth']), " / ".join(pc(g, 0) for g in G['DCF growth']), " / ".join(pc(g, 0) for g in P['DCF growth'])],
       ["Core EBIT margin FY26 → target", f"{pc(D['Core EBIT margin'][3],0)} → {pc(D['DCF margin'],0)}", f"{pc(G['Core EBIT margin'][3],0)} → {pc(G['DCF margin'],0)}", f"{pc(P['Core EBIT margin'][3],0)} → {pc(P['DCF margin'],0)}"],
       ["Sales-to-capital (marginal)", f"{D['DCF s2c']:.1f}", f"{G['DCF s2c']:.1f}", f"{P['DCF s2c']:.1f}"],
       ["WACC years 1–5 → stable (β → 1)", f"{pc(D['W WACC'])} → {pc(D['DCF stableWACC'])}", f"{pc(G['W WACC'])} → {pc(G['DCF stableWACC'])}", f"{pc(P['W WACC'])} → {pc(P['DCF stableWACC'])}"]],
      [5.4, 3.7, 3.7, 3.7], size=8)
para("Reality check. We tested every FY27 assumption against the two FY27 quarters already reported. DLF's revenue fell 37% year on year in H1 FY27 as recognition "
     "paused between project completions, so we cut its FY27 growth from +40% to −15% and moved the step-up to FY28–30, when Privana and the Dahlias complete; the new path needs only "
     "about 7% growth in H2. Godrej's H1 revenue more than doubled and Phoenix's rose 14%, both consistent with our assumptions (Quarterly sheet).")
para(f"How aggressive is that? Against a naive linear trend of FY23–26 revenue (Excel FORECAST, the method earlier cohorts used), our FY31 revenue is {NAIVE['DLF']:.1f}x the trend for DLF, "
     f"{NAIVE['GPL']:.1f}x for Godrej and {NAIVE['PML']:.1f}x for Phoenix. The developers' multiples are deliberate: four years of completion-based revenue say little about sales already contracted, "
     "which customer advances (2.9x and 7.8x revenue) show are far larger. Even so generous a path leaves value below price — the conclusion does not depend on a conservative forecast.")
fig("dcf_paths", "Figure 10 — Revenue and margin paths in the ten-year FCFF model.", 13)
table(["₹ crore", "DLF", "Godrej", "Phoenix"],
      [[k, *[(pc(d['DCF'][k]) if "%" in k else f"{d['DCF'][k]:,.0f}") for d in (D, G, P)]] for k in
       ["PV of FCFF FY27–FY36", "PV of terminal value", "Value of operating assets", "Terminal value as % of operating value", "Add: cash & liquid investments (FY26)",
        "Add: JV / associate investments", "Less: total debt incl. leases", "Less: minority interest (proportional)", "Equity value to owners",
        "Intrinsic value per share (Rs)", "Current market price (Rs)"]], [6.5, 3.2, 3.2, 3.2], size=8.5)
para(f"DCCDL is valued by capitalising DLF's share of its profit ({cr(D['DCCDL']['jv_pat'])}) at Ke less growth: {cr(D['DCCDL']['value'])}, almost exactly its book value of {cr(D['DCCDL']['book'])}. "
     f"The same cash flows valued through EVA (invested capital plus PV of EVA) reproduce the FCFF value to the rupee (difference {N['DLF']['EVA_diff']:.0f}); APV confirms debt adds little — DLF is net "
     "cash and Godrej's tax shield is offset by distress risk.")
doc.add_heading("What the price implies", 2)
fig("lens_compare", "Figure 11 — DCF value under both lenses and a bull case, against price.", 12.5)
fig("implied_growth", "Figure 12 — The perpetual growth rate each price implies.", 10)
para(f"Sensitivity grids move DLF between {rs(D['gridA_min'])} and {rs(D['gridA_max'])} and no sensible combination reaches the price. Solving the model backwards: the price needs a target margin "
     f"of {pc(D['implied margin'],0)} for DLF and {pc(P['implied margin'],0)} for Phoenix (impossible), or a uniform discount rate of {pc(D['implied WACC'])}, {pc(G['implied WACC'])} and {pc(P['implied WACC'])}, "
     f"or — holding our discount rates — perpetual growth of {pc(imp['DLF']['terminal_g'])}, {pc(imp['GPL']['terminal_g'])} and {pc(imp['PML']['terminal_g'])}. The third is the most economically meaningful: "
     "investors are treating these firms as perpetual claims on Indian nominal GDP. That is not irrational for an economy the IMF expects to grow 7% in real and about 10% in nominal terms in FY27 "
     "(nominal growth slowed to 8–8.5% in FY26 on low inflation), but it "
     "abandons the textbook discipline that terminal growth should not exceed the risk-free rate, and it leaves little margin of safety: the spread between the stable "
     f"discount rate and the implied growth is only {(D['DCF stableWACC']-imp['DLF']['terminal_g'])*100:.1f}, {(G['DCF stableWACC']-imp['GPL']['terminal_g'])*100:.1f} and {(P['DCF stableWACC']-imp['PML']['terminal_g'])*100:.1f} percentage points (H1).")
doc.add_heading("Scenarios and simulation", 2)
table(["₹ per share", "Bear", "Base", "Bull", "Bull + lens B", "Price"],
      [[n, *[f"{scn[c][k]:,.0f}" for k in ("bear", "base", "bull", "bull_lensB", "price")]] for n, c in [("DLF", "DLF"), ("Godrej Properties", "GPL"), ("Phoenix Mills", "PML")]],
      [4.0, 2.4, 2.4, 2.4, 2.8, 2.4], "Bear: growth ×0.6, margin −8pp, S/C ×0.75, WACC +1pp, g 5%. Bull: growth ×1.3, margin +8pp, S/C ×1.25, WACC −1pp, g 6%.", size=8.5)
fig("monte_carlo", "Figure 13 — 10,000-draw Monte Carlo on growth, margin, capital intensity, discount rates and terminal growth.", 13)
para(f"Godrej is the only stock with a meaningful chance of being cheap: {pc(MC['GPL']['A']['prob_above_price'],0)} under lens A and {pc(MC['GPL']['B']['prob_above_price'],0)} under lens B, because its "
     "value is the most sensitive to whether margins normalise. Godrej clears its price in the bull case under either lens; DLF and Phoenix do not clear it even then.")
doc.add_heading("Other intrinsic routes", 2)
para(f"Residual income (Palepu). With ROE fading to 15% over ten years, abnormal-earnings value is {rs(N['DLF']['RI']['Value per share — lens A (₹)'])} for DLF and {rs(N['GPL']['RI']['Value per share — lens A (₹)'])} for Godrej under lens A. "
     f"The justified P/B on current ROE is {N['DLF']['RI']['Justified P/B on current ROE — lens A']:.2f} for DLF against a market P/B of {RV['DLF Ltd'][13]:.2f}; put the other way, DLF's price "
     f"implies a sustained ROE of {pc(N['DLF']['RI']['ROE the market price implies (lens A Ke) = g + P/B × (Ke − g)'],0)}. Part of this gap is accounting: land bought decades ago sits in book value "
     "at cost, so book understates economic capital and ROE overstates economic returns (H7). For developers, net asset value is a better anchor than book. "
     f"Palepu's abnormal-earnings-growth model, which starts from earnings rather than book, lands in the same place ({rs(AEG['DLF'])} for DLF, {rs(AEG['GPL'])} for Godrej, {rs(AEG['PML'])} for Phoenix): "
     f"the price capitalises next year's earnings at {FPE['DLF']:.0f}x, {FPE['GPL']:.0f}x and {FPE['PML']:.0f}x against a no-growth multiple (1/Ke) of about 6–8x.")
para(f"DDM. A two-stage dividend model, using dividends declared in the last twelve months, gives {rs(D['DDM']['DDM value per share (Rs)'])} for DLF, {rs(G['DDM']['DDM value per share (Rs)'])} for Godrej "
     f"and {rs(P['DDM']['DDM value per share (Rs)'])} for Phoenix. Godrej paid nothing from FY17 to FY26 and resumed with ₹10 a share in FY27; DLF's dividend has compounded about 4% a year since FY16. Payouts are low, so dividends capture little of the value. Real options. Undeveloped land is a call option on developed property "
     f"(Damodaran). An illustrative land bank worth ₹90,000 cr developed, costing ₹1,00,000 cr to build — negative NPV today — is still worth {cr(RO['Option value = S·e^(−yT)·N(d1) − K·e^(−rT)·N(d2)'])} "
     f"as an option at 30% volatility over ten years. DLF's market value exceeds our DCF equity value by {cr(RO['DLF: market cap − DCF equity value (₹ cr)'])}; land-bank optionality is one candidate explanation.")

# ================================================================ 8 RELATIVE
doc.add_heading("8. Relative valuation", 1)
module_tag("Module 8 · four-step process; P/E, PEG, P/B, P/S, EV/EBITDA; controlling for differences")
para(f"Step one, comparables: {N['n_peers']} listed developers from ₹4,600 cr to ₹1.2 lakh cr market value. Step two, standardise: FY26 consolidated figures, one price date. "
     "Step three, distribution: medians and inter-quartile ranges, because a few firms have depressed earnings (Sobha and Puravankara trade above 70x). "
     "Step four, control for differences: regress P/B on ROE.")
rvrows = [[r[0].replace(" Ltd", "").replace(" (Macrotech)", ""), *[("n.m." if isinstance(r[i], str) else (f"{r[i]:.1f}" if i != 13 else f"{r[i]:.2f}")) for i in (12, 13, 14, 15)],
           ("n.m." if isinstance(r[16], str) else f"{r[16]:.2f}"), pc(r[11])] for r in N["RelVal"]]
rvrows.append(["Peer median", f"{med[0]:.1f}", f"{med[1]:.2f}", f"{med[2]:.1f}", f"{med[3]:.1f}", f"{med[4]:.2f}", ""])
table(["Company", "P/E", "P/B", "P/S", "EV/EBITDA", "PEG", "ROE"], rvrows, [4.6, 1.8, 1.8, 1.8, 2.2, 1.8, 1.8], size=8)
fig("pb_roe", "Figure 14 — P/B against ROE across the peer set.", 10.5)
reg = N["Reg"]; ri = N["RelImplied"]
para(f"The regression (P/B = {reg['a']:.2f} + {reg['b']:.1f} × ROE, R² {reg['r2']:.2f}; Signature Global excluded because its 85% ROE reflects a tiny post-IPO equity base) explains little: cost-based book values and land banks break the link between "
     "current ROE and price. We use it as a cross-check.")
table(["Implied value (₹/share)", "P/E median", "P/E IQR", "P/B median", "EV/EBITDA median", "P/B on ROE"],
      [[k, f"{v[0]:,.0f}", f"{v[1]:,.0f}–{v[2]:,.0f}", f"{v[3]:,.0f}", f"{v[6]:,.0f}", f"{v[8]:,.0f}"] for k, v in ri.items()], [4.6, 2.4, 3.0, 2.4, 2.8, 2.4], size=8.5)
fig("cap_rates", "Figure 15 — The yield investors accept on Phoenix versus listed REITs and the G-Sec.", 11)
para(f"For an income-producing owner the right relative measure is yield. Phoenix's enterprise value (including minorities at market value) is {cr(CAP['ev'])} against EBITDA of {cr(CAP['ebitda'])} — "
     f"a {pc(CAP['yield'])} yield, {-CAP['spread']*100:.1f} percentage points below the G-Sec. Listed REITs yield {pc(CAP['reit_median'])}. Priced at the mall REIT's yield, Phoenix would be worth about "
     f"{rs(CAP['pml_at_reit'])} a share. The premium over that is payment for growth a REIT cannot fund, because it must distribute 90% of its cash (H8).")

# ================================================================ 9 PRACTITIONER VIEW
KPI = N["KPI"]; NAV = N["NAV"]
doc.add_heading("9. The practitioner's view: operating KPIs, NAV and the sell-side", 1)
module_tag("Cross-check · company disclosures · sum-of-the-parts · broker consensus")
para("A sector analyst would not sign off a developer valuation built only on recognised revenue. The market trades on sales bookings, collections, "
     "launch pipelines and rental growth, and the sell-side values developers on net asset value. We collected these from public reports of company "
     "results and broker notes, verified our dataset against them, and rebuilt the practitioner method.")
table(["FY26 (₹ crore)", "DLF", "Godrej", "Phoenix"],
      [["Sales bookings / collections", f"{KPI['Sales bookings (pre-sales) FY26'][0]:,.0f} / {KPI['Customer collections FY26'][0]:,.0f}", f"{KPI['Sales bookings (pre-sales) FY26'][1]:,.0f} / {KPI['Customer collections FY26'][1]:,.0f}", "—"],
       ["Bookings ÷ recognised revenue", f"{KPI['Bookings ÷ recognised revenue FY26 (x)'][0]:.1f}x", f"{KPI['Bookings ÷ recognised revenue FY26 (x)'][1]:.1f}x", "—"],
       ["FY27 guidance (bookings)", f"{KPI['Bookings guidance FY27'][0]:,.0f}", f"{KPI['Bookings guidance FY27'][1]:,.0f}", "Double-digit consumption growth"],
       ["Retail consumption / rental income", "—", "—", f"{KPI['Retail consumption FY26'][2]:,.0f} / {KPI['Retail rental income FY26'][2]:,.0f}"],
       ["Rental platform", f"DCCDL EBITDA {KPI['Rental platform (DCCDL) EBITDA FY26'][0]:,.0f}; ~50 msf, ~95% let", "—", f"Retail EBITDA {KPI['Retail EBITDA FY26'][2]:,.0f}"],
       ["Net cash / debt", f"Dev. net cash {KPI['Company-reported net cash (development) FY26'][0]:,.0f}; DCCDL net debt {KPI['DCCDL net debt Q4 FY26'][0]:,.0f}", "Pre-land OCF 7,830", "—"]],
      [4.4, 4.6, 3.6, 3.9], "Sources: company results and calls as reported by the financial press (see the Operating_KPIs sheet for each source).", size=8)
dcx = N["DataCheck"]
para(f"Verification. Our profit lines match the companies (Godrej ₹1,850 cr and Phoenix ₹1,224 cr exactly; DLF within 0.2%). Revenue and cash differ by definition: our DLF revenue "
     f"is {pc(-dcx[0][3],1)} below 'revenue from operations' as reported, and our DLF net cash excludes ₹5,003 cr of RERA-restricted cash. DLF's share of JV profit in our data "
     f"(₹{dcx[7][1]:,.0f} cr) is within {pc(abs(dcx[7][3]),0)} of 66.66% of DCCDL's reported profit, confirming that line is essentially DCCDL. Against DLF's audited FY26 annual report, our equity, total assets, inventory, share of JV profit and operating cash flow match to the rupee, and the RERA balances in its notes (about ₹11,170 cr) confirm the escrow figure management gave on its call. Godrej's audited FY26 statements tie equally exactly (total assets ₹81,894 cr, inventory ₹57,807 cr, profit ₹1,841 cr, operating cash flow −₹2,003 cr); its other income of ₹3,279 cr is 39% of total income.")
fig("nav_bridge", "Figure 17 — Rebuilding NAV from public data: DLF's parts versus its market value; Phoenix's NAV versus price.", 13)
para(f"DLF. At the 7.5% cap rate a leading broker uses, DCCDL is worth {cr(NAV['dccdl_gav'])} gross and DLF's stake {cr(NAV['dccdl_stake'])} after DCCDL's debt — more than twice the "
     f"{cr(D['DCCDL']['value'])} we get by capitalising DLF's share of DCCDL's after-tax profit at our cost of equity. That gap is itself a finding: a 7.5% cap rate on EBITDA embeds a far lower "
     f"required return than CAPM gives. Adding five years of pipeline margin at guided sales ({cr(NAV['dlf_res_pv'])}) and net cash gives identifiable NAV of {rs(NAV['dlf_nav_ps'])} a share, "
     f"close to our DCF ({rs(NAV['dlf_nav_ps'])}–{NAV['dlf_nav_ps_hi']:,.0f} if all of the ₹24,500 cr of gross margin management says is still to be recognised on sold units were added; part of it already sits in net cash). The market's remaining {cr(NAV['dlf_land'])} is, by elimination, the value placed on land beyond the visible pipeline: about ₹{NAV['dlf_psf']:,.0f} per sq ft of the "
     f"112 million sq ft of potential outside the launch pipeline (137 msf balance potential per management, less ~25 msf in the pipeline), against a book value of about ₹{NAV['dlf_book_psf']:,.0f} per sq ft of inventory and land (H7). That is the real-option argument in rupees.")
para(f"Phoenix. Retail EBITDA at a 7% cap rate, offices at 8%, hotels at 12x EBITDA and work-in-progress at cost give a NAV to owners of {rs(NAV['pml_nav_ps'])} a share; the price is "
     f"{pc(NAV['pml_prem'],0)} above it. A 7% cap rate at the 11.75% discount rate an Indian REIT valuer uses implies perpetual rent growth of {pc(NAV['pml_g_in_cap'],2)}, so practitioners' own "
     "conventions sit close to our 5.5% terminal growth. What closes the gap is an explicit growth premium; one broker adds 70% to its NAV.")
para(f"Godrej. Brokers value Godrej on the profit already embedded in its sales. Twelve times FY28 embedded profit (bookings of {cr(NAV['gpl_emb_pat']/0.15)} at a 15% margin) gives "
     f"{rs(NAV['gpl_emb_ps'])} a share, against a price of {rs(G['DCF']['Current market price (Rs)'])} and broker consensus near {rs(NAV['gpl_consensus'])}. A 12x multiple is itself a perpetual-growth "
     f"assumption: at our cost of equity it implies growth of {pc(NAV['gpl_g_in_mult'])}. Godrej does not disclose an embedded margin, so we test 12–18% margins and 10–14x multiples: "
     f"value ranges from {rs(NAV['gpl_grid_lo'])} to {rs(NAV['gpl_grid_hi'])}, and only the harshest combination falls below the price.")
para("The latest quarter (Q2 FY27) sharpens each story. DLF booked ₹3,800 cr, taking H1 to ₹4,457 cr against ₹20,000 cr full-year guidance — the year now rests on "
     "second-half launches, a real execution risk; net cash rose to ₹15,100 cr. Godrej's H1 bookings rose 7% to ₹16,659 cr and collections 25% to ₹9,666 cr, with H1 operating cash flow of "
     "₹1,983 cr — cash conversion, the risk we flagged, is improving. Phoenix's retail rental income grew 16% in H1 and management guides 14–15% for FY27–28, almost exactly our DCF path. "
     "Relative to its own history the sector is not stretched: the Nifty Realty index trades at about 40x earnings against a five-year median near 48x. But those five years were the up-cycle; "
     "measured against intrinsic value, not recent multiples, the premium remains.")
doc.add_heading("What management says: transcripts, guidance and BRSR", 2)
MG = N["MGMT"]; ES = N["ESG"]; gc = {r[0]: r for r in N["GC"]}
para("We read the companies' own earnings-call transcripts (DLF and Phoenix Q4 FY26; Godrej Q2 FY27) and sustainability filings (DLF BRSR FY25, Godrej BRSR FY26, DCCDL "
     "Sustainability Report FY26). Three findings change how our numbers should be read. First, DLF's headline net cash is mostly not free: management "
     "said about ₹11,200 cr of the ₹14,155 cr sits in RERA escrow accounts, released only as projects complete in FY27–28. Second, DLF guides to "
     "₹9,000–10,000 cr of new margin and ₹7,000–8,000 cr of development free cash flow every year — cash that recognised revenue, booked only on "
     f"completion, reports years late. Capitalising management's own ₹{MG['fcf']:,.0f} cr at our cost of equity, growing 5% a year, gives a development business "
     f"worth {cr(MG['dev'])}; adding DCCDL and free net cash gives {rs(MG['ps'])} a share, or {rs(MG['ps_nav'])} with DCCDL at the 7.5% cap rate — still below the "
     f"{rs(price['DLF'])} price. On management's numbers, the market is paying for land beyond any guided horizon. Third, guidance has been credible: DLF met its "
     f"FY26 bookings guide ({pc(gc['DLF FY26 sales bookings (₹ cr)'][3],0)}) and Godrej beat its own ({pc(gc['Godrej FY26 bookings (₹ cr)'][3],0)}), though Godrej missed "
     f"its collections target ({pc(gc['Godrej FY26 collections (₹ cr)'][3],0)}) and DLF's H1 FY27 run-rate is only {pc(gc['DLF H1 FY27 bookings vs pro-rata FY27 guidance (₹ cr)'][3],0)} of pro-rata guidance.")
para(f"Phoenix's call supports our forecast: retail rental growth guided at 14–15% for FY27–28, with 36–50% of leased area renewing in two to three years at about 20% "
     f"uplifts; offices are 70% occupied (EBITDA ₹141 cr) and hotels earned ₹276 cr. On ESG, DLF used {ES['DLF total energy consumed (GJ)'][0]/1e6:.2f} million GJ in FY25, "
     f"{pc(ES['Renewable share'][0],0)} renewable (up from {pc(ES['Renewable share'][1],0)}); women are only 10% of employees and their turnover ({pc(ES['Employee turnover (male / female)'][1],0)}) "
     f"is almost twice men's — a social-pillar flag. DCCDL's emissions were flat at about {ES['DCCDL total emissions (ktCO2e)'][0]:,.0f} ktCO2e while rent grew about 15%, and its "
     "whole rental portfolio is LEED Platinum. That matters for value: green Grade-A offices are what multinational tenants and global capital (GIC, CPPIB) require, "
     "and they explain DCCDL's 98–99% non-SEZ occupancy. Godrej's FY26 BRSR is the contrast: women are 38% of permanent staff (DLF 10%), renewables 33% of energy (15% a year earlier), zero lost-time injuries — but its boundary covers only its own sites, not contractors, so the energy totals are not comparable with DLF's. Phoenix's filings could not be retrieved; we did not use second-hand ESG figures for it.")
fig("practitioner_vs_textbook", "Figure 18 — Textbook DCF, practitioner NAV, broker targets and price.", 12.5)
bk_ = {r[0]: r for r in N["Brokers"] if r[0] in ("DLF Ltd", "Godrej Properties", "Phoenix Mills")}
para(f"The sell-side sits close to the market: median targets are {rs(bk_['DLF Ltd'][1])} for DLF, {rs(bk_['Godrej Properties'][1])} for Godrej and {rs(bk_['Phoenix Mills'][1])} for Phoenix, against prices of "
     f"{rs(price['DLF'])}, {rs(price['GPL'])} and {rs(price['PML'])}. The difference from our DCF is not arithmetic; it is the required return (asset-level 11.75–12% and cap rates of 6.5–8%, "
     "against CAPM rates of 13–15%) and the willingness to pay for land and growth beyond any explicit forecast. Brokers and our model agree on the ranking: "
     "Godrej offers the most upside, DLF is roughly fair, Phoenix is fully priced (H9).")

# ================================================================ 10 THROUGH TIME
E = N["EV"]; DLY = N["Delay"]; RO = N["REITopt"]; SV = E["survivorship"]; BK = E["by_kind"]; ER = E["earnings"]
mm = {r["event"].split(" (")[0]: r for r in E["macro"]}
def mcar(k, s): return (mm[k].get(s) or {}).get("ann")
def mb(k, s): return (mm[k].get(s) or {}).get("bhar250")
doc.add_heading("10. Through time: announcements, shocks, survivors and REITs", 1)
module_tag("Event studies · market efficiency · survivorship · REIT instruments · value of delay")
para("A valuation at one date hides how the market has priced news in the past. We ran market-model event studies on daily prices since 2007: abnormal "
     "return = actual return less the return the stock's beta against the Nifty predicts, estimated over the year before each event and summed over three days.")
fig("event_macro", "Figure 99 — Three-day abnormal returns around seventeen macro, regulatory and REIT events.", 13.5)
para(f"Shocks hit hard but briefly. Demonetisation cost DLF {pc(mcar('Demonetisation','DLF'),0)} in three days, the COVID lockdown {pc(mcar('COVID national lockdown','DLF'),0)}, "
     f"the IL&FS credit freeze cost Godrej {pc(mcar('IL&FS / DHFL credit shock','GPL'),0)}; yet a year later DLF was {pc(mb('Demonetisation','DLF'),0)} and {pc(mb('COVID national lockdown','DLF'),0)} ahead of the Nifty "
     f"and Godrej {pc(mb('IL&FS / DHFL credit shock','GPL'),0)} ahead (H11). These were repricings of timing, not of franchise value. REIT listings barely registered (|CAR| ≤ 4%, none significant): "
     "the market already knew rental assets could be monetised. Rate decisions moved prices less than the rate-sensitivity debate suggests, and cuts were often 'sold on the news'. "
     "Single-event figures can be contaminated by same-week company news (Godrej's jump at RERA's start, Phoenix's fall in late August 2020), so we rely on averages and t-statistics.")
para(f"Company news tells a sharper story. Asset monetisations — GIC's purchase of a third of DCCDL (2017), Phoenix's GIC platform (2020–21) and its CPPIB buy-out (2025) — earned "
     f"{pc(BK['monetisation']['ann'])} on average (t {BK['monetisation']['t_cs']:.1f}): the market rewards proof that private capital values rental assets above book. DLF's sell-out "
     f"launches averaged {pc(BK['launch']['ann'])} (The Arbour, ₹8,000 cr in three days: +7.4%, t 3.0). Results days are different: across {sum(v['n'] for v in ER.values())} results announcements "
     f"since 2008, the EPS surprise explains only {pc(min(v['r2'] for v in ER.values()),0)}–{pc(max(v['r2'] for v in ER.values()),0)} of the price move and gets its direction right about half the time (H10). "
     "Under completion accounting, profit is old news; bookings and launches are the information. This is the strongest evidence for valuing developers on cash and pre-sales rather than earnings. "
     f"Equity issues show the mirror image: the five equity-issue announcements followed run-ups of {pc(BK['equity issue']['run'])}, mostly near the top of their three-year range (Godrej's three QIPs at the 85th–100th percentile), "
     f"and were followed by a drift of {pc(BK['equity issue']['drift'])} over sixty days (H12). Godrej's ₹6,000 cr QIP of November 2024 preceded a 33% fall relative to the Nifty.")
fig("survivors_reit", "Figure 99 — Left: survivors versus developers that failed. Right: REIT distribution yields against the 10-year G-Sec.", 13.5)
para(f"Survivorship and delivery. A sector index built from today's listed names flatters history. An equal-weighted basket of nine survivors returned {pc(SV['total']['survivors'],0)} since January 2008; "
     f"six developers that failed or stalled — Unitech, HDIL, Parsvnath, Ansal, Omaxe, Peninsula — lost {pc(-SV['total']['failed'],0)}, four of them more than 99%. Their betas were higher "
     f"(Unitech {SV['beta_2010_19']['UNITECH']:.2f}, HDIL {SV['beta_2010_19']['HDIL']:.2f}), so excluding them biases the industry beta down: our lens-A beta is a floor, not a midpoint. "
     f"Between demonetisation and COVID, quality developers rose {pc(SV['flight_to_quality']['quality'],0)} while the stressed basket fell {pc(-SV['flight_to_quality']['stressed'],0)}: RERA, escrow and the credit freeze turned "
     f"on-time delivery into a moat. Delay has a price even for survivors. If every cash flow slips a year, value falls by V × r/(1+r): ₹{DLY['dlf_ps']:.0f} a share for DLF on our DCF, ₹{DLY['gpl_ps']:.0f} for Godrej, "
     f"₹{DLY['pml_ps']:.0f} for Phoenix; on management's own cash-flow case DLF loses ₹{DLY['mgmt_ps']:.0f} a share per year of slippage. With H1 FY27 bookings at 45% of pro-rata guidance, that is a live risk.")
para(f"REITs as instruments. Listed REITs distribute at least 90% of cash and now yield {pc(E['reit']['latest_median'])} against a G-Sec of {pc(E['reit']['latest_gsec'])} — a spread of "
     f"{pc(E['reit']['latest_spread'])}, averaging {pc(E['reit']['mean_spread'])} since 2020: investors accept less than the risk-free rate because distributions grow. Yet monthly changes in REIT yields do not "
     f"explain developer returns (|t| < 1): DLF and Phoenix are priced as growth stocks, not yield vehicles (H8). The REIT market is nonetheless Phoenix's exit option: at the mall REIT's yield its retail EBITDA "
     f"is worth {cr(RO['at_reit'])}, against {cr(RO['at_capm'])} on our CAPM rate — {pc(RO['prem'],0)} more. The CPPIB and GIC transactions show that option being exercised, and it explains why "
     "practitioner NAVs sit above our DCF.")

# ================================================================ 9 LOOSE ENDS
doc.add_heading("11. Loose ends", 1)
module_tag("Module 9 · cross holdings, minority interests, distress, liquidity")
bullets([("Cross holdings.", "DCCDL is valued separately and added to operating value rather than mixed into EBIT; consolidating it would double-count."),
         ("Minority interests.", "CPPIB and GIC own stakes in Phoenix's mall platforms; we deduct their share of value in proportion to their share of profit (about 21%). Phoenix is buying out CPPIB's 49% of Island Star Mall Developers for about ₹5,450 cr in four tranches over three years (its stake has reached 68.1%). Bought at a fair price this is value-neutral — cash out, minority leakage down — so we keep the FY26 minority share."),
         ("Distress.", f"Godrej's original Altman Z is in the distress zone and its cash cover is {G['Cash interest coverage: EBIT / interest paid (x)'][3]:.1f}x; we add an expected distress cost in the APV check."),
         ("Liquidity and control.", "All three are large and liquid, so no illiquidity discount applies; no control premium is relevant to a minority investor.")])

# ================================================================ 10 SYNTHESIS
doc.add_heading("12. Synthesis: what you have to believe", 1)
fig("football_field", "Figure 19 — Football field: every method against the market price.")
para("The methods disagree, and the disagreement is the finding. Relative valuation compares each stock with peers that are also expensive, so it cannot see a "
     "sector-wide premium; intrinsic valuation can. To own these stocks at today's prices you have to believe one of three things: that their cash flows will grow with "
     "India's economy for ever; that the right long-run cost of equity for Indian real estate is close to the government bond yield; or that land banks hold option "
     "value our cash-flow model does not capture. Each is defensible for some investors. None is a margin of safety.")
callout("Recommendation (relative, within the sector)", [
    f"Godrej Properties — preferred. Multiples at the peer median and the lowest of our three; the highest chance in our simulation of value exceeding price; valued above price on 12x embedded profit. Watch: collections vs ₹24,000 cr guidance, land spend, net debt.",
    f"DLF — neutral. Best balance sheet and a rental platform worth roughly its book value; fully priced for long-run growth. Watch: luxury demand, DCCDL monetisation.",
    f"Phoenix Mills — least preferred. Excellent assets priced at a {pc(CAP['yield'])} yield. Watch: rental growth on new malls, consumption, minority leakage."])
doc.add_heading("Limitations", 2)
bullets(["Four years of statements from one aggregated source, plus prices from 2007; operating KPIs and broker views come from public reports of company "
         "results and broker notes, not from the original filings, and should be checked against investor presentations.",
         "Two credible cost-of-capital lenses give materially different values; we report both rather than pretend one is correct.",
         "Growth and margin paths are judgements; the scenario grid, reverse DCF and Monte Carlo show how much each matters.",
         "Book-value metrics are distorted by cost-based accounting for land and investment property.",
         "Timing: the RBI's October 2026 rate hike and rising unsold inventory are the main near-term risks to the developers; our valuation does not depend on them, but the market prices will."])

doc.add_heading("References", 1)
for ref in ["Palepu, K., Healy, P. & Bernard, V. Business Analysis & Valuation: Using Financial Statements (3rd ed.). Cengage.",
            "Damodaran, A. Damodaran on Valuation (2nd ed.). Wiley.  ·  Damodaran, A. The Dark Side of Valuation (2nd ed.). Pearson, 2010.",
            "Damodaran Online, January 2026: country risk premiums; ratings and spreads; India industry betas, WACC, margins, ROE, multiples, reinvestment.",
            "Bank for International Settlements, residential property prices: India (nominal and real), via FRED (QINN628BIS, QINR628BIS).",
            "OECD (INDIRLTLT01STM) and IMF (INTGSBINM193N) 10-year government bond yields for India; India 3-month interbank rate (INDIR3TIB01STM), via FRED.",
            "Yahoo Finance: consolidated statements, quarterly results, dividend-adjusted price histories for 13 developers, 4 REITs and Indian indices.",
            "Altman, E. (1968), Journal of Finance 23(4); Altman, E. (2005), Emerging Markets Review 6(4).",
            "MacKinlay, A. C. (1997), Event studies in economics and finance, Journal of Economic Literature 35(1). Loughran, T. & Ritter, J. (1995), The new issues puzzle, Journal of Finance 50(1). Brown, S., Goetzmann, W. & Ross, S. (1995), Survival, Journal of Finance 50(3). Amihud, Y. (2002), Journal of Financial Markets 5(1).",
            "Blume, M. (1971), Journal of Finance 26(1). Hamada, R. (1972), Journal of Finance 27(2). Scholes, M. & Williams, J. (1977), Journal of Financial Economics 5(3). Dimson, E. (1979), Journal of Financial Economics 7(2).",
            "Real Estate (Regulation and Development) Act, 2016; Ind AS 23, 40, 111, 115.",
            "DLF Ltd, Integrated Annual Report 2025-26 (audited consolidated statements); Q4 FY26 earnings call transcript (May 2026); DLF Business Responsibility & Sustainability Report FY2024-25; DCCDL Sustainability Report FY2025-26.",
            "Godrej Properties Ltd, Integrated Annual Report 2025-26 (audited statements and BRSR); Q2 FY27 earnings call (October 2026). Phoenix Mills Ltd, Q4 FY26 earnings call transcript (April 2026)."]:
    p = doc.add_paragraph(ref, style="List Number"); p.paragraph_format.space_after = Pt(2)
    for r in p.runs:
        r.font.size = Pt(9)
doc.add_heading("Appendix — model map", 2)
table(["Sheets", "Module", "Content"],
      [["Inputs, Data_* (13 companies)", "1, 6", "Sourced inputs; standardised statements"], ["Recast", "3–4", "Operating / financing / JV split; capitalised interest"],
       ["Ratios, DuPont, AltmanZ, Growth_EVA, Quarterly, Industry_Benchmark", "5", "50 ratios; 3/5-step DuPont; Palepu; Z/Z''; EVA; TTM; industry comparison"],
       ["Beta_Monthly/Weekly/REIT, BottomUp_Beta, RollingBeta, RateFactor, HistERP, WACC", "6", "Regression statistics; bottom-up and industry lenses; rate factor; historical ERP"],
       ["DCF_*, ResidualIncome, Alt_Valuations, DDM, RealOption, Scenarios_Implied, MonteCarlo", "7", "FCFF, EVA, FCFE/APV, RI, DDM, options, scenarios, simulation"],
       ["RelVal, CapRates, Summary", "8", "Peer multiples, regression, cap rates, football field"],
       ["LongCycle, Housing", "Sector", "Prices since 2007 with drawdowns; BIS house prices"]], [7.6, 1.6, 7.3], size=8)
doc.add_heading("Appendix — concept coverage", 2)
cm = [r for r in _wbx["Concept_Map"].iter_rows(min_row=5, values_only=True) if r and r[0]]
table(["Module", "Concept / method", "Source", "Where applied"], [[str(a), b, c_, d_] for a, b, c_, d_ in cm], [1.4, 7.6, 2.6, 4.9], size=7.5)
OUT.parent.mkdir(parents=True, exist_ok=True); doc.save(OUT); print("saved", OUT)

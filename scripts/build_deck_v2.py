"""Presentation v2 — 14 slides, visual-first, every number from the model, speaker notes on each slide."""
import pathlib
exec(open(pathlib.Path(__file__).resolve().parent / "deck_common.py").read())
MC, SC = N["MC"], N["SC"]; imp, scn = SC["implied"], SC["scenarios"]
RV = {r[0]: r for r in N["RelVal"]}; med = N["RelStats"]["Median"]
CAP, LC, RB, RF, HS, IB = N["Cap"], N["LongCycle"], N["RollingBeta"], N["RateFactor"], N["Housing"], N["Industry"]
price = {c: N[c]["DCF"]["Current market price (Rs)"] for c in ("DLF", "GPL", "PML")}
vA = {c: N[c]["DCF"]["Intrinsic value per share (Rs)"] for c in ("DLF", "GPL", "PML")}
vB = {c: N[c]["lensB"]["vps"] for c in ("DLF", "GPL", "PML")}
cr = lambda x: f"₹{x:,.0f} cr"
BKMED = {r[0]: r[1] for r in N["Brokers"] if r[0] in ("DLF Ltd", "Godrej Properties", "Phoenix Mills")}
COL = {"DLF": ACC, "GPL": OCH, "PML": RUST}; NMS = {"DLF": "DLF", "GPL": "Godrej Properties", "PML": "Phoenix Mills"}


def card(s, x, y, w, h, big, small, color=ACC, bigsize=30):
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    r.fill.solid(); r.fill.fore_color.rgb = rgb("FFFFFF"); r.line.color.rgb = rgb(RULE); r.shadow.inherit = False
    rule(s, x, y, 0.06, color, h)
    tb(s, x + 0.2, y + 0.1, w - 0.3, h * 0.55, big, bigsize, color, HEAD, True)
    tb(s, x + 0.2, y + h * 0.58, w - 0.3, h * 0.4, small, 11, INK)


def below(shape, gap=0.1):
    return (shape.top + shape.height) / 914400 + gap


n = 0
# 1 TITLE --------------------------------------------------------------
n += 1
s = prs.slides.add_slide(BLANK); s.background.fill.solid(); s.background.fill.fore_color.rgb = rgb(BG)
rule(s, 0.6, 2.0, 0.9, ACC, 0.06)
tb(s, 0.6, 2.25, 12, 1.1, "Paying for the Future", 50, INK, HEAD, True)
tb(s, 0.6, 3.35, 11.5, 0.9, "What Indian real-estate equities are really priced on — DLF, Godrej Properties, Phoenix Mills", 20, ACC)
tb(s, 0.6, 5.5, 8, 0.9, ["ECON F355 · Business Analysis & Valuation · Prof. Mohit Kumar", "Group 27 · Saatvik Nagpal · Atharvaa Khanzode"], 13, MUTE)
for i, k in enumerate(["DLF", "GPL", "PML"]):
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(10.3 + i * 0.85), Inches(5.5), Inches(0.7), Inches(0.7))
    r.fill.solid(); r.fill.fore_color.rgb = rgb(COL[k]); r.line.fill.background(); r.shadow.inherit = False
    tb(s, 10.3 + i * 0.85, 6.25, 0.7, 0.3, k, 9, MUTE, BODY, True, PP_ALIGN.CENTER)
notes(s, "We valued the three business models of Indian real estate. Our title is our conclusion: today's prices pay for growth that is many years — arguably decades — away.")

# 2 ANSWER FIRST -------------------------------------------------------
n += 1
s = base("Investment summary", "The answer first: prices assume these firms grow with India for ever", n, "Summary, Scenarios_Implied")
for i, c in enumerate(["DLF", "GPL", "PML"]):
    x = 0.6 + i * 4.1
    card(s, x, 1.85, 3.85, 1.55, f"{imp[c]['terminal_g']:.1%}", f"{NMS[c]}: perpetual growth the price implies (we allow 5.5%)", COL[c], 34)
table(s, 0.6, 3.65, 12.13, [["₹ per share", "DLF", "Godrej", "Phoenix"],
                            ["Market price", rs(price['DLF']), rs(price['GPL']), rs(price['PML'])],
                            ["DCF — lens A (large-cap β) / lens B (industry β)", f"{vA['DLF']:,.0f} / {vB['DLF']:,.0f}", f"{vA['GPL']:,.0f} / {vB['GPL']:,.0f}", f"{vA['PML']:,.0f} / {vB['PML']:,.0f}"],
                            ["P(value > price), 10,000 simulations", f"{MC['DLF']['A']['prob_above_price']:.1%}", f"{MC['GPL']['A']['prob_above_price']:.0%}", f"{MC['PML']['A']['prob_above_price']:.0%}"],
                            ["Broker median target / our practitioner NAV", f"{BKMED['DLF Ltd']:,.0f} / {N['NAV']['dlf_nav_ps']:,.0f}", f"{BKMED['Godrej Properties']:,.0f} / {N['NAV']['gpl_emb_ps']:,.0f}", f"{BKMED['Phoenix Mills']:,.0f} / {N['NAV']['pml_nav_ps']:,.0f}"],
                            ["Versus 10 peers (P/E, P/B)", "Above median, in IQR", "At median", "Top of range"],
                            ["Relative ranking", "2", "1", "3"]], [5.4, 2.25, 2.25, 2.23], 11.5, 0.36)
method(s, "Seven valuation routes (FCFF ×2 lenses, residual income, EVA, DDM, multiples, cap rates) + reverse DCF + Monte Carlo · same numbers in the Excel model")
notes(s, "We start with the answer. Holding our discount rates, the prices of all three imply perpetual growth of 10 to 12 percent — about India's nominal GDP growth — double the 5.5 percent the textbook allows. Under either cost-of-capital lens, intrinsic value is well below price; in 10,000 simulations the chance that value exceeds price is negligible for DLF and Phoenix and about one in twenty for Godrej. Relative to peers, Godrej is the cheapest of the three and Phoenix the most expensive.")

# 3 HOW WE WORKED + HYPOTHESES ----------------------------------------
n += 1
s = base("Approach · Module 1", "Nine hypotheses, tested with twenty years of data", n, "Index")
steps = [("Data", "1"), ("Strategy", "2"), ("Accounting", "3"), ("Recast", "4"), ("Ratios · DuPont\nEVA · Z''", "5"), ("Beta · WACC\n2 lenses", "6"), ("DCF · RI · DDM\noptions · MC", "7"), ("Multiples\ncap rates", "8")]
for i, (t, m) in enumerate(steps):
    x = 0.6 + i * 1.53
    r = s.shapes.add_shape(MSO_SHAPE.CHEVRON if i else MSO_SHAPE.PENTAGON, Inches(x), Inches(1.8), Inches(1.5), Inches(0.85))
    r.fill.solid(); r.fill.fore_color.rgb = rgb("E4E8E6" if i % 2 else "D5DEDC"); r.line.fill.background(); r.shadow.inherit = False
    tb(s, x + 0.2, 1.84, 1.15, 0.78, t, 10, INK, BODY, True, PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    tb(s, x + 0.2, 2.68, 1.15, 0.25, f"M{m}", 9, MUTE, BODY, False, PP_ALIGN.CENTER)
H = [("H1", "Prices embed growth beyond textbook terminal", "Supported"), ("H2", "Large developers riskier than industry average", "Supported"),
     ("H3", "Beta unstable through the cycle", "Supported"), ("H4", "Developers hurt by rising rates", "Weak"),
     ("H5", "Realty stocks follow house prices", "Rejected"), ("H6", "Customer advances fund growth", "Supported (DLF)"),
     ("H7", "Book value understates capital", "Supported"), ("H8", "Phoenix priced for growth, not yield", "Supported"),
     ("H9", "Brokers reach price only via land & growth premia", "Supported")]
for i, (h, t, res) in enumerate(H):
    x = 0.6 + (i % 2) * 6.15; y = 3.05 + (i // 2) * 0.6
    tb(s, x, y, 0.6, 0.4, h, 14, ACC, HEAD, True)
    tb(s, x + 0.6, y + 0.03, 4.0, 0.4, t, 12.5, INK)
    clr = {"Supported": ACC, "Rejected": RUST, "Weak": OCH}.get(res.split(" ")[0], ACC)
    tb(s, x + 4.6, y + 0.03, 1.4, 0.4, res, 12, clr, BODY, True)
method(s, f"13 developers (12 in the beta work) × FY23–FY26 + 5 quarters · prices since 2007 (Sensex 1997) · BIS house prices 2009–26 · G-Sec IMF+OECD 2005–26 · Damodaran India industry data (156 firms) · 4 REITs")
notes(s, "Before modelling we wrote down nine hypotheses. Seven are supported, one is weak, and one — that realty stocks follow house prices — is rejected. We'll point to the evidence for each as we go. The data run as far back as we could reach: statements for 13 developers, prices since 2007, house prices since 2009.")

# 4 CYCLE ----------------------------------------------------------------
n += 1
s = base("Module 2 · The sector", "Two decades of boom and bust: DLF is still below its 2008 peak", n, "LongCycle, Housing")
pp = pic(s, "long_cycle", 0.6, 1.7, h=3.9)
card(s, 9.1, 1.85, 3.63, 1.15, f"{LC['DLF'][2]:.1%}", "DLF annual total return since its 2007 IPO", ACC, 26)
card(s, 9.1, 3.1, 3.63, 1.15, f"{LC['DLF'][3]:.0%}", "DLF's worst drawdown; Phoenix fell 90% too", RUST, 26)
card(s, 9.1, 4.35, 3.63, 1.15, f"{HS['Real house-price CAGR']:.1%}", "real growth in Indian house prices a year since 2009 (BIS)", OCH, 26)
method(s, f"Dividend-adjusted monthly prices; drawdown = price ÷ running peak − 1 (live formulas) · BIS nominal & real indices · correlation of annual changes stocks vs houses = {HS['Correlation: realty YoY vs house-price YoY (same quarter)']:.2f} (H5 rejected)")
notes(s, "This is the context most valuations miss. DLF listed at the top of the 2007 boom and is still below its December 2007 peak nineteen years later — a 2 percent annual return. Phoenix fell 90 percent in 2008. Meanwhile house prices grew only 3.5 percent a year in real terms. Equities swing far more than the physical market and don't track it quarter to quarter, so we reject the idea that realty stocks simply follow house prices.")

# 5 STRATEGY ------------------------------------------------------------
n += 1
s = base("Module 2 · Strategy", "RERA rewards brands that can pre-sell; malls reward location", n)
table(s, 0.6, 1.85, 6.3, [["Force", "Level", "Driver"], ["Entry", "Low–mod", "Land, approvals, RERA, brand trust"], ["Suppliers", "High", "Owners of prime land"],
                          ["Buyers", "Moderate", "Mid-income price-sensitive; luxury not"], ["Substitutes", "Moderate", "Renting, REITs; e-commerce for malls"],
                          ["Rivalry", "High ↓", "Fragmented, consolidating to listed"]], [1.3, 1.1, 3.9], 11)
table(s, 7.2, 1.85, 5.53, [["Business unit", "BCG", "Porter"], ["DLF luxury housing", "Star", "Focus-differentiation"], ["DLF DCCDL rental", "Cash cow", "Location"],
                           ["Godrej core cities", "Star", "Brand breadth"], ["Godrej new cities", "Question mark", "Land-led"], ["Phoenix malls", "Cash cow", "Location, tenant mix"]], [2.5, 1.45, 1.58], 11)
tb(s, 0.6, 4.3, 12.1, 1.8, [[("SPACE  ", True, ACC), ("DLF aggressive · Godrej competitive · Phoenix conservative–aggressive", False, INK)],
                            [("Value chain  ", True, ACC), ("developers win at land, approvals, pre-sales; Phoenix at leasing → sales-to-capital 2.0 vs 0.5 in the DCF", False, INK)],
                            [("Blind spots  ", True, ACC), ("DLF: luxury demand as structural · Godrej: bookings = cash · Phoenix: rents compound with GDP for ever", False, INK)]], 13)
method(s, "Porter five forces & generic strategies · BCG by business unit · SPACE · value chain · PESTEL · SWOT + blind-spot · customer segments & lifetime value (report §2)")
notes(s, "Strategy feeds the numbers. After RERA, buyers pay into escrow in instalments, so brands that can pre-sell get customer money as their cheapest financing. The value chain tells us capital intensity: developers already hold land, malls must be built — hence very different sales-to-capital ratios. We also name each company's blind spot: the assumption its investors are most likely to over-trust.")

# 6 ACCOUNTING + RECAST --------------------------------------------------
n += 1
s = base("Modules 3–4 · Accounting analysis and recasting", "Strip out JV, treasury and one-offs: core profit looks very different", n, "Recast, Quarterly")
pp = pic(s, "profit_mix", 0.6, 1.72, w=7.3)
items = [("Ind AS 115", f"Revenue on completion · Godrej advances {G['Customer advances / revenue (x)'][3]:.1f}× revenue"),
         ("Ind AS 23", f"Interest capitalised · Godrej P&L cover {G['Interest coverage: EBIT / P&L finance cost (x)'][3]:.0f}× vs cash {G['Cash interest coverage: EBIT / interest paid (x)'][3]:.1f}×"),
         ("Ind AS 111", f"JVs one line · {pc(D['JV/associate share of PAT'][3],0)} of DLF profit"),
         ("Ind AS 40", f"Malls at cost · Phoenix P/B {RV['Phoenix Mills'][13]:.1f}×")]
for i, (k, t) in enumerate(items):
    y = 1.85 + i * 0.95
    tb(s, 8.2, y, 1.5, 0.4, k, 16, ACC, HEAD, True); tb(s, 8.2, y + 0.38, 4.5, 0.5, t, 11.5, INK)
method(s, "Core EBIT = PBT + finance cost − interest income − exceptional · NOPAT at 25.17% · NOA = equity + MI + debt − liquid assets − JV investments · RERA cash kept operating · cash interest for credit rating")
notes(s, "Four accounting rules distort this sector. Revenue arrives on completion; interest is parked in inventory; joint ventures appear as one line; malls sit at historical cost. Recasting shows what FY26 profit is really made of: Godrej's core operations lost money, and its reported profit came from treasury income and one-off gains. DLF's profit is mostly its rental JV and treasury income. Only Phoenix's is genuinely operating.")

# 7 FINANCIAL ANALYSIS ---------------------------------------------------
n += 1
s = base("Module 5 · Financial analysis", "Similar ROE (~10%), three different engines — none earns its cost of capital", n, "Ratios, DuPont, AltmanZ, Growth_EVA, Industry_Benchmark")
pic(s, "dupont", 0.6, 1.7, w=8.2)
table(s, 9.05, 1.8, 3.68, [["FY26", "DLF", "GPL", "PML"],
                           ["RNOA", pc(D['DP Return on net operating assets (RNOA)'][2], 0), pc(G['DP Return on net operating assets (RNOA)'][2], 0), pc(P['DP Return on net operating assets (RNOA)'][2], 0)],
                           ["EVA ₹cr", f"{D['EVA = NOPAT − WACC × opening NOA'][2]:,.0f}", f"{G['EVA = NOPAT − WACC × opening NOA'][2]:,.0f}", f"{P['EVA = NOPAT − WACC × opening NOA'][2]:,.0f}"],
                           ["CFO/PAT", f"{D['CFO / PAT (x)'][3]:.2f}", f"{G['CFO / PAT (x)'][3]:.2f}", f"{P['CFO / PAT (x)'][3]:.2f}"],
                           ["Altman Z''", f"{D['Zpp'][3]:.1f}", f"{G['Zpp'][3]:.1f}", f"{P['Zpp'][3]:.1f}"],
                           ["Inv. days", f"{D['Inventory days (on cost of revenue)'][3]:,.0f}", f"{G['Inventory days (on cost of revenue)'][3]:,.0f}", f"{P['Inventory days (on cost of revenue)'][3]:,.0f}"]],
      [0.95, 0.91, 0.91, 0.91], 10.5, 0.33)
pic(s, "industry_bench", 0.6, 4.3, h=1.85)
tb(s, 8.4, 4.35, 4.3, 1.8, [f"DLF: margin {pc(D['DP Net profit margin'][2],0)}, turnover {D['DP Asset turnover'][2]:.2f}×", f"Godrej: leverage {G['DP Equity multiplier'][2]:.1f}×; {pc(G['DP Non-operating (JV, exceptional) contribution'][2],0)} of ROE non-operating",
                           f"Phoenix: turnover {P['DP Asset turnover'][2]:.2f}×; ROE almost all operating", f"Industry ROE {pc(IB['ROE'][0])}; ours 10–11%"], 12)
method(s, "50 ratios × 4 yrs · DuPont 3-step → 5-step (tax & JV, interest burden) → Palepu ROE = RNOA + (RNOA − NBC) × NFL · EVA & CVA · Altman Z vs Z'' · Damodaran India benchmark", y=6.3, h=0.55)
notes(s, "All three earn about 10 to 11 percent ROE but through different engines: DLF margin, Godrej leverage, Phoenix turnover. Palepu's split shows most of Godrej's ROE is non-operating. EVA is negative for all three — on current accounting returns none earns its cost of capital, so value must come from the future. Against Damodaran's India industry, our firms are more profitable than average.")

# 8 COST OF CAPITAL -------------------------------------------------------
n += 1
s = base("Module 6 · Hurdle rate", "Which beta? The answer moves WACC by four to five points", n, "Beta_*, RollingBeta, BottomUp_Beta, RateFactor, HistERP, WACC")
pp = pic(s, "rolling_beta", 0.6, 1.7, w=7.0)
pic(s, "rate_factor", 0.6, below(pp, 0.05), h=6.2 - below(pp, 0.05))
table(s, 8.05, 1.8, 4.68, [["", "DLF", "GPL", "PML"],
                           ["Regression β", f"{N['Beta_Monthly']['DLF Ltd']['Raw beta (SLOPE)']:.2f}", f"{N['Beta_Monthly']['Godrej Propert']['Raw beta (SLOPE)']:.2f}", f"{N['Beta_Monthly']['Phoenix Mills']['Raw beta (SLOPE)']:.2f}"],
                           ["Lens A β (bottom-up)", f"{D['W Beta used']:.2f}", f"{G['W Beta used']:.2f}", f"{P['W Beta used']:.2f}"],
                           ["Lens B β (industry)", f"{D['W_B']['beta']:.2f}", f"{G['W_B']['beta']:.2f}", f"{P['W_B']['beta']:.2f}"],
                           ["WACC lens A", pc(D['W WACC']), pc(G['W WACC']), pc(P['W WACC'])],
                           ["WACC lens B", pc(D['W_B']['wacc']), pc(G['W_B']['wacc']), pc(P['W_B']['wacc'])],
                           ["Rating (cash cover)", D['W Synthetic rating'], G['W Synthetic rating'], P['W Synthetic rating']]], [1.8, 0.96, 0.96, 0.96], 10.5, 0.33)
tb(s, 6.0, 4.3, 6.7, 1.9, [f"Rf {pc(I['Rupee risk-free rate = G-Sec − default spread'],2)} = G-Sec {pc(I['India 10-yr G-Sec yield'],2)} − default spread", f"ERP {pc(I['India total ERP = mature ERP + CRP'],2)} implied; history 2005–26: {pc(N['HistERP']['Geometric excess (total)'],1)} ± {pc(N['HistERP']['Standard error of arithmetic mean'],0)}",
                           "Industry β pulled down by thin trading: Dimson median 1.47 → 1.59", f"Rates: −{pc(-RF['DLF'][2],0)} to −{pc(-RF['Godrej'][2],0)} per +100bp, t ≈ {RF['DLF'][4]:.1f}"], 11.5)
method(s, f"60 monthly + 156 weekly returns · SE, t, 95% CI · rolling 36-m SLOPE · Hamada unlever/relever, median of {len(N['BU'])} developers · Damodaran industry β · LINEST two-factor with ΔG-Sec · synthetic rating on cash interest", y=6.3, h=0.55)
notes(s, "This is the decision that decides the answer. Beta is not stable — Phoenix's rolling beta has moved between 0.5 and 1.9. Our base, lens A, uses the median beta of 12 large developers. Lens B uses Damodaran's India industry beta across 156 developers, which is lower because thinly traded small caps react to the market with a lag. The two lenses differ by four to five points of WACC. A two-factor model shows developers lose about 5 percent per 100bp rise in bond yields, but the evidence is statistically weak.")

# 9 DCF DESIGN -------------------------------------------------------------
n += 1
s = base("Module 7 · Intrinsic valuation — design", "Growth must be paid for: reinvestment = Δrevenue ÷ sales-to-capital", n, "DCF_DLF, DCF_GPL, DCF_PML")
pic(s, "dcf_paths", 0.6, 1.72, w=12.1)
table(s, 0.6, 4.85, 12.13, [["Assumption", "DLF", "Godrej", "Phoenix"],
                            ["Growth FY27–31 (fades to 5.5%)", " · ".join(pc(g, 0) for g in D['DCF growth']), " · ".join(pc(g, 0) for g in G['DCF growth']), " · ".join(pc(g, 0) for g in P['DCF growth'])],
                            ["Core EBIT margin FY26 → target", f"{pc(D['Core EBIT margin'][3],0)} → {pc(D['DCF margin'],0)}", f"{pc(G['Core EBIT margin'][3],0)} → {pc(G['DCF margin'],0)}", f"{pc(P['Core EBIT margin'][3],0)} → {pc(P['DCF margin'],0)}"],
                            ["S/C · WACC → stable (β → 1)", f"{D['DCF s2c']:.1f} · {pc(D['W WACC'])} → {pc(D['DCF stableWACC'])}", f"{G['DCF s2c']:.1f} · {pc(G['W WACC'])} → {pc(G['DCF stableWACC'])}", f"{P['DCF s2c']:.1f} · {pc(P['W WACC'])} → {pc(P['DCF stableWACC'])}"]],
      [3.8, 2.8, 2.8, 2.73], 11, 0.3)
method(s, "H1 FY27 check: DLF −37% → FY27 cut to −15% · 10 years: 5 explicit + 5 fade · FCFF = NOPAT − reinvestment · terminal reinvestment = g/RONIC · beta → 1 in stable phase · mid-year · DCCDL = JV PAT × (1+g)/(Ke − g) ≈ book · EVA route reproduces FCFF to the rupee", y=6.25)
notes(s, "Our DCF makes growth pay for itself: reinvestment equals the change in revenue divided by sales-to-capital. We also tested FY27 against the two quarters already reported: DLF's H1 revenue fell 37 percent, so we cut its FY27 to minus 15 percent and moved recognition to FY28 to 30. Developer growth comes from sales already made but not yet recognised. After five years growth fades to 5.5 percent and beta moves to one. As a check, valuing the same forecast through EVA gives exactly the same firm value.")

# 10 WHAT THE PRICE IMPLIES ---------------------------------------------------
n += 1
s = base("Module 7 · Reverse DCF", "It is the long run, not the next five years, that the price is paying for", n, "DCF_* (reverse DCF), Scenarios_Implied")
pic(s, "lens_compare", 0.6, 1.72, w=6.9)
pic(s, "implied_growth", 7.7, 1.72, w=5.0)
tb(s, 0.6, 4.6, 12.1, 1.5, [[("Implied margin  ", True, ACC), (f"{pc(D['implied margin'],0)} DLF · {pc(P['implied margin'],0)} Phoenix — impossible, so not a margin story.", False, INK)],
                            [("Implied WACC  ", True, ACC), (f"{pc(D['implied WACC'])} · {pc(G['implied WACC'])} · {pc(P['implied WACC'])} (Phoenix ≈ the G-Sec).", False, INK)],
                            [("Implied perpetual g  ", True, ACC), (f"{pc(imp['DLF']['terminal_g'])} · {pc(imp['GPL']['terminal_g'])} · {pc(imp['PML']['terminal_g'])} ≈ India's nominal GDP growth; spread to WACC only 0.4–1.3 pts.", False, INK)]], 13)
method(s, "Value is linear in target margin → exact solution; implied WACC and g by bisection on a Python replica verified to the rupee · lens B fades to the same stable WACC (β → 1)")
notes(s, "We then ran the model backwards. Could margins explain the price? No — it would need margins above 100 percent. Could the discount rate? Only if it were close to the government bond yield. The most meaningful answer is growth: holding our discount rates, prices imply these firms grow at 10 to 12 percent a year for ever, roughly India's nominal GDP growth. That's defensible as a belief about India, but it leaves almost no gap between growth and the discount rate — no margin of safety.")

# 11 UNCERTAINTY + OTHER ROUTES -------------------------------------------------
n += 1
s = base("Module 7 · Uncertainty and other routes", "10,000 simulations: only Godrej has a real chance of being cheap", n, "MonteCarlo, ResidualIncome, Alt_Valuations, DDM, RealOption")
pic(s, "monte_carlo", 0.6, 1.72, w=12.1)
cards = [(f"{rs(scn['GPL']['bear'])}–{scn['GPL']['bull']:,.0f}", "Godrej bear–bull range (price ₹1,878)", OCH),
         (f"{N['DLF']['RI']['Justified P/B on current ROE — lens A']:.2f}×", f"DLF justified P/B vs market {RV['DLF Ltd'][13]:.1f}× — land at cost", ACC),
         (rs(D['DDM']['DDM value per share (Rs)']), "DLF DDM: low payout → dividends miss value", MUTE),
         (f"₹{N['RO']['Option value = S·e^(−yT)·N(d1) − K·e^(−rT)·N(d2)']:,.0f} cr", "option value of negative-NPV land (illustrative)", RUST)]
for i, (b, t, c) in enumerate(cards):
    card(s, 0.6 + i * 3.06, 4.95, 2.9, 1.15, b, t, c, 20)
method(s, "MC draws: growth scale, margin, S/C, high-growth & stable WACC, g · residual income (Palepu) with ROE fading to 15% · FCFE/APV · two-stage DDM · Black–Scholes land option", y=6.3, h=0.55)
notes(s, "We stress-tested the result. Across 10,000 draws on every key input, DLF and Phoenix almost never reach their prices; Godrej does about 5 percent of the time under lens A and 12 percent under lens B, because its value depends most on margins normalising. Residual income tells the same story: DLF's justified price-to-book is about half, versus a market multiple above four — partly because land bought decades ago sits in book value at cost. Land banks also carry option value, one possible reason markets pay above DCF.")

# 12 RELATIVE + CAP RATES -----------------------------------------------------
n += 1
s = base("Module 8 · Relative valuation", "Against ten peers, Godrej sits at the median; Phoenix yields less than a bond", n, "RelVal, CapRates")
rows = [["", "P/E", "P/B", "EV/EBITDA", "ROE"]]
for nm in ["DLF Ltd", "Godrej Properties", "Phoenix Mills"]:
    r = RV[nm]; rows.append([nm.replace(" Ltd", ""), f"{r[12]:.1f}", f"{r[13]:.2f}", f"{r[15]:.1f}", pc(r[11])])
rows.append([f"Peer median (n = {N['n_peers']})", f"{med[0]:.1f}", f"{med[1]:.2f}", f"{med[3]:.1f}", ""])
rows.append(["Peer 25th–75th pct P/E", f"{N['RelStats']['25th percentile'][0]:.0f}–{N['RelStats']['75th percentile'][0]:.0f}", "", "", ""])
table(s, 0.6, 1.8, 5.9, rows, [2.4, 0.85, 0.85, 1.0, 0.8], 12, 0.42)
pic(s, "cap_rates", 6.8, 1.72, w=5.9)
tb(s, 0.6, 4.55, 12.1, 1.5, [f"Step 4 — P/B on ROE: R² {N['Reg']['r2']:.2f}; cost-based book values break the link, so it is a cross-check only.",
                             f"Phoenix EV {cr(CAP['ev'])} on EBITDA {cr(CAP['ebitda'])} = {pc(CAP['yield'])} yield vs REITs {pc(CAP['reit_median'])} → at a REIT yield ≈ {rs(CAP['pml_at_reit'])}/share."], 13)
method(s, "Four steps: comparables (10 listed developers) → standardise (FY26, one date) → distribution (median, IQR) → control for differences (P/B = a + b·ROE) · cap rate = EBITDA ÷ EV incl. minorities")
notes(s, "Relative valuation follows Damodaran's four steps with ten peers. Godrej trades right at the peer median and is the cheapest of our three; DLF is above the median but inside the normal range; Phoenix has the highest price-to-book in the set. For an income-producing owner the right relative measure is yield: Phoenix's EBITDA yield is 2.6 percent, less than half what listed REITs pay and below the government bond. The premium is payment for growth a REIT can't fund.")

# 12b PRACTITIONER VIEW -------------------------------------------------------
n += 1
s = base("Cross-check · Operating KPIs, NAV, sell-side", "Practitioners close the gap with land and growth premia", n, "Operating_KPIs, Data_Check, NAV_SOTP, Broker_Views")
pp = pic(s, "nav_bridge", 0.6, 1.7, w=8.0)
NV = N["NAV"]; K = N["KPI"]
card(s, 8.85, 1.8, 3.88, 1.05, f"₹{K['Sales bookings (pre-sales) FY26'][0]:,.0f} / {K['Sales bookings (pre-sales) FY26'][1]:,.0f} cr", "FY26 bookings: DLF / Godrej (2.6x and 6.8x recognised revenue)", ACC, 18)
card(s, 8.85, 2.95, 3.88, 1.05, f"₹{NV['dlf_psf']:,.0f} / sq ft", "value the price puts on DLF's unscheduled land potential", OCH, 18)
card(s, 8.85, 4.1, 3.88, 1.05, f"₹{NV['gpl_emb_ps']:,.0f}", "Godrej at 12x FY28 embedded profit (price ₹1,878)", RUST, 18)
tb(s, 0.6, below(pp, 0.1), 8.0, 1.2, [[("Data check  ", True, ACC), ("profit lines match company filings (Godrej, Phoenix exact); DLF's JV share = 66.66% of DCCDL profit within 1%.", False, INK)],
                                       [("Godrej cash  ", True, ACC), ("statutory CFO −₹2,003 cr vs management pre-land OCF +₹7,830 cr: land is inventory.", False, INK)]], 11.5)
method(s, "DCCDL EBITDA × (1+g) ÷ 7.5% cap − net debt × 66.66% · pipeline: ₹20k cr/yr × 40% margin × (1−t), 5 yrs, 12% · Phoenix: retail 7%, office 8%, hotels 12x, CWIP at cost · Godrej: 12x embedded PAT · g in a cap rate = r − cap", y=6.3, h=0.55)
notes(s, "A sector analyst would also look at bookings, collections and NAV, so we rebuilt the sell-side method from company disclosures. DLF's identifiable assets — the DCCDL stake at a 7.5 percent cap rate, five years of pipeline margin and net cash — come to about 312 rupees a share, close to our DCF. So 59 percent of DLF's market value is the land beyond its visible pipeline: about 7,600 rupees per square foot of unscheduled potential. Phoenix trades at well over double our sum-of-the-parts NAV; even brokers add a 70 percent growth premium. Godrej is the one stock the practitioner method values above its price. Note too that Godrej's negative cash flow is mostly land buying: management's pre-land operating cash flow was 7,830 crore.")

# 13 SYNTHESIS -----------------------------------------------------------------
n += 1
s = base("Synthesis · Modules 7–8", "What you have to believe to own these at today's prices", n, "Summary")
pp = pic(s, "football_field", 0.6, 1.7, h=3.55)
tb(s, 0.6, below(pp, 0.05), 12.1, 1.0, [[("Godrej · preferred  ", True, OCH), ("peer-median multiples, best odds in simulation, above price on embedded profit.   ", False, INK),
                                         ("DLF · neutral  ", True, ACC), ("best balance sheet, priced for long-run growth.   ", False, INK),
                                         ("Phoenix · least preferred  ", True, RUST), ("great assets at a 2.6% yield.", False, INK)]], 12.5)
method(s, "Believe one of: cash flows grow with India's GDP for ever · long-run cost of equity ≈ bond yield · land banks hold option value the DCF misses — each defensible, none a margin of safety", y=6.3, h=0.55)
notes(s, "The methods disagree, and that is the finding. Relative valuation can't see a sector-wide premium because the peers are also expensive; intrinsic valuation can. To own these stocks today you must believe that their cash flows grow with India for ever, or that the long-run cost of equity is near the bond yield, or that land banks hold option value our model misses. Within the sector we prefer Godrej, are neutral on DLF and least prefer Phoenix.")

# 14 LIMITS -----------------------------------------------------------------------
n += 1
s = base("Limitations · CLO3", "What would change our answer", n)
tb(s, 0.6, 1.9, 6.2, 4.2, [[("Data  ", True, ACC), ("four years of statements; KPIs and broker views from press reports of filings — to be verified against investor presentations.", False, INK)],
                           [("Cost of capital  ", True, ACC), ("two credible lenses, four to five points apart — reported, not hidden.", False, INK)],
                           [("Terminal value  ", True, ACC), ("52–79% of value; the g ≤ Rf rule is the single most consequential assumption.", False, INK)],
                           [("Accounting  ", True, ACC), ("land at ~₹1,300/sq ft book vs ~₹7,600 market-implied: P/B and ROE mislead.", False, INK)],
                           [("Cycle  ", True, ACC), ("RBI hike to 5.50%, inventory +12%: near-term risk to developers.", False, INK)]], 14)
tb(s, 7.2, 1.9, 5.5, 3.2, [[("Monitor", True, INK)], "Bookings vs collections (Godrej)", "Net debt and cash interest cover", "Rental growth on new malls (Phoenix)",
                           "DCCDL monetisation (DLF)", "RBI tightening (repo 5.50%) & unsold inventory +12%"], 14)
tb(s, 7.2, 5.4, 5.5, 0.6, "Thank you — questions welcome.", 20, ACC, HEAD, True)
notes(s, "Our main limits: we lacked project-level data for a net-asset-value model; two credible cost-of-capital lenses give different answers, and we show both; and the terminal growth rule drives much of the value. These are the things we would monitor.")
prs.save(OUT); print("saved", OUT, "slides", n)

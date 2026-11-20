"""Viva preparation pack: numbers to know, concept Q&A by module, project Q&A, Excel moves."""
import json, pathlib
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.oxml.ns import qn

ROOT = pathlib.Path(__file__).resolve().parents[1]
N = json.loads((ROOT / "data/processed/numbers.json").read_text())
D, G, P, I = N["DLF"], N["GPL"], N["PML"], N["Inputs"]
OUT = ROOT / "reports/Viva_Prep_Pack.docx"
pc = lambda x, d=1: f"{x*100:.{d}f}%"
rs = lambda x: f"₹{x:,.0f}"
cr = lambda x: f"₹{x:,.0f} cr"
bm = N["Beta_Monthly"]; dl, gp, ph = bm["DLF Ltd"], bm["Godrej Propert"], bm["Phoenix Mills"]
BKM = {r[0]: r[1] for r in N["Brokers"] if r[1] is not None}
ri = N["RelImplied"]; med = N["RelStats"]["Median"]; reg = N["Reg"]

doc = Document()
s = doc.sections[0]; s.left_margin = s.right_margin = Cm(2); s.top_margin = s.bottom_margin = Cm(1.8)
st = doc.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(10.5); st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
st.paragraph_format.space_after = Pt(3)


def qa(q, a):
    p = doc.add_paragraph(); r = p.add_run("Q. " + q); r.bold = True; r.font.color.rgb = RGBColor(0x2F, 0x5D, 0x62)
    p.paragraph_format.space_after = Pt(1)
    p = doc.add_paragraph(a); p.paragraph_format.left_indent = Cm(0.5); p.paragraph_format.space_after = Pt(6)


doc.add_heading("Viva preparation pack — Group 27 (DLF · Godrej Properties · Phoenix Mills)", 0)
doc.add_paragraph("How to use: read Part A and B until you can say them without notes; then cover the answers in Parts C–D and "
                  "answer aloud. Every number here comes from the workbook — if asked 'where is that?', the sheet name is given.")

doc.add_heading("A. The two-minute story", 1)
doc.add_paragraph(
    "We valued three companies that represent the three business models in Indian real estate. Accounting analysis showed that reported "
    f"profit hides very different engines: {pc(D['JV/associate share of PAT'][3],0)} of DLF's profit is its share of the DCCDL rental JV, and Godrej's core operations "
    f"lost money (core EBIT {cr(G['RC Core operating EBIT'][3])}) — its profit came from treasury income and exceptional gains, while interest of "
    f"{cr(G['RC Interest capitalised (cash paid − P&L cost)'][3])} was capitalised into inventory. ROEs are about 10–11% for all three, below their costs of equity, so EVA is negative. "
    f"Using a rupee risk-free rate of {pc(I['Rupee risk-free rate = G-Sec − default spread'],2)} and ERP of {pc(I['India total ERP = mature ERP + CRP'],2)}, WACCs are {pc(D['W WACC'])}, {pc(G['W WACC'])} and {pc(P['W WACC'])}. "
    f"A 10-year FCFF DCF gives {rs(D['DCF']['Intrinsic value per share (Rs)'])}, {rs(G['DCF']['Intrinsic value per share (Rs)'])} and {rs(P['DCF']['Intrinsic value per share (Rs)'])} against prices of "
    f"{rs(D['DCF']['Current market price (Rs)'])}, {rs(G['DCF']['Current market price (Rs)'])} and {rs(P['DCF']['Current market price (Rs)'])}. The reverse DCF shows the market is discounting at about "
    f"{pc(D['implied WACC'],0)}, {pc(G['implied WACC'],0)} and {pc(P['implied WACC'],0)}. Against ten peers Godrej sits at the median (cheapest of our three), DLF above it, Phoenix at the top. Prices imply perpetual growth of 10–12%, about India's nominal GDP growth. Conclusion: the sector is priced for "
    "long-duration growth; within it Godrej > DLF > Phoenix.")

doc.add_heading("B. Numbers to know cold", 1)
rows = [("Price (₹)", rs(D['DCF']['Current market price (Rs)']), rs(G['DCF']['Current market price (Rs)']), rs(P['DCF']['Current market price (Rs)'])),
        ("Market cap (₹ cr)", f"{N['RelVal'][0][3]:,.0f}", f"{N['RelVal'][1][3]:,.0f}", f"{N['RelVal'][2][3]:,.0f}"),
        ("Revenue FY26 (₹ cr)", f"{N['RelVal'][0][8]:,.0f}", f"{N['RelVal'][1][8]:,.0f}", f"{N['RelVal'][2][8]:,.0f}"),
        ("PAT FY26 (₹ cr)", f"{N['RelVal'][0][6]:,.0f}", f"{N['RelVal'][1][6]:,.0f}", f"{N['RelVal'][2][6]:,.0f}"),
        ("Core EBIT FY26", f"{D['RC Core operating EBIT'][3]:,.0f}", f"{G['RC Core operating EBIT'][3]:,.0f}", f"{P['RC Core operating EBIT'][3]:,.0f}"),
        ("ROE FY26 (avg)", pc(D['DP ROE (3-step product)'][2]), pc(G['DP ROE (3-step product)'][2]), pc(P['DP ROE (3-step product)'][2])),
        ("Net margin / ATO / EM", f"{pc(D['DP Net profit margin'][2],0)} / {D['DP Asset turnover'][2]:.2f} / {D['DP Equity multiplier'][2]:.2f}", f"{pc(G['DP Net profit margin'][2],0)} / {G['DP Asset turnover'][2]:.2f} / {G['DP Equity multiplier'][2]:.2f}", f"{pc(P['DP Net profit margin'][2],0)} / {P['DP Asset turnover'][2]:.2f} / {P['DP Equity multiplier'][2]:.2f}"),
        ("Net debt / equity", f"{D['Net debt / equity (x)'][3]:.2f}", f"{G['Net debt / equity (x)'][3]:.2f}", f"{P['Net debt / equity (x)'][3]:.2f}"),
        ("CFO / PAT", f"{D['CFO / PAT (x)'][3]:.2f}", f"{G['CFO / PAT (x)'][3]:.2f}", f"{P['CFO / PAT (x)'][3]:.2f}"),
        ("Altman Z / Z''", f"{D['Z'][3]:.2f} / {D['Zpp'][3]:.2f}", f"{G['Z'][3]:.2f} / {G['Zpp'][3]:.2f}", f"{P['Z'][3]:.2f} / {P['Zpp'][3]:.2f}"),
        ("Regression β (5y monthly)", f"{dl['Raw beta (SLOPE)']:.2f}", f"{gp['Raw beta (SLOPE)']:.2f}", f"{ph['Raw beta (SLOPE)']:.2f}"),
        ("β used", f"{D['W Beta used']:.2f} (bottom-up)", f"{G['W Beta used']:.2f} (bottom-up)", f"{P['W Beta used']:.2f} (own Blume)"),
        ("Ke / Kd pre-tax / WACC", f"{pc(D['W Cost of equity (CAPM)'])} / {pc(D['W Pre-tax Kd used'])} / {pc(D['W WACC'])}", f"{pc(G['W Cost of equity (CAPM)'])} / {pc(G['W Pre-tax Kd used'])} / {pc(G['W WACC'])}", f"{pc(P['W Cost of equity (CAPM)'])} / {pc(P['W Pre-tax Kd used'])} / {pc(P['W WACC'])}"),
        ("Synthetic rating", D['W Synthetic rating'], G['W Synthetic rating'], P['W Synthetic rating']),
        ("DCF value (₹)", rs(D['DCF']['Intrinsic value per share (Rs)']), rs(G['DCF']['Intrinsic value per share (Rs)']), rs(P['DCF']['Intrinsic value per share (Rs)'])),
        ("TV share of value", pc(D['DCF']['Terminal value as % of operating value'],0), pc(G['DCF']['Terminal value as % of operating value'],0), pc(P['DCF']['Terminal value as % of operating value'],0)),
        ("Implied WACC (reverse DCF)", pc(D['implied WACC']), pc(G['implied WACC']), pc(P['implied WACC'])),
        ("DDM (₹)", rs(D['DDM']['DDM value per share (Rs)']), "n.a.", rs(P['DDM']['DDM value per share (Rs)'])),
        ("P/E · P/B", f"{N['RelVal'][0][12]:.1f} · {N['RelVal'][0][13]:.2f}", f"{N['RelVal'][1][12]:.1f} · {N['RelVal'][1][13]:.2f}", f"{N['RelVal'][2][12]:.1f} · {N['RelVal'][2][13]:.2f}"),
        ("Implied at peer median P/E (₹)", f"{ri['DLF Ltd'][0]:,.0f}", f"{ri['Godrej Properties'][0]:,.0f}", f"{ri['Phoenix Mills'][0]:,.0f}")]
t = doc.add_table(rows=1, cols=4); t.style = "Light Grid Accent 1"
for i, h in enumerate(["", "DLF", "Godrej", "Phoenix"]):
    t.rows[0].cells[i].text = h
for r in rows:
    c = t.add_row().cells
    for i, v in enumerate(r):
        c[i].text = str(v)
doc.add_paragraph(f"Macro: G-Sec {pc(I['India 10-yr G-Sec yield'],2)} · India default spread {pc(I['India sovereign default spread (Baa3)'],2)} · rupee Rf {pc(I['Rupee risk-free rate = G-Sec − default spread'],2)} · "
                  f"mature ERP {pc(I['Mature market ERP'],2)} · CRP {pc(I['India country risk premium (CRP)'],2)} · total ERP {pc(I['India total ERP = mature ERP + CRP'],2)} · tax 25.17% · terminal g 5.5% · RONIC 15% · "
                  f"bottom-up unlevered β median {N['BU_median']:.2f} · peer medians P/E {med[0]:.1f}, P/B {med[1]:.2f}, EV/EBITDA {med[3]:.1f}.")

doc.add_heading("C. Course concepts (expect 'explain' and 'why' questions)", 1)
C = [
 ("M1", "Why does business analysis matter for capital markets?", "Managers know more than investors (information asymmetry). Financial statements, audited and regulated, reduce that gap; analysts add value by separating real economics from accounting noise — which is exactly what our recast did."),
 ("M2", "Porter's generic strategies?", "Cost leadership, differentiation, and focus (cost-focus or differentiation-focus). DLF = differentiation focus (luxury, one region); Godrej = brand-led differentiation with breadth; Phoenix = differentiation by location and tenant mix."),
 ("M2", "What does the BCG matrix assume, and its weakness?", "Market growth and relative share proxy for cash needs and cash generation. Weakness: share ≠ profitability, ignores synergies, and growth is hard to define for real-estate micro-markets. We applied it to business units, not companies."),
 ("M2", "SPACE axes?", "Financial strength and environmental stability (internal/external stability), competitive advantage and industry attractiveness. Quadrant = aggressive, competitive, conservative, defensive."),
 ("M2", "Value chain?", "Primary activities (inbound, operations, outbound, marketing & sales, service) plus support activities. For developers: land, approvals, construction (outsourced), pre-sales. It explains why customer advances are a strategic asset."),
 ("M3", "Sources of noise and bias in accounting data?", "Noise: rigid rules that don't fit the business (e.g., completion-method revenue). Bias: managerial discretion (estimates, timing, capitalisation). Also forecast errors in estimates. Red flags: profit without cash, rising receivables/inventory faster than sales, unexplained changes in policy, large related-party or JV transactions."),
 ("M3", "Accounting flexibility — give an example from your firms.", "Capitalising borrowing costs (Ind AS 23): Godrej's FY26 interest paid was far above the P&L charge; the difference sits in inventory and inflates current profit and P&L interest cover."),
 ("M4", "What does recasting mean?", "Re-organising statements into a standard format and adjusting distortions: separating operating vs financing vs non-operating items, reclassifying, undoing aggressive capitalisation. We split NOA vs NFO and removed treasury, exceptional and JV income from EBIT."),
 ("M4", "Asset, liability and equity distortions?", "Assets: overstated (capitalised costs, delayed write-downs) or understated (investment property at cost). Liabilities: off-balance-sheet JV debt, customer advances. Equity: follows the other two."),
 ("M5", "Operating vs strategic ratio analysis?", "Operating ratios measure efficiency and liquidity; strategic analysis links ratios to how the firm creates value — e.g., DuPont and the Palepu RNOA/leverage split showing whether ROE comes from operations or financing."),
 ("M5", "When can leverage increase ROE?", "When RNOA exceeds the after-tax net borrowing cost: ROE = RNOA + (RNOA − NBC) × NFL. If spread is negative, leverage destroys ROE."),
 ("M5", "EVA vs CVA?", "EVA = NOPAT − WACC × invested capital (accrual-based). CVA = operating cash flow − capex − capital charge (cash-based). DLF: EVA negative but cash generation strong, because advances front-load cash."),
 ("M5", "Balanced scorecard?", "Four perspectives — financial, customer, internal process, learning & growth — linking non-financial drivers to financial outcomes."),
 ("M5", "Why Altman Z'' rather than Z?", "Original Z was built on US manufacturers and includes sales/assets and market value of equity; developers have structurally low turnover, so Z misclassifies them (Godrej 'distress' on Z, grey on Z'')."),
 ("M6", "Why subtract the default spread from the G-Sec?", "The risk-free rate must have no default risk. India's local-currency bonds embed a sovereign default spread (Baa3 ≈ 1.87%), so rupee Rf = 7.38% − 1.87% = 5.51%. Country risk then enters through the ERP."),
 ("M6", "How is the country risk premium estimated?", "Damodaran: default spread × (σ equity / σ government bond) ≈ 1.87% × 1.52 = 2.85%. Added to the mature-market implied ERP (4.23%)."),
 ("M6", "Problems with regression beta?", "Standard error (Godrej SE ≈ 0.25), sensitivity to period/interval/index, reflects past capital structure, thin trading. Fix: bottom-up beta averaging many firms; Blume adjustment."),
 ("M6", "Explain bottom-up beta step by step.", "Find comparable firms → regress or obtain their betas → unlever each with its market D/E: βu = βL/(1+(1−t)D/E) → take median → relever at target's D/E. Averaging n firms cuts SE by ~√n."),
 ("M6", "Fundamental beta?", "Beta determined by business type, operating leverage (fixed costs) and financial leverage. Real estate has high operating and cyclical leverage → β > 1."),
 ("M6", "APM / multi-factor models vs CAPM?", "APM allows several macro factors with their own betas; multi-factor models (e.g., Fama-French) add size, value. They may fit better but need more estimation; CAPM is standard in practice."),
 ("M6", "How is cost of debt estimated without a bond rating?", "Synthetic rating: interest coverage → rating → default spread; Kd = Rf + country spread + company spread. We used cash interest to avoid the capitalisation distortion."),
 ("M7", "Three approaches to valuation?", "Intrinsic (DCF: value from cash flows), relative (multiples of comparables), contingent claim (option pricing — e.g., undeveloped land as a call option)."),
 ("M7", "FCFF vs FCFE vs dividends?", "FCFF = NOPAT − reinvestment, discounted at WACC, gives firm value. FCFE = cash after debt flows, discounted at Ke. DDM discounts dividends; it understates value when payout is low."),
 ("M7", "How do you estimate growth?", "Historical (CAGR), analyst forecasts, fundamentals: g(EPS) = retention × ROE; g(EBIT) = reinvestment rate × ROIC. Growth must be consistent with reinvestment."),
 ("M7", "Why must terminal g ≤ risk-free rate?", "No firm can outgrow the economy forever; the nominal risk-free rate is a proxy for long-run nominal growth. Higher g makes the firm larger than the economy."),
 ("M7", "Mid-year convention?", "Cash flows arrive through the year, so discount at t − 0.5. Raises value slightly."),
 ("M7", "Main biases in valuation?", "Prior views, institutional pressures (sell-side), anchoring to market price. We guarded by fixing inputs from sources before looking at the result and reporting the reverse DCF openly."),
 ("M8", "Four steps of relative valuation?", "(1) Define comparables (2) standardise multiples (3) examine distribution (median, outliers) (4) control for differences in growth, risk and cash flows (regressions, PEG)."),
 ("M8", "What determines P/B fundamentally?", "Justified P/B = (ROE − g)/(Ke − g). Higher ROE → higher P/B; that's why we regress P/B on ROE."),
 ("M8", "PEG ratio — and its flaw?", "PEG = P/E ÷ growth (%). Assumes linear relationship and similar risk; meaningless with negative/near-zero growth (Phoenix 'n.m.')."),
 ("M8", "Why can relative valuation miss mispricing?", "It assumes the comparable set is fairly priced on average; if the whole sector is overvalued, multiples carry that error. Our DCF exposes it."),
 ("M9", "Cross holdings — relevant to you?", "Yes: DCCDL is a minority/JV holding. Value it separately (we capitalised DLF's share of DCCDL profit) and add to operating value rather than mixing its income into EBIT."),
]
for m, q, a in C:
    qa(f"[{m}] {q}", a)

doc.add_heading("D. Project-specific questions (expect 'why did you…')", 1)
PQ = [
 ("Why these three companies?", "They cover the three models: luxury developer with a rental JV (DLF), national high-growth developer (Godrej), and rental annuity (Phoenix). Comparing them tests whether tools built for manufacturing work in real estate."),
 ("Where does your data come from?", "Consolidated statements FY23–FY26 via Yahoo Finance (scripts/pull_data.py), NSE prices, G-Sec from OECD/FRED, Damodaran Jan-2026 datasets for ERP, CRP and spreads. Blue cells in the workbook show each source."),
 ("Why only four years?", "The consistent consolidated series available covered FY23–FY26; ratios needing averages start FY24. It is a limitation we state; trends are cross-checked with prices over five years."),
 ("Why is DLF's net margin above 50%?", f"Because PAT includes the DCCDL share ({cr(D['RC Share of JV/associate profit (post-tax)'][3])}) and large treasury income on {cr(D['RC Cash & liquid investments'][3])} of liquid funds; core EBIT margin is only {pc(D['Core EBIT margin'][3])}."),
 ("Why is DLF's 'tax & JV burden' above 1?", "JV profit is added after the tax line, so PAT including JV share exceeds PBT. It flags that a big part of profit is non-operating."),
 ("Godrej shows profit but negative core EBIT — explain.", "Completion-based revenue lags; overheads and marketing are expensed now; interest is capitalised; and FY26 included large exceptional/other gains and interest income. Strip those out and core operations lost money."),
 ("Why is Godrej's CFO negative? Is it a red flag?", "It is buying land and building inventory (inventory 71% of assets). Growth-phase, not manipulation — but profit isn't cash-backed yet, so value depends on execution."),
 ("Why are inventory days so high?", "Inventory = land + work-in-progress + unsold units, which take years to become revenue; days are measured on cost of revenue recognised only on completion."),
 ("Why did DLF's invested capital fall?", "Customer advances (≈2.9× revenue) fund construction; they are operating liabilities, so they reduce net operating assets."),
 ("Why bottom-up beta and not regression beta?", f"Single regressions are noisy (Godrej 95% CI {gp['95% CI low']:.2f}–{gp['95% CI high']:.2f}). Median of eight unlevered betas ({N['BU_median']:.2f}) has SE ≈ {N['BU_se']:.2f} and reflects the business, not one stock."),
 ("Why a different beta for Phoenix?", "It's a rental business; developer betas overstate its risk. We tested four REITs but their R² was below 12% (bond-like, illiquid), so we used Phoenix's own Blume-adjusted beta (1.06)."),
 ("Why use cash interest for the synthetic rating?", f"P&L finance cost excludes capitalised interest. Godrej's P&L cover is ~{G['Interest coverage: EBIT / P&L finance cost (x)'][3]:.0f}x but cash cover is {G['Cash interest coverage: EBIT / interest paid (x)'][3]:.1f}x → BB rather than AAA."),
 ("Why 5.5% terminal growth when India's nominal GDP grows ~10%?", "Terminal g must not exceed the rupee risk-free rate (5.51%); the sensitivity grid shows 4.5–6.5%."),
 ("Why a 10-year model?", "Growth for developers persists beyond five years; a fade period avoids jumping from high growth to stable growth, and lets beta move to 1."),
 ("Explain sales-to-capital.", "Revenue generated per rupee of new invested capital. Reinvestment = Δrevenue ÷ S/C. Developers 2.0 (land and inventory already funded), Phoenix 0.5 (malls must be built)."),
 ("Your DCF is far below price — is the model wrong?", f"We checked by reversing it: required margins exceed 100% for DLF/Phoenix, which is impossible, so the gap is the discount rate. The price implies WACC ≈ {pc(D['implied WACC'],0)}/{pc(G['implied WACC'],0)}/{pc(P['implied WACC'],0)} vs our {pc(D['W WACC'],0)}/{pc(G['W WACC'],0)}/{pc(P['W WACC'],0)}. Either the market expects longer growth, values land banks as options, or uses lower risk premia."),
 ("DLF's forecast ROIC rises above 30% — isn't that unrealistic?", f"It is high because invested capital is small: customer advances fund construction, so each rupee of new revenue needs only ₹0.5 of capital (S/C 2.0). Forecast ROIC on DCF_DLF row 28 goes from {pc(D['DCF roic'][0])} to {pc(D['DCF roic'][9])}. If you think it is too high, Grid B shows value at S/C 1.0 — it falls, which only widens the gap to price, so our conclusion is not driven by an aggressive assumption."),
 ("How did you value DCCDL?", f"DLF's share of DCCDL profit {cr(D['DCCDL']['jv_pat'])} × (1+g) ÷ (Ke − g) = {cr(D['DCCDL']['value'])}, close to book {cr(D['DCCDL']['book'])}."),
 ("How do you treat minority interest in Phoenix?", "Proportionally: minority share of PAT (≈21%) applied to firm equity value — CPPIB and GIC own stakes in mall platforms."),
 ("Why does DDM give such low values?", "Payouts are low (TTM DPS ₹8 DLF, ₹10 Godrej, ₹2.5 Phoenix against EPS of ₹18, ₹61, ₹34); value sits in reinvestment. Godrej paid nothing FY17–FY26 and resumed with ₹10 in FY27 — a useful viva fact."),
 ("Why is P/B regression R² so low?", "Book values are distorted (malls at cost; capitalised interest) and current ROE doesn't capture land banks. Used as cross-check only."),
 ("Why exclude the targets from peer medians?", "To avoid circularity — a company shouldn't be compared with a set that includes itself."),
 ("Why two cost-of-capital lenses?", f"Because the beta choice moves WACC by 4–5 points. Lens A: median unlevered beta of 12 large developers ({N['BU_median']:.2f}) → WACC {pc(D['W WACC'])}/{pc(G['W WACC'])}/{pc(P['W WACC'])}. Lens B: Damodaran's India industry unlevered beta (0.69 developers, 0.24 operators) → {pc(D['W_B']['wacc'])}/{pc(G['W_B']['wacc'])}/{pc(P['W_B']['wacc'])}. Industry averages are pulled down by thinly traded small caps (Scholes–Williams/Dimson bias)."),
 ("Why does lens B still give values below price?", f"Because beta moves to 1 in the stable phase under both lenses, and the terminal value is 52–79% of value. Lens B only lowers the first five years' discount rate: values become {rs(N['DLF']['lensB']['vps'])}, {rs(N['GPL']['lensB']['vps'])}, {rs(N['PML']['lensB']['vps'])}."),
 ("What does the reverse DCF tell you?", f"Three ways to close the gap: margin (needs >100% for DLF/Phoenix — impossible), uniform WACC ({pc(D['implied WACC'])}/{pc(G['implied WACC'])}/{pc(P['implied WACC'])}), or perpetual growth holding WACC ({pc(N['SC']['implied']['DLF']['terminal_g'])}/{pc(N['SC']['implied']['GPL']['terminal_g'])}/{pc(N['SC']['implied']['PML']['terminal_g'])}) ≈ India's nominal GDP growth."),
 ("Why cap terminal growth at the risk-free rate if India grows ~10% nominal?", "Damodaran's rule: no firm can outgrow the economy for ever, and the nominal risk-free rate proxies long-run nominal growth. India's rupee riskless rate is 5.5% because the G-Sec includes a default spread. If you believe 10% perpetual growth, today's prices are roughly fair — that is the central debate, and we show it explicitly."),
 ("Explain the Monte Carlo.", f"10,000 draws on growth scale, target margin, sales-to-capital, high-growth and stable WACC, terminal g. P(value > price): DLF {pc(N['MC']['DLF']['A']['prob_above_price'],1)}, Godrej {pc(N['MC']['GPL']['A']['prob_above_price'],0)} (lens B {pc(N['MC']['GPL']['B']['prob_above_price'],0)}), Phoenix 0%. The engine is a Python replica of the sheet, verified to the rupee."),
 ("What is residual income valuation and what did it show?", f"Palepu's abnormal-earnings model: value = book + PV of (ROE − Ke) × opening book. DLF's justified P/B on current ROE is {N['DLF']['RI']['Justified P/B on current ROE — lens A']:.2f} vs market {N['RelVal'][0][13]:.2f}; the price implies a sustained ROE of {pc(N['DLF']['RI']['ROE the market price implies (lens A Ke) = g + P/B × (Ke − g)'],0)}. Book value understates land bought decades ago at cost."),
 ("How do EVA and DCF relate?", f"Firm value = opening invested capital + PV of future EVA. Our Alt_Valuations sheet reproduces the FCFF value exactly (difference {N['DLF']['EVA_diff']:.0f}) using year-end discounting; the main DCF adds a mid-year uplift."),
 ("What is Phoenix's implied cap rate?", f"EV incl. minorities {cr(N['Cap']['ev'])} vs EBITDA {cr(N['Cap']['ebitda'])} → {pc(N['Cap']['yield'])}, below the G-Sec and listed REIT yields ({pc(N['Cap']['reit_median'])}). At a REIT yield Phoenix would be worth ~{rs(N['Cap']['pml_at_reit'])}. The premium pays for growth a REIT cannot fund (90% payout)."),
 ("Is beta stable?", f"No. Rolling 36-month betas: DLF {N['RollingBeta']['DLF'][0]:.2f}–{N['RollingBeta']['DLF'][1]:.2f}, Godrej {N['RollingBeta']['Godrej'][0]:.2f}–{N['RollingBeta']['Godrej'][1]:.2f}, Phoenix {N['RollingBeta']['Phoenix'][0]:.2f}–{N['RollingBeta']['Phoenix'][1]:.2f}."),
 ("Are developers interest-rate sensitive?", f"Two-factor model (market + ΔG-Sec, 2012–26): DLF {pc(N['RateFactor']['DLF'][2],1)} and Godrej {pc(N['RateFactor']['Godrej'][2],1)} per +100bp, but t ≈ {N['RateFactor']['DLF'][4]:.1f} — weak evidence. Phoenix shows none."),
 ("How did you check the ERP?", f"Sensex vs G-Sec 2005–2026: geometric excess ≈ {pc(N['HistERP']['Geometric excess (total)'])} with a 1.3% dividend-yield assumption; standard error ≈ {pc(N['HistERP']['Standard error of arithmetic mean'],0)} — too noisy, so we use the implied {pc(N['Inputs']['India total ERP = mature ERP + CRP'],2)}."),
 ("Do realty stocks follow house prices?", f"No — BIS house prices grew {pc(N['Housing']['Nominal house-price CAGR'])} nominal, {pc(N['Housing']['Real house-price CAGR'])} real a year since 2009; the correlation of annual changes with the realty index is {N['Housing']['Correlation: realty YoY vs house-price YoY (same quarter)']:.2f}. Equities lead and overshoot."),
 ("What's the real-option argument?", "Undeveloped land is a call option: S = value of developed property, K = development cost, σ = property volatility, T = holding period, y = cost of delay. Land with negative NPV today still has value. It's one explanation for markets paying above DCF for land-rich developers; our numbers are illustrative because project data were unavailable."),
 ("Module 9 — any loose ends?", "Cross holdings (DCCDL valued separately), minority interests (CPPIB/GIC in Phoenix platforms, ~21% of profit), distress (Godrej original Z in distress zone; APV adds expected distress cost). No illiquidity discount — all large, liquid."),
 ("Is your revenue forecast aggressive?", "Yes, deliberately: versus a naive linear trend of FY23–26 revenue (FORECAST), our FY31 revenue is about 2x for DLF and higher for Godrej, because customer advances (2.9x and 7.8x revenue) show sales far ahead of recognition. Even with that generous path, value is below price — so the conclusion is not an artefact of conservatism."),
 ("What is the AEG model?", "Palepu's abnormal-earnings-growth model: value = next-year earnings / Ke + PV of abnormal earnings growth, where AEG_t = E_t + Ke·D_(t−1) − (1+Ke)·E_(t−1). It is the earnings-based twin of residual income; our AEG and RI values agree (DLF ≈ ₹158 vs ₹160)."),
 ("How do brokers value these companies, and why are their targets near the price?", f"On NAV/SOTP: rental assets at cap rates (DLF commercial 7.5%; Phoenix retail 6.5–7.5%, office 7–8%), residential at PV of pipeline margins with ~12% discount rates, plus growth premia. Median targets: DLF ₹{BKM['DLF Ltd']:,.0f}, Godrej ₹{BKM['Godrej Properties']:,.0f}, Phoenix ₹{BKM['Phoenix Mills']:,.0f}. The gap to our DCF is the required return and the payment for land/growth beyond the forecast."),
 ("What does your NAV say about DLF?", f"Identifiable parts — DCCDL stake ₹{N['NAV']['dccdl_stake']:,.0f} cr, 5-yr pipeline margin ₹{N['NAV']['dlf_res_pv']:,.0f} cr, net cash ₹{N['NAV']['dlf_netcash']:,.0f} cr — give ₹{N['NAV']['dlf_nav_ps']:,.0f}/share, close to our DCF. So {N['NAV']['dlf_land']/N['NAV']['dlf_mcap']:.0%} of market cap (₹{N['NAV']['dlf_land']:,.0f} cr) is land beyond the pipeline — about ₹{N['NAV']['dlf_psf']:,.0f} per sq ft of unscheduled potential."),
 ("Why is the DCCDL stake worth ₹20k cr in your DCF but ₹45k cr in the NAV?", "The DCF capitalises DLF's after-tax JV profit at our cost of equity (~14.7%) less 5.5% growth; the NAV applies a 7.5% cap rate to EBITDA and deducts DCCDL's ₹18,150 cr net debt. A 7.5% EBITDA cap implies a much lower required return — the same discount-rate gap that runs through the whole valuation."),
 ("Is Godrej's negative cash flow a red flag?", "Statutory CFO (−₹2,003 cr) includes land purchases because land is inventory. Management's pre-land operating cash flow was ₹7,830 cr in FY26; the ~₹9,800 cr gap is land and business development. It is a growth choice, but it means free cash flow depends on how much land it keeps buying (FY27 BD guidance ₹20,000 cr)."),
 ("Did you verify the data?", "Yes — the Data_Check sheet reconciles our dataset to company-reported FY26 figures: PAT matches exactly for Godrej and Phoenix and within 0.2% for DLF; revenue and net cash differ by definition (revenue from operations vs total income; RERA-restricted cash)."),
 ("What are the key operating KPIs?", "FY26 bookings: DLF ₹20,143 cr, Godrej ₹34,171 cr; collections ₹13,517 cr and ₹19,965 cr; FY27 guidance ₹20,000 cr and ₹39,000 cr. Phoenix retail consumption ₹16,578 cr (+21%), retail rental income ₹2,157 cr (+10%), retail EBITDA ₹2,246 cr."),
 ("Which hypotheses did you reject?", "H5 (realty stocks follow house prices) — rejected. H4 (rate sensitivity) — weak. H1–H3, H6–H8 supported."),
 ("Which is your final recommendation?", "Relative: Godrej at the peer median (cheapest of our three), Phoenix highest P/B in the set. Intrinsic: all above value at CAPM rates. Ranking Godrej > DLF > Phoenix, with the caveat that Godrej carries cash-flow and execution risk."),
 ("What would change your view on Godrej?", "Bookings not converting to collections, further rise in net debt, margins not normalising toward ~22%. Grid B shows value at 12–32% margins."),
 ("What would you do with more time?", "NAV model using project-level bookings and land bank; value DCCDL on its own cash flows; reconcile lines to annual reports."),
 ("What did each member do?", "Prepare your own honest answer: who built which sheets, who wrote which sections — and be ready to walk through those sheets live."),
]
for q, a in PQ:
    qa(q, a)

doc.add_heading("E. Live Excel moves to rehearse", 1)
for t in ["Change the terminal growth (Inputs!B12) and show all three values update.",
          "On DCF_DLF, change the target margin (B6) and show the value; then point to the reverse-DCF block (columns U–Y).",
          "Goal Seek: Data → What-if → Goal Seek: set DCF_DLF!Y28 (value at implied WACC) to the price by changing Y25 — reproduces the implied WACC.",
          "Show Beta_Monthly: SLOPE formula, standard error, confidence interval.",
          "Show Recast: how core EBIT is built from PBT, and the capitalised-interest line for Godrej.",
          "Show RelVal: the four steps, peer medians and the P/B–ROE regression."]:
    doc.add_paragraph(t, style="List Bullet")

doc.add_heading("F. Suggested split for the 10-minute talk", 1)
for t in ["Speaker 1 (≈5 min): slides 1–7 — scope, strategy, accounting, recast, ratios, DuPont/EVA.",
          "Speaker 2 (≈5 min): slides 8–13 — beta and WACC, DCF design and results, reverse DCF, relative valuation, synthesis, limitations.",
          "Both: know every number in Part B; either may be asked about any slide."]:
    doc.add_paragraph(t, style="List Bullet")
doc.save(OUT); print("saved", OUT)

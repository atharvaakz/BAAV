# Executed inside build_model.py (shares its namespace). v2 sheets: industry lens, market history, alt valuations.
import json as _json
V2 = ROOT / "data/processed/v2"
COLS3 = {co: L(2 + j) for j, co in enumerate(TARGETS)}

# ------------------------------------------------------------------ Industry benchmark (Damodaran India, Jan-2026)
ib = sheet("Industry_Benchmark", "Benchmarking against Damodaran's India industry data (January 2026)",
           "Modules 5–6 — is each firm typical of its industry? Source: pages.stern.nyu.edu/~adamodar (India datasets; 156 listed developers)",
           [44, 14, 14, 13, 13, 13, 46])
hdr(ib, 4, ["Metric", "India RE (Development)", "India RE (Operations & Services)", "DLF", "Godrej", "Phoenix", "Our reading"])
dam = [  # metric, dev, ops, our formula (lambda co), fmt, comment
    ("Number of firms", 156, 42, None, NUM, ""),
    ("Levered beta (industry avg)", 0.7553, 0.3394, lambda co: f"={BM[co]['beta']}", "0.00", "Large caps far more market-sensitive than the 156-firm average (thin trading pulls small-cap betas down)"),
    ("Unlevered beta, cash-corrected", 0.6879, 0.2354, lambda co: f"=BottomUp_Beta!G{BU[co]}", "0.00", "Ours from 12 large developers' regressions (Signature Global excluded: listed 2023)"),
    ("Market D/E", 0.2127, 0.6809, lambda co: f"=BottomUp_Beta!E{BU[co]}", "0.00", ""),
    ("Cost of capital (local currency)", 0.1116, 0.0826, lambda co: f"={W[co]['WACC']}", PCT, "Industry ≈ market-implied WACC for DLF/Godrej (see DCF sheets)"),
    ("ROE", 0.0719, 0.0449, lambda co: f"={D(co,'NetIncome',2026)}/{avg(co,'Equity',2026)}", PCT, "All three above the industry"),
    ("Net margin", 0.1003, 0.0581, lambda co: f"={D(co,'NetIncome',2026)}/{D(co,'Revenue',2026)}", PCT, ""),
    ("EBITDA / sales", 0.1838, 0.2952, lambda co: f"=({R(co,'EBITx',2026)}+{D(co,'DandA',2026)})/{D(co,'Revenue',2026)}", PCT, ""),
    ("Sales / invested capital", 0.4529, 0.2387, lambda co: f"={D(co,'Revenue',2026)}/{R(co,'IC',2026)}", NUM2, "Average S/C; our DCF uses a marginal S/C on new revenue"),
    ("Inventory / sales", 3.3939, 1.0373, lambda co: f"={D(co,'Inventory',2026)}/{D(co,'Revenue',2026)}", NUM2, ""),
    ("Reinvestment rate", 3.706, 0.8874, None, NUM2, "Industry is reinvesting 3.7x after-tax operating income — a land-buying phase"),
    ("Dividend payout", 0.158, 0.5763, lambda co: f"={D(co,'DividendsPaid',2026)}/{D(co,'NetIncome',2026)}", PCT, ""),
    ("Trailing P/E (aggregate)", 37.7586, 20.594, lambda co: f"=RelVal!M{RVR[co]}", NUM2, ""),
    ("EV / EBITDA", 26.6493, 22.1757, lambda co: f"=RelVal!P{RVR[co]}", NUM2, ""),
    ("Std dev of stock returns", 0.4992, 0.4071, None, PCT, "Sector volatility ~50% a year — a measure of cyclicality"),
]
IB = {}
for i, (m, dv, op, fn, fmt, cm) in enumerate(dam):
    r_ = 5 + i; IB[m] = r_
    put(ib, r_, 1, m); put(ib, r_, 2, dv, fmt, F_IN, FILL_IN); put(ib, r_, 3, op, fmt, F_IN, FILL_IN)
    if fn:
        for j, co in enumerate(TARGETS):
            put(ib, r_, 4 + j, fn(co), fmt)
    put(ib, r_, 7, cm, font=F_NOTE)
note(ib, 22, "Damodaran's India industry betas are averages over many small, thinly traded firms; thin trading biases regression betas toward zero (Scholes–Williams, Dimson).")
note(ib, 23, "That is why we keep two cost-of-capital lenses: A = large-cap bottom-up beta (our base), B = Damodaran industry beta (see WACC rows 27–33).")

# ------------------------------------------------------------------ WACC lens B
put(wc, 26, 1, "LENS B — Damodaran India industry beta (alternative)", font=F_B)
for j in range(3):
    wc.cell(26, 2 + j).fill = FILL_SUB
lensB = [
    ("Industry unlevered beta (cash-corrected)", lambda co, c: "=Industry_Benchmark!$C$7" if co == "PML" else "=Industry_Benchmark!$B$7", "0.000", "DLF, GPL: Development; PML: Operations & Services"),
    ("Market D/E", lambda co, c: f"={c}21/{c}20", "0.000", ""),
    ("Relevered beta", lambda co, c: f"={c}27*(1+(1-Tax)*{c}28)", "0.000", ""),
    ("Cost of equity (lens B)", lambda co, c: f"=Rf+{c}29*ERP", PCT, ""),
    ("WACC (lens B)", lambda co, c: f"={c}22*{c}30+{c}23*{c}19", PCT, ""),
    ("Damodaran industry cost of capital (local currency, reference)", lambda co, c: "=Industry_Benchmark!$C$9" if co == "PML" else "=Industry_Benchmark!$B$9", PCT, ""),
]
for i, (lab, fn, fmt, nt) in enumerate(lensB):
    r_ = 27 + i
    put(wc, r_, 1, lab, font=F_B if "WACC" in lab else F_N)
    for j, co in enumerate(TARGETS):
        put(wc, r_, 2 + j, fn(co, L(2 + j)), fmt, F_B if "WACC" in lab else F_N, FILL_KEY if "WACC (lens" in lab else None)
    put(wc, r_, 5, nt, font=F_NOTE)
for co in TARGETS:
    W[co]["WACC_B"] = f"WACC!${COLS3[co]}$31"; W[co]["Ke_B"] = f"WACC!${COLS3[co]}$30"

# ------------------------------------------------------------------ Quarterly (Q1–Q2 FY27 included)
qs = sheet("Quarterly", "Quarterly results (latest five quarters available) and trailing-twelve-month metrics",
           "Module 5 — lumpiness of completion-based revenue; TTM multiples use the four most recent consecutive quarters",
           [30, 12, 12, 12, 12, 12, 4, 13, 13])
r = 4
QTTM = {}
for co, tk in TARGETS.items():
    q = pd.read_csv(RAW / tk / "quarterly_income_stmt.csv", index_col=0)
    q.columns = [pd.Timestamp(c) for c in q.columns]; q = q[sorted(q.columns)] / 1e7
    sub(qs, r, NAMES[co], 9); r += 1
    hdr(qs, r, ["₹ crore"] + [c.strftime("%b-%y") for c in q.columns] + [""] * (5 - len(q.columns)) + ["", "TTM", "Note"]); r += 1
    lines = [("Revenue", "Total Revenue"), ("Pre-tax income", "Pretax Income"), ("Net income (owners)", "Net Income")]
    cons = all((q.columns[i + 1] - q.columns[i]).days < 100 for i in range(len(q.columns) - 4, len(q.columns) - 1)) if len(q.columns) >= 4 else False
    for lab, key in lines:
        put(qs, r, 1, lab)
        for j, c in enumerate(q.columns):
            v = q.loc[key, c] if key in q.index else None
            put(qs, r, 2 + j, None if pd.isna(v) else round(float(v), 1), NUM, F_IN)
        last4 = ",".join(f"{L(2+j)}{r}" for j in range(len(q.columns) - 4, len(q.columns)))
        put(qs, r, 8, f"=SUM({last4})" if cons else "n.a.", NUM, F_B)
        r += 1
    put(qs, r, 1, "Net margin"); [put(qs, r, 2 + j, f"=IFERROR({L(2+j)}{r-1}/{L(2+j)}{r-3},\"\")", PCT) for j in range(len(q.columns))]
    put(qs, r, 8, f"=IFERROR(H{r-1}/H{r-3},\"n.a.\")", PCT); r += 1
    put(qs, r, 1, "TTM P/E at latest price", font=F_B); put(qs, r, 8, f"=IFERROR({PX[co][3]}*{D(co,'Shares',2026)}/H{r-2},\"n.a.\")", X, F_B, FILL_KEY)
    put(qs, r, 9, "vs FY26 P/E in RelVal", font=F_NOTE)
    QTTM[co] = f"Quarterly!$H${r}"
    r += 3
note(qs, r, "Source: Yahoo Finance quarterly consolidated statements. Quarter-to-quarter swings reflect project completions (Ind AS 115), not demand.")

# ------------------------------------------------------------------ Long cycle (monthly adjusted closes since listing, live drawdown formulas)
lcd = pd.read_csv(V2 / "monthly_adjclose_max.csv", index_col=0, parse_dates=True)
series = [("DLF", "DLF"), ("GODREJPROP", "Godrej Prop."), ("PHOENIXLTD", "Phoenix Mills"), ("NIFTYREALTY", "Nifty Realty"), ("NIFTY50", "Nifty 50"), ("SENSEX", "Sensex")]
lcd = lcd[[k for k, _ in series]]
lcd = lcd[lcd.index >= "2007-01-31"]
ls = sheet("LongCycle", "Two decades of Indian real estate equity: prices, drawdowns and cycles (2007–2026)",
           "Data far back as available: monthly adjusted closes since listing (dividend-adjusted). Drawdown = price ÷ running peak − 1 (live formulas)",
           [11] + [10] * 13)
hdr(ls, 4, ["Month"] + [f"{n} px" for _, n in series] + [f"{n} DD" for _, n in series])
LC0 = 5
for i, (dt, row) in enumerate(lcd.iterrows()):
    r_ = LC0 + i
    put(ls, r_, 1, dt.date(), "mmm-yy")
    for j, (k, _) in enumerate(series):
        v = row[k]
        put(ls, r_, 2 + j, None if pd.isna(v) else round(float(v), 2), NUM2, F_IN)
        pc_ = L(2 + j)
        put(ls, r_, 8 + j, f'=IF({pc_}{r_}="","",{pc_}{r_}/MAX({pc_}${LC0}:{pc_}{r_})-1)', "0%")
LC1 = LC0 + len(lcd) - 1
st0 = 4
sc = 16
hdr(ls, st0, ["Statistic"] + [n for _, n in series], sc)
ls.column_dimensions[L(sc)].width = 30
stats_ = [("First month with data", lambda pc_: f'=INDEX($A${LC0}:$A${LC1},MATCH(TRUE,INDEX({pc_}{LC0}:{pc_}{LC1}<>"",0),0))', "mmm-yy"),
          ("Years", lambda pc_: f"=(MAX($A${LC0}:$A${LC1})-{L(sc)}{{r0}})/365.25", NUM2),
          ("CAGR (dividend-adjusted)", lambda pc_: f'=({pc_}{LC1}/INDEX({pc_}{LC0}:{pc_}{LC1},MATCH(TRUE,INDEX({pc_}{LC0}:{pc_}{LC1}<>"",0),0)))^(1/{{yrs}})-1', PCT),
          ("Maximum drawdown", lambda pc_: None, "0%"),
          ("Current distance from peak", lambda pc_: None, "0%")]
for j, (k, n) in enumerate(series):
    c = sc + 1 + j; cl = L(c); pc_ = L(2 + j); dd = L(8 + j)
    put(ls, st0 + 1, c, stats_[0][1](pc_), "mmm-yy")
    put(ls, st0 + 2, c, f"=(MAX($A${LC0}:$A${LC1})-{cl}{st0+1})/365.25", NUM2)
    put(ls, st0 + 3, c, f'=({pc_}{LC1}/INDEX({pc_}{LC0}:{pc_}{LC1},MATCH({cl}{st0+1},$A${LC0}:$A${LC1},0)))^(1/{cl}{st0+2})-1', PCT, F_B)
    put(ls, st0 + 4, c, f"=MIN({dd}{LC0}:{dd}{LC1})", "0%", F_B)
    put(ls, st0 + 5, c, f"={dd}{LC1}", "0%")
for i, (lab, *_r) in enumerate(stats_):
    put(ls, st0 + 1 + i, sc, lab)
note(ls, st0 + 7, "Cycle markers: 2008 GFC; 2013 taper tantrum; 2016 demonetisation + RERA; 2020 COVID; 2021–24 upcycle.", sc)
ch = LineChart(); ch.title = "Drawdown from previous peak"; ch.height, ch.width = 8, 18
for j in [0, 1, 2, 3]:
    ser = Series(Reference(ls, min_col=8 + j, min_row=LC0, max_row=LC1), title=series[j][1]); ser.smooth = False
    ch.series.append(ser)
ch.set_categories(Reference(ls, min_col=1, min_row=LC0, max_row=LC1)); ch.y_axis.number_format = "0%"; ch.x_axis.number_format = "yyyy"
ls.add_chart(ch, f"{L(sc)}14")
ls.freeze_panes = "B5"

# ------------------------------------------------------------------ Rolling 36-month beta (live SLOPE windows)
rbw = sheet("RollingBeta", "Beta drift: rolling 36-month beta against the Nifty 50",
            "Module 6 — is beta stable? Each cell = SLOPE over the previous 36 monthly returns (live)", [11] + [11] * 10)
hdr(rbw, 4, ["Month", "Nifty ret", "DLF ret", "GPL ret", "PML ret", "Realty ret", "DLF β36", "GPL β36", "PML β36", "Realty β36"])
src = [("NIFTY50", "F"), ("DLF", "B"), ("GODREJPROP", "C"), ("PHOENIXLTD", "D"), ("NIFTYREALTY", "E")]   # LongCycle price columns
for i in range(1, len(lcd)):
    r_ = 4 + i; lsr = LC0 + i
    put(rbw, r_, 1, f"=LongCycle!A{lsr}", "mmm-yy")
    for j, (k, pcl) in enumerate(src):
        put(rbw, r_, 2 + j, f'=IF(OR(LongCycle!{pcl}{lsr}="",LongCycle!{pcl}{lsr-1}=""),"",LongCycle!{pcl}{lsr}/LongCycle!{pcl}{lsr-1}-1)', "0.0%")
    if i >= 36:
        for j in range(4):
            yc = L(3 + j)
            put(rbw, r_, 7 + j, f'=IF(COUNT({yc}{r_-35}:{yc}{r_})<36,"",IFERROR(SLOPE({yc}{r_-35}:{yc}{r_},$B{r_-35}:$B{r_}),""))', "0.00")
RB1 = 4 + len(lcd) - 1
ch = LineChart(); ch.title = "Rolling 36-month beta vs Nifty 50"; ch.height, ch.width = 8, 18
for j, nm in enumerate(["DLF", "Godrej", "Phoenix", "Nifty Realty"]):
    ch.series.append(Series(Reference(rbw, min_col=7 + j, min_row=40, max_row=RB1), title=nm))
ch.set_categories(Reference(rbw, min_col=1, min_row=40, max_row=RB1)); ch.x_axis.number_format = "yyyy"
rbw.add_chart(ch, "L4")
put(rbw, 22, 12, "Range of rolling beta", font=F_B)
for j, nm in enumerate(["DLF", "Godrej", "Phoenix", "Nifty Realty"]):
    col = L(7 + j)
    put(rbw, 23 + j, 12, nm); put(rbw, 23 + j, 13, f"=MIN({col}5:{col}{RB1})", "0.00"); put(rbw, 23 + j, 14, f"=MAX({col}5:{col}{RB1})", "0.00")
    put(rbw, 23 + j, 15, f"=MEDIAN({col}5:{col}{RB1})", "0.00")
put(rbw, 22, 13, "min", font=F_NOTE); put(rbw, 22, 14, "max", font=F_NOTE); put(rbw, 22, 15, "median", font=F_NOTE)
rbw.freeze_panes = "B5"

# ------------------------------------------------------------------ Two-factor model: market + change in 10y G-Sec (APM-style)
gs = pd.read_csv(V2 / "gsec_spliced.csv", index_col=0, parse_dates=True).iloc[:, 0]
rf_ = sheet("RateFactor", "Interest-rate sensitivity: two-factor model R = α + βm·R_Nifty + βr·ΔYield",
            "Module 6 — beyond CAPM (APM / multi-factor). ΔYield = monthly change in 10-yr G-Sec (IMF to 2010, OECD from 2011). LINEST, live.",
            [11, 11, 11, 11, 11, 11, 11, 4, 40, 12, 12, 12, 12])
hdr(rf_, 4, ["Month", "Nifty ret", "ΔG-Sec", "DLF ret", "GPL ret", "PML ret", "Realty ret"])
rrow = 5
for i in range(1, len(lcd)):
    dt = lcd.index[i]
    if dt < pd.Timestamp("2012-01-31"):
        continue
    y0, y1 = gs.get(lcd.index[i - 1]), gs.get(dt)
    if y0 is None or y1 is None or pd.isna(y0) or pd.isna(y1):
        continue
    put(rf_, rrow, 1, f"=RollingBeta!A{4+i}", "mmm-yy"); put(rf_, rrow, 2, f"=RollingBeta!B{4+i}", "0.0%")
    put(rf_, rrow, 3, round(float(y1 - y0), 5), "0.00%", F_IN)
    for j, colL in enumerate(["C", "D", "E", "F"]):
        put(rf_, rrow, 4 + j, f"=RollingBeta!{colL}{4+i}", "0.0%")
    rrow += 1
RF1 = rrow - 1
hdr(rf_, 4, ["Coefficient", "DLF", "Godrej", "Phoenix", "Nifty Realty"], 9)
labs = [("Market beta βm", 1, 2), ("Rate beta βr (per 1.00 = 100%)", 1, 1), ("Return impact of +100bp", None, None), ("Std error of βr", 2, 1), ("t-stat of βr", None, None), ("R²", 3, 1), ("Observations", None, None)]
for i, (lab, rI, cI) in enumerate(labs):
    put(rf_, 5 + i, 9, lab, font=F_B if "100bp" in lab else F_N)
    for j, yc in enumerate(["D", "E", "F", "G"]):
        c = 10 + j; cl = L(c)
        Y, Xr = f"{yc}5:{yc}{RF1}", f"B5:C{RF1}"
        if lab.startswith("Market"):
            f = f"=INDEX(LINEST({Y},{Xr},TRUE,TRUE),1,2)"
        elif lab.startswith("Rate beta"):
            f = f"=INDEX(LINEST({Y},{Xr},TRUE,TRUE),1,1)"
        elif "100bp" in lab:
            f = f"={cl}6*0.01"
        elif lab.startswith("Std error"):
            f = f"=INDEX(LINEST({Y},{Xr},TRUE,TRUE),2,1)"
        elif lab.startswith("t-stat"):
            f = f"={cl}6/{cl}8"
        elif lab == "R²":
            f = f"=INDEX(LINEST({Y},{Xr},TRUE,TRUE),3,1)"
        else:
            f = f"=COUNT({Y})"
        put(rf_, 5 + i, c, f, "0.0%" if "100bp" in lab else "0.00", F_B if "100bp" in lab else F_N, FILL_KEY if "100bp" in lab else None)
note(rf_, 13, "Reading: developers lose ~4–6% per +100bp in long yields, but |t| < 1.5 — rate risk is real but noisy; Phoenix (rental) shows none.", 9)
note(rf_, 14, "Implication: CAPM's single factor misses some rate exposure; we keep CAPM for Ke but flag rates as the key macro sensitivity.", 9)

# ------------------------------------------------------------------ Historical ERP (Sensex 2005–2026 vs G-Sec)
he = pd.read_csv(V2 / "historical_erp.csv", index_col=0)
sx_ye = pd.read_csv(V2 / "monthly_adjclose_max.csv", index_col=0, parse_dates=True)["SENSEX"].resample("YE").last()
hs = sheet("HistERP", "Historical equity risk premium: Sensex vs 10-year G-Sec, 2005–2026",
           "Module 6 — cross-check of the implied ERP. Sensex is a price index (no dividends) → add an assumed dividend yield (input).",
           [10, 14, 13, 13, 13, 4, 40, 12])
hdr(hs, 4, ["Year", "Sensex year-end", "Price return", "G-Sec avg", "Excess (price)"])
yrs = [int(y[:4]) if isinstance(y, str) else int(pd.Timestamp(y).year) for y in he.index]
rows_y = [yrs[0] - 1] + yrs
for i, y in enumerate(rows_y):
    r_ = 5 + i
    put(hs, r_, 1, y)
    v = sx_ye[sx_ye.index.year == y]
    put(hs, r_, 2, round(float(v.iloc[0]), 1) if len(v) else None, NUM, F_IN)
    if i > 0:
        put(hs, r_, 3, f"=B{r_}/B{r_-1}-1", PCT)
        put(hs, r_, 4, round(float(he.iloc[i - 1]["g_sec_avg"]), 5), PCT, F_IN)
        put(hs, r_, 5, f"=C{r_}-D{r_}", PCT)
H1 = 5 + len(rows_y) - 1
put(hs, 4, 7, "Summary", font=F_B)
items = [("Assumed dividend yield (input)", 0.013, PCT), ("Arithmetic mean excess (price)", f"=AVERAGE(E6:E{H1})", PCT),
         ("Arithmetic mean excess (total, + div yield)", "=H6+H5", PCT), ("Geometric Sensex price return", f"=(B{H1}/B5)^(1/(A{H1}-A5))-1", PCT),
         ("Average G-Sec", f"=AVERAGE(D6:D{H1})", PCT), ("Geometric excess (total)", "=H8+H5-H9", PCT),
         ("Standard error of arithmetic mean", f"=STDEV(E6:E{H1})/SQRT(COUNT(E6:E{H1}))", PCT), ("Implied ERP used (Damodaran)", "=ERP", PCT)]
for i, (lab, v, fmt) in enumerate(items):
    put(hs, 5 + i, 7, lab, font=F_B if "Geometric excess" in lab or "Implied" in lab else F_N)
    put(hs, 5 + i, 8, v, fmt, F_IN if isinstance(v, float) else F_B, FILL_IN if isinstance(v, float) else None)
note(hs, 14, "With a standard error near 6 points, 21 years of history cannot pin down the ERP — which is why forward-looking implied ERPs are preferred (TB2 Ch-2).", 7)

# ------------------------------------------------------------------ Housing cycle (BIS)
hcyc = pd.read_csv(V2 / "housing_cycle.csv", index_col=0, parse_dates=True)
hsw = sheet("Housing", "Housing-price cycle: BIS residential property prices for India vs realty stocks",
            "Real-estate specific: BIS (via FRED) nominal & real indices, 2010=100 basis as published; realty index from LongCycle", [12, 12, 12, 12, 12, 12, 4, 46, 12])
hdr(hsw, 4, ["Quarter", "Nominal idx", "Real idx", "Nominal YoY", "Real YoY", "Nifty Realty YoY"])
for i, (dt, row) in enumerate(hcyc.iterrows()):
    r_ = 5 + i
    put(hsw, r_, 1, dt.date(), "mmm-yy"); put(hsw, r_, 2, round(float(row["nominal_idx"]), 2), NUM2, F_IN); put(hsw, r_, 3, round(float(row["real_idx"]), 2), NUM2, F_IN)
    if i >= 4:
        put(hsw, r_, 4, f"=B{r_}/B{r_-4}-1", PCT); put(hsw, r_, 5, f"=C{r_}/C{r_-4}-1", PCT)
    v = row["realty_idx_yoy"]
    put(hsw, r_, 6, None if pd.isna(v) else round(float(v), 4), PCT, F_IN)
HS1 = 5 + len(hcyc) - 1
items = [("Nominal house-price CAGR", f"=(B{HS1}/B5)^(4/(ROWS(B5:B{HS1})-1))-1"), ("Real house-price CAGR", f"=(C{HS1}/C5)^(4/(ROWS(C5:C{HS1})-1))-1"),
         ("Latest nominal YoY", f"=D{HS1}"), ("Latest real YoY", f"=E{HS1}")]
for i, (lab, f) in enumerate(items):
    put(hsw, 5 + i, 8, lab); put(hsw, 5 + i, 9, f, PCT, F_B)
put(hsw, 10, 8, "Correlation: realty YoY vs house-price YoY (same quarter)"); put(hsw, 10, 9, f"=CORREL(D9:D{HS1-1},F9:F{HS1-1})", NUM2, F_B)
note(hsw, 12, "Real prices have grown only ~3.5% a year: most 'appreciation' is inflation. Stocks move on expectations and rates,", 8)
note(hsw, 13, "so they are negatively correlated with contemporaneous house-price growth — equity leads and overshoots the physical market.", 8)
ch = LineChart(); ch.title = "BIS India house prices (nominal vs real)"; ch.height, ch.width = 7, 14
ch.series.append(Series(Reference(hsw, min_col=2, min_row=5, max_row=HS1), title="Nominal")); ch.series.append(Series(Reference(hsw, min_col=3, min_row=5, max_row=HS1), title="Real"))
ch.set_categories(Reference(hsw, min_col=1, min_row=5, max_row=HS1)); ch.x_axis.number_format = "yyyy"
hsw.add_chart(ch, "H15")

# ------------------------------------------------------------------ Residual income (Palepu abnormal earnings) + justified P/B
ri = sheet("ResidualIncome", "Abnormal-earnings (residual income) valuation and justified price-to-book",
           "TB1 (Palepu) valuation: V = B₀ + Σ (ROE_t − Ke)·B_(t−1)/(1+Ke)^t ; ROE fades linearly to target over 10 years; justified P/B = (ROE − g)/(Ke − g)",
           [40] + [11] * 12)
RIR = {}
r = 4
for co in TARGETS:
    c3 = COLS3[co]
    sub(ri, r, NAMES[co], 13); r += 1
    put(ri, r, 1, "Book equity FY26 (B₀)"); put(ri, r, 2, f"={D(co,'Equity',2026)}", NUM)
    put(ri, r + 1, 1, "ROE FY26 (avg equity)"); put(ri, r + 1, 2, f"={D(co,'NetIncome',2026)}/{avg(co,'Equity',2026)}", PCT)
    put(ri, r + 2, 1, "Target ROE in year 10 (input)"); put(ri, r + 2, 2, 0.15, PCT, F_IN, FILL_IN)
    put(ri, r + 3, 1, "Payout ratio (FY26, held)"); put(ri, r + 3, 2, f"=MIN(0.9,{D(co,'DividendsPaid',2026)}/{D(co,'NetIncome',2026)})", PCT)
    put(ri, r + 4, 1, "Cost of equity — lens A / lens B"); put(ri, r + 4, 2, f"={W[co]['Ke']}", PCT); put(ri, r + 4, 3, f"={W[co]['Ke_B']}", PCT)
    put(ri, r + 5, 1, "Terminal growth"); put(ri, r + 5, 2, "=gT", PCT)
    hr_ = r + 7
    hdr(ri, hr_, ["Year", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])
    labs = ["ROE", "Opening book", "Net income", "Dividends", "Closing book", "Residual income (lens A)", "PV factor (lens A)", "PV RI (lens A)",
            "Residual income (lens B)", "PV factor (lens B)", "PV RI (lens B)"]
    for i, lb in enumerate(labs):
        put(ri, hr_ + 1 + i, 1, lb)
    for t in range(1, 11):
        c = L(1 + t); pcl = L(t)
        rr0 = hr_ + 1
        put(ri, rr0, 1 + t, f"=$B${r+1}+($B${r+2}-$B${r+1})*{t}/10", PCT)
        put(ri, rr0 + 1, 1 + t, f"=$B${r}" if t == 1 else f"={pcl}{rr0+4}", NUM)
        put(ri, rr0 + 2, 1 + t, f"={c}{rr0}*{c}{rr0+1}", NUM)
        put(ri, rr0 + 3, 1 + t, f"={c}{rr0+2}*$B${r+3}", NUM)
        put(ri, rr0 + 4, 1 + t, f"={c}{rr0+1}+{c}{rr0+2}-{c}{rr0+3}", NUM)
        put(ri, rr0 + 5, 1 + t, f"=({c}{rr0}-$B${r+4})*{c}{rr0+1}", NUM)
        put(ri, rr0 + 6, 1 + t, f"=1/(1+$B${r+4})^{t}", "0.000")
        put(ri, rr0 + 7, 1 + t, f"={c}{rr0+5}*{c}{rr0+6}", NUM)
        put(ri, rr0 + 8, 1 + t, f"=({c}{rr0}-$C${r+4})*{c}{rr0+1}", NUM)
        put(ri, rr0 + 9, 1 + t, f"=1/(1+$C${r+4})^{t}", "0.000")
        put(ri, rr0 + 10, 1 + t, f"={c}{rr0+8}*{c}{rr0+9}", NUM)
    rr0 = hr_ + 1; K = L(11)
    out0 = hr_ + 13
    res = [("Terminal RI (year 11) ÷ (Ke − g), discounted — lens A", f"={K}{rr0+5}*(1+$B${r+5})/($B${r+4}-$B${r+5})*{K}{rr0+6}"),
           ("Equity value — lens A = B₀ + ΣPV RI + PV terminal", f"=$B${r}+SUM(B{rr0+7}:{K}{rr0+7})+B{out0}"),
           ("Value per share — lens A (₹)", f"=B{out0+1}/{D(co,'Shares',2026)}"),
           ("Terminal RI — lens B", f"={K}{rr0+8}*(1+$B${r+5})/($C${r+4}-$B${r+5})*{K}{rr0+9}"),
           ("Equity value — lens B", f"=$B${r}+SUM(B{rr0+10}:{K}{rr0+10})+B{out0+3}"),
           ("Value per share — lens B (₹)", f"=B{out0+4}/{D(co,'Shares',2026)}"),
           ("Justified P/B on current ROE — lens A", f"=($B${r+1}-$B${r+5})/($B${r+4}-$B${r+5})"),
           ("Justified P/B on current ROE — lens B", f"=($B${r+1}-$B${r+5})/($C${r+4}-$B${r+5})"),
           ("Market P/B", f"=RelVal!N{RVR[co]}"),
           ("ROE the market price implies (lens A Ke) = g + P/B × (Ke − g)", f"=$B${r+5}+B{out0+8}*($B${r+4}-$B${r+5})")]
    for i, (lab, f) in enumerate(res):
        put(ri, out0 + i, 1, lab, font=F_B if "per share" in lab or "implies" in lab else F_N)
        put(ri, out0 + i, 2, f, NUM2 if "P/B" in lab or "per share" in lab else (PCT if "implies" in lab else NUM),
            F_B if "per share" in lab else F_N, FILL_KEY if "per share" in lab or "implies" in lab else None)
    RIR[co] = {"vpsA": f"ResidualIncome!$B${out0+2}", "vpsB": f"ResidualIncome!$B${out0+5}", "impROE": f"ResidualIncome!$B${out0+9}",
               "jpbA": f"ResidualIncome!$B${out0+6}"}
    r = out0 + 12
note(ri, r, "Book value is a weak anchor in real estate: land is carried at historical cost (DLF's Gurugram land was bought decades ago), so book understates economic capital", 1)
note(ri, r + 1, "and ROE overstates true returns on current land values. A justified P/B far below market P/B is partly an accounting artefact — NAV is the better anchor.", 1)

# ------------------------------------------------------------------ Alternative valuations: EVA reconciliation, FCFE, APV
av = sheet("Alt_Valuations", "Same firm, other routes: EVA-based value, FCFE equity value and APV",
           "Damodaran: firm value = invested capital + PV(EVA); FCFE discounted at Ke; APV = unlevered value + PV(tax shields) − expected distress cost",
           [46, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12])
r = 4
ALT = {}
for co in TARGETS:
    dsh = f"DCF_{co}"
    sub(av, r, NAMES[co], 13); r += 1
    hdr(av, r, ["Year-end discounting (to show exact equivalence)"] + [f"FY{27+i}" for i in range(10)] + ["Terminal"]); r += 1
    rw = {k: r + i for i, k in enumerate(["NOPAT", "Opening IC", "WACC", "EVA = NOPAT − WACC × opening IC", "FCFF", "Year-end DF",
                                          "PV EVA", "PV FCFF"])}
    for k, rr_ in rw.items():
        put(av, rr_, 1, k)
    for t in range(1, 11):
        c = L(1 + t); dc = L(2 + t); dp_ = L(1 + t)
        put(av, rw["NOPAT"], 1 + t, f"={dsh}!{dc}24", NUM)
        put(av, rw["Opening IC"], 1 + t, f"={dsh}!{dp_}27", NUM)
        put(av, rw["WACC"], 1 + t, f"={dsh}!{dc}29", PCT)
        put(av, rw["EVA = NOPAT − WACC × opening IC"], 1 + t, f"={c}{rw['NOPAT']}-{c}{rw['WACC']}*{c}{rw['Opening IC']}", NUM, F_B)
        put(av, rw["FCFF"], 1 + t, f"={dsh}!{dc}26", NUM)
        put(av, rw["Year-end DF"], 1 + t, f"={dsh}!{dc}32", "0.0000")
        put(av, rw["PV EVA"], 1 + t, f"={c}{rw['EVA = NOPAT − WACC × opening IC']}*{c}{rw['Year-end DF']}", NUM)
        put(av, rw["PV FCFF"], 1 + t, f"={c}{rw['FCFF']}*{c}{rw['Year-end DF']}", NUM)
    o = r + 9
    res = [("Terminal value of FCFF (from DCF)", f"={dsh}!B37"),
           ("Firm value via FCFF (year-end) = ΣPV FCFF + PV TV", f"=SUM(B{rw['PV FCFF']}:K{rw['PV FCFF']})+B{o}*{dsh}!L32"),
           ("Terminal EVA value = (TV − closing IC in FY36) discounted", f"=(B{o}-{dsh}!L27)*{dsh}!L32"),
           ("Firm value via EVA = opening IC + ΣPV EVA + PV terminal EVA", f"={dsh}!B27+SUM(B{rw['PV EVA']}:K{rw['PV EVA']})+B{o+2}"),
           ("Difference (should be ~0)", f"=B{o+3}-B{o+1}"),
           ("Mid-year uplift used in main DCF", f"={dsh}!B39-B{o+1}")]
    for i, (lab, f) in enumerate(res):
        put(av, o + i, 1, lab, font=F_B if "Difference" in lab or "via EVA" in lab else F_N)
        put(av, o + i, 2, f, NUM, F_B if "via" in lab else F_N, FILL_KEY if "Difference" in lab else None)
    # FCFE & APV (single-period perpetuity-consistent approximations on the same NOPAT path)
    f0 = o + 7
    ci = list(TARGETS).index(co); wcol = L(2 + ci)
    put(av, f0, 1, "FCFE route (debt kept at current D/V; Ke discounting)", font=F_B)
    fl = [("Equity value via FCFE ≈ firm value × E/V adj.: (Firm value − debt) using Ke-consistent check", f"={dsh}!B47"),
          ("Ke (lens A)", f"={W[co]['Ke']}"),
          ("Implied equity value per share", f"={dsh}!B49"),
          ("Note", "With constant D/V, FCFE at Ke and FCFF at WACC give the same equity value (Miles–Ezzell); differences arise only if leverage changes.")]
    for i, (lab, f) in enumerate(fl):
        put(av, f0 + 1 + i, 1, lab); put(av, f0 + 1 + i, 2, f, PCT if "Ke" in lab and "value" not in lab else NUM2, F_N)
    a0 = f0 + 6
    put(av, a0, 1, "APV route", font=F_B)
    al = [("Unlevered cost of equity Ku = Rf + βu × ERP", f"=Rf+BottomUp_Beta!$G${lr}*ERP", PCT),
          ("Debt (FY26)", f"={D(co,'TotalDebt',2026)}", NUM),
          ("PV of tax shields (permanent debt) = t × D", f"=Tax*B{a0+2}", NUM),
          ("Probability of distress (from synthetic rating, input)", 0.02 if co == "GPL" else 0.005, PCT),
          ("Distress cost as % of firm value (input)", 0.25, PCT),
          ("Expected distress cost = p × cost × firm value", f"=B{a0+4}*B{a0+5}*{dsh}!B39", NUM),
          ("Net benefit of debt (tax shield − expected distress cost)", f"=B{a0+3}-B{a0+6}", NUM)]
    for i, (lab, f, fmt) in enumerate(al):
        put(av, a0 + 1 + i, 1, lab); put(av, a0 + 1 + i, 2, f, fmt, F_IN if isinstance(f, float) else F_N, FILL_IN if isinstance(f, float) else None)
    note(av, a0 + 8, "Debt adds little value here: DLF is net cash; Godrej's tax shield is offset by distress risk — consistent with low sector leverage (Damodaran India D/E 0.21).")
    r = a0 + 11

# ------------------------------------------------------------------ Cap rates (Phoenix vs REIT yields vs G-Sec)
reit = {}
for k, nm in [("NEXUS", "Nexus Select Trust (malls)"), ("EMBASSY", "Embassy Office Parks"), ("MINDSPACE", "Mindspace Business Parks"), ("BIRET", "Brookfield India REIT")]:
    dv = pd.read_csv(RAW / k / "px_daily.csv", index_col=0); dv.index = pd.to_datetime(dv.index, utc=True)
    last = dv["Close"].dropna(); end = last.index[-1]
    ttm = dv.loc[dv.index > end - pd.Timedelta(days=365), "Dividends"].sum() if "Dividends" in dv else 0
    reit[nm] = (round(float(ttm), 2), round(float(last.iloc[-1]), 2), str(end.date()))
cr_ = sheet("CapRates", "What yield is the market accepting? Phoenix's implied cap rate vs listed REITs and the G-Sec",
            "Real-estate specific: cap rate = operating income ÷ property value. For a listed owner, EV ÷ EBITDA inverts to an implied yield",
            [46, 14, 14, 14, 40])
hdr(cr_, 4, ["Item", "Value", "", "", "Note"])
cl_ = [("Phoenix market cap", f"=RelVal!D{RVR['PML']}", NUM), ("Phoenix net debt", f"=RelVal!E{RVR['PML']}", NUM),
       ("Minority interest at proportional market value", f"=B5*{D('PML','NetIncomeInclMI',2026)}/{D('PML','NetIncome',2026)}-B5", NUM),
       ("Enterprise value incl. minorities", "=B5+B6+B7", NUM),
       ("Consolidated EBITDA FY26 (core EBIT + D&A)", f"={R('PML','CoreEBIT',2026)}+{D('PML','DandA',2026)}", NUM),
       ("Implied EBITDA yield (≈ cap rate proxy)", "=B9/B8", PCT), ("10-yr G-Sec", "=Gsec", PCT), ("Spread over G-Sec", "=B10-B11", PCT)]
for i, (lab, f, fmt) in enumerate(cl_):
    put(cr_, 5 + i, 1, lab, font=F_B if "yield" in lab or "Spread" in lab else F_N)
    put(cr_, 5 + i, 2, f, fmt, F_B if "yield" in lab else F_N, FILL_KEY if "yield" in lab else None)
hdr(cr_, 15, ["Listed REIT", "TTM distribution (₹/unit)", "Unit price (₹)", "Distribution yield", "Price date"])
for i, (nm, (d_, p_, dt_)) in enumerate(reit.items()):
    r_ = 16 + i
    put(cr_, r_, 1, nm); put(cr_, r_, 2, d_, NUM2, F_IN, FILL_IN); put(cr_, r_, 3, p_, NUM2, F_IN, FILL_IN)
    put(cr_, r_, 4, f"=IFERROR(B{r_}/C{r_},\"n.a.\")", PCT, F_B); put(cr_, r_, 5, dt_, font=F_NOTE)
put(cr_, 21, 1, "Median REIT distribution yield", font=F_B); put(cr_, 21, 4, "=MEDIAN(D16:D19)", PCT, F_B)
put(cr_, 22, 1, "Phoenix value if priced at the mall-REIT yield (EBITDA ÷ Nexus yield − net debt − MI) per share", font=F_B)
put(cr_, 22, 4, f"=(B9/D16-B6-B7)/{D('PML','Shares',2026)}", NUM2, F_B, FILL_KEY)
note(cr_, 24, "Phoenix's EBITDA yield (~3%) is far below the mall REIT's cash yield and the G-Sec: investors pay for growth (new malls, rent escalations, consumption) that a REIT,")
note(cr_, 25, "which distributes 90% of cash, cannot reinvest for. The gap is the 'growth premium' — it must be earned by building malls at yields above the cost of capital.")
note(cr_, 26, "Caveat: REIT distributions include return of capital and interest; Phoenix EBITDA includes hotels, offices and residential — a proxy, not a like-for-like cap rate.")

# ------------------------------------------------------------------ Real option view of land (Damodaran, undeveloped land)
ro = sheet("RealOption", "Contingent-claim view: undeveloped land as a call option (illustrative)",
           "Module 7 (contingent-claim valuation; TB2 & Dark Side Ch. on options): land = right, not obligation, to develop when prices justify it", [52, 14, 46])
ops = [("S — present value of developed property (₹ cr, illustrative input)", 90000, NUM, "Scale to a land bank's gross development value"),
       ("K — present value of development cost (₹ cr, input)", 100000, NUM, "Construction + approvals"),
       ("σ — annual volatility of property value (input)", 0.30, PCT, "Below stock volatility (~36–50%), which embeds leverage and sentiment"),
       ("T — years the option can be held", 10, NUM2, "Land bank horizon"),
       ("r — rupee risk-free rate", "=Rf", PCT, ""),
       ("y — cost of delay (yield forgone ≈ 1/T)", "=1/B8", PCT, "Damodaran: annual cost of waiting"),
       ("d1", "=(LN(B5/B6)+(B9-B10+B7^2/2)*B8)/(B7*SQRT(B8))", "0.000", ""),
       ("d2", "=B11-B7*SQRT(B8)", "0.000", ""),
       ("Option value = S·e^(−yT)·N(d1) − K·e^(−rT)·N(d2)", "=B5*EXP(-B10*B8)*NORMSDIST(B11)-B6*EXP(-B9*B8)*NORMSDIST(B12)", NUM, ""),
       ("Static NPV (develop now) = S − K", "=B5-B6", NUM, ""),
       ("Value of flexibility = max(option, NPV) − max(NPV, 0)", "=MAX(B13,B14)-MAX(B14,0)", NUM, "European approximation; if option < NPV, develop now"),
       ("DLF: market cap − DCF equity value (₹ cr)", f"=RelVal!D{RVR['DLF']}-DCF_DLF!B47", NUM, "The gap an option story would need to explain")]
for i, (lab, v, fmt, nt) in enumerate(ops):
    r_ = 5 + i
    put(ro, r_, 1, lab, font=F_B if "Option value" in lab or "flexibility" in lab else F_N)
    put(ro, r_, 2, v, fmt, F_IN if isinstance(v, (int, float)) else F_N, FILL_IN if isinstance(v, (int, float)) else (FILL_KEY if "Option value" in lab else None))
    put(ro, r_, 3, nt, font=F_NOTE)
hdr(ro, 19, ["Option value (₹ cr) for σ (rows) × S/K (cols)", "", ""])
sk = [0.8, 1.0, 1.25, 1.5]; sg = [0.15, 0.25, 0.35]
for j, k in enumerate(sk):
    put(ro, 20, 2 + j, k, NUM2, F_B, FILL_SUB)
for i, sgm in enumerate(sg):
    r_ = 21 + i
    put(ro, r_, 1, sgm, PCT, F_B, FILL_SUB)
    for j in range(len(sk)):
        kk = f"{L(2+j)}$20"
        d1 = f"(LN({kk})+($B$9-$B$10+$A{r_}^2/2)*$B$8)/($A{r_}*SQRT($B$8))"
        f = f"=$B$6*{kk}*EXP(-$B$10*$B$8)*NORMSDIST({d1})-$B$6*EXP(-$B$9*$B$8)*NORMSDIST({d1}-$A{r_}*SQRT($B$8))"
        put(ro, r_, 2 + j, f, NUM)
for cc in "DE":
    ro.column_dimensions[cc].width = 14
note(ro, 25, "Illustrative, not a valuation: project-level land-bank data (area, approvals, GDV) sit in investor presentations we could not access from this environment.")
note(ro, 26, "The point: even land with negative NPV today has option value when σ is high and T long — one reason markets pay above DCF for land-rich developers.")

# ------------------------------------------------------------------ Monte Carlo results (computed in scripts/monte_carlo.py; pasted values)
mcf = ROOT / "data/processed/v2/monte_carlo.json"
if mcf.exists():
    MC = _json.loads(mcf.read_text())
    mc = sheet("MonteCarlo", "Monte Carlo simulation of the FCFF model (10,000 draws per company and lens)",
               "Inputs drawn: growth scale, target margin, sales-to-capital, WACC shift, terminal g — distributions stated below. Values in ₹/share.",
               [40, 14, 14, 14, 14, 14, 14, 14])
    hdr(mc, 4, ["Statistic", "DLF — lens A", "DLF — lens B", "Godrej — lens A", "Godrej — lens B", "Phoenix — lens A", "Phoenix — lens B"])
    keys = [("p5", "5th percentile"), ("p25", "25th percentile"), ("median", "Median"), ("mean", "Mean"), ("p75", "75th percentile"), ("p95", "95th percentile"),
            ("prob_above_price", "P(value > market price)"), ("price", "Market price")]
    for i, (k, lab) in enumerate(keys):
        put(mc, 5 + i, 1, lab, font=F_B if k in ("median", "prob_above_price") else F_N)
        for j, (co, lens) in enumerate([(c, l) for c in ["DLF", "GPL", "PML"] for l in ["A", "B"]]):
            v = MC[co][lens][k]
            put(mc, 5 + i, 2 + j, v, PCT if k == "prob_above_price" else NUM, F_IN, FILL_KEY if k in ("median", "prob_above_price") else FILL_IN)
    r_ = 15
    put(mc, r_, 1, "Input distributions", font=F_B)
    for i, line in enumerate(MC["spec"]):
        put(mc, r_ + 1 + i, 1, line, font=F_NOTE)
    note(mc, r_ + 2 + len(MC["spec"]), "Values pasted from scripts/monte_carlo.py (Python re-implementation of the DCF sheet, checked to reproduce the base case exactly).")
    imgp = ROOT / "reports/charts/monte_carlo.png"
    if imgp.exists():
        from openpyxl.drawing.image import Image as XLImage
        im = XLImage(str(imgp)); im.width, im.height = 900, 300
        mc.add_image(im, "A26")

# ------------------------------------------------------------------ Scenarios & market-implied assumptions (engine-computed, pasted)
scf = ROOT / "data/processed/v2/scenarios.json"
if scf.exists():
    SC = _json.loads(scf.read_text())
    sc_ = sheet("Scenarios_Implied", "Bear / base / bull scenarios and what today's price implies about the long run",
                "Values from scripts/monte_carlo.py (Python replica of the DCF sheets, verified to reproduce base values exactly)",
                [46, 13, 13, 13, 13, 13, 46])
    hdr(sc_, 4, ["Scenario (₹/share)", "DLF", "Godrej", "Phoenix", "", "", "Definition"])
    defs = {"bear": "growth ×0.6, margin −8pp, S/C ×0.75, WACC +1pp, g 5.0%", "base": "as in DCF sheets (lens A)",
            "bull": "growth ×1.3, margin +8pp, S/C ×1.25, WACC −1pp, g 6.0%", "bull_lensB": "bull with lens-B high-growth WACC",
            "price": "latest market price"}
    for i, k in enumerate(["bear", "base", "bull", "bull_lensB", "price"]):
        put(sc_, 5 + i, 1, {"bull_lensB": "Bull + lens B", "price": "Market price"}.get(k, k.capitalize()), font=F_B)
        for j, co in enumerate(["DLF", "GPL", "PML"]):
            put(sc_, 5 + i, 2 + j, round(SC["scenarios"][co][k], 1), NUM, F_IN, FILL_KEY if k == "price" else FILL_IN)
        put(sc_, 5 + i, 7, defs[k], font=F_NOTE)
    hdr(sc_, 12, ["What the price implies (lens A)", "DLF", "Godrej", "Phoenix", "", "", "Reading"])
    imp = SC["implied"]
    put(sc_, 13, 1, "Implied perpetual growth (stable WACC held)", font=F_B)
    put(sc_, 14, 1, "Implied stable WACC (g = 5.5% held)", font=F_B)
    for j, co in enumerate(["DLF", "GPL", "PML"]):
        put(sc_, 13, 2 + j, imp[co]["terminal_g"], PCT, F_IN, FILL_KEY); put(sc_, 14, 2 + j, imp[co]["stable_wacc"], PCT, F_IN, FILL_KEY)
    put(sc_, 13, 7, "≈ India's long-run nominal GDP growth: the market prices real estate as an India-growth perpetuity", font=F_NOTE)
    put(sc_, 14, 7, "≈ the 10-yr G-Sec: as if long-run equity risk in real estate were near zero", font=F_NOTE)
    r_ = 17
    put(sc_, r_, 1, "Terminal-assumption grid (₹/share): stable WACC (rows) × perpetual growth (cols)", font=F_B); r_ += 1
    for co in ["DLF", "GPL", "PML"]:
        grid = imp[co]["terminal_grid"]; gs_ = list(next(iter(grid.values())).keys())
        hdr(sc_, r_, [NAMES[co]] + [f"g = {float(g):.1%}" for g in gs_]); r_ += 1
        for wsv, rowv in grid.items():
            put(sc_, r_, 1, float(wsv), PCT, F_B, FILL_SUB)
            for j, g in enumerate(gs_):
                v = rowv[g]
                put(sc_, r_, 2 + j, "n.m." if v is None else round(v, 0), NUM, F_IN)
            r_ += 1
        r_ += 1
    note(sc_, r_, "The last row in each block is our stable WACC (β → 1). Reading across shows how much of today's price rests on perpetual growth above the risk-free cap.")

# ------------------------------------------------------------------ AEG (abnormal earnings growth) appended to ResidualIncome
r_ = ri.max_row + 3
put(ri, r_, 1, "Abnormal earnings growth (AEG) model — Palepu: V₀ = E₁/Ke + Σ AEG_t / [Ke·(1+Ke)^(t−1)], AEG_t = E_t + Ke·D_(t−1) − (1+Ke)·E_(t−1)", font=F_B)
r_ += 1
for co in TARGETS:
    # locate this company's RI block rows (ROE row = header+1) by scanning labels
    start = [rr for rr in range(1, ri.max_row) if ri.cell(rr, 1).value == NAMES[co]][0]
    hrow = start + 8          # 'Year' header row (block start + 7 + 1)
    ni, dv = hrow + 3, hrow + 4
    put(ri, r_, 1, NAMES[co], font=F_B); r_ += 1
    put(ri, r_, 1, "AEG_t (lens A Ke)")
    for t in range(2, 11):
        c, pcl = L(1 + t), L(t)
        put(ri, r_, 1 + t, f"={c}{ni}+$B${start+5}*{pcl}{dv}-(1+$B${start+5})*{pcl}{ni}", NUM)
    put(ri, r_ + 1, 1, "PV of AEG_t = AEG_t / [Ke(1+Ke)^(t−1)]")
    for t in range(2, 11):
        c = L(1 + t)
        put(ri, r_ + 1, 1 + t, f"={c}{r_}/($B${start+5}*(1+$B${start+5})^({t}-1))", NUM)
    put(ri, r_ + 2, 1, "Capitalised next-year earnings E₁ / Ke"); put(ri, r_ + 2, 2, f"=B{ni}/$B${start+5}", NUM)
    put(ri, r_ + 3, 1, "AEG value (10-yr, no terminal) per share (₹)", font=F_B)
    put(ri, r_ + 3, 2, f"=(B{r_+2}+SUM(C{r_+1}:K{r_+1}))/{D(co,'Shares',2026)}", NUM2, F_B, FILL_KEY)
    put(ri, r_ + 4, 1, "Implied forward P/E = price ÷ E₁ vs 1/Ke", font=F_NOTE)
    put(ri, r_ + 4, 2, f"={PX[co][3]}*{D(co,'Shares',2026)}/B{ni}", NUM2); put(ri, r_ + 4, 3, f"=1/$B${start+5}", NUM2)
    r_ += 6
note(ri, r_, "AEG and residual income are algebraically linked (both anchor on accounting earnings); forward P/E far above 1/Ke means the price capitalises abnormal earnings growth.")

# ------------------------------------------------------------------ Concept coverage matrix (textbooks + handout + prior projects)
cc = sheet("Concept_Map", "Concept coverage: course modules, textbook concepts and prior-project methods → where each is applied",
           "TB1 = Palepu, Healy & Bernard; TB2 = Damodaran on Valuation; RB1 = Dark Side of Valuation. Sheet references are to this workbook.",
           [10, 44, 14, 46])
hdr(cc, 4, ["Module", "Concept / method", "Source", "Where applied"])
CM = [
 ("1", "Role of financial reporting; business activities → statements", "TB1", "Report §1; Data_* sheets"),
 ("2", "Porter five forces; generic strategies", "TB1", "Report §2; deck slide 5"),
 ("2", "BCG matrix (by business unit); SPACE; value chain", "Handout", "Report §2"),
 ("2", "PESTEL, SWOT, blind-spot, consumer segmentation & CLV", "Prior projects", "Report §2"),
 ("2", "Real-estate cycle; house-price data", "Extension", "LongCycle, Housing"),
 ("3", "Accounting policies, flexibility, noise vs bias, red flags", "TB1", "Recast; Ratios (CFO/PAT, accruals); report §3"),
 ("3", "Revenue recognition (Ind AS 115), borrowing costs (23), JVs (111), investment property (40)", "TB1 / Ind AS", "Recast; report §3"),
 ("4", "Recasting: operating vs financing vs non-operating; NOA, NFO, NOPAT", "TB1", "Recast"),
 ("4", "Asset/liability distortions (restricted cash, customer advances, capitalised interest)", "TB1", "Recast rows; WACC (cash interest)"),
 ("5", "Ratio analysis: growth, margins, turnover, liquidity, solvency, cash flow (50 ratios)", "TB1 / prior", "Ratios"),
 ("5", "DuPont 3-step, 5-step; ROE change attribution", "TB1 / prior", "DuPont"),
 ("5", "Palepu decomposition ROE = RNOA + (RNOA − NBC) × NFL", "TB1", "DuPont"),
 ("5", "Cash-flow analysis; FCF; accruals", "TB1", "Ratios"),
 ("5", "EVA, CVA, balanced scorecard", "Handout", "Growth_EVA; Alt_Valuations; report §5"),
 ("5", "Altman Z and Z'' (credit/distress analysis)", "TB1 (credit) / prior", "AltmanZ"),
 ("5", "Industry benchmarking", "TB2 data", "Industry_Benchmark"),
 ("5", "Quarterly analysis, TTM", "Prior projects", "Quarterly"),
 ("6", "Risk-free rate net of default spread; ERP; CRP", "TB2 / RB1", "Inputs; WACC"),
 ("6", "Implied vs historical ERP", "TB2", "HistERP"),
 ("6", "Regression beta: SE, t, CI, R², alpha, Jensen's alpha", "TB2", "Beta_Monthly, Beta_Weekly"),
 ("6", "Blume adjustment; beta drift (rolling)", "Prior / TB2", "Beta_*; RollingBeta"),
 ("6", "Bottom-up beta (Hamada unlever/relever, median)", "TB2", "BottomUp_Beta"),
 ("6", "Fundamental/industry beta; thin-trading bias", "TB2 data", "Industry_Benchmark; WACC lens B"),
 ("6", "Multi-factor / APM (market + interest-rate factor)", "Handout", "RateFactor"),
 ("6", "Cost of debt via synthetic rating; WACC with market weights", "TB2", "WACC"),
 ("7", "Growth estimation: historical, fundamental (RR × ROIC; b × ROE)", "TB2 / TB1", "Growth_EVA; Ratios"),
 ("7", "Prospective analysis: forecasting revenue, margins, reinvestment", "TB1", "DCF_* (drivers)"),
 ("7", "Naive time-series (FORECAST) benchmark", "Prior projects", "DCF_* (benchmark row)"),
 ("7", "FCFF two-phase DCF; terminal value; stable beta → 1; mid-year", "TB2", "DCF_*"),
 ("7", "FCFE; APV; EVA-based firm value", "TB2", "Alt_Valuations"),
 ("7", "DDM two-stage; payout consistent with g/ROE", "TB2", "DDM"),
 ("7", "Abnormal earnings (residual income) and AEG; justified P/B", "TB1", "ResidualIncome"),
 ("7", "Contingent-claim valuation (land as an option)", "TB2 / RB1", "RealOption"),
 ("7", "Sensitivity, scenarios, simulation; reverse DCF", "TB2 / RB1", "DCF_* grids; Scenarios_Implied; MonteCarlo"),
 ("8", "Four-step relative valuation; P/E, PEG, P/B, P/S, EV/EBITDA", "TB2", "RelVal"),
 ("8", "Controlling for differences: regression of P/B on ROE", "TB2", "RelVal"),
 ("8", "Yield-based relative value (cap rates vs REITs)", "Extension", "CapRates"),
 ("9", "Cross holdings, minority interests, distress, illiquidity, control", "TB2", "DCF bridge; Alt_Valuations (APV); report §9"),
]
for i, (m, c_, src_, w_) in enumerate(CM):
    put(cc, 5 + i, 1, m); put(cc, 5 + i, 2, c_); put(cc, 5 + i, 3, src_, font=F_NOTE); put(cc, 5 + i, 4, w_)

# ------------------------------------------------------------------ cosmetics: tab colours by module
TAB = {"Index": "1F2A30", "Inputs": "6B7780", "Concept_Map": "1F2A30"}
for ws_ in wb.worksheets:
    n_ = ws_.title
    col = TAB.get(n_) or ("B9C6C8" if n_.startswith("Data_") else "2F5D62" if n_ in ("Recast", "Ratios", "DuPont", "AltmanZ", "Growth_EVA", "Quarterly", "Industry_Benchmark")
                          else "C08A3E" if n_.startswith(("Beta", "BottomUp", "WACC", "RollingBeta", "RateFactor", "HistERP"))
                          else "8C4A3C" if n_.startswith(("DCF", "DDM", "ResidualIncome", "Alt_", "RealOption", "Scenarios", "MonteCarlo"))
                          else "88A6A8")
    ws_.sheet_properties.tabColor = col

# ====================================================================== v3: practitioner cross-checks (public company & broker data)
SRC = {
 "dlf_fy26": "DLF Q4 FY26 release/transcript (dlf.in), Zee Business, Whalesbook, Geojit (May-2026)",
 "dccdl": "DCCDL FY26 via DLF results coverage (Whalesbook/Investywise); net debt/EBITDA 3.2x (Q4 FY26)",
 "dlf_pipe": "DLF FY27 guidance & pipeline: Business Standard 5-Aug-2026, DSIJ, Arthneeti (Q1 FY27 call)",
 "gpl_fy26": "Godrej Properties FY26 results: Outlook Business, Kotak Neo, Free Press Journal (May-2026)",
 "gpl_g": "Godrej FY27 guidance: Angel One, Outlook Business, Sahi (May–Aug 2026)",
 "pml_fy26": "Phoenix Mills Q4 FY26 call (Tijori transcript), Free Press Journal, ICICI Direct Q4 FY26 note",
 "brokers": "Broker notes as reported by Business Today, Business Standard, Multibagg, MarketScreener, Investing.com, StockAnalysis (Jun–Sep 2026)",
}
ok_ = sheet("Operating_KPIs", "Operating KPIs from company disclosures (what the market actually trades on)",
            "Public company results, calls and guidance (FY26 actuals; FY27 guidance). Hard inputs — verify against investor presentations before final use.",
            [46, 14, 14, 14, 52])
hdr(ok_, 4, ["KPI (₹ crore unless stated)", "DLF", "Godrej", "Phoenix", "Source"])
KP = [
 ("Sales bookings (pre-sales) FY26", 20143, 34171, None, "dlf_fy26 / gpl_fy26"),
 ("Customer collections FY26", 13517, 19965, None, "dlf_fy26 / gpl_g"),
 ("Bookings guidance FY27", 20000, 39000, None, "dlf_pipe / gpl_g"),
 ("Collections guidance FY27", None, 24000, None, "gpl_g"),
 ("Launch pipeline (medium term / FY27 launch target)", 60000, 48000, None, "dlf_pipe / gpl_g"),
 ("Development potential (msf)", 188, None, None, "dlf_pipe (DSIJ)"),
 ("Company-reported net cash (development) FY26", 14155, None, None, "dlf_fy26"),
 ("Management 'operating cash flow' FY26 (pre-land)", None, 7830, None, "gpl_fy26 (Free Press Journal)"),
 ("Business development FY26 (expected booking value)", None, 42100, None, "gpl_g"),
 ("Retail consumption FY26", None, None, 16578, "pml_fy26"),
 ("Retail rental income FY26", None, None, 2157, "pml_fy26"),
 ("Retail EBITDA FY26", None, None, 2246, "pml_fy26"),
 ("Office EBITDA (9M FY26, annualised ×4/3)", None, None, round(103 * 4 / 3), "pml_fy26 (quartr 9M)"),
 ("Hospitality EBITDA (9M FY26, annualised ×4/3)", None, None, round(190 * 4 / 3), "pml_fy26 (quartr 9M)"),
 ("Company consolidated EBITDA FY26", 3070, 2826, 2637, "company releases"),
 ("Rental platform (DCCDL) EBITDA FY26", 5718, None, None, "dccdl"),
 ("DCCDL net debt Q4 FY26", 18150, None, None, "dccdl"),
 ("DCCDL operational portfolio (msf) / occupancy", 50, None, None, "dccdl (≈95% occupied)"),
]
KR = {}
for i, (lab, a, b, c, s_) in enumerate(KP):
    r_ = 5 + i; KR[lab] = r_
    put(ok_, r_, 1, lab)
    for j, v in enumerate([a, b, c]):
        if v is not None:
            put(ok_, r_, 2 + j, v, NUM, F_IN, FILL_IN)
    put(ok_, r_, 5, s_, font=F_NOTE)
r_ = 5 + len(KP) + 1
put(ok_, r_, 1, "Derived", font=F_B); r_ += 1
der = [("Bookings ÷ recognised revenue FY26 (x)", f"=B5/{D('DLF','Revenue',2026)}", f"=C5/{D('GPL','Revenue',2026)}", None),
       ("Collections ÷ bookings FY26", "=B6/B5", "=C6/C5", None),
       ("Godrej: management OCF − statutory CFO = land & BD spend proxy", None, f"=C12-{D('GPL','CFO',2026)}", None),
       ("Phoenix: rental income ÷ consumption (effective rent-to-sales)", None, None, "=D15/D14"),
       ("Phoenix: consumption growth needed for rent growth (FY26 rent +10%, consumption +21%)", None, None, "lag: rents reset with leases")]
for i, (lab, a, b, c) in enumerate(der):
    put(ok_, r_ + i, 1, lab)
    for j, v in enumerate([a, b, c]):
        if v is not None:
            put(ok_, r_ + i, 2 + j, v, X if "(x)" in lab else (PCT if "÷" in lab else NUM), F_B)
r_ += len(der) + 1
for k, v in SRC.items():
    put(ok_, r_, 1, k, font=F_NOTE); put(ok_, r_, 2, v, font=F_NOTE); r_ += 1

# ---------------------------------------------------------------------- Data verification (Yahoo vs company)
dv = sheet("Data_Check", "Data verification: our dataset (Yahoo consolidated) vs company-reported FY26 figures",
           "Headline reconciliation. Differences come from definitions (revenue from operations vs total income; restricted cash; EBITDA incl./excl. other income)",
           [44, 14, 14, 12, 52])
hdr(dv, 4, ["Item", "Our dataset", "Company / press", "Difference", "Comment"])
chk = [("DLF revenue from operations", f"={D('DLF','Revenue',2026)}", 8194, "Geojit: revenue from operations ₹8,194 cr; total income ₹10,174 cr"),
       ("DLF PAT", f"={D('DLF','NetIncome',2026)}", 4408, "Company PAT ~₹4,408 cr (₹4,256 cr pre-exceptional)"),
       ("DLF net cash", f"={R('DLF','Liquid',2026)}-{R('DLF','Debt',2026)}", 14155, "We exclude RERA-restricted cash (₹5,003 cr); adding it back ≈ company figure"),
       ("Godrej PAT", f"={D('GPL','NetIncome',2026)}", 1850, "Exact match"),
       ("Phoenix revenue", f"={D('PML','Revenue',2026)}", 4423, "Company consolidated revenue ₹4,423 cr"),
       ("Phoenix EBITDA (ours: core EBIT + D&A)", f"={R('PML','CoreEBIT',2026)}+{D('PML','DandA',2026)}", 2637, "Definitions differ (other income, exceptional)"),
       ("Phoenix PAT (owners)", f"={D('PML','NetIncome',2026)}", 1224, "Exact match"),
       ("DLF share of JV profit vs 66.66% × DCCDL PAT pre-exceptional (₹2,726 cr)", f"={R('DLF','JV',2026)}", round(0.6666 * 2726, 0), "Within ~1%: our JV line is essentially DCCDL")]
for i, (lab, ours, comp, cm) in enumerate(chk):
    r_ = 5 + i
    put(dv, r_, 1, lab); put(dv, r_, 2, ours, NUM); put(dv, r_, 3, comp, NUM, F_IN, FILL_IN)
    put(dv, r_, 4, f"=B{r_}/C{r_}-1", PCT, F_B); put(dv, r_, 5, cm, font=F_NOTE)
note(dv, 15, "Conclusion: profit lines match; revenue and cash differ by definition, not error. Ratios use our consistent dataset; KPIs come from company disclosures.")

# ---------------------------------------------------------------------- NAV / SOTP (practitioner method)
nv = sheet("NAV_SOTP", "Practitioner cross-check: net asset value / sum-of-the-parts (the method the sell-side uses)",
           "Rental assets at cap rates; residential at PV of after-tax margin on the sales pipeline; Godrej also on embedded PAT. Inputs blue; edit to test.",
           [56, 14, 14, 52])
def nrow(r_, lab, v, fmt=NUM, inp=False, note_=""):
    put(nv, r_, 1, lab, font=F_B if lab.startswith(("=", "NAV", "Equity", "Implied", "Value")) else F_N)
    put(nv, r_, 2, v, fmt, F_IN if inp else F_N, FILL_IN if inp else None)
    if note_: put(nv, r_, 4, note_, font=F_NOTE)
put(nv, 4, 1, "DLF — sum of the parts", font=F_B)
rows_dlf = [
 ("DCCDL EBITDA FY26", f"=Operating_KPIs!B{KR['Rental platform (DCCDL) EBITDA FY26']}", NUM, False, ""),
 ("Forward growth to FY27 (input)", 0.12, PCT, True, "Rental growth ~15–18% in FY26 quarters; 12% conservative"),
 ("Cap rate (input)", 0.075, PCT, True, "Motilal Oswal uses 7.5% on DLF commercial"),
 ("DCCDL gross asset value = EBITDA × (1+g) ÷ cap", "=B5*(1+B6)/B7", NUM, False, ""),
 ("Less: DCCDL net debt", f"=-Operating_KPIs!B{KR['DCCDL net debt Q4 FY26']}", NUM, False, ""),
 ("DLF share (66.66%)", 0.6666, PCT, True, "GIC owns 33.34%"),
 ("Value of DCCDL stake", "=(B8+B9)*B10", NUM, False, ""),
 ("Residential: annual pre-sales (input, FY27 guidance held)", f"=Operating_KPIs!B{KR['Bookings guidance FY27']}", NUM, False, ""),
 ("Years of pipeline (input)", 5, NUM2, True, "₹60k cr medium-term pipeline + Dahlias inventory ≈ 5 yrs at ₹20k cr"),
 ("EBITDA margin on pre-sales (input)", 0.40, PCT, True, "Luxury Gurugram; core EBIT margin was 21–33% on recognised revenue"),
 ("Cash lag from booking to margin realisation (years, input)", 1.5, NUM2, True, "construction-linked payment plans"),
 ("Discount rate for residential cash flows (input)", 0.12, PCT, True, "Practitioner range 11.75–12% (REIT valuers); our Ke lens A ≈ 14.7%"),
 ("PV of after-tax pipeline margin", "=B12*B14*(1-Tax)*SUMPRODUCT(1/(1+B16)^(ROW(INDIRECT(\"1:\"&B13))+B15))", NUM, False, ""),
 ("Add: development net cash (company-reported)", f"=Operating_KPIs!B{KR['Company-reported net cash (development) FY26']}", NUM, False, ""),
 ("NAV of identifiable parts", "=B11+B17+B18", NUM, False, ""),
 ("NAV per share (identifiable parts)", f"=B19/{D('DLF','Shares',2026)}", NUM2, False, ""),
 ("Market cap", f"=RelVal!D{RVR['DLF']}", NUM, False, ""),
 ("Implied value of the residual land bank (market cap − identifiable NAV)", "=B21-B19", NUM, False, "What the market pays for land beyond the 5-year pipeline"),
 ("Residual development potential (msf, input: 188 total less ~40 in pipeline)", 148, NUM, True, "DSIJ: 188 msf potential; pipeline share is our estimate"),
 ("Implied value per sq ft of residual potential (₹)", "=B22*1e7/(B23*1e6)", NUM, False, "₹ per saleable sq ft of undeveloped potential"),
]
for i, (lab, v, fmt, inp, nt) in enumerate(rows_dlf):
    nrow(5 + i, lab, v, fmt, inp, nt)
put(nv, 30, 1, "Phoenix Mills — sum of the parts", font=F_B)
rows_pml = [
 ("Retail EBITDA FY26", f"=Operating_KPIs!D{KR['Retail EBITDA FY26']}", NUM, False, ""),
 ("Forward growth to FY27 (input)", 0.12, PCT, True, "Management guides double-digit consumption growth"),
 ("Retail cap rate (input)", 0.07, PCT, True, "Motilal Oswal 6.5–7.5%"),
 ("Office EBITDA (annualised)", f"=Operating_KPIs!D{KR['Office EBITDA (9M FY26, annualised ×4/3)']}", NUM, False, ""),
 ("Office cap rate (input)", 0.08, PCT, True, "Motilal Oswal 7–8%"),
 ("Hospitality EBITDA (annualised)", f"=Operating_KPIs!D{KR['Hospitality EBITDA (9M FY26, annualised ×4/3)']}", NUM, False, ""),
 ("Hospitality EV/EBITDA (input)", 12, NUM2, True, ""),
 ("Capital work in progress at book", f"={D('PML','CWIP',2026)}", NUM, False, "New malls (Kolkata, Surat) at cost"),
 ("Gross asset value", "=B31*(1+B32)/B33+B34/B35+B36*B37+B38", NUM, False, ""),
 ("Less: net debt", f"=-RelVal!E{RVR['PML']}", NUM, False, ""),
 ("Owners' share after minority platforms (input)", "=1-DCF_PML!B45", PCT, False, "CPPIB/GIC share ≈ minority share of PAT"),
 ("Equity NAV to owners", "=(B39+B40)*B41", NUM, False, ""),
 ("NAV per share", f"=B42/{D('PML','Shares',2026)}", NUM2, False, ""),
 ("Market price", f"={PX['PML'][3]}", NUM2, False, ""),
 ("Implied growth premium over NAV", "=B44/B43-1", PCT, False, "ICICI Securities adds an explicit 70% growth premium to its ₹1,287 NAV"),
 ("Perpetual NOI growth implied by the retail cap rate at an 11.75% discount rate (g = r − cap)", "=0.1175-B33", PCT, False, "11.75% = WACC used by an Indian REIT valuer"),
]
for i, (lab, v, fmt, inp, nt) in enumerate(rows_pml):
    nrow(31 + i, lab, v, fmt, inp, nt)
put(nv, 49, 1, "Godrej Properties — embedded-profit and pipeline methods", font=F_B)
rows_gpl = [
 ("FY27 bookings guidance", f"=Operating_KPIs!C{KR['Bookings guidance FY27']}", NUM, False, ""),
 ("FY28 bookings (FY27 × (1+g), input g)", 0.10, PCT, True, "growth after guidance year"),
 ("FY28 bookings", "=B50*(1+B51)", NUM, False, ""),
 ("Embedded PAT margin on bookings (input)", 0.15, PCT, True, "≈ 20% EBITDA margin after tax and interest; normalised"),
 ("Embedded PAT FY28", "=B52*B53", NUM, False, ""),
 ("Multiple on embedded PAT (input)", 12, NUM2, True, "Jefferies: 12x embedded PAT of Mar-28 pre-sales"),
 ("Equity value (embedded PAT method)", "=B54*B55", NUM, False, ""),
 ("Value per share — embedded PAT", f"=B56/{D('GPL','Shares',2026)}", NUM2, False, ""),
 ("Earnings yield implied by the multiple (1 ÷ multiple)", "=1/B55", PCT, False, ""),
 ("Growth implied by the multiple at lens-A Ke (g = Ke − 1/multiple)", f"={W['GPL']['Ke']}-B58", PCT, False, "a 12x multiple is itself a perpetual-growth assumption"),
 ("Market price", f"={PX['GPL'][3]}", NUM2, False, ""),
 ("Broker consensus target (avg of 22–23 analysts)", 2296, NUM2, True, "Investing.com ₹2,266; StockAnalysis ₹2,326 — midpoint"),
]
for i, (lab, v, fmt, inp, nt) in enumerate(rows_gpl):
    nrow(50 + i, lab, v, fmt, inp, nt)
note(nv, 63, "Reading: practitioner NAVs use asset-level discount rates of ~11.75–12% and cap rates of 6.5–8%, which embed perpetual NOI growth of ~4–5% — close to our 5.5% cap.")
note(nv, 64, "What reconciles NAV with price is (i) land beyond the visible pipeline and (ii) an explicit or implicit growth premium — both judgements about the very long run.")
NAVR = {"dlf_nav_ps": "NAV_SOTP!$B$20", "dlf_land": "NAV_SOTP!$B$22", "dlf_psf": "NAV_SOTP!$B$24", "dccdl": "NAV_SOTP!$B$11",
        "pml_nav_ps": "NAV_SOTP!$B$43", "pml_prem": "NAV_SOTP!$B$45", "gpl_emb_ps": "NAV_SOTP!$B$57"}

# ---------------------------------------------------------------------- Broker consensus
bk = sheet("Broker_Views", "What the sell-side thinks: public broker ratings and targets (Jun–Sep 2026)",
           "As reported in the financial press and aggregators; for context, not inputs. Dates and methods vary — check the original notes.",
           [22, 16, 12, 12, 60])
hdr(bk, 4, ["Company / broker", "Rating", "Target (₹)", "Date", "Method as reported"])
BKS = [("DLF", None, None, None, None),
       ("Motilal Oswal", "Buy", 755, "Aug-26", "NAV, 0% premium; 7.5% cap on commercial"), ("Kotak", "Buy", 940, "Aug-26", ""),
       ("Citi", "Buy", 750, "Aug-26", ""), ("Jefferies", "Buy", 815, "2026", ""), ("ICICI Securities", "Buy", 810, "2026", "No premium to NAV"),
       ("Nomura", "Buy", 740, "2026", "Trades ~3% below residential NAV"), ("Morgan Stanley", "Hold", 730, "Jul-26", "Downgrade"), ("BofA", "Sell", 695, "Aug-26", "Downgrade"),
       ("Godrej Properties", None, None, None, None),
       ("HSBC", "Buy", 2900, "2026", "14% discount to Jun-26 NAV"), ("Motilal Oswal", "Buy", 2350, "Aug-26", ""), ("Choice", "Buy", 2520, "Feb-26", "SOTP"),
       ("Geojit", "Buy", 2096, "2026", "FY28 book value"), ("BOBCAPS", "Hold", 1911, "May-26", "~1.9x NAV (cut to 1.2x in Aug)"), ("Jefferies", "Buy", None, "2026", "12x embedded PAT of Mar-28 pre-sales"),
       ("Phoenix Mills", None, None, None, None),
       ("ICICI Securities", "Buy", 2200, "Jul-26", "SOTP NAV ₹1,287 + 70% growth premium ₹901 + cash ₹8"), ("Motilal Oswal", "Buy", 2200, "2026", "SOTP; retail cap 6.5–7.5%, office 7–8%"),
       ("SBI Securities", "Buy", 2230, "Jun-26", ""), ("Jefferies", "Buy", 2085, "Apr-26", ""), ("Nomura", "Neutral", 1700, "Apr-26", "")]
r_ = 5; BKR = {}; BKSUM = {}
for nm, rt, tp, dtt, mth in BKS:
    if rt is None:
        sub(bk, r_, nm, 5); cur = nm; BKR[cur] = [r_ + 1, None]; r_ += 1; continue
    put(bk, r_, 1, nm); put(bk, r_, 2, rt); put(bk, r_, 3, tp, NUM, F_IN, FILL_IN) if tp else put(bk, r_, 3, "n.a.")
    put(bk, r_, 4, dtt); put(bk, r_, 5, mth, font=F_NOTE); BKR[cur][1] = r_; r_ += 1
r_ += 1
hdr(bk, r_, ["Summary", "Median target", "Our DCF A", "Price", "Reading"]); r_ += 1
for co, nm in [("DLF", "DLF"), ("GPL", "Godrej Properties"), ("PML", "Phoenix Mills")]:
    a, b = BKR[nm]
    put(bk, r_, 1, NAMES[co], font=F_B); put(bk, r_, 2, f"=MEDIAN(C{a}:C{b})", NUM, F_B, FILL_KEY)
    put(bk, r_, 3, f"={DCF[co]['vps']}", NUM); put(bk, r_, 4, f"={PX[co][3]}", NUM)
    put(bk, r_, 5, "Brokers price on NAV with ~12% discount rates and growth premia; our DCF uses CAPM with g ≤ Rf", font=F_NOTE)
    BKSUM[co] = f"Broker_Views!$B${r_}"; r_ += 1
note(bk, r_ + 1, "Sources: " + SRC["brokers"])

# ---------------------------------------------------------------------- Dimson (thin-trading) betas and macro/cycle context
dmf = ROOT / "data/processed/v2/dimson.json"
if dmf.exists():
    DM = _json.loads(dmf.read_text())
    dmw = sheet("Dimson_Beta", "Thin-trading check: Dimson (1979) sum beta = β(market, t) + β(market, t−1)",
                "60 monthly returns; if a stock reacts to the market with a lag, OLS beta is biased toward zero and the lag coefficient is positive", [26, 13, 13, 13, 44])
    hdr(dmw, 4, ["Company", "OLS beta", "Dimson sum beta", "Lag coefficient", "Reading"])
    for i, (k, v) in enumerate(DM.items()):
        r_ = 5 + i
        nm = {"DLF": "DLF", "GODREJPROP": "Godrej Properties", "PHOENIXLTD": "Phoenix Mills", "OBEROIRLTY": "Oberoi Realty", "PRESTIGE": "Prestige",
              "BRIGADE": "Brigade", "SOBHA": "Sobha", "LODHA": "Lodha", "MAHLIFE": "Mahindra Lifespace", "SUNTECK": "Sunteck", "PURVA": "Puravankara", "ANANTRAJ": "Anant Raj"}[k]
        put(dmw, r_, 1, nm); put(dmw, r_, 2, v["ols"], "0.00", F_IN); put(dmw, r_, 3, v["dimson_sum"], "0.00", F_IN); put(dmw, r_, 4, v["lag_coef"], "0.00", F_IN)
        put(dmw, r_, 5, "lagged response → OLS understates" if v["lag_coef"] > 0.2 else ("no lag effect" if abs(v["lag_coef"]) <= 0.2 else "negative lag (noise)"), font=F_NOTE)
    n_ = len(DM)
    put(dmw, 6 + n_, 1, "Median", font=F_B); put(dmw, 6 + n_, 2, f"=MEDIAN(B5:B{4+n_})", "0.00", F_B); put(dmw, 6 + n_, 3, f"=MEDIAN(C5:C{4+n_})", "0.00", F_B, FILL_KEY)
    note(dmw, 8 + n_, "Small caps (Puravankara, Anant Raj, Mahindra Lifespace, Sobha) show large positive lag coefficients: their OLS betas are too low.")
    note(dmw, 9 + n_, "Industry averages dominated by such firms (Damodaran's 156) understate the risk of large, liquid developers — support for lens A and hypothesis H2.")
    note(dmw, 10 + n_, "Computed in Python (scripts in repo) on the same 60-month window as Beta_Monthly; values pasted.")

mcx = sheet("Macro_Cycle", "Where are we in the cycle? Rates, housing volumes and growth (latest public data)",
            "Context for the long-run assumptions; inputs from RBI, Anarock/PropEquity and IMF as reported in the press (Jul–Oct 2026)", [52, 16, 56])
hdr(mcx, 4, ["Indicator", "Value", "Source / reading"])
MCX = [("RBI policy repo rate (7-Oct-2026)", 0.055, PCT, "RBI MPC hiked 25bp to 5.50%; stance 'calibrated tightening' (RBI press release; Drishti, Moneylife)"),
       ("10-yr G-Sec, Oct-2026 monthly average", "=Gsec", PCT, "OECD/FRED; multi-year highs in Sep–Oct 2026 (Trading Economics)"),
       ("Housing sales, top-7 cities, Q3 2026 (units)", 100220, NUM, "Anarock: +3% y/y after −6% in Q2 2026"),
       ("Housing sales, PropEquity set, Q3 2026 (units)", 103170, NUM, "PropEquity: −6% y/y, −4% q/q"),
       ("Unsold inventory, top-7 cities (units)", 630590, NUM, "Anarock: +12% y/y"),
       ("New launches growth, Q3 2026 y/y", 0.18, PCT, "Anarock: supply rising faster than sales"),
       ("Average price growth, Q3 2026 y/y", 0.07, PCT, "Anarock"),
       ("Real GDP growth FY27 (IMF, Oct-2026 WEO)", 0.07, PCT, "IMF raised to 7.0%"),
       ("Nominal GDP growth FY27 (projection)", 0.101, PCT, "As reported; FY26 nominal growth slowed to ~8–8.5% on low inflation"),
       ("BIS real house-price growth, latest y/y", f"=Housing!I8", PCT, "Real prices flat to slightly negative")]
for i, (lab, v, fmt, s_) in enumerate(MCX):
    r_ = 5 + i
    put(mcx, r_, 1, lab); put(mcx, r_, 2, v, fmt, F_IN if not isinstance(v, str) else F_N, FILL_IN if not isinstance(v, str) else None); put(mcx, r_, 3, s_, font=F_NOTE)
note(mcx, 17, "Late-cycle signals: sales volumes flat, inventory and launches rising, prices still up, and policy rates turning higher.")
note(mcx, 18, "Implied perpetual growth of 10–12% (Scenarios_Implied) sits at or above projected nominal GDP growth — little room for a slowdown.")

# NAV_SOTP additions: DLF embedded margin on sold units (upper-bound reconciling item) and Godrej sensitivity grid
put(nv, 26, 1, "Memo: gross margin still to be recognised on units already sold (management)", font=F_N); put(nv, 26, 2, 24500, NUM, F_IN, FILL_IN)
put(nv, 26, 4, "DLF Q4 FY26 call: ₹24,500 cr from sales made; >₹40,000 cr incl. launched inventory. FY26 gross margin 39%, target 45%+", font=F_NOTE)
put(nv, 27, 1, "Upper bound if none of it were already in net cash: after-tax per share (₹)", font=F_N)
put(nv, 27, 2, f"=B26*(1-Tax)/{D('DLF','Shares',2026)}", NUM2)
put(nv, 28, 1, "Identifiable NAV per share — range (₹)", font=F_B); put(nv, 28, 2, "=B20", NUM2, F_B, FILL_KEY); put(nv, 28, 3, "=B20+B27", NUM2, F_B, FILL_KEY)
put(nv, 28, 4, "Part of the sold-unit margin is already in net cash via customer advances; true value lies within the range", font=F_NOTE)
put(nv, 66, 1, "Godrej sensitivity: value per share (₹) — embedded PAT margin (rows) × multiple (cols)", font=F_B)
mults, margins = [10, 12, 14], [0.12, 0.15, 0.18]
for j, mlt in enumerate(mults):
    put(nv, 67, 2 + j, mlt, NUM2, F_B, FILL_SUB)
for i, mg in enumerate(margins):
    put(nv, 68 + i, 1, mg, PCT, F_B, FILL_SUB)
    for j in range(3):
        put(nv, 68 + i, 2 + j, f"=$B$52*$A{68+i}*{L(2+j)}$67/{D('GPL','Shares',2026)}", NUM)
note(nv, 72, "Godrej does not disclose an embedded margin; FY26 EBITDA was ~34% of total income but ~15% in Q4. Only the harshest cell (12%, 10x) is below price (−9%); all others are above.")


# ---------------------------------------------------------------------- H1 FY27 reality check on DCF growth assumptions
r_ = qs.max_row + 3
put(qs, r_, 1, "Reality check: H1 FY27 vs H1 FY26 revenue against the FY27 growth assumed in the DCF", font=F_B); r_ += 1
hdr(qs, r_, ["Company", "H1 FY26 (₹ cr)", "H1 FY27 (₹ cr)", "H1 growth", "FY27 assumed", "H2 growth needed", "", "Note"]); r_ += 1
for co, tk in TARGETS.items():
    q = pd.read_csv(RAW / tk / "quarterly_income_stmt.csv", index_col=0)
    q.columns = [pd.Timestamp(c) for c in q.columns]; rev = (q.loc["Total Revenue"] / 1e7)
    g_ = lambda d: float(rev.get(pd.Timestamp(d), float("nan")))
    jun25, dec25, mar26, jun26, sep26 = g_("2025-06-30"), g_("2025-12-31"), g_("2026-03-31"), g_("2026-06-30"), g_("2026-09-30")
    put(qs, r_, 1, NAMES[co], font=F_B)
    put(qs, r_, 2, f"={round(jun25,1)}+({D(co,'Revenue',2026)}-{round(jun25,1)}-{round(dec25,1)}-{round(mar26,1)})", NUM)
    put(qs, r_, 3, round(jun26 + sep26, 1), NUM, F_IN)
    put(qs, r_, 4, f"=C{r_}/B{r_}-1", PCT, F_B)
    put(qs, r_, 5, f"=DCF_{co}!C5", PCT)
    put(qs, r_, 6, f"=({D(co,'Revenue',2026)}*(1+E{r_})-C{r_})/({D(co,'Revenue',2026)}-B{r_})-1", PCT, F_B, FILL_KEY)
    put(qs, r_, 8, "Sep-25 quarter derived as FY26 total − other three quarters", font=F_NOTE)
    r_ += 1
note(qs, r_ + 1, "DLF's FY27 assumption was cut from +40% to −15% after this check; Godrej and Phoenix assumptions are consistent with H1.")

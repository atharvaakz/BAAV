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
 ("9", "Cross holdings, minority interests, distress, illiquidity, control", "TB2", "DCF bridge; Alt_Valuations (APV); report §10"),
 ("6", "Thin-trading adjustment (Dimson sum beta)", "TB2 / Dimson (1979)", "Dimson_Beta"),
 ("7", "Prospective analysis reality check against latest quarters", "TB1", "Quarterly (H1 FY27 test)"),
 ("7–8", "Practitioner NAV / SOTP; embedded-profit multiple; cap rates", "Practice / brokers", "NAV_SOTP; Broker_Views"),
 ("3", "Data verification vs company-reported figures", "TB1 (accounting quality)", "Data_Check"),
 ("2", "Cycle position: rates, volumes, inventory, GDP", "Extension", "Macro_Cycle"),
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
 ("Office EBITDA (9M FY26, annualised ×4/3)", None, None, 141, "Phoenix Q4 FY26 call: operational office EBITDA ₹141 cr (FY26 actual)"),
 ("Hospitality EBITDA (9M FY26, annualised ×4/3)", None, None, 276, "Phoenix Q4 FY26 call: hotel EBITDA ₹276 cr (FY26 actual)"),
 ("Company consolidated EBITDA FY26", 3070, 2826, 2637, "company releases"),
 ("Rental platform (DCCDL) EBITDA FY26", 5718, None, None, "dccdl"),
 ("DCCDL net debt Q4 FY26", 18150, None, None, "dccdl"),
 ("DCCDL operational portfolio (msf) / occupancy", 50, None, None, "dccdl (≈95% occupied)"),
 ("H1 FY27 bookings", 4457, 16659, None, "Q1+Q2 FY27 results (Oct-2026): DLF 657+3,800; Godrej +7% y/y"),
 ("H1 FY27 collections", None, 9666, None, "Godrej +25% y/y; Q2 ₹5,318 cr"),
 ("H1 FY27 retail rental income / growth", None, None, 1200, "Phoenix +16% y/y; FY27–28 guidance 14–15%"),
 ("Q2 FY27 retail consumption (growth +25%)", None, None, 4685, "Phoenix; Mall of Asia occupancy 96%"),
 ("Net cash, Sep-2026", 15100, None, None, "DLF, after ₹1,900 cr dividend"),
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
 ("Residual development potential (msf): 137 balance potential − 25 in launch pipeline", 112, NUM, True, "DLF Q4 FY26 call: '137 million sq ft of balance potential', ~25 msf pipeline"),
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
       ("BIS real house-price growth, latest y/y", f"=Housing!I8", PCT, "Real prices flat to slightly negative"),
       ("Nifty Realty trailing P/E (Jul-2026)", 40.5, NUM2, "indexPe; 5-yr median 48.5, 3-yr median 47.7 — below its own recent history"),
       ("Nifty Realty 5-yr median P/E", 48.5, NUM2, "The last five years were the up-cycle; earlier history (2010–20) included far lower prices (LongCycle)")]
for i, (lab, v, fmt, s_) in enumerate(MCX):
    r_ = 5 + i
    put(mcx, r_, 1, lab); put(mcx, r_, 2, v, fmt, F_IN if not isinstance(v, str) else F_N, FILL_IN if not isinstance(v, str) else None); put(mcx, r_, 3, s_, font=F_NOTE)
note(mcx, 19, "Late-cycle signals: sales volumes flat, inventory and launches rising, prices still up, and policy rates turning higher.")
note(mcx, 20, "Implied perpetual growth of 9–12% (Scenarios_Implied) sits at or above projected nominal GDP growth — little room for a slowdown.")

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
put(nv, 25, 1, "Book inventory per sq ft of total development potential (₹) — land at historical cost", font=F_N)
put(nv, 25, 2, f"={D('DLF','Inventory',2026)}*1e7/(137*1e6)", NUM)
put(nv, 25, 4, "Inventory (incl. WIP) ÷ 137 msf balance potential; compare with the market-implied value per sq ft above", font=F_NOTE)


# ---------------------------------------------------------------------- Official disclosures: transcripts, guidance credibility, management-case DCF, ESG/BRSR
of = sheet("Official_Disclosures", "From the companies' own mouths: earnings-call transcripts, guidance credibility and a management-case valuation",
           "Primary sources: DLF Q4 FY26 call (14-May-2026, dlf.in); Phoenix Q4 FY26 call (Apr-2026); Godrej Q2 FY27 call (Oct-2026, via third-party write-up). Text extracted with pdftotext; see references/official/",
           [58, 16, 16, 16, 52])
hdr(of, 4, ["Statement / metric", "DLF", "Godrej", "Phoenix", "Source & reading"])
OFF = [("FY26 gross margin (reported)", 0.39, None, None, PCT, "DLF call: 'gross margin of 39% for the fiscal' (Q4: ~46%)"),
       ("New margin created per year (guidance, ₹ cr)", 9500, None, None, NUM, "DLF: '₹9,000–10,000 cr of margin every year' on ~₹20,000 cr sales (≈45–50%)"),
       ("Development free cash flow per year (guidance, ₹ cr)", 7500, None, None, NUM, "DLF: '₹7,000–8,000 cr of free cash flow every year on the Devco side'"),
       ("Net cash FY26 (₹ cr) / of which in RERA escrow", 14155, None, None, NUM, "DLF: 'of the ₹14,000 cr … almost ₹11,200 cr sitting in RERA balance', unlocking from FY27–28"),
       ("RERA escrow balance (₹ cr)", 11200, None, None, NUM, "Not free cash until projects complete"),
       ("Balance land potential (msf) / in launch pipeline (msf)", 137, None, None, NUM, "DLF: 137 msf balance potential, ~25 msf pipeline; ~40 msf North & metros outside pipeline"),
       ("Super-luxury pricing (₹ per sq ft, super area): Dahlias / Camellias", 100000, None, 120000, NUM, "DLF call: Dahlias ~₹1 lakh/sq ft, Camellias ~₹1.2 lakh (Camellias shown in col D for layout)"),
       ("Rental: FY27 exit run-rate (₹ cr) / NOI growth guidance", 8200, None, None, NUM, "DLF: total rental ~₹8,200 cr; 'mid-teens growth in NOI' for 4–5 years"),
       ("Office occupancy: non-SEZ / SEZ", 0.985, None, 0.70, PCT, "DLF non-SEZ 98–99% (SEZ 88–89%); Phoenix office portfolio 70% (mature 83%)"),
       ("H2 FY27 targets: collections / operating cash flow (₹ cr)", None, 15000, None, NUM, "Godrej Q2 FY27 call (write-up): ₹15,000 cr collections, ₹7,000 cr OCF in H2; FY28 reported ROE ~20%"),
       ("H2 FY27 launch pipeline (₹ cr)", None, 32000, None, NUM, "Godrej: only one-third of annual launches done in H1"),
       ("Retail rental growth guidance FY27–28", None, None, 0.145, PCT, "Phoenix: 14–15%; 36–50% of area renews in 2–3 yrs at ~20% uplift"),
       ("Retail consumption FY26 (₹ cr) / growth", None, None, 16587, NUM, "Phoenix call: ₹16,587 cr, +21%; fashion ~60% of area, +16%"),
       ("Operating free cash flow FY26 (₹ cr)", None, 7830, 2140, NUM, "Godrej pre-land OCF; Phoenix 'operating FCF after WC, tax and interest'"),
       ("Hotel: St Regis ARR (₹) / EBITDA margin", None, None, 21000, NUM, "Phoenix: ARR > ₹21,000, EBITDA margin 49%")]
for i, (lab, a, b, c, fmt, s_) in enumerate(OFF):
    r_ = 5 + i
    put(of, r_, 1, lab)
    for j, v in enumerate([a, b, c]):
        if v is not None:
            put(of, r_, 2 + j, v, fmt, F_IN, FILL_IN)
    put(of, r_, 5, s_, font=F_NOTE)
r0 = 5 + len(OFF) + 2
put(of, r0, 1, "Guidance credibility: what they said vs what they did", font=F_B)
hdr(of, r0 + 1, ["Item", "Guidance", "Actual", "Hit rate", "Source"])
GC = [("DLF FY26 sales bookings (₹ cr)", 20000, 20143, "Guided ₹20,000 cr; delivered despite deferring launches"),
      ("Godrej FY26 bookings (₹ cr)", 32500, 34171, "FY26 guidance ₹32,500 cr (company); historically beats bookings guidance by ~18% on average"),
      ("Godrej FY26 collections (₹ cr)", 21000, 19965, "Missed internal collections target by ~5% (press)"),
      ("DLF H1 FY27 bookings vs pro-rata FY27 guidance (₹ cr)", 10000, 4457, "Back-ended: launches deferred (Aureva) — watch H2")]
for i, (lab, g, a_, s_) in enumerate(GC):
    r_ = r0 + 2 + i
    put(of, r_, 1, lab); put(of, r_, 2, g, NUM, F_IN, FILL_IN); put(of, r_, 3, a_, NUM, F_IN, FILL_IN)
    put(of, r_, 4, f"=C{r_}/B{r_}", PCT, F_B); put(of, r_, 5, s_, font=F_NOTE)
m0 = r0 + 8
put(of, m0, 1, "Management-case cash DCF for DLF's development business (using management's own FCF guidance)", font=F_B)
mrow = [("Development FCF, year 1 (₹ cr)", "=B7", NUM, False, "midpoint of ₹7,000–8,000 cr"),
        ("Growth years 2–10 (input)", 0.05, PCT, True, "sales guidance flat at ~₹20k cr; margin & price growth"),
        ("Discount rate (lens A Ke; DLF is net cash)", f"={W['DLF']['Ke']}", PCT, False, ""),
        ("Terminal growth", "=gT", PCT, False, ""),
        ("Stable discount rate (β → 1)", "=DCF_DLF!B14", PCT, False, ""),
        ("PV of FCF years 1–10", None, NUM, False, ""),
        ("PV of terminal value", None, NUM, False, ""),
        ("Development business value", None, NUM, False, ""),
        ("Add: DCCDL stake — DCF (capitalised) / NAV (7.5% cap)", f"={DCF['DLF']['vps']}*0+DCF_DLF!B42", NUM, False, "capitalised-earnings value from DCF sheet"),
        ("Less: escrow cash already counted inside development FCF (avoid double count)", 0, NUM, True, "FCF guidance includes escrow release; net cash added only ex-escrow below"),
        ("Add: free net cash ex-escrow (₹14,155 − ₹11,200 cr)", "=B8-B9", NUM, False, ""),
        ("Equity value — management case", None, NUM, False, ""),
        ("Per share (₹)", None, NUM2, False, ""),
        ("Per share with DCCDL at the 7.5% cap-rate NAV (₹)", None, NUM2, False, ""),
        ("Market price (₹)", f"={PX['DLF'][3]}", NUM2, False, "")]
for i, (lab, v, fmt, inp, nt) in enumerate(mrow):
    r_ = m0 + 1 + i
    put(of, r_, 1, lab, font=F_B if lab.startswith(("Equity", "Per share")) else F_N)
    if v is not None:
        put(of, r_, 2, v, fmt, F_IN if inp else F_N, FILL_IN if inp else None)
    put(of, r_, 5, nt, font=F_NOTE)
b = m0 + 1
put(of, b + 5, 2, f"=SUMPRODUCT(B{b}*(1+B{b+1})^(ROW(INDIRECT(\"1:10\"))-1)/(1+B{b+2})^ROW(INDIRECT(\"1:10\")))", NUM)
put(of, b + 6, 2, f"=B{b}*(1+B{b+1})^9*(1+B{b+3})/(B{b+4}-B{b+3})/(1+B{b+2})^10", NUM)
put(of, b + 7, 2, f"=B{b+5}+B{b+6}", NUM, F_B)
put(of, b + 11, 2, f"=B{b+7}+B{b+8}-B{b+9}+B{b+10}", NUM, F_B, FILL_KEY)
put(of, b + 12, 2, f"=B{b+11}/{D('DLF','Shares',2026)}", NUM2, F_B, FILL_KEY)
put(of, b + 13, 2, f"=(B{b+11}-B{b+8}+NAV_SOTP!B11)/{D('DLF','Shares',2026)}", NUM2, F_B, FILL_KEY)
MGMT = {"ps": f"Official_Disclosures!$B${b+12}", "ps_nav": f"Official_Disclosures!$B${b+13}", "dev": f"Official_Disclosures!$B${b+7}"}
note(of, b + 16, "Reading: on management's own cash-flow guidance, DLF is worth far more than our recognised-revenue DCF — recognition (completed-contract method) lags cash by years.")
note(of, b + 17, "Even so, the price needs DCCDL at broker cap rates plus value for land beyond the guided horizon. Guidance is the company's, not ours: treat as the bull anchor.")

esg = sheet("ESG_BRSR", "ESG and BRSR: what the sustainability filings show, and why it matters for value",
            "DLF BRSR FY2024-25 (reasonable assurance on BRSR Core); DCCDL Sustainability Report FY2025-26 (ISAE 3000/3410 assured). Godrej/Phoenix BRSRs: NSE/BSE blocked automated access (503/403) — to be added",
            [56, 18, 18, 50])
hdr(esg, 4, ["Indicator", "Value", "Prior year", "Source / reading"])
ES = [("DLF total energy consumed (GJ)", 1199213, 1203703, NUM, "BRSR P6 Q1; flat while portfolio grew"),
      ("of which renewable (GJ)", 193584, 169868, NUM, "≈16% renewable"),
      ("Renewable share", "=B6/B5", "=C6/C5", PCT, ""),
      ("Energy intensity per unit of physical output", 0.123, 0.144, NUM2, "BRSR: falling 15%"),
      ("Water consumption (kilolitres)", 11553788, 7241284, NUM, "BRSR P6; rose with occupancy"),
      ("Employees (permanent) / women share", 3103, 0.1015, NUM, "Women 10.15% (prior-year column shows share)"),
      ("Employee turnover (male / female)", 0.19, 0.35, PCT, "Female turnover far higher — a social-pillar flag"),
      ("LTIFR (employees) / fatalities", 0.13, 0, NUM2, "Zero fatalities FY25"),
      ("DCCDL Scope 1 emissions (ktCO2e)", 16.02, 11.78, NUM2, "SR FY26 (prior FY25)"),
      ("DCCDL Scope 2 emissions (ktCO2e)", 97.84, 98.05, NUM2, "Purchased electricity"),
      ("DCCDL Scope 3 emissions (ktCO2e)", 190.57, 190.92, NUM2, "63% of total — tenants & embodied carbon"),
      ("DCCDL total emissions (ktCO2e)", "=SUM(B13:B15)", "=SUM(C13:C15)", NUM2, "Flat y/y while rental income grew ~15% → intensity falling"),
      ("Water recycled & reused (million KL)", 2.35, None, NUM2, "DCCDL SR FY26"),
      ("Green certification", "LEED Platinum (entire rental portfolio); 32 LEED Zero Water", None, None, "DCCDL; also WiredScore Platinum, GRESB participant")]
for i, (lab, v, pv, fmt, s_) in enumerate(ES):
    r_ = 5 + i
    put(esg, r_, 1, lab); put(esg, r_, 2, v, fmt, F_IN if not str(v).startswith("=") else F_N, FILL_IN if not str(v).startswith("=") else None)
    if pv is not None: put(esg, r_, 3, pv, fmt if lab != "Employees (permanent) / women share" else PCT, F_IN if not str(pv).startswith("=") else F_N)
    put(esg, r_, 4, s_, font=F_NOTE)
note(esg, 21, "Why ESG matters for value here: (1) green-certified Grade-A offices command rent premia and lower vacancy (DCCDL non-SEZ 98–99% occupied);")
note(esg, 22, "(2) multinational tenants and global capital (GIC, CPPIB) require it; (3) it lowers cost of capital via ratings and sustainability-linked debt;")
note(esg, 23, "(4) residential developers face construction-dust bans (NCR) and water stress — an operational risk visible in BRSR 'areas of water stress' disclosures.")


# ---------------------------------------------------------------------- Audited annual-report tie-out (DLF FY26 integrated annual report, dlf.in)
a0 = of.max_row + 3
put(of, a0, 1, "Tie-out to DLF's audited FY2025-26 consolidated statements (annual report, ₹ lakh ÷ 100 = ₹ cr)", font=F_B)
hdr(of, a0 + 1, ["Line", "Our dataset", "Annual report", "Difference", "Reading"])
AR = [("Total equity (owners)", "="+D('DLF', 'Equity', 2026), 45473.37, "Exact"),
      ("Total assets", "="+D('DLF', 'TotalAssets', 2026), 74874.77, "Exact"),
      ("Inventories", "="+D('DLF', 'Inventory', 2026), 24717.48, "Exact"),
      ("Share of profit of JVs & associates", "="+R('DLF','JV',2026), 1792.83, "Exact: the DCCDL line"),
      ("Cash flow from operations", "="+D('DLF', 'CFO', 2026), 6347.38, "Exact"),
      ("Revenue from operations", "="+D('DLF', 'Revenue', 2026), 8194.02, "Data vendor nets some items; AR is the reported figure"),
      ("Finance costs (P&L, net of capitalisation)", "="+D('DLF', 'InterestExpense', 2026), 199.07, "Most interest is capitalised into inventory (Ind AS 23)"),
      ("Cash & cash equivalents", "="+D('DLF', 'Cash', 2026), 2273.22, "Vendor 'cash' field excludes deposits; AR adds ₹5,473 cr other bank balances"),
      ("RERA-designated balances in the notes (current a/c 6,201 + escrow 2,994 + 116 + 1,858)", 11169.0, 11200, "Audited notes ≈ management's '₹11,200 cr in RERA'")]
for i, (lab, ours, ar, rd) in enumerate(AR):
    r_ = a0 + 2 + i
    put(of, r_, 1, lab)
    put(of, r_, 2, ours if not isinstance(ours, str) or ours.startswith("=") else ours, NUM)
    put(of, r_, 3, ar, NUM, F_IN, FILL_IN)
    put(of, r_, 4, f"=IFERROR(B{r_}/C{r_}-1,\"\")", PCT, F_B)
    put(of, r_, 5, rd, font=F_NOTE)
note(of, a0 + 3 + len(AR), "Balance sheet, JV profit and operating cash flow tie to the rupee; differences are definitional (revenue, cash) and explained.")


# ---------------------------------------------------------------------- Godrej: audited annual-report tie-out and BRSR FY26
g0 = of.max_row + 3
put(of, g0, 1, "Tie-out to Godrej Properties' audited FY2025-26 consolidated statements (Integrated Annual Report, ₹ cr)", font=F_B)
hdr(of, g0 + 1, ["Line", "Our dataset", "Annual report", "Difference", "Reading"])
GAR = [("Total assets", "=" + D('GPL', 'TotalAssets', 2026), 81894.43, "Exact"),
       ("Inventories", "=" + D('GPL', 'Inventory', 2026), 57806.91, "Exact"),
       ("Total equity (owners + NCI)", "=" + D('GPL', 'Equity', 2026) + "+" + D('GPL', 'MinorityInterest', 2026), 19354.89, "Exact"),
       ("Profit for the year", "=" + D('GPL', 'NetIncomeInclMI', 2026), 1840.66, "Exact"),
       ("Profit attributable to owners", "=" + D('GPL', 'NetIncome', 2026), 1850.20, "Exact"),
       ("Cash flow from operations", "=" + D('GPL', 'CFO', 2026), -2003.34, "Exact — negative because land is inventory"),
       ("Cash & cash equivalents", "=" + D('GPL', 'Cash', 2026), 1860.74, "Exact"),
       ("Revenue from operations", "=" + D('GPL', 'Revenue', 2026), 5131.43, "Vendor nets some items"),
       ("Other income", "=" + D('GPL', 'InterestIncome', 2026) + "+" + D('GPL', 'SpecialItems', 2026), 3279.45, "AR other income ₹3,279 cr = 39% of total income — confirms profit is non-operating"),
       ("Finance costs (P&L)", "=" + D('GPL', 'InterestExpense', 2026), 136.86, "Most of ₹1,247 cr interest paid is capitalised into inventory")]
for i, (lab, ours, ar, rd) in enumerate(GAR):
    r_ = g0 + 2 + i
    put(of, r_, 1, lab); put(of, r_, 2, ours, NUM); put(of, r_, 3, ar, NUM, F_IN, FILL_IN)
    put(of, r_, 4, f"=IFERROR(B{r_}/C{r_}-1,\"\")", PCT, F_B); put(of, r_, 5, rd, font=F_NOTE)

e0 = esg.max_row + 3
put(esg, e0, 1, "Godrej Properties BRSR FY2025-26 (Integrated Report; reasonable assurance on BRSR Core by TÜV SÜD)", font=F_B)
hdr(esg, e0 + 1, ["Indicator", "FY26", "FY25", "Reading"])
GE = [("Total energy consumed (GJ) — own sites & offices", 44462, 37202, NUM, "Boundary excludes contractor energy; not comparable to DLF's rental-asset boundary"),
      ("of which renewable (GJ)", 14560, 5651, NUM, ""),
      ("Renewable share", f"=B{e0+3}/B{e0+2}", f"=C{e0+3}/C{e0+2}", PCT, "Up sharply; claims Scope 1+2 carbon neutrality"),
      ("Scope 1 / Scope 2 emissions (tCO2e)", 936.16, 3831.81, NUM, "FY26 Scope 1 (col B) and Scope 2 (col C)"),
      ("Water consumption (kilolitres)", 531252, 408565, NUM, "Of which 90,137 kl recycled in FY26"),
      ("Permanent employees / women share", 5124, 0.38, NUM, "Women 38% (col C) — vs DLF 10%"),
      ("Employee turnover (male / female)", 0.22, 0.17, PCT, "Total 20% (FY25 23%)"),
      ("LTIFR (employees) / fatalities", 0, 0, NUM, "")]
for i, (lab, v, pv, fmt, s_) in enumerate(GE):
    r_ = e0 + 2 + i
    put(esg, r_, 1, lab); put(esg, r_, 2, v, fmt); put(esg, r_, 3, pv, PCT if lab.startswith("Permanent") else fmt); put(esg, r_, 4, s_, font=F_NOTE)

# ====================================================================== v4: timeline nuance — events, shocks, survivorship, REITs, delay
EV = _json.loads((V2 / "events.json").read_text())
CO3 = ["DLF", "GPL", "PML", "REALTY"]
es_ = sheet("Event_Study", "Event study: did announcements and shocks move the stocks — and did the effect last?",
            "Market model vs Nifty 50, estimation window [−250,−30] trading days (MacKinlay 1997). CAR = cumulative abnormal return; t = CAR ÷ (σ_resid·√days). "
            "BHAR = buy-and-hold return minus Nifty. Computed by scripts/events.py from daily prices since 2007.",
            [44, 11, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9])
put(es_, 4, 1, "A. Macro, regulatory and REIT shocks — 3-day CAR [−1,+1] and 1-year BHAR", font=F_B)
hdr(es_, 5, ["Event", "Day 0", "DLF CAR", "t", "DLF 1y", "Godrej CAR", "t", "Godrej 1y", "Phoenix CAR", "t", "Phoenix 1y", "Realty CAR", "t", "Realty 1y"])
for i, r in enumerate(EV["macro"]):
    rr = 6 + i
    put(es_, rr, 1, r["event"] + f"  [{r['kind']}]"); put(es_, rr, 2, r["date"])
    for j, s in enumerate(CO3):
        d = r.get(s) or {}
        for k, (key, fmt) in enumerate([("ann", PCT), ("ann_t", NUM2), ("bhar250", PCT)]):
            v = d.get(key)
            if v is not None:
                put(es_, rr, 3 + j * 3 + k, v, fmt, F_B if key == "ann_t" and abs(v) >= 1.96 else F_N)
m1 = 6 + len(EV["macro"]) + 1
note(es_, m1, "Reading: shocks hit hard (demonetisation −15% DLF; COVID −16% DLF; IL&FS −9% Godrej) but 1-year BHARs are mostly positive → temporary, not permanent, repricing.")
note(es_, m1 + 1, "REIT listings barely moved the developers (|CAR| ≤ 4%, insignificant): the market already knew rental assets could be monetised. Rate decisions: small and often 'sell the news'.")
c0 = m1 + 3
put(es_, c0, 1, "B. Company announcements — run-up [−20,−2], announcement [−1,+1], drift [+2,+60]", font=F_B)
hdr(es_, c0 + 1, ["Event", "Day 0", "Company", "Type", "Run-up", "CAR [−1,+1]", "t", "Drift", "BHAR 1y"])
for i, r in enumerate(EV["company"]):
    rr = c0 + 2 + i
    put(es_, rr, 1, r["event"]); put(es_, rr, 2, r["date"]); put(es_, rr, 3, {"DLF": "DLF", "GPL": "Godrej", "PML": "Phoenix"}[r["co"]]); put(es_, rr, 4, r["kind"])
    for k, (key, fmt) in enumerate([("run", PCT), ("ann", PCT), ("ann_t", NUM2), ("drift", PCT), ("bhar250", PCT)]):
        if r.get(key) is not None:
            put(es_, rr, 5 + k, r[key], fmt, F_B if key == "ann_t" and abs(r[key]) >= 1.96 else F_N)
k0 = c0 + 2 + len(EV["company"]) + 1
hdr(es_, k0, ["Average by type", "n", "", "", "Run-up", "CAR [−1,+1]", "t (cross-section)", "Drift"])
for i, (k, v) in enumerate(EV["by_kind"].items()):
    rr = k0 + 1 + i
    put(es_, rr, 1, k, font=F_B); put(es_, rr, 2, v["n"], NUM)
    put(es_, rr, 5, v["run"], PCT); put(es_, rr, 6, v["ann"], PCT, F_B); put(es_, rr, 7, v["t_cs"], NUM2); put(es_, rr, 8, v["drift"], PCT)
e0 = k0 + 6
put(es_, e0, 1, "C. Results days: does the profit surprise explain the price move?", font=F_B)
hdr(es_, e0 + 1, ["Company", "Results days", "First", "Last", "Slope (CAR per 100% surprise)", "R²", "Mean |CAR|", "Sign hit rate"])
for i, (k, v) in enumerate(EV["earnings"].items()):
    rr = e0 + 2 + i
    put(es_, rr, 1, {"DLF": "DLF", "GPL": "Godrej", "PML": "Phoenix"}[k]); put(es_, rr, 2, v["n"], NUM); put(es_, rr, 3, v["first"]); put(es_, rr, 4, v["last"])
    put(es_, rr, 5, v["slope"], PCT); put(es_, rr, 6, v["r2"], NUM2, F_B); put(es_, rr, 7, v["mean_abs_car"], PCT); put(es_, rr, 8, v["hit"], PCT)
note(es_, e0 + 6, "EPS surprise (vs consensus) explains 0–15% of results-day moves and predicts direction barely better than a coin. Profit under completion accounting is old news;")
note(es_, e0 + 7, "the market trades on bookings, launches and collections. That is direct evidence for our choice to forecast from bookings and advances rather than recognised revenue.")
note(es_, e0 + 9, "Caveats: n is small per event type, events can overlap other news (e.g. Phoenix's Aug-2020 window), and dates are announcement dates from company filings/press (see references).")

sv = sheet("Survivorship", "Survivorship bias: the developers that are no longer here",
           "Equal-weighted daily-rebalanced indices from Jan-2008. Survivors: DLF, Phoenix, Sobha, Brigade, Puravankara, Kolte-Patil, Mahindra Lifespace, Anant Raj, Sunteck. "
           "Failed/stressed: Unitech, HDIL, Parsvnath, Ansal API, Omaxe, Peninsula Land.", [48, 16, 16, 16, 40])
S_ = EV["survivorship"]
hdr(sv, 4, ["Measure", "Survivors", "Failed / stressed", "All", "Reading"])
put(sv, 5, 1, "Total return since Jan-2008 (EW)"); [put(sv, 5, 2 + j, S_["total"][k], PCT) for j, k in enumerate(["survivors", "failed", "all"])]
put(sv, 5, 5, "A 'sector index' built from today's listed names overstates history", font=F_NOTE)
put(sv, 6, 1, "Annualised"); [put(sv, 6, 2 + j, S_["cagr"][k], PCT, F_B) for j, k in enumerate(["survivors", "failed", "all"])]
put(sv, 7, 1, "Median monthly beta 2010–19 (survivors incl. Godrej/Oberoi/Prestige vs all)"); put(sv, 7, 2, S_["median_beta_survivors"], NUM2); put(sv, 7, 4, S_["median_beta_all"], NUM2)
put(sv, 7, 5, "Dropping the dead firms lowers the industry beta — our lens-A beta is a floor", font=F_NOTE)
hdr(sv, 9, ["Failed / stressed developer", "Fall from 2008-26 peak", "Beta 2010–19", "", "What happened"])
WHAT = {"UNITECH": "Promoters jailed (2017); government took over the board (2020); thousands of stalled homes",
        "HDIL": "PMC Bank fraud (2019); insolvency", "PARSVNATH": "Stalled NCR projects; lender actions",
        "ANSALAPI": "Insolvency proceedings; stalled projects", "OMAXE": "Delays and losses; survives but −78%", "PENINLAND": "Mumbai stress; debt restructuring"}
for i, (k, v) in enumerate(S_["drawdown_failed"].items()):
    rr = 10 + i
    put(sv, rr, 1, k.title()); put(sv, rr, 2, v, PCT, F_B); put(sv, rr, 3, S_["beta_2010_19"].get(k), NUM2); put(sv, rr, 5, WHAT.get(k, ""), font=F_NOTE)
f0 = 18
put(sv, f0, 1, "Flight to quality, Nov-2016 → Feb-2020 (demonetisation, RERA, GST, IL&FS)", font=F_B)
hdr(sv, f0 + 1, ["Basket", "Return", "", "", "Reading"])
for i, (k, lab) in enumerate([("quality", "Quality developers (DLF, Godrej, Phoenix, Oberoi, Prestige, Brigade, Sobha)"), ("stressed", "Failed / stressed basket"), ("nifty", "Nifty 50")]):
    put(sv, f0 + 2 + i, 1, lab); put(sv, f0 + 2 + i, 2, S_["flight_to_quality"][k], PCT, F_B)
put(sv, f0 + 2, 5, "RERA + escrow + credit stress shifted buyers and lenders to brands that deliver on time", font=F_NOTE)
note(sv, f0 + 6, "Delivery is the real risk in this sector: the failures were not cyclical dips but permanent losses (−78% to −99.9%), driven by stalled projects and diverted customer money.")
note(sv, f0 + 7, "RERA (2017) was designed to stop exactly this; it converted delivery track record into a competitive moat — the source of our three firms' market-share gains.")
hdr(sv, f0 + 9, ["Drawdowns (daily adjusted close)", "Peak", "Trough", "Depth", "Recovered (years from peak)"])
rr = f0 + 10
for s, lst in EV["drawdowns"].items():
    for d in lst:
        put(sv, rr, 1, {"DLF": "DLF", "GPL": "Godrej", "PML": "Phoenix", "REALTY": "Nifty Realty"}[s]); put(sv, rr, 2, d["peak"]); put(sv, rr, 3, d["trough"])
        put(sv, rr, 4, d["depth"], PCT, F_B); put(sv, rr, 5, f"{d['recovered']} ({d['years_to_recover']:.1f} yrs)")
        rr += 1

rs_ = sheet("REIT_Spread", "REITs as instruments: yields, the spread to the G-Sec, and the cap-rate channel",
            "Trailing-12-month distributions ÷ unit price, month-end (Embassy, Mindspace, Brookfield, Nexus). G-Sec: OECD 10-yr. Regression: monthly stock return on Nifty return and Δ median REIT yield.",
            [40, 14, 14, 14, 14, 14, 14])
R_ = EV["reit"]
hdr(rs_, 4, ["Metric", "Value", "", "Reading"])
rows_ = [("Median REIT distribution yield (latest)", R_["latest_median"], "Office REITs 5–7%; mall REIT (Nexus) ~6%"),
         ("10-yr G-Sec (latest)", R_["latest_gsec"], "After the Oct-2026 hike"),
         ("Spread: REIT yield − G-Sec (latest)", R_["latest_spread"], "Negative: investors accept less than the G-Sec because distributions grow"),
         ("Average spread since 2020", R_["mean_spread"], ""), ("Range of the spread", R_["min_spread"], f"to {R_['max_spread']:.1%}")]
for i, (lab, v, s_) in enumerate(rows_):
    put(rs_, 5 + i, 1, lab); put(rs_, 5 + i, 2, v, PCT, F_B); put(rs_, 5 + i, 4, s_, font=F_NOTE)
put(rs_, 11, 1, "Latest yield by REIT", font=F_B)
for i, (k, v) in enumerate(R_["latest"].items()):
    put(rs_, 12 + i, 1, k.title()); put(rs_, 12 + i, 2, v, PCT)
hdr(rs_, 17, ["Cap-rate channel regression", "Months", "β market", "β ΔREIT yield", "t", "Return per +25bp"])
for i, (k, v) in enumerate(EV["reit_reg"].items()):
    rr = 18 + i
    put(rs_, rr, 1, {"DLF": "DLF", "GPL": "Godrej", "PML": "Phoenix", "REALTY": "Nifty Realty"}[k]); put(rs_, rr, 2, v["n"], NUM)
    put(rs_, rr, 3, v["b_mkt"], NUM2); put(rs_, rr, 4, v["b_dY"], NUM2); put(rs_, rr, 5, v["t_dY"], NUM2, F_B); put(rs_, rr, 6, v["per_25bp"], PCT)
note(rs_, 23, "Finding: REIT yield changes do not explain developer returns (|t| < 1). The listed market prices DLF and Phoenix as growth stocks, not as yield vehicles —")
note(rs_, 24, "consistent with Phoenix's ~3% EBITDA yield versus ~6% for the mall REIT. A REIT is the 'no-growth' exit value; the gap is the growth option the market pays for.")
note(rs_, 25, "Instrument notes: REIT units distribute ≥90% of net distributable cash; distributions mix dividend, interest and capital repayment (taxed differently); SM-REITs (2024) open fractional assets.")
put(rs_, 27, 1, "Hold vs sell-to-REIT option for Phoenix (₹ cr)", font=F_B)
put(rs_, 28, 1, "Retail EBITDA FY26 (Operating_KPIs)"); put(rs_, 28, 2, f"=Operating_KPIs!D{KR['Retail EBITDA FY26']}", NUM); put(rs_, 28, 4, "Company-reported retail EBITDA", font=F_NOTE)
put(rs_, 29, 1, "Value at Nexus yield (EBITDA ÷ mall-REIT yield)"); put(rs_, 29, 2, f"=B28/B{12+list(R_['latest']).index('NEXUS')}" if "NEXUS" in R_["latest"] else "=B28/B5", NUM, F_B)
put(rs_, 30, 1, "Value at our CAPM cost of equity less terminal growth (cash proxy = 75% of EBITDA)"); put(rs_, 30, 2, f"=B28*0.75/({W['PML']['Ke']}-gT)", NUM)
put(rs_, 31, 1, "Sell-to-REIT premium over hold (if REIT pays more than intrinsic)"); put(rs_, 31, 2, "=B29/B30-1", PCT, F_B)
note(rs_, 32, "Pre-tax EBITDA vs after-tax-and-capex proxy (×0.75) — indicative. A REIT bid above intrinsic value is a real monetisation option (GIC/CPPIB deals show it is exercised).")

isu = sheet("Issuance_Timing", "Do developers sell shares near the top? Equity issues and what followed",
            "Return from issue/launch date; vs Nifty and vs Nifty Realty. Percentile = where the price sat in its own prior 3-year range on the issue date.",
            [30, 12, 12, 12, 12, 12, 12, 12, 12])
hdr(isu, 4, ["Issue", "Date", "3-yr price percentile", "1-yr return", "1-yr vs Nifty", "1-yr vs Realty", "3-yr return", "3-yr vs Nifty", "3-yr vs Realty"])
for i, r in enumerate(EV["issues"]):
    rr = 5 + i
    put(isu, rr, 1, r["event"]); put(isu, rr, 2, r["date"]); put(isu, rr, 3, r["pctile_3y"], PCT, F_B)
    for j, k in enumerate(["r1y", "r1y_vs_nifty", "r1y_vs_realty", "r3y", "r3y_vs_nifty", "r3y_vs_realty"]):
        if r.get(k) is not None:
            put(isu, rr, 4 + j, r[k], PCT)
eqk = EV["by_kind"].get("equity issue", {})
put(isu, 11, 1, "Event-study average for equity issues (Event_Study)", font=F_B)
put(isu, 12, 1, "Run-up before"); put(isu, 12, 2, eqk.get("run"), PCT, F_B)
put(isu, 13, 1, "Announcement CAR"); put(isu, 13, 2, eqk.get("ann"), PCT)
put(isu, 14, 1, "Drift over next 60 days"); put(isu, 14, 2, eqk.get("drift"), PCT, F_B)
note(isu, 16, "Pattern (Loughran–Ritter 'market timing'): issues follow run-ups (+7%) and come when the price sits high in its range (Godrej: 85–100th percentile), and are followed by negative drift.")
note(isu, 17, "Management's own actions are a signal: when insiders sell new equity, they judge the price rich. Godrej's Nov-2024 QIP at ~₹2,727 preceded a ~30% fall relative to Nifty.")

dly = sheet("Delay_Cost", "What is a delay worth? The value of one and two years' slip in deliveries",
            "Live formulas off the DCF and management-case sheets. A slip moves every cash flow back; at discount rate r the value lost is V × (1 − 1/(1+r)^n).",
            [52, 16, 16, 16, 40])
hdr(dly, 4, ["", "DLF", "Godrej", "Phoenix", "Reading"])
DL = [("Value of operating assets (lens A DCF)", lambda c: f"=DCF_{c}!B39", NUM),
      ("Discount rate, year 1 (WACC)", lambda c: f"=DCF_{c}!C29", PCT),
      ("Shares (crore)", lambda c: f"=DCF_{c}!B48", NUM2),
      ("Owners' share (1 − minority share)", lambda c: f"=1-DCF_{c}!B45", PCT),
      ("Value lost if everything slips 1 year (₹ cr)", None, NUM),
      ("… per share (₹)", None, NUM2),
      ("… as % of market price", None, PCT),
      ("Value lost if everything slips 2 years, per share (₹)", None, NUM2)]
for i, (lab, f, fmt) in enumerate(DL):
    put(dly, 5 + i, 1, lab, font=F_B if lab.startswith(("Value lost", "…")) else F_N)
    for j, c in enumerate(["DLF", "GPL", "PML"]):
        col = L(2 + j)
        if f:
            put(dly, 5 + i, 2 + j, f(c), fmt)
        elif i == 4:
            put(dly, 9, 2 + j, f"={col}5*(1-1/(1+{col}6))*{col}8", NUM, F_B)
        elif i == 5:
            put(dly, 10, 2 + j, f"={col}9/{col}7", NUM2, F_B, FILL_KEY)
        elif i == 6:
            put(dly, 11, 2 + j, f"={col}10/DCF_{c}!B50", PCT)
        elif i == 7:
            put(dly, 12, 2 + j, f"={col}5*(1-1/(1+{col}6)^2)*{col}8/{col}7", NUM2)
put(dly, 5, 5, "Phoenix: a delay affects only new malls; whole-firm figure is an upper bound", font=F_NOTE)
put(dly, 14, 1, "DLF management case: a 1-year slip in development cash flow", font=F_B)
put(dly, 15, 1, "Development business value (Official_Disclosures)"); put(dly, 15, 2, f"={MGMT['dev']}", NUM)
put(dly, 16, 1, "Cost of equity"); put(dly, 16, 2, f"={W['DLF']['Ke']}", PCT)
put(dly, 17, 1, "Value lost per year of delay (₹ cr)"); put(dly, 17, 2, "=B15*(1-1/(1+B16))", NUM, F_B)
put(dly, 18, 1, "… per share (₹)"); put(dly, 18, 2, f"=B17/{D('DLF','Shares',2026)}", NUM2, F_B, FILL_KEY)
put(dly, 19, 1, "Of which: RERA escrow (₹11,200 cr) released a year later (₹ cr)"); put(dly, 19, 2, "=11200*(1-1/(1+B16))", NUM)
put(dly, 20, 1, "H1 FY27 bookings vs pro-rata guidance (the live delay signal)"); put(dly, 20, 2, 4457 / 10000, PCT)
note(dly, 22, "Reading: one year of slippage costs DLF ~13% of development value — the same order as the gap between our DCF lenses. Delivery risk is a first-order valuation input.")
note(dly, 23, "Under completion accounting a delay also defers recognised revenue, so reported P/E rises even if value is unchanged — another reason to value cash, not earnings.")
note(dly, 24, "Empirically (Survivorship sheet), chronic delay was fatal: Unitech, HDIL, Parsvnath and Ansal lost 99%+. On-time delivery is what separates our three firms from them.")
for n_ in ["Event_Study", "Survivorship", "REIT_Spread", "Issuance_Timing", "Delay_Cost"]:
    wb[n_].sheet_properties.tabColor = "5B4A8C"
_cm4 = [("8–9", "Event study (market model, CAR, BHAR); semi-strong market efficiency", "MacKinlay 1997", "Event_Study; Report §10"),
        ("6", "Survivorship bias in industry betas and returns", "Brown, Goetzmann & Ross 1995", "Survivorship"),
        ("6–7", "REITs as instruments: payout rule, yield spread, monetisation option", "Extension", "REIT_Spread, CapRates"),
        ("9", "Equity-issue market timing (new-issues puzzle)", "Loughran & Ritter 1995", "Issuance_Timing"),
        ("7", "Value of delay: V·r/(1+r) per year; escrow release timing", "Extension", "Delay_Cost"),
        ("9", "Liquidity: Amihud illiquidity, traded value", "Amihud 2002", "Report §11")]
r_ = cc.max_row + 1
for i, row in enumerate(_cm4):
    for j, v in enumerate(row):
        put(cc, r_ + i, 1 + j, v, font=F_NOTE if j == 2 else F_N)

# ====================================================================== v5: industry dataset, company vs industry, literature learnings
import importlib.util as _ilu
_sp = _ilu.spec_from_file_location("industry_inputs", ROOT / "scripts/industry_inputs.py"); IND = _ilu.module_from_spec(_sp); _sp.loader.exec_module(IND)
idd = sheet("Industry_Data", "The Indian real-estate industry: residential cycle, stalled homes, prices, offices, malls, credit",
            IND.RESI_SRC, [26, 13, 13, 13, 13, 13, 40])
hdr(idd, 4, ["Year (top-7 cities)", "Sales (lakh units)", "Launches (lakh)", "Unsold stock (lakh)", "Overhang (months)", "Sales ÷ launches", "Reading"])
yrs = sorted(IND.RESI)
for i, y in enumerate(yrs):
    r_ = 5 + i
    s, l_, u, o = IND.RESI[y]
    put(idd, r_, 1, y)
    for j, v in enumerate([s, l_, u, o]):
        if v is not None:
            put(idd, r_, 2 + j, v, NUM2 if j < 3 else NUM, F_IN, FILL_IN)
    if l_ is not None:
        put(idd, r_, 6, f"=B{r_}/C{r_}", NUM2)
RE_ = 5 + len(yrs) - 1
put(idd, 5, 7, "2014 peak, then a five-year bust (launches −73% to 2017)", font=F_NOTE)
put(idd, 5 + yrs.index(2020), 7, "COVID trough", font=F_NOTE)
put(idd, 5 + yrs.index(2023), 7, "Record sales; 2025 −14% (value +6%: premiumisation)", font=F_NOTE)
r0 = RE_ + 2
put(idd, r0, 1, "Sales CAGR 2014→2025 (units)", font=F_B); put(idd, r0, 2, f"=(B{RE_}/B{5+yrs.index(2014)})^(1/11)-1", PCT, F_B)
put(idd, r0 + 1, 1, "Peak-to-trough fall in sales (2014→2020)"); put(idd, r0 + 1, 2, f"=B{5+yrs.index(2020)}/B{5+yrs.index(2014)}-1", PCT)
put(idd, r0 + 2, 1, "Sales value 2025 (₹ lakh cr)"); put(idd, r0 + 2, 2, IND.RESI_VALUE[2025], NUM2, F_IN, FILL_IN); put(idd, r0 + 2, 3, "2024:"); put(idd, r0 + 2, 4, IND.RESI_VALUE[2024], NUM2, F_IN, FILL_IN)
c0 = r0 + 4
put(idd, c0, 1, "City inventory overhang (months)", font=F_B); hdr(idd, c0 + 1, ["City", "2020", "2023–24", "2025"])
for i, (k, v) in enumerate(IND.CITY_OVERHANG.items()):
    put(idd, c0 + 2 + i, 1, k); [put(idd, c0 + 2 + i, 2 + j, x, NUM) for j, x in enumerate(v) if x is not None]
note(idd, c0 + 4, "NCR — DLF's home market — went from 88 months of unsold stock in 2020 to 17: the post-COVID cycle cleared the overhang that the 2014–19 bust left behind.")
s0 = c0 + 6
put(idd, s0, 1, "Delivery risk across the industry", font=F_B)
DR = [("Homes stuck or delayed, top-7 cities (lakh)", IND.STALLED["homes_stuck_or_delayed_lakh"], NUM2), ("… value (₹ lakh cr)", IND.STALLED["value_lakh_cr"], NUM2),
      ("… of which fully stalled (lakh)", IND.STALLED["fully_stalled_lakh"], NUM2), ("NCR share of stuck/delayed stock", IND.STALLED["ncr_share"], PCT),
      ("MMR share", IND.STALLED["mmr_share"], PCT), ("Stuck homes ÷ one year of 2025 sales", None, PCT),
      ("MahaRERA: registered projects", IND.MAHARERA["registered"], NUM), ("… completed share", IND.MAHARERA["completed_share"], PCT),
      ("… lapsed projects (Mar-2022)", IND.MAHARERA["lapsed_mar22"], NUM), ("… projects in insolvency (NCLT)", IND.MAHARERA["nclt_projects"], NUM)]
for i, (lab, v, fmt) in enumerate(DR):
    r_ = s0 + 1 + i
    put(idd, r_, 1, lab)
    if v is not None:
        put(idd, r_, 2, v, fmt, F_IN, FILL_IN)
put(idd, s0 + 6, 2, f"=B{s0+1}/B{RE_}", PCT, F_B)
put(idd, s0 + 1, 7, IND.STALLED["src"], font=F_NOTE); put(idd, s0 + 7, 7, IND.MAHARERA["src"], font=F_NOTE)
h0 = s0 + 12
put(idd, h0, 1, "RBI all-India house price index, y/y", font=F_B)
for i, (k, v) in enumerate(IND.HPI.items()):
    put(idd, h0 + 1 + i, 1, k); put(idd, h0 + 1 + i, 2, v, PCT, F_IN, FILL_IN)
put(idd, h0 + 1, 7, IND.HPI_SRC, font=F_NOTE)
note(idd, h0 + 6, "Prices rose only 2–4% a year in FY26 while sales value rose 6% and DLF sold at ₹1 lakh/sq ft — the market is premiumising, not inflating broadly.")
o0 = h0 + 8
put(idd, o0, 1, "Offices 2025 (record year)", font=F_B)
for i, (k, v) in enumerate(IND.OFFICE_2025.items()):
    put(idd, o0 + 1 + i, 1, k); put(idd, o0 + 1 + i, 2, v, NUM2, F_IN, FILL_IN)
m0 = o0 + 8
put(idd, m0, 1, "Malls", font=F_B)
MM = [("New Grade-A mall supply 2025 (msf)", IND.MALLS["new_supply_2025_msf"], NUM2), ("Mall leasing 2025 (msf, record)", IND.MALLS["leasing_2025_msf"], NUM2),
      ("Grade-A mall vacancy, H1 2026", IND.MALLS["gradeA_vacancy_h1_2026"], PCT), ("Share of malls that are 'ghost' (>40% vacant)", IND.MALLS["ghost_malls_share"], PCT)]
for i, (lab, v, fmt) in enumerate(MM):
    put(idd, m0 + 1 + i, 1, lab); put(idd, m0 + 1 + i, 2, v, fmt, F_IN, FILL_IN)
put(idd, m0 + 1, 7, IND.MALLS["src"] + "; Grade-A rents growing " + IND.MALLS["gradeA_rent_cagr"] + " a year", font=F_NOTE)
n0 = m0 + 6
put(idd, n0, 1, "Developer credit", font=F_B)
put(idd, n0 + 1, 1, "NBFC share of developer funding (FY18)"); put(idd, n0 + 1, 2, IND.NBFC["nbfc_share_dev_funding_fy18"], PCT, F_IN, FILL_IN)
put(idd, n0 + 2, 1, "NBFC developer loans (₹ trn, FY18)"); put(idd, n0 + 2, 2, IND.NBFC["nbfc_dev_loans_trn"], NUM2, F_IN, FILL_IN)
put(idd, n0 + 3, 1, "Developer loans as share of NBFC books"); put(idd, n0 + 3, 2, IND.NBFC["dev_loans_share_nbfc_books"], PCT, F_IN, FILL_IN)
put(idd, n0 + 1, 7, IND.NBFC["src"], font=F_NOTE)
IDROW = {"sales25": f"Industry_Data!$B${RE_}", "val25": f"Industry_Data!$B${r0+2}", "val24": f"Industry_Data!$D${r0+2}", "stuck": f"Industry_Data!$B${s0+1}"}

ivc = sheet("Industry_vs_Company", "How each company compares with the industry",
            "Company bookings are fiscal years (Apr–Mar); industry figures are calendar years, so FY26 is compared with CY2025 (nine months overlap). Shares are indicative.",
            [52, 16, 16, 16, 44])
hdr(ivc, 4, ["Metric", "DLF", "Godrej", "Phoenix / industry", "Reading"])
put(ivc, 5, 1, "Bookings FY26 (₹ cr)"); put(ivc, 5, 2, IND.BOOKINGS["DLF"]["FY26"], NUM, F_IN, FILL_IN); put(ivc, 5, 3, IND.BOOKINGS["GPL"]["FY26"], NUM, F_IN, FILL_IN)
put(ivc, 6, 1, "Bookings FY25 (₹ cr)"); put(ivc, 6, 2, IND.BOOKINGS["DLF"]["FY25"], NUM, F_IN, FILL_IN); put(ivc, 6, 3, IND.BOOKINGS["GPL"]["FY25"], NUM, F_IN, FILL_IN)
put(ivc, 7, 1, "Bookings growth FY26"); put(ivc, 7, 2, "=B5/B6-1", PCT, F_B); put(ivc, 7, 3, "=C5/C6-1", PCT, F_B)
put(ivc, 7, 4, f"={IDROW['val25']}/{IDROW['val24']}-1", PCT, F_B); put(ivc, 7, 5, "Industry sales value +6% (volume −14%): Godrej grew 2.7x faster than the market", font=F_NOTE)
put(ivc, 8, 1, "Share of top-7-city sales value, FY26 vs CY2025"); put(ivc, 8, 2, f"=B5/({IDROW['val25']}*1e5)", PCT, F_B); put(ivc, 8, 3, f"=C5/({IDROW['val25']}*1e5)", PCT, F_B)
put(ivc, 9, 1, "Share, FY25 vs CY2024"); put(ivc, 9, 2, f"=B6/({IDROW['val24']}*1e5)", PCT); put(ivc, 9, 3, f"=C6/({IDROW['val24']}*1e5)", PCT)
put(ivc, 9, 5, "Godrej gaining share, DLF holding (launch-timed): consolidation toward branded developers", font=F_NOTE)
put(ivc, 11, 1, "Inventory at cost ÷ annual bookings (years)"); put(ivc, 11, 2, f"={D('DLF','Inventory',2026)}/B5", NUM2); put(ivc, 11, 3, f"={D('GPL','Inventory',2026)}/C5", NUM2)
put(ivc, 11, 4, 18 / 12, NUM2); put(ivc, 11, 5, "Industry: unsold stock ≈ 18 months of sales (at value). Ours at cost incl. land — a rough comparison", font=F_NOTE)
put(ivc, 12, 1, "Customer advances ÷ annual bookings (years of pre-sold work)"); put(ivc, 12, 2, f"={R('DLF','Adv',2026)}/B5", NUM2); put(ivc, 12, 3, f"={R('GPL','Adv',2026)}/C5", NUM2)
put(ivc, 14, 1, "Godrej deliveries (msf) FY24 / FY25 / FY26 / FY27 guidance", font=F_B)
for j, k in enumerate(["FY24", "FY25", "FY26", "FY27G"]):
    put(ivc, 15, 2 + j if j < 3 else 4, None)
put(ivc, 15, 1, "Delivered (msf)"); put(ivc, 15, 2, IND.GPL_DELIVERIES["FY24"][0], NUM2, F_IN, FILL_IN); put(ivc, 15, 3, IND.GPL_DELIVERIES["FY25"][0], NUM2, F_IN, FILL_IN); put(ivc, 15, 4, IND.GPL_DELIVERIES["FY26"][0], NUM2, F_IN, FILL_IN)
put(ivc, 16, 1, "Delivered ÷ delivery guidance"); put(ivc, 16, 3, IND.GPL_DELIVERIES["FY25"][1], PCT, F_IN, FILL_IN); put(ivc, 16, 4, IND.GPL_DELIVERIES["FY26"][1], PCT, F_IN, FILL_IN)
put(ivc, 15, 5, "Cols B–D = FY24, FY25, FY26; FY27 guidance 13.5 msf. Beat guidance by 21–23% two years running", font=F_NOTE)
put(ivc, 17, 1, "Industry: stuck/delayed homes ÷ one year of sales"); put(ivc, 17, 4, f"={IDROW['stuck']}/{IDROW['sales25']}", PCT, F_B)
put(ivc, 17, 5, "≈1.6 years of national sales are stuck — the delivery risk our three firms are paid to avoid", font=F_NOTE)
put(ivc, 19, 1, "Phoenix mall openings: guided vs actual", font=F_B)
hdr(ivc, 20, ["Mall", "Guided", "Actual", "Slip (months)", ""])
for i, (mll, g, a, sl) in enumerate(IND.PHOENIX_OPENINGS):
    put(ivc, 21 + i, 1, mll); put(ivc, 21 + i, 2, g); put(ivc, 21 + i, 3, a)
    if sl is not None:
        put(ivc, 21 + i, 4, sl, NUM)
note(ivc, 26, "Phoenix's three 2023 malls opened within 0–4 months of guidance; DLF received OCs for three office towers in FY26 with the fourth due Q2 FY27.")
note(ivc, 27, "Against an industry where ~6.3 lakh homes are stuck and only 26% of MahaRERA-registered projects are complete, small slips are the mark of reliable developers.")
put(ivc, 29, 1, "Phoenix retail vs the mall industry", font=F_B)
put(ivc, 30, 1, "Phoenix retail rental growth guidance FY27–28"); put(ivc, 30, 4, 0.145, PCT, F_IN, FILL_IN)
put(ivc, 31, 1, "Industry Grade-A mall rent growth (CAGR, midpoint)"); put(ivc, 31, 4, 0.065, PCT, F_IN, FILL_IN)
put(ivc, 32, 1, "Phoenix consumption growth FY26"); put(ivc, 32, 4, 0.21, PCT, F_IN, FILL_IN)
note(ivc, 33, "Phoenix grows rent at twice the Grade-A market rate (new malls + renewals at ~20% uplift) — while ~20% of India's malls are 'ghost' assets: dominance in a bifurcated market.")

lit = sheet("Literature", "What Indian real-estate research tells us — and what we borrowed", IND.LIT_SRC, [30, 9, 26, 52, 56, 16])
hdr(lit, 4, ["Authors", "Year", "Venue", "Finding", "What we borrow", "Where used"])
for i, row in enumerate(IND.LIT):
    for j, v in enumerate(row):
        put(lit, 5 + i, 1 + j, v, font=F_NOTE if j in (3, 4) else F_N)
l0 = 5 + len(IND.LIT) + 2
put(lit, l0, 1, "Borrowed learning, quantified: value of pre-sale financing (Dutta et al.)", font=F_B)
hdr(lit, l0 + 1, ["", "DLF", "Godrej", "", "Reading"])
put(lit, l0 + 2, 1, "Customer advances FY26 (₹ cr)"); put(lit, l0 + 2, 2, f"={R('DLF','Adv',2026)}", NUM); put(lit, l0 + 2, 3, f"={R('GPL','Adv',2026)}", NUM)
put(lit, l0 + 3, 1, "Spread: construction loan − home loan rate"); put(lit, l0 + 3, 2, 0.08, PCT, F_IN, FILL_IN); put(lit, l0 + 3, 3, "=B" + str(l0 + 3), PCT)
put(lit, l0 + 3, 5, "16–18% developer construction finance vs 8–10% buyer mortgages (Dutta et al.)", font=F_NOTE)
put(lit, l0 + 4, 1, "Annual after-tax financing saving (₹ cr)"); put(lit, l0 + 4, 2, f"=B{l0+2}*B{l0+3}*(1-Tax)", NUM, F_B); put(lit, l0 + 4, 3, f"=C{l0+2}*C{l0+3}*(1-Tax)", NUM, F_B)
put(lit, l0 + 5, 1, "… as % of FY26 PAT"); put(lit, l0 + 5, 2, f"=B{l0+4}/{D('DLF','NetIncome',2026)}", PCT); put(lit, l0 + 5, 3, f"=C{l0+4}/{D('GPL','NetIncome',2026)}", PCT)
put(lit, l0 + 6, 1, "… per share (₹, per year)"); put(lit, l0 + 6, 2, f"=B{l0+4}/{D('DLF','Shares',2026)}", NUM2, F_B); put(lit, l0 + 6, 3, f"=C{l0+4}/{D('GPL','Shares',2026)}", NUM2, F_B)
note(lit, l0 + 7, "The customer is the developer's cheapest lender. RERA's escrow keeps that money tied to the project, so only brands buyers trust can raise it — a moat with a rupee value.")
put(lit, l0 + 9, 1, "Borrowed learning, quantified: litigation-driven delay (Gandhi et al.)", font=F_B)
put(lit, l0 + 10, 1, "Extra completion time from litigation (share of cycle)"); put(lit, l0 + 10, 2, 0.20, PCT, F_IN, FILL_IN)
put(lit, l0 + 11, 1, "Typical development cycle (years)"); put(lit, l0 + 11, 2, 4, NUM, F_IN, FILL_IN)
put(lit, l0 + 12, 1, "Implied slip (years)"); put(lit, l0 + 12, 2, f"=B{l0+10}*B{l0+11}", NUM2)
put(lit, l0 + 13, 1, "Godrej value at risk per share (Delay_Cost 1-yr cost × slip)"); put(lit, l0 + 13, 2, f"=Delay_Cost!C10*B{l0+12}", NUM2, F_B)
LITQ = {"adv_dlf": f"Literature!$B${l0+2}", "adv_gpl": f"Literature!$C${l0+2}", "save_dlf": f"Literature!$B${l0+4}", "save_gpl": f"Literature!$C${l0+4}",
        "pat_dlf": f"Literature!$B${l0+5}", "pat_gpl": f"Literature!$C${l0+5}", "lit_gpl": f"Literature!$B${l0+13}"}
for n_ in ["Industry_Data", "Industry_vs_Company", "Literature"]:
    wb[n_].sheet_properties.tabColor = "3E6B4A"
_cm5 = [("1–2", "Industry dataset: residential cycle, stalled homes, HPI, offices, malls, developer credit", "ANAROCK, RBI, consultants", "Industry_Data; Report §2"),
        ("2, 5", "Company vs industry: market share, growth, delivery vs guidance, inventory", "Extension", "Industry_vs_Company"),
        ("1–9", "Literature review (Indian real-estate research) and borrowed, quantified lessons", "Research papers", "Literature; Report §1")]
r_ = cc.max_row + 1
for i, row in enumerate(_cm5):
    for j, v in enumerate(row):
        put(cc, r_ + i, 1 + j, v, font=F_NOTE if j == 2 else F_N)
note(lit, lit.max_row + 2, "Caveat: our 'customer advances' line is derived (current liabilities − current debt − payables) and includes other operating liabilities, so the saving is an upper bound.")

# ====================================================================== Start_Here: guided path through the workbook
sh = sheet("Start_Here", "Start here: how to walk through this workbook in eight stops",
           "Read the sheets in this order. Each stop answers one question; the key output is the cell to point at. Blue cells are inputs, black are formulas.",
           [6, 26, 30, 62, 34])
hdr(sh, 4, ["Stop", "Sheet", "Question it answers", "What to look at", "Key output"])
STOPS = [
    ("1", "Inputs", "What did we assume?", "Risk-free rate (G-Sec less default spread), equity risk premium, tax rate, terminal growth. Every other sheet reads from here.", "Rf, ERP, tax, g"),
    ("2", "Data_DLF / Data_GPL / Data_PML", "What did the companies report?", "Four years of statements, tied to DLF's and Godrej's audited FY26 reports (Official_Disclosures).", "Revenue, PAT, equity"),
    ("3", "Recast", "What is the real operating profit?", "Core EBIT after removing treasury income, JV share and one-offs; net operating assets.", "Core EBIT, NOPAT, NOA"),
    ("4", "Ratios and DuPont", "How well do they perform?", "ROE broken into margin, turnover and leverage; RNOA vs borrowing cost; EVA.", "RNOA, EVA"),
    ("5", "WACC", "What return do investors need?", "Beta (base case and industry version), cost of equity, cost of debt from a synthetic rating, weights.", "WACC lens A / lens B"),
    ("6", "DCF_DLF / DCF_GPL / DCF_PML", "What is each company worth?", "Ten-year projection, terminal value, bridge to equity value per share; reverse DCF on the right.", "Value per share; implied g"),
    ("7", "RelVal and NAV_SOTP", "Do other methods agree?", "Peer multiples (median, IQR) and the brokers' NAV method rebuilt from disclosures.", "Peer-implied value; NAV/share"),
    ("8", "Summary", "So what is the answer?", "Every method against the price, with the ranking.", "Football field; ranking"),
]
for i, row in enumerate(STOPS):
    for j, v in enumerate(row):
        put(sh, 5 + i, 1 + j, v, font=F_B if j in (0, 1) else F_N)
put(sh, 14, 1, "Going further (optional)", font=F_B)
MORE = [("Event_Study, Survivorship, Delay_Cost", "How the shares reacted to shocks and news; what delay costs"),
        ("Industry_Data, Industry_vs_Company, Literature", "The industry in numbers; how each company compares; research we used"),
        ("MonteCarlo, Scenarios_Implied, ResidualIncome", "How uncertain the DCF is; other valuation routes"),
        ("Concept_Map", "Where each course concept is applied")]
for i, (a, b_) in enumerate(MORE):
    put(sh, 15 + i, 2, a, font=F_B); put(sh, 15 + i, 4, b_)
note(sh, 20, "Tip for the viva: change a blue input on Inputs (for example terminal growth) and watch value per share move on the DCF sheets and Summary.")
wb.move_sheet("Start_Here", offset=-(len(wb.sheetnames) - 1))
wb["Start_Here"].sheet_properties.tabColor = "C08A3E"
wb.active = 0

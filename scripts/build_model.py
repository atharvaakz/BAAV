"""Build the BAV valuation workbook (live Excel formulas) for DLF, Godrej Properties, Phoenix Mills.

Every analytical number is an Excel formula that traces back to the Data_* sheets or the Inputs sheet.
Run:  python scripts/build_model.py   -> models/excel/BAV_RealEstate_Model.xlsx
"""
import json, pathlib, sys
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.chart import LineChart, BarChart, ScatterChart, Reference, Series
from openpyxl.workbook.defined_name import DefinedName

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from bav.data import load, fy_end_prices, last_price, RAW  # noqa: E402

OUT = ROOT / "models" / "excel" / "BAV_RealEstate_Model.xlsx"
YEARS = [2023, 2024, 2025, 2026]
YC = {y: L(3 + i) for i, y in enumerate(YEARS)}          # FY23->C ... FY26->F
TARGETS = {"DLF": "DLF", "GPL": "GODREJPROP", "PML": "PHOENIXLTD"}
NAMES = {"DLF": "DLF Ltd", "GPL": "Godrej Properties", "PML": "Phoenix Mills",
         "OBEROI": "Oberoi Realty", "PRESTIGE": "Prestige Estates", "BRIGADE": "Brigade Enterprises",
         "SOBHA": "Sobha Ltd", "LODHA": "Lodha (Macrotech)", "MAHLIFE": "Mahindra Lifespace", "SUNTECK": "Sunteck Realty",
         "PURVA": "Puravankara", "ANANTRAJ": "Anant Raj", "SIGNATURE": "Signature Global"}
PEERS = {"OBEROI": "OBEROIRLTY", "PRESTIGE": "PRESTIGE", "BRIGADE": "BRIGADE", "SOBHA": "SOBHA", "LODHA": "LODHA",
         "MAHLIFE": "MAHLIFE", "SUNTECK": "SUNTECK", "PURVA": "PURVA", "ANANTRAJ": "ANANTRAJ", "SIGNATURE": "SIGNATURE"}
BETA_EXCL = {"SIGNATURE"}   # listed Sep-2023: <60 monthly returns
ALL = {**TARGETS, **PEERS}

# ---------- styles ----------
INK, MUTED, ACC = "1F2A30", "6B7780", "2F5D62"
F_TITLE = Font(name="Calibri", size=14, bold=True, color=INK)
F_H = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
F_B = Font(name="Calibri", size=10, bold=True, color=INK)
F_N = Font(name="Calibri", size=10, color=INK)
F_IN = Font(name="Calibri", size=10, color="1F4E9E")          # blue = hard input
F_NOTE = Font(name="Calibri", size=9, italic=True, color=MUTED)
FILL_H = PatternFill("solid", fgColor=ACC)
FILL_SUB = PatternFill("solid", fgColor="E6EEEE")
FILL_IN = PatternFill("solid", fgColor="FFF7E0")
FILL_KEY = PatternFill("solid", fgColor="DCEBDD")
THIN = Side(style="thin", color="C9D1D3")
BOX = Border(top=THIN, bottom=THIN, left=THIN, right=THIN)
PCT, NUM, NUM2, X = "0.0%", "#,##0", "#,##0.00", '0.00"x"'

wb = Workbook()
wb.remove(wb.active)


def sheet(name, title, module=None, widths=None):
    ws = wb.create_sheet(name)
    ws["A1"] = title
    ws["A1"].font = F_TITLE
    if module:
        ws["A2"] = module
        ws["A2"].font = F_NOTE
    ws.sheet_view.showGridLines = False
    for i, w in enumerate(widths or [34, 12, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13]):
        ws.column_dimensions[L(i + 1)].width = w
    return ws


def hdr(ws, r, labels, c0=1):
    for i, t in enumerate(labels):
        c = ws.cell(r, c0 + i, t)
        c.font, c.fill, c.alignment = F_H, FILL_H, Alignment(horizontal="center", vertical="center", wrap_text=True)


def sub(ws, r, text, ncol=7):
    for i in range(ncol):
        ws.cell(r, 1 + i).fill = FILL_SUB
    ws.cell(r, 1, text).font = F_B


def put(ws, r, c, v, fmt=None, font=F_N, fill=None):
    cell = ws.cell(r, c, v)
    cell.font = font
    if fmt:
        cell.number_format = fmt
    if fill:
        cell.fill = fill
    return cell


def note(ws, r, text, c=1):
    put(ws, r, c, text, font=F_NOTE)


# =====================================================================================
# 0. INDEX
# =====================================================================================
idx = sheet("Index", "Business Analysis & Valuation — Indian Real Estate: DLF | Godrej Properties | Phoenix Mills",
            "ECON F355 project model. Blue cells = hard inputs (sourced); black = formulas. Rs crore unless stated.",
            [6, 26, 70, 22])

# =====================================================================================
# 1. INPUTS
# =====================================================================================
macro = pd.read_csv(RAW / "macro" / "india_10y.csv")
macro.columns = ["date", "y"]
gsec_date, gsec = macro.iloc[-1]["date"], float(macro.iloc[-1]["y"]) / 100

inp = sheet("Inputs", "Global inputs and assumptions", "Module 6 — hurdle rate building blocks", [42, 14, 60])
rows = [
    ("Valuation date", None, "Prices: last NSE close available in dataset"),
    ("India 10-yr G-Sec yield", gsec, f"OECD/FRED series INDIRLTLT01STM, {gsec_date} (monthly avg)"),
    ("India sovereign default spread (Baa3)", 0.018677954, "Damodaran ctryprem.xlsx, Jan-2026 update"),
    ("Rupee risk-free rate = G-Sec − default spread", "=B5-B6", "Damodaran: govt bond yield contains default risk; strip it"),
    ("Mature market ERP", 0.0423, "Damodaran implied ERP (S&P 500), Jan-2026"),
    ("India country risk premium (CRP)", 0.028453587, "Damodaran: default spread × σEquity/σBond (1.52)"),
    ("India total ERP = mature ERP + CRP", "=B8+B9", "Used in CAPM"),
    ("Marginal corporate tax rate", 0.2517, "Sec 115BAA: 22% + 10% surcharge + 4% cess"),
    ("Terminal growth rate (nominal, Rs)", 0.055, "Capped at rupee risk-free rate (TB2 Ch-6 rule g ≤ Rf)"),
    ("Blume weight on raw beta", 0.67, "Blume (1971) mean reversion"),
    ("Return on new invested capital in terminal year", 0.15, "Excess return fades; RONIC > WACC modestly"),
    ("Mid-year discounting (1 = yes)", 1, "Cash flows assumed to arrive mid-year"),
]
hdr(inp, 3, ["Parameter", "Value", "Source / rationale"])
for i, (k, v, s) in enumerate(rows):
    r = 4 + i
    put(inp, r, 1, k)
    c = put(inp, r, 2, v, PCT if isinstance(v, (float, str)) else None,
            font=F_IN if isinstance(v, float) or isinstance(v, int) else F_N,
            fill=FILL_IN if isinstance(v, (float, int)) else None)
    put(inp, r, 3, s, font=F_NOTE)
inp["B4"] = str(last_price("DLF")[0])
inp["B15"].number_format = "0"
for nm, ref in [("Gsec", "$B$5"), ("DefSpread", "$B$6"), ("Rf", "$B$7"), ("ERP", "$B$10"), ("Tax", "$B$11"),
                ("gT", "$B$12"), ("Blume", "$B$13"), ("RONIC", "$B$14"), ("MidYr", "$B$15")]:
    wb.defined_names[nm] = DefinedName(nm, attr_text=f"Inputs!{ref}")

# synthetic rating table (Damodaran, large non-financial firms, Jan-2026)
put(inp, 18, 1, "Synthetic rating table (Damodaran, large non-financial firms, Jan-2026)", font=F_B)
hdr(inp, 19, ["ICR greater than", "Rating", "Default spread"])
table = [(-1e5, "D", .19), (.2, "C", .16), (.65, "CC", .1261), (.8, "CCC", .0885), (1.25, "B-", .0509),
         (1.5, "B", .0321), (1.75, "B+", .0275), (2, "BB", .0184), (2.25, "BB+", .0138), (2.5, "BBB", .0111),
         (3, "A-", .0089), (4.25, "A", .0078), (5.5, "A+", .0070), (6.5, "AA", .0055), (8.5, "AAA", .0040)]
for i, (a, b, c) in enumerate(table):
    put(inp, 20 + i, 1, a, NUM2, F_IN, FILL_IN)
    put(inp, 20 + i, 2, b, None, F_IN, FILL_IN)
    put(inp, 20 + i, 3, c, PCT, F_IN, FILL_IN)
RT = "Inputs!$A$20:$A$34"
RT_R, RT_S = "Inputs!$B$20:$B$34", "Inputs!$C$20:$C$34"

# =====================================================================================
# 2. DATA SHEETS
# =====================================================================================
DATA_ROWS = ["Revenue", "COGS", "SGA", "DandA", "InterestExpense", "InterestIncome", "SpecialItems", "PBT", "Tax",
             "NetIncomeInclMI", "NetIncome",
             "TotalAssets", "CurrentAssets", "CurrentLiabilities", "Inventory", "Receivables", "Cash", "STInvestments",
             "RestrictedCash", "LTFinInvestments", "EquityInvestments", "InvestmentProperty", "NetPPE", "CWIP",
             "TotalDebt", "CurrentDebt", "Payables", "Equity", "MinorityInterest", "RetainedEarnings",
             "TotalLiabilities", "NonCurrentLiabilities", "Shares",
             "CFO", "Capex", "CFI", "CFF", "DividendsPaid", "InterestPaid", "ChgInventory", "FYEndPrice"]
LABEL = {"Revenue": "Revenue from operations", "COGS": "Cost of revenue", "SGA": "Selling, general & admin",
         "DandA": "Depreciation & amortisation", "InterestExpense": "Finance cost (P&L)",
         "InterestIncome": "Interest income", "SpecialItems": "Exceptional / special items",
         "PBT": "Profit before tax", "Tax": "Tax expense", "NetIncomeInclMI": "PAT incl. minority & JV share",
         "NetIncome": "PAT attributable to owners", "TotalAssets": "Total assets", "CurrentAssets": "Current assets",
         "CurrentLiabilities": "Current liabilities", "Inventory": "Inventory (land, WIP, finished units)",
         "Receivables": "Trade receivables (net)", "Cash": "Cash & equivalents", "STInvestments": "Short-term investments",
         "RestrictedCash": "Restricted cash (RERA escrow etc.)", "LTFinInvestments": "Non-current financial investments",
         "EquityInvestments": "Investments in JVs/associates", "InvestmentProperty": "Investment property",
         "NetPPE": "Net PP&E", "CWIP": "Capital work-in-progress", "TotalDebt": "Total borrowings incl. leases",
         "CurrentDebt": "Current borrowings incl. leases", "Payables": "Trade & other payables",
         "Equity": "Equity attributable to owners", "MinorityInterest": "Non-controlling interest",
         "RetainedEarnings": "Retained earnings", "TotalLiabilities": "Total liabilities",
         "NonCurrentLiabilities": "Non-current liabilities", "Shares": "Shares outstanding (crore)",
         "CFO": "Cash flow from operations", "Capex": "Capex (PP&E + investment property)",
         "CFI": "Cash flow from investing", "CFF": "Cash flow from financing", "DividendsPaid": "Dividends paid",
         "InterestPaid": "Interest paid (cash, incl. capitalised)", "ChgInventory": "Change in inventory (CF)",
         "FYEndPrice": "Share price at 31-Mar (Rs)"}
DROW = {k: 5 + i for i, k in enumerate(DATA_ROWS)}


def D(co, field, year):
    return f"Data_{co}!${YC[year]}${DROW[field]}"


PX = {}
for co, tk in ALL.items():
    t = load(tk)
    t.loc["FYEndPrice"] = fy_end_prices(tk).reindex(t.columns).values
    dt, px, px6 = last_price(tk)
    PX[co] = (dt, px, px6)
    ws = sheet(f"Data_{co}", f"{NAMES[co]} — consolidated financials (Rs crore)",
               "Source: Yahoo Finance consolidated statements (FY = year ending 31 March). Raw pull: scripts/pull_data.py",
               [40, 14, 13, 13, 13, 13])
    hdr(ws, 4, ["Line item", "Key"] + [f"FY{str(y)[2:]}" for y in YEARS])
    for k in DATA_ROWS:
        r = DROW[k]
        put(ws, r, 1, LABEL[k])
        put(ws, r, 2, k, font=F_NOTE)
        for y in YEARS:
            v = t.loc[k, y] if k in t.index else 0
            v = 0 if pd.isna(v) else round(float(v), 2)
            put(ws, r, 3 + YEARS.index(y), v, NUM2 if k in ("Shares", "FYEndPrice") else NUM, F_IN)
    r = DROW["FYEndPrice"] + 2
    put(ws, r, 1, "Latest price (Rs)", font=F_B); put(ws, r, 3, round(px, 2), NUM2, F_IN, FILL_IN)
    put(ws, r, 4, f"NSE close {dt}", font=F_NOTE)
    put(ws, r + 1, 1, "6-month average price (Rs)", font=F_B); put(ws, r + 1, 3, round(px6, 2), NUM2, F_IN, FILL_IN)
    PX[co] = (dt, px, px6, f"Data_{co}!$C${r}", f"Data_{co}!$C${r+1}")
    ws.freeze_panes = "C5"

# =====================================================================================
# 3. RECAST (Module 4) — operating vs financing split, NOPAT
# =====================================================================================
rc = sheet("Recast", "Recast financial statements: operating vs. financing vs. non-operating",
           "Module 4 — Implementing accounting analysis (TB1 Ch-4/5). Separates core development/leasing from treasury & JV income.")
RC = {}
r = 4
for co in TARGETS:
    sub(rc, r, f"{NAMES[co]}", 6); r += 1
    hdr(rc, r, ["Item", "Formula logic"] + [f"FY{str(y)[2:]}" for y in YEARS]); r += 1
    items = [
        ("EBIT incl. other income", "PBT + finance cost − interest income?", lambda y: f"={D(co,'PBT',y)}+{D(co,'InterestExpense',y)}"),
        ("Less: interest income (treasury)", "non-operating", lambda y: f"=-{D(co,'InterestIncome',y)}"),
        ("Less: exceptional / special items", "non-recurring", lambda y: f"=-{D(co,'SpecialItems',y)}"),
        ("Core operating EBIT", "recurring project/leasing profit", None),
        ("NOPAT = core EBIT × (1 − t)", "t = marginal 25.17%", None),
        ("Share of JV/associate profit (post-tax)", "PAT incl. MI − (PBT − tax)", lambda y: f"={D(co,'NetIncomeInclMI',y)}-({D(co,'PBT',y)}-{D(co,'Tax',y)})"),
        ("Cash & liquid investments", "cash + ST inv + LT fin. inv (excl. restricted)", lambda y: f"={D(co,'Cash',y)}+{D(co,'STInvestments',y)}+{D(co,'LTFinInvestments',y)}"),
        ("Restricted cash (kept operating)", "RERA 70% escrow — not free cash", lambda y: f"={D(co,'RestrictedCash',y)}"),
        ("Total debt incl. leases", "", lambda y: f"={D(co,'TotalDebt',y)}"),
        ("Net financial obligations (NFO)", "debt − liquid assets", None),
        ("Equity incl. minority", "", lambda y: f"={D(co,'Equity',y)}+{D(co,'MinorityInterest',y)}"),
        ("Non-operating JV/associate investments", "valued separately", lambda y: f"={D(co,'EquityInvestments',y)}"),
        ("Net operating assets = invested capital", "equity + NFO − JV investments", None),
        ("Customer advances & other op. liabilities (derived)", "CL − current debt − payables", lambda y: f"={D(co,'CurrentLiabilities',y)}-{D(co,'CurrentDebt',y)}-{D(co,'Payables',y)}"),
        ("Interest capitalised (cash paid − P&L cost)", "Ind AS 23 red flag", lambda y: f"=MAX(0,{D(co,'InterestPaid',y)}-{D(co,'InterestExpense',y)})"),
    ]
    start = r
    for i, (lab, logic, fn) in enumerate(items):
        put(rc, r + i, 1, lab, font=F_B if lab.startswith(("Core", "NOPAT", "Net operating", "Net financial")) else F_N)
        put(rc, r + i, 2, logic, font=F_NOTE)
    for j, y in enumerate(YEARS):
        c = 3 + j
        col = L(c)
        for i, (lab, logic, fn) in enumerate(items):
            if fn:
                put(rc, r + i, c, fn(y), NUM)
        put(rc, r + 3, c, f"=SUM({col}{r}:{col}{r+2})", NUM, F_B, FILL_KEY)
        put(rc, r + 4, c, f"={col}{r+3}*(1-Tax)", NUM, F_B, FILL_KEY)
        put(rc, r + 9, c, f"={col}{r+8}-{col}{r+6}", NUM, F_B)
        put(rc, r + 12, c, f"={col}{r+10}+{col}{r+9}-{col}{r+11}", NUM, F_B, FILL_KEY)
    RC[co] = {"EBITx": start, "CoreEBIT": start + 3, "NOPAT": start + 4, "JV": start + 5, "Liquid": start + 6,
              "Debt": start + 8, "NFO": start + 9, "EqMI": start + 10, "EqInv": start + 11, "IC": start + 12,
              "Adv": start + 13, "CapInt": start + 14}
    r += len(items) + 2


def R(co, key, y):
    return f"Recast!${YC[y]}${RC[co][key]}"


# =====================================================================================
# 4. RATIOS (Module 5)
# =====================================================================================
ra = sheet("Ratios", "Ratio analysis FY23–FY26 (average balances where flows meet stocks)",
           "Module 5 — Financial analysis: profitability, efficiency, liquidity, solvency, cash-flow quality, market")
RA = {}


def avg(co, f, y):
    return f"AVERAGE({D(co,f,y-1)},{D(co,f,y)})"


def ratio_defs(co):
    return [
        ("Growth & profitability", None, None),
        ("Revenue growth", PCT, lambda y: f"={D(co,'Revenue',y)}/{D(co,'Revenue',y-1)}-1" if y > 2023 else None),
        ("EBITDA growth", PCT, lambda y: f"=IFERROR(({R(co,'EBITx',y)}+{D(co,'DandA',y)})/({R(co,'EBITx',y-1)}+{D(co,'DandA',y-1)})-1,\"n.m.\")" if y > 2023 else None),
        ("EBIT growth (incl. other income)", PCT, lambda y: f"=IFERROR({R(co,'EBITx',y)}/{R(co,'EBITx',y-1)}-1,\"n.m.\")" if y > 2023 else None),
        ("Core EBIT growth", PCT, lambda y: f"=IF({R(co,'CoreEBIT',y-1)}<=0,\"n.m.\",{R(co,'CoreEBIT',y)}/{R(co,'CoreEBIT',y-1)}-1)" if y > 2023 else None),
        ("PAT growth", PCT, lambda y: f"={D(co,'NetIncome',y)}/{D(co,'NetIncome',y-1)}-1" if y > 2023 else None),
        ("Dividend growth", PCT, lambda y: f"=IFERROR({D(co,'DividendsPaid',y)}/{D(co,'DividendsPaid',y-1)}-1,\"n.m.\")" if y > 2023 else None),
        ("Gross margin", PCT, lambda y: f"=1-{D(co,'COGS',y)}/{D(co,'Revenue',y)}"),
        ("EBITDA margin (incl. other income)", PCT, lambda y: f"=({R(co,'EBITx',y)}+{D(co,'DandA',y)})/{D(co,'Revenue',y)}"),
        ("EBT margin", PCT, lambda y: f"={D(co,'PBT',y)}/{D(co,'Revenue',y)}"),
        ("SG&A % of revenue", PCT, lambda y: f"={D(co,'SGA',y)}/{D(co,'Revenue',y)}"),
        ("D&A % of revenue", PCT, lambda y: f"={D(co,'DandA',y)}/{D(co,'Revenue',y)}"),
        ("Effective tax rate", PCT, lambda y: f"={D(co,'Tax',y)}/{D(co,'PBT',y)}"),
        ("Core EBIT margin", PCT, lambda y: f"={R(co,'CoreEBIT',y)}/{D(co,'Revenue',y)}"),
        ("Net profit margin (owners)", PCT, lambda y: f"={D(co,'NetIncome',y)}/{D(co,'Revenue',y)}"),
        ("JV/associate share of PAT", PCT, lambda y: f"={R(co,'JV',y)}/{D(co,'NetIncomeInclMI',y)}"),
        ("Return on equity (avg)", PCT, lambda y: f"={D(co,'NetIncome',y)}/{avg(co,'Equity',y)}" if y > 2023 else None),
        ("Return on assets (avg)", PCT, lambda y: f"={D(co,'NetIncomeInclMI',y)}/{avg(co,'TotalAssets',y)}" if y > 2023 else None),
        ("ROIC = NOPAT / avg invested capital", PCT, lambda y: f"={R(co,'NOPAT',y)}/AVERAGE({R(co,'IC',y-1)},{R(co,'IC',y)})" if y > 2023 else None),
        ("ROCE = EBIT / avg (equity+MI+debt)", PCT, lambda y: f"={R(co,'EBITx',y)}/AVERAGE({D(co,'Equity',y-1)}+{D(co,'MinorityInterest',y-1)}+{D(co,'TotalDebt',y-1)},{D(co,'Equity',y)}+{D(co,'MinorityInterest',y)}+{D(co,'TotalDebt',y)})" if y > 2023 else None),
        ("Retention ratio (retained earnings %)", PCT, lambda y: f"=1-{D(co,'DividendsPaid',y)}/{D(co,'NetIncome',y)}"),
        ("Self-sustained growth = ROE × retention", PCT, lambda y: f"={D(co,'NetIncome',y)}/{avg(co,'Equity',y)}*(1-{D(co,'DividendsPaid',y)}/{D(co,'NetIncome',y)})" if y > 2023 else None),
        ("Efficiency", None, None),
        ("Fixed-asset turnover (PP&E + inv. property) (x)", X, lambda y: f"={D(co,'Revenue',y)}/AVERAGE({D(co,'NetPPE',y-1)}+{D(co,'InvestmentProperty',y-1)},{D(co,'NetPPE',y)}+{D(co,'InvestmentProperty',y)})" if y > 2023 else None),
        ("Capital turnover = revenue / avg (equity+MI+debt) (x)", X, lambda y: f"={D(co,'Revenue',y)}/AVERAGE({D(co,'Equity',y-1)}+{D(co,'MinorityInterest',y-1)}+{D(co,'TotalDebt',y-1)},{D(co,'Equity',y)}+{D(co,'MinorityInterest',y)}+{D(co,'TotalDebt',y)})" if y > 2023 else None),
        ("Creditor turnover = cost of revenue / avg payables (x)", X, lambda y: f"={D(co,'COGS',y)}/{avg(co,'Payables',y)}" if y > 2023 else None),
        ("Inventory turnover = cost of revenue / avg inventory (x)", X, lambda y: f"={D(co,'COGS',y)}/{avg(co,'Inventory',y)}" if y > 2023 else None),
        ("Asset turnover (x)", X, lambda y: f"={D(co,'Revenue',y)}/{avg(co,'TotalAssets',y)}" if y > 2023 else None),
        ("Inventory days (on cost of revenue)", NUM, lambda y: f"=365*{avg(co,'Inventory',y)}/{D(co,'COGS',y)}" if y > 2023 else None),
        ("Receivable days", NUM, lambda y: f"=365*{avg(co,'Receivables',y)}/{D(co,'Revenue',y)}" if y > 2023 else None),
        ("Payable days", NUM, lambda y: f"=365*{avg(co,'Payables',y)}/{D(co,'COGS',y)}" if y > 2023 else None),
        ("Cash conversion cycle (days)", NUM, "CCC"),
        ("Inventory / total assets", PCT, lambda y: f"={D(co,'Inventory',y)}/{D(co,'TotalAssets',y)}"),
        ("Customer advances / revenue (x)", X, lambda y: f"={R(co,'Adv',y)}/{D(co,'Revenue',y)}"),
        ("Liquidity", None, None),
        ("Current ratio (x)", X, lambda y: f"={D(co,'CurrentAssets',y)}/{D(co,'CurrentLiabilities',y)}"),
        ("Quick ratio (x)", X, lambda y: f"=({D(co,'CurrentAssets',y)}-{D(co,'Inventory',y)})/{D(co,'CurrentLiabilities',y)}"),
        ("Cash ratio (x)", X, lambda y: f"=({D(co,'Cash',y)}+{D(co,'STInvestments',y)})/{D(co,'CurrentLiabilities',y)}"),
        ("Solvency", None, None),
        ("Debt / equity (x)", X, lambda y: f"={D(co,'TotalDebt',y)}/{D(co,'Equity',y)}"),
        ("Net debt / equity (x)", X, lambda y: f"={R(co,'NFO',y)}/{D(co,'Equity',y)}"),
        ("Net debt / EBITDA (x)", X, lambda y: f"={R(co,'NFO',y)}/({R(co,'EBITx',y)}+{D(co,'DandA',y)})"),
        ("Interest coverage: EBIT / P&L finance cost (x)", X, lambda y: f"=IFERROR({R(co,'EBITx',y)}/{D(co,'InterestExpense',y)},\"n.m.\")"),
        ("Cash interest coverage: EBIT / interest paid (x)", X, lambda y: f"=IFERROR({R(co,'EBITx',y)}/{D(co,'InterestPaid',y)},\"n.m.\")"),
        ("Cash-flow quality (Module 3 red-flag screen)", None, None),
        ("CFO / PAT (x)", X, lambda y: f"={D(co,'CFO',y)}/{D(co,'NetIncomeInclMI',y)}"),
        ("CFO / revenue", PCT, lambda y: f"={D(co,'CFO',y)}/{D(co,'Revenue',y)}"),
        ("CFO / total debt (x)", X, lambda y: f"=IFERROR({D(co,'CFO',y)}/{D(co,'TotalDebt',y)},\"n.m.\")"),
        ("CFO / total assets", PCT, lambda y: f"={D(co,'CFO',y)}/{D(co,'TotalAssets',y)}"),
        ("Capex / D&A (x)", X, lambda y: f"=IFERROR({D(co,'Capex',y)}/{D(co,'DandA',y)},\"n.m.\")"),
        ("Free cash flow = CFO − capex", NUM, lambda y: f"={D(co,'CFO',y)}-{D(co,'Capex',y)}"),
        ("Accruals ratio = (PAT − CFO) / avg assets", PCT, lambda y: f"=({D(co,'NetIncomeInclMI',y)}-{D(co,'CFO',y)})/{avg(co,'TotalAssets',y)}" if y > 2023 else None),
        ("Dividend payout", PCT, lambda y: f"={D(co,'DividendsPaid',y)}/{D(co,'NetIncome',y)}"),
        ("Market (at 31-Mar price)", None, None),
        ("Market capitalisation", NUM, lambda y: f"={D(co,'FYEndPrice',y)}*{D(co,'Shares',y)}"),
        ("P/E (x)", X, lambda y: f"={D(co,'FYEndPrice',y)}*{D(co,'Shares',y)}/{D(co,'NetIncome',y)}"),
        ("P/B (x)", X, lambda y: f"={D(co,'FYEndPrice',y)}*{D(co,'Shares',y)}/{D(co,'Equity',y)}"),
        ("EV / EBITDA (x)", X, lambda y: f"=({D(co,'FYEndPrice',y)}*{D(co,'Shares',y)}+{R(co,'NFO',y)})/({R(co,'EBITx',y)}+{D(co,'DandA',y)})"),
    ]


r = 4
for co in TARGETS:
    sub(ra, r, NAMES[co], 6); r += 1
    hdr(ra, r, ["Ratio", ""] + [f"FY{str(y)[2:]}" for y in YEARS]); r += 1
    RA[co] = {}
    for lab, fmt, fn in ratio_defs(co):
        if fmt is None:
            put(ra, r, 1, lab, font=F_B); r += 1; continue
        put(ra, r, 1, lab)
        RA[co][lab] = r
        for j, y in enumerate(YEARS):
            if fn == "CCC":
                if y > 2023:
                    c = L(3 + j)
                    put(ra, r, 3 + j, f"={c}{RA[co]['Inventory days (on cost of revenue)']}+{c}{RA[co]['Receivable days']}-{c}{RA[co]['Payable days']}", fmt)
                continue
            f = fn(y)
            if f:
                put(ra, r, 3 + j, f, fmt)
        r += 1
    r += 1

# =====================================================================================
# 5. DUPONT (Module 5) — 3-step, 5-step, Palepu operating/financing decomposition
# =====================================================================================
dp = sheet("DuPont", "DuPont decomposition of ROE — 3-step, extended 5-step, and Palepu operating vs. financing split",
           "Module 5 — strategic ratio analysis. Average balances. FY24–FY26 (FY23 used only as opening balance).")
DP = {}
r = 4
Y3 = YEARS[1:]
for co in TARGETS:
    sub(dp, r, NAMES[co], 6); r += 1
    hdr(dp, r, ["Component", "Definition"] + [f"FY{str(y)[2:]}" for y in Y3]); r += 1
    s = r
    lines = [
        ("3-STEP", "", None),
        ("Net profit margin", "PAT(owners) / revenue", lambda y: f"={D(co,'NetIncome',y)}/{D(co,'Revenue',y)}", PCT),
        ("Asset turnover", "revenue / avg total assets", lambda y: f"={D(co,'Revenue',y)}/{avg(co,'TotalAssets',y)}", X),
        ("Equity multiplier", "avg assets / avg owners' equity", lambda y: f"={avg(co,'TotalAssets',y)}/{avg(co,'Equity',y)}", X),
        ("ROE (3-step product)", "NPM × ATO × EM", "P3", PCT),
        ("ROE (direct check)", "PAT / avg equity", lambda y: f"={D(co,'NetIncome',y)}/{avg(co,'Equity',y)}", PCT),
        ("5-STEP (extended)", "", None),
        ("Tax & JV burden", "PAT incl MI & JV / PBT  (>1 ⇒ JV income below PBT)", lambda y: f"={D(co,'NetIncomeInclMI',y)}/{D(co,'PBT',y)}", X),
        ("Interest burden", "PBT / EBIT", lambda y: f"={D(co,'PBT',y)}/{R(co,'EBITx',y)}", X),
        ("EBIT margin", "EBIT / revenue", lambda y: f"={R(co,'EBITx',y)}/{D(co,'Revenue',y)}", PCT),
        ("Asset turnover", "revenue / avg assets", lambda y: f"={D(co,'Revenue',y)}/{avg(co,'TotalAssets',y)}", X),
        ("Equity multiplier", "avg assets / avg equity", lambda y: f"={avg(co,'TotalAssets',y)}/{avg(co,'Equity',y)}", X),
        ("Owners' share of PAT", "PAT owners / PAT incl MI", lambda y: f"={D(co,'NetIncome',y)}/{D(co,'NetIncomeInclMI',y)}", X),
        ("ROE (5-step product)", "product of six factors", "P5", PCT),
        ("PALEPU SPLIT", "ROE = RNOA + (RNOA − NBC) × NFL + other", None),
        ("Return on net operating assets (RNOA)", "NOPAT / avg NOA", lambda y: f"={R(co,'NOPAT',y)}/AVERAGE({R(co,'IC',y-1)},{R(co,'IC',y)})", PCT),
        ("Net financial leverage (NFL)", "avg NFO / avg equity incl MI", lambda y: f"=AVERAGE({R(co,'NFO',y-1)},{R(co,'NFO',y)})/AVERAGE({R(co,'EqMI',y-1)},{R(co,'EqMI',y)})", X),
        ("Net borrowing cost after tax (NBC)", "(fin. cost − int. income)(1−t) / avg NFO", lambda y: f"=IFERROR(({D(co,'InterestExpense',y)}-{D(co,'InterestIncome',y)})*(1-Tax)/AVERAGE({R(co,'NFO',y-1)},{R(co,'NFO',y)}),0)", PCT),
        ("Operating ROE contribution", "RNOA + (RNOA − NBC) × NFL", "PAL", PCT),
        ("Non-operating (JV, exceptional) contribution", "ROE(owners, on equity incl MI) − operating", "RES", PCT),
    ]
    rows_ = {}
    for i, (lab, de, fn, *fmt) in enumerate(lines):
        rr = r + i
        rows_[lab + str(i)] = rr
        if fn is None:
            put(dp, rr, 1, lab, font=F_B); continue
        put(dp, rr, 1, lab, font=F_B if lab.startswith("ROE") or "contribution" in lab else F_N)
        put(dp, rr, 2, de, font=F_NOTE)
        for j, y in enumerate(Y3):
            c = L(3 + j)
            if fn == "P3":
                f = f"={c}{r+1}*{c}{r+2}*{c}{r+3}"
            elif fn == "P5":
                f = f"=PRODUCT({c}{r+7}:{c}{r+12})"
            elif fn == "PAL":
                f = f"={c}{r+15}+({c}{r+15}-{c}{r+17})*{c}{r+16}"
            elif fn == "RES":
                f = f"={D(co,'NetIncomeInclMI',y)}/AVERAGE({R(co,'EqMI',y-1)},{R(co,'EqMI',y)})-{c}{r+18}"
            else:
                f = fn(y)
            put(dp, rr, 3 + j, f, fmt[0], F_B if fn in ("P3", "P5", "PAL") else F_N,
                FILL_KEY if fn in ("P3", "P5", "PAL") else None)
    DP[co] = {"NPM": r + 1, "ATO": r + 2, "EM": r + 3, "ROE": r + 4, "RNOA": r + 15}
    r += len(lines)
    # ROE change attribution (FY24->FY26) by sequential substitution
    put(dp, r, 1, "ROE change FY24→FY26 attributed (sequential substitution)", font=F_B); r += 1
    a, b = "C", "E"
    put(dp, r, 1, "  from margin"); put(dp, r, 3, f"=({b}{s+1}-{a}{s+1})*{a}{s+2}*{a}{s+3}", PCT)
    put(dp, r + 1, 1, "  from asset turnover"); put(dp, r + 1, 3, f"={b}{s+1}*({b}{s+2}-{a}{s+2})*{a}{s+3}", PCT)
    put(dp, r + 2, 1, "  from leverage"); put(dp, r + 2, 3, f"={b}{s+1}*{b}{s+2}*({b}{s+3}-{a}{s+3})", PCT)
    put(dp, r + 3, 1, "  total = ΔROE", font=F_B); put(dp, r + 3, 3, f"=SUM(C{r}:C{r+2})", PCT, F_B)
    put(dp, r + 3, 4, f"={b}{s+4}-{a}{s+4}", PCT); note(dp, r + 3, "check", 5)
    r += 6

# chart: ROE by company
ch = LineChart(); ch.title = "ROE (3-step) FY24–FY26"; ch.height, ch.width = 7, 14
for co in TARGETS:
    rr = DP[co]["ROE"]
    ser = Series(Reference(dp, min_col=3, max_col=5, min_row=rr), title=NAMES[co])
    ch.series.append(ser)
ch.set_categories(Reference(dp, min_col=3, max_col=5, min_row=5))
ch.y_axis.number_format = "0%"
dp.add_chart(ch, "H4")

# =====================================================================================
# 6. ALTMAN Z (Module 5 distress screen)
# =====================================================================================
az = sheet("AltmanZ", "Altman Z-score (1968, public) and Z''-score (emerging-market, non-manufacturer)",
           "Module 5 / Module 9 link — distress screening. Z'' preferred for asset-heavy developers (drops sales/TA bias).")
r = 4
for co in TARGETS:
    sub(az, r, NAMES[co], 6); r += 1
    hdr(az, r, ["Component", "Weight (Z / Z'')"] + [f"FY{str(y)[2:]}" for y in YEARS]); r += 1
    comps = [
        ("X1 Working capital / total assets", "1.2 / 6.56", lambda y: f"=({D(co,'CurrentAssets',y)}-{D(co,'CurrentLiabilities',y)})/{D(co,'TotalAssets',y)}"),
        ("X2 Retained earnings / total assets", "1.4 / 3.26", lambda y: f"={D(co,'RetainedEarnings',y)}/{D(co,'TotalAssets',y)}"),
        ("X3 EBIT / total assets", "3.3 / 6.72", lambda y: f"={R(co,'EBITx',y)}/{D(co,'TotalAssets',y)}"),
        ("X4 Market value of equity / total liabilities", "0.6 / –", lambda y: f"={D(co,'FYEndPrice',y)}*{D(co,'Shares',y)}/{D(co,'TotalLiabilities',y)}"),
        ("X4'' Book equity / total liabilities", "– / 1.05", lambda y: f"=({D(co,'Equity',y)}+{D(co,'MinorityInterest',y)})/{D(co,'TotalLiabilities',y)}"),
        ("X5 Sales / total assets", "1.0 / –", lambda y: f"={D(co,'Revenue',y)}/{D(co,'TotalAssets',y)}"),
    ]
    for i, (lab, w, fn) in enumerate(comps):
        put(az, r + i, 1, lab); put(az, r + i, 2, w, font=F_NOTE)
        for j, y in enumerate(YEARS):
            put(az, r + i, 3 + j, fn(y), NUM2)
    for j, y in enumerate(YEARS):
        c = L(3 + j)
        put(az, r + 6, 3 + j, f"=1.2*{c}{r}+1.4*{c}{r+1}+3.3*{c}{r+2}+0.6*{c}{r+3}+1*{c}{r+5}", NUM2, F_B, FILL_KEY)
        put(az, r + 7, 3 + j, f'=IF({c}{r+6}>2.99,"Safe",IF({c}{r+6}>1.81,"Grey","Distress"))')
        put(az, r + 8, 3 + j, f"=3.25+6.56*{c}{r}+3.26*{c}{r+1}+6.72*{c}{r+2}+1.05*{c}{r+4}", NUM2, F_B, FILL_KEY)
        put(az, r + 9, 3 + j, f'=IF({c}{r+8}>5.85,"Safe",IF({c}{r+8}>4.35,"Grey","Distress"))')
    put(az, r + 6, 1, "Altman Z (original)", font=F_B); put(az, r + 7, 1, "  zone (>2.99 safe, <1.81 distress)")
    put(az, r + 8, 1, "Altman Z'' (EM, with 3.25 constant)", font=F_B); put(az, r + 9, 1, "  zone (>5.85 safe, <4.35 distress)")
    r += 12

# =====================================================================================
# 7. BETA — regression (monthly 5y, weekly 3y), peers, bottom-up (Module 6)
# =====================================================================================
def prices(tk, f):
    d = pd.read_csv(RAW / tk / f, index_col=0)
    d.index = pd.to_datetime(d.index, utc=True).tz_convert(None)
    return d["Close"].dropna()


def beta_sheet(name, f, n, cos, title):
    ws = sheet(name, title, "Module 6 — regression beta: R_stock = α + β·R_Nifty50 + ε. Price → return formulas live.",
               [12] + [11] * (2 * (len(cos) + 1)) + [3, 34, 12, 12, 12, 12, 12, 12, 12, 12, 12])
    series = {"NIFTY50": prices("NIFTY50", f)}
    for co in cos:
        series[co] = prices(ALL.get(co, co), f)
    df = pd.concat(series, axis=1, join="inner").iloc[-(n + 1):]
    keys = ["NIFTY50"] + cos
    hdr(ws, 4, ["Period"] + [f"{k} px" for k in keys] + [f"{k} ret" for k in keys])
    for i, (dt, row) in enumerate(df.iterrows()):
        rr = 5 + i
        put(ws, rr, 1, dt.date(), "mmm-yy")
        for j, k in enumerate(keys):
            put(ws, rr, 2 + j, round(float(row[k]), 2), NUM2, F_IN)
            if i > 0:
                pc = L(2 + j)
                put(ws, rr, 2 + len(keys) + j, f"={pc}{rr}/{pc}{rr-1}-1", "0.00%")
    first, last = 6, 5 + len(df) - 1
    mcol = L(2 + len(keys))
    sc = 4 + 2 * len(keys)            # stats block start col
    hdr(ws, 4, ["Statistic"] + [NAMES.get(c, c)[:14] for c in cos], sc)
    stats = ["Observations", "Raw beta (SLOPE)", "Beta check: COVAR/VAR", "Alpha (INTERCEPT, per period)",
             "R-squared", "Std error of regression (STEYX)", "Std error of beta", "t-stat of beta",
             "95% CI low", "95% CI high", "Blume-adjusted beta", "Jensen's alpha check: α − Rf(1−β)/periods",
             "Diversifiable (firm-specific) risk = 1 − R²"]
    per = 12 if "monthly" in title else 52
    for i, s in enumerate(stats):
        put(ws, 5 + i, sc, s, font=F_B if "beta" in s.lower() else F_N)
    out = {}
    for j, co in enumerate(cos):
        c = sc + 1 + j
        yc = L(2 + len(keys) + 1 + j)
        Y, Xr = f"{yc}{first}:{yc}{last}", f"{mcol}{first}:{mcol}{last}"
        cl = L(c)
        fs = [f"=COUNT({Y})", f"=SLOPE({Y},{Xr})", f"=COVAR({Y},{Xr})/VARP({Xr})", f"=INTERCEPT({Y},{Xr})",
              f"=RSQ({Y},{Xr})", f"=STEYX({Y},{Xr})", f"={cl}10/(STDEV({Xr})*SQRT({cl}5-1))", f"={cl}6/{cl}11",
              f"={cl}6-TINV(0.05,{cl}5-2)*{cl}11", f"={cl}6+TINV(0.05,{cl}5-2)*{cl}11", f"=Blume*{cl}6+(1-Blume)",
              f"={cl}8-Rf/{per}*(1-{cl}6)", f"=1-{cl}9"]
        fm = [NUM, "0.000", "0.000", "0.00%", "0.000", "0.0000", "0.000", "0.00", "0.000", "0.000", "0.000", "0.00%", PCT]
        for i, (fx, fmx) in enumerate(zip(fs, fm)):
            put(ws, 5 + i, c, fx, fmx, F_B if i in (1, 10) else F_N, FILL_KEY if i in (1, 10) else None)
        out[co] = {"beta": f"{name}!${cl}$6", "adj": f"{name}!${cl}$15", "se": f"{name}!${cl}$11", "r2": f"{name}!${cl}$9"}
    # scatter chart for first company
    sch = ScatterChart(); sch.title = f"{NAMES[cos[0]]} vs Nifty 50 ({'monthly' if per == 12 else 'weekly'} returns)"
    sch.style = 13; sch.height, sch.width = 8, 13
    xs = Reference(ws, min_col=2 + len(keys), min_row=first, max_row=last)
    ys = Reference(ws, min_col=2 + len(keys) + 1, min_row=first, max_row=last)
    se = Series(ys, xs, title=NAMES[cos[0]]); se.marker.symbol = "circle"; se.graphicalProperties.line.noFill = True
    sch.series.append(se); sch.x_axis.title = "Nifty 50 return"; sch.y_axis.title = "Stock return"
    ws.add_chart(sch, f"{L(sc)}20")
    ws.freeze_panes = "B5"
    return out


BM = beta_sheet("Beta_Monthly", "px_monthly.csv", 60, [c for c in ALL if c not in BETA_EXCL] + ["NIFTYREALTY"],
                "Regression beta — 60 monthly returns vs Nifty 50 (5 years)")
NAMES["NIFTYREALTY"] = "Nifty Realty idx"
NAMES.update({"NEXUS": "Nexus Select Trust (mall REIT)", "EMBASSY": "Embassy Office REIT", "MINDSPACE": "Mindspace REIT", "BIRET": "Brookfield India REIT"})
BR = beta_sheet("Beta_REIT", "px_monthly.csv", 40, ["NEXUS", "EMBASSY", "MINDSPACE", "BIRET"],
                "REIT regression betas — 40 monthly returns vs Nifty 50 (tested as rental-business comparables for Phoenix)")
BW = beta_sheet("Beta_Weekly", "px_weekly.csv", 156, list(TARGETS), "Regression beta — 156 weekly returns vs Nifty 50 (3 years)")

bu = sheet("BottomUp_Beta", "Bottom-up (fundamental) beta from listed real-estate peers",
           "Module 6 — unlever each comparable at its own market D/E (Hamada), take the median, relever at target D/E",
           [26, 12, 13, 13, 12, 12, 12, 12])
hdr(bu, 4, ["Company", "Raw beta (5y m)", "Market cap", "Total debt FY26", "D/E (mkt)", "Tax", "Unlevered beta", "R²"])
BU = {}
BU_SET = [c for c in ALL if c not in BETA_EXCL]
for i, co in enumerate(BU_SET):
    rr = 5 + i
    put(bu, rr, 1, NAMES[co])
    put(bu, rr, 2, f"={BM[co]['beta']}", "0.000")
    put(bu, rr, 3, f"={PX[co][3]}*{D(co,'Shares',2026)}", NUM)
    put(bu, rr, 4, f"={D(co,'TotalDebt',2026)}", NUM)
    put(bu, rr, 5, f"=D{rr}/C{rr}", "0.000")
    put(bu, rr, 6, "=Tax", PCT)
    put(bu, rr, 7, f"=B{rr}/(1+(1-F{rr})*E{rr})", "0.000", F_B)
    put(bu, rr, 8, f"={BM[co]['r2']}", "0.000")
    BU[co] = rr
n_all = len(BU_SET)
lr = 5 + n_all
put(bu, lr, 1, f"Median unlevered beta (all {n_all})", font=F_B); put(bu, lr, 7, f"=MEDIAN(G5:G{lr-1})", "0.000", F_B, FILL_KEY)
put(bu, lr + 1, 1, "Average unlevered beta"); put(bu, lr + 1, 7, f"=AVERAGE(G5:G{lr-1})", "0.000")
put(bu, lr + 2, 1, "Std error of median ≈ avg SE/√n"); put(bu, lr + 2, 7,
    "=AVERAGE(" + ",".join(BM[c]["se"] for c in BU_SET) + f")/SQRT({n_all})", "0.000")
note(bu, lr + 3, f"Averaging {n_all} regression betas cuts standard error by ~√{n_all}; bottom-up beta reflects the business (real estate) rather than one stock's noise.")
put(bu, lr + 5, 1, "Relevered beta for targets", font=F_B)
hdr(bu, lr + 6, ["Target", "Unlevered (median)", "Market D/E", "Tax", "Relevered beta", "Regression β", "Blume β (m)", "Weekly β"])
for i, co in enumerate(TARGETS):
    rr = lr + 7 + i
    put(bu, rr, 1, NAMES[co]); put(bu, rr, 2, f"=$G${lr}", "0.000"); put(bu, rr, 3, f"=E{BU[co]}", "0.000")
    put(bu, rr, 4, "=Tax", PCT); put(bu, rr, 5, f"=B{rr}*(1+(1-D{rr})*C{rr})", "0.000", F_B, FILL_KEY)
    put(bu, rr, 6, f"={BM[co]['beta']}", "0.000"); put(bu, rr, 7, f"={BM[co]['adj']}", "0.000")
    put(bu, rr, 8, f"={BW[co]['beta']}", "0.000")
    BU[co + "_relev"] = f"BottomUp_Beta!$E${rr}"

# =====================================================================================
# 8. WACC (Module 6)
# =====================================================================================
wc = sheet("WACC", "Cost of capital: CAPM cost of equity, synthetic-rating cost of debt, market-value weights",
           "Module 6 — Ke = Rf + β × ERP ;  Kd = Rf + country default spread + company spread ;  WACC = E/V·Ke + D/V·Kd(1−t)",
           [44, 15, 15, 15, 46])
hdr(wc, 4, ["Item", "DLF", "Godrej Prop.", "Phoenix Mills", "Note"])
W = {}
wrows = [
    ("Rupee risk-free rate", lambda co, c: "=Rf", PCT, "G-Sec less sovereign default spread"),
    ("Beta used", lambda co, c: f"={BM[co]['adj']}" if co == "PML" else f"={BU[co+'_relev']}", "0.000",
     "DLF, GPL: bottom-up developer beta. PML: own Blume β — rental model differs from developers; REIT betas have R² < 12% (Beta_REIT)"),
    ("India equity risk premium", lambda co, c: "=ERP", PCT, "Mature ERP + India CRP"),
    ("Cost of equity (CAPM)", lambda co, c: f"={c}5+{c}6*{c}7", PCT, ""),
    ("— memo: Ke with regression beta", lambda co, c: f"={c}5+{BM[co]['beta']}*{c}7", PCT, "Shows sensitivity to beta choice"),
    ("— memo: Ke with Blume beta", lambda co, c: f"={c}5+{BM[co]['adj']}*{c}7", PCT, ""),
    ("EBIT incl. other income FY26", lambda co, c: f"={R(co,'EBITx',2026)}", NUM, ""),
    ("Interest paid (cash, incl. capitalised) FY26", lambda co, c: f"=MAX({D(co,'InterestPaid',2026)},{D(co,'InterestExpense',2026)})", NUM, "Cash basis avoids Ind AS 23 capitalisation distortion"),
    ("Interest coverage ratio (cash basis)", lambda co, c: f"={c}11/{c}12", X, ""),
    ("Synthetic rating", lambda co, c: f"=LOOKUP({c}13,{RT},{RT_R})", None, "Damodaran large-firm table"),
    ("Company default spread", lambda co, c: f"=LOOKUP({c}13,{RT},{RT_S})", PCT, ""),
    ("Pre-tax Kd (synthetic) = Rf + country DS + company spread", lambda co, c: f"=Rf+DefSpread+{c}15", PCT, "equals G-Sec + company spread"),
    ("Pre-tax Kd (actual) = interest paid / avg debt", lambda co, c: f"=IFERROR({D(co,'InterestPaid',2026)}/AVERAGE({D(co,'TotalDebt',2025)},{D(co,'TotalDebt',2026)}),{c}16)", PCT, "Cross-check"),
    ("Pre-tax Kd used", lambda co, c: f"={c}16", PCT, "Synthetic (forward-looking, market-based)"),
    ("After-tax Kd", lambda co, c: f"={c}18*(1-Tax)", PCT, ""),
    ("Market value of equity", lambda co, c: f"={PX[co][3]}*{D(co,'Shares',2026)}", NUM, "Latest price × shares"),
    ("Debt (book, incl. leases)", lambda co, c: f"={D(co,'TotalDebt',2026)}", NUM, "Book ≈ market for floating-rate INR debt"),
    ("E / V", lambda co, c: f"={c}20/({c}20+{c}21)", PCT, ""),
    ("D / V", lambda co, c: f"={c}21/({c}20+{c}21)", PCT, ""),
    ("WACC", lambda co, c: f"={c}22*{c}8+{c}23*{c}19", PCT, ""),
]
KEYROWS = ("Cost of equity (CAPM)", "WACC")
for i, (lab, fn, fmt, nt) in enumerate(wrows):
    rr = 5 + i
    put(wc, rr, 1, lab, font=F_B if lab in KEYROWS or lab == "Pre-tax Kd used" else F_N)
    for j, co in enumerate(TARGETS):
        put(wc, rr, 2 + j, fn(co, L(2 + j)), fmt, F_B if lab in KEYROWS else F_N, FILL_KEY if lab in KEYROWS else None)
    put(wc, rr, 5, nt, font=F_NOTE)
for j, co in enumerate(TARGETS):
    W[co] = {"Ke": f"WACC!${L(2+j)}$8", "WACC": f"WACC!${L(2+j)}$24", "Kd": f"WACC!${L(2+j)}$19"}

# =====================================================================================
# 9. GROWTH (Module 7) & EVA (Module 5)
# =====================================================================================
gr = sheet("Growth_EVA", "Growth estimation (historical, fundamental) and Economic Value Added",
           "Module 7 growth: g = reinvestment rate × ROIC ; g(EPS) = retention × ROE.   Module 5: EVA = (ROIC − WACC) × invested capital")
r = 4
GR = {}
for co in TARGETS:
    sub(gr, r, NAMES[co], 6); r += 1
    hdr(gr, r, ["Measure", ""] + [f"FY{str(y)[2:]}" for y in YEARS]); r += 1
    put(gr, r, 1, "Revenue CAGR FY23→FY26"); put(gr, r, 6, f"=({D(co,'Revenue',2026)}/{D(co,'Revenue',2023)})^(1/3)-1", PCT, F_B)
    put(gr, r + 1, 1, "PAT CAGR FY23→FY26"); put(gr, r + 1, 6, f"=({D(co,'NetIncome',2026)}/{D(co,'NetIncome',2023)})^(1/3)-1", PCT, F_B)
    put(gr, r + 2, 1, "Net reinvestment = ΔNOA (invested capital)")
    put(gr, r + 3, 1, "Reinvestment rate = ΔNOA / NOPAT")
    put(gr, r + 4, 1, "ROIC (on opening NOA)")
    put(gr, r + 5, 1, "Fundamental growth = RR × ROIC", font=F_B)
    put(gr, r + 6, 1, "Retention ratio = 1 − payout")
    put(gr, r + 7, 1, "ROE (avg)")
    put(gr, r + 8, 1, "Sustainable EPS growth = b × ROE", font=F_B)
    put(gr, r + 9, 1, "EVA = NOPAT − WACC × opening NOA", font=F_B)
    put(gr, r + 10, 1, "EVA spread = ROIC − WACC")
    for j, y in enumerate(YEARS[1:]):
        c = 4 + j
        cl = L(c)
        put(gr, r + 2, c, f"={R(co,'IC',y)}-{R(co,'IC',y-1)}", NUM)
        put(gr, r + 3, c, f"={cl}{r+2}/{R(co,'NOPAT',y)}", PCT)
        put(gr, r + 4, c, f"={R(co,'NOPAT',y)}/{R(co,'IC',y-1)}", PCT)
        put(gr, r + 5, c, f"={cl}{r+3}*{cl}{r+4}", PCT, F_B)
        put(gr, r + 6, c, f"=1-{D(co,'DividendsPaid',y)}/{D(co,'NetIncome',y)}", PCT)
        put(gr, r + 7, c, f"={D(co,'NetIncome',y)}/{avg(co,'Equity',y)}", PCT)
        put(gr, r + 8, c, f"={cl}{r+6}*{cl}{r+7}", PCT, F_B)
        put(gr, r + 9, c, f"={R(co,'NOPAT',y)}-{W[co]['WACC']}*{R(co,'IC',y-1)}", NUM, F_B, FILL_KEY)
        put(gr, r + 10, c, f"={cl}{r+4}-{W[co]['WACC']}", PCT)
    GR[co] = {"sust": r + 8, "fund": r + 5, "roe": r + 7}
    note(gr, r + 11, "Note: EVA uses today's WACC for all years (simplification). Negative/erratic reinvestment shows why historical fundamentals are noisy for developers.")
    r += 14

wb._ctx = dict(TARGETS=TARGETS, NAMES=NAMES, D=D, R=R, W=W, PX=PX, YC=YC)

# =====================================================================================
# 10. DCF — 10-year FCFF with fade, sales-to-capital reinvestment, beta → 1 in stable phase (Module 7)
# =====================================================================================
ASSUME = {
    "DLF": dict(g=[-0.15, 0.55, 0.45, 0.20, 0.10], m=0.40, s2c=2.0,
                why="H1 FY27 revenue fell 37% y/y, so FY27 is cut to −15%. Luxury launches sold FY24–26 (Gurugram: Privana, Dahlias, Arbour) are recognised on completion (Ind AS 115) in FY28–30, so "
                    "recognised revenue catches up with sales (customer advances = 2.9x revenue); margin moves from ~21% core to 40% as high-ticket "
                    "Gurugram projects dominate. Inventory/land already sits on the balance sheet and customer advances fund construction, "
                    "so incremental capital per rupee of revenue is low (S/C 2.0)."),
    "GPL": dict(g=[0.60, 0.50, 0.40, 0.25, 0.15], m=0.22, s2c=2.0,
                why="Sales are recognised with a 3–4 year lag (customer advances = 7.8x FY26 revenue), so revenue converges toward the sales run-rate. Core margin is "
                    "negative today because marketing/overheads hit P&L before project revenue (Ind AS 115 timing) and interest is capitalised "
                    "into inventory; it normalises to ~22%. Rs 57.8k cr of inventory already funded = low incremental capital (S/C 2.0)."),
    "PML": dict(g=[0.15, 0.14, 0.12, 0.10, 0.08], m=0.57, s2c=0.50,
                why="Rental annuity: ramp-up of malls opened FY24–25 (Mall of Asia Bengaluru, Millennium Pune, Palladium Ahmedabad), new "
                    "malls already in CWIP (Rs 4.0k cr), rent escalations and consumption growth. Margin already ~55%. Malls are capital-heavy: "
                    "Rs 2 of capital per Re 1 of new revenue (S/C 0.5)."),
}
N = 10
YRS = [f"FY{27+i}E" for i in range(N)]
DCF = {}
for co in TARGETS:
    a = ASSUME[co]
    ws = sheet(f"DCF_{co}", f"{NAMES[co]} — Free cash flow to firm (FCFF) DCF: 10-year two-phase model",
               "Module 7 — intrinsic valuation. Growth fades to stable; reinvestment = ΔRevenue ÷ sales-to-capital; beta → 1 in stable phase (TB2 Ch-6)",
               [44, 12, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11])
    put(ws, 4, 1, "Assumptions (blue = judgement inputs)", font=F_B)
    lab = ["Revenue growth FY27–FY31 (then fades linearly to terminal g)", "Target core EBIT margin (reached FY31, held)",
           "Sales-to-capital ratio", "Tax rate", "WACC — high-growth phase (FY27–FY31)", "Terminal growth",
           "Terminal RONIC", "Stable-phase beta", "Stable cost of equity = Rf + 1.0 × ERP", "Stable WACC (same D/V, same Kd)"]
    for i, t in enumerate(lab):
        put(ws, 5 + i, 1, t)
    for j, g in enumerate(a["g"]):
        put(ws, 5, 3 + j, g, PCT, F_IN, FILL_IN)
    put(ws, 6, 2, a["m"], PCT, F_IN, FILL_IN); put(ws, 7, 2, a["s2c"], NUM2, F_IN, FILL_IN)
    put(ws, 8, 2, "=Tax", PCT); put(ws, 9, 2, f"={W[co]['WACC']}", PCT, F_B); put(ws, 10, 2, "=gT", PCT)
    put(ws, 11, 2, "=RONIC", PCT); put(ws, 12, 2, 1.0, NUM2, F_IN, FILL_IN); put(ws, 13, 2, "=Rf+B12*ERP", PCT)
    ci = list(TARGETS).index(co); wcol = L(2 + ci)
    put(ws, 14, 2, f"=WACC!{wcol}22*B13+WACC!{wcol}23*WACC!{wcol}19", PCT, F_B)
    put(ws, 15, 1, "Rationale: " + a["why"], font=F_NOTE)
    ws.merge_cells("A15:M16"); ws["A15"].alignment = Alignment(wrap_text=True, vertical="top"); ws.row_dimensions[15].height = 34
    ws.row_dimensions[16].height = 20
    H = 18
    hdr(ws, H, ["Projection (Rs crore)", "FY26A"] + YRS + ["Terminal"])
    rows = ["Revenue", "Growth", "Margin weight (→ target by yr 5)", "Core EBIT margin", "Core EBIT", "NOPAT",
            "Reinvestment = ΔRevenue ÷ S-to-C", "FCFF", "Invested capital (end)", "ROIC on opening capital",
            "WACC for the year", "Discount factor (mid-year)", "PV of FCFF", "Discount factor (year-end)"]
    RW = {k: H + 1 + i for i, k in enumerate(rows)}
    for k, rr in RW.items():
        put(ws, rr, 1, k, font=F_B if k in ("FCFF", "PV of FCFF", "NOPAT") else F_N)
    b = "B"
    put(ws, RW["Revenue"], 2, f"={D(co,'Revenue',2026)}", NUM)
    put(ws, RW["Core EBIT"], 2, f"={R(co,'CoreEBIT',2026)}", NUM)
    put(ws, RW["Core EBIT margin"], 2, f"=B{RW['Core EBIT']}/B{RW['Revenue']}", PCT)
    put(ws, RW["NOPAT"], 2, f"=B{RW['Core EBIT']}*(1-$B$8)", NUM)
    put(ws, RW["Invested capital (end)"], 2, f"={R(co,'IC',2026)}", NUM)
    for t in range(1, N + 1):
        c, p = L(2 + t), L(1 + t)
        g5 = f"{L(2+min(t,5))}$5"
        if t <= 5:
            gf = f"=$" + L(2 + t) + "$5"
        else:
            gf = f"=$G$5+($B$10-$G$5)*{t-5}/5"
        put(ws, RW["Growth"], 2 + t, gf, PCT)
        put(ws, RW["Revenue"], 2 + t, f"={p}{RW['Revenue']}*(1+{c}{RW['Growth']})", NUM)
        put(ws, RW["Margin weight (→ target by yr 5)"], 2 + t, min(t, 5) / 5, "0.00")
        mw = f"{c}{RW['Margin weight (→ target by yr 5)']}"
        put(ws, RW["Core EBIT margin"], 2 + t, f"=$B${RW['Core EBIT margin']}*(1-{mw})+$B$6*{mw}", PCT)
        put(ws, RW["Core EBIT"], 2 + t, f"={c}{RW['Revenue']}*{c}{RW['Core EBIT margin']}", NUM)
        put(ws, RW["NOPAT"], 2 + t, f"={c}{RW['Core EBIT']}*(1-$B$8)", NUM, F_B)
        put(ws, RW["Reinvestment = ΔRevenue ÷ S-to-C"], 2 + t, f"=({c}{RW['Revenue']}-{p}{RW['Revenue']})/$B$7", NUM)
        put(ws, RW["FCFF"], 2 + t, f"={c}{RW['NOPAT']}-{c}{RW['Reinvestment = ΔRevenue ÷ S-to-C']}", NUM, F_B, FILL_KEY)
        put(ws, RW["Invested capital (end)"], 2 + t, f"={p}{RW['Invested capital (end)']}+{c}{RW['Reinvestment = ΔRevenue ÷ S-to-C']}", NUM)
        put(ws, RW["ROIC on opening capital"], 2 + t, f"={c}{RW['NOPAT']}/{p}{RW['Invested capital (end)']}", PCT)
        wf = "=$B$9" if t <= 5 else f"=$B$9+($B$14-$B$9)*{t-5}/5"
        put(ws, RW["WACC for the year"], 2 + t, wf, PCT)
        wr = RW["WACC for the year"]
        if t == 1:
            put(ws, RW["Discount factor (year-end)"], 2 + t, f"=1/(1+{c}{wr})", "0.0000")
            put(ws, RW["Discount factor (mid-year)"], 2 + t, f"=1/(1+{c}{wr})^(1-0.5*MidYr)", "0.0000")
        else:
            put(ws, RW["Discount factor (year-end)"], 2 + t, f"={p}{RW['Discount factor (year-end)']}/(1+{c}{wr})", "0.0000")
            put(ws, RW["Discount factor (mid-year)"], 2 + t, f"={p}{RW['Discount factor (year-end)']}/(1+{c}{wr})^(1-0.5*MidYr)", "0.0000")
        put(ws, RW["PV of FCFF"], 2 + t, f"={c}{RW['FCFF']}*{c}{RW['Discount factor (mid-year)']}", NUM, F_B)
    T = L(3 + N)   # terminal column (M)
    E10 = L(2 + N)  # year-10 column (L)
    put(ws, RW["Revenue"], 3 + N, f"={E10}{RW['Revenue']}*(1+$B$10)", NUM)
    put(ws, RW["Growth"], 3 + N, "=$B$10", PCT)
    put(ws, RW["Core EBIT margin"], 3 + N, "=$B$6", PCT)
    put(ws, RW["Core EBIT"], 3 + N, f"={T}{RW['Revenue']}*{T}{RW['Core EBIT margin']}", NUM)
    put(ws, RW["NOPAT"], 3 + N, f"={T}{RW['Core EBIT']}*(1-$B$8)", NUM, F_B)
    put(ws, RW["Reinvestment = ΔRevenue ÷ S-to-C"], 3 + N, f"={T}{RW['NOPAT']}*$B$10/$B$11", NUM)
    put(ws, RW["FCFF"], 3 + N, f"={T}{RW['NOPAT']}-{T}{RW['Reinvestment = ΔRevenue ÷ S-to-C']}", NUM, F_B, FILL_KEY)
    put(ws, RW["WACC for the year"], 3 + N, "=$B$14", PCT)
    note(ws, RW["Discount factor (year-end)"] + 1, "Terminal reinvestment = g ÷ RONIC × NOPAT, so stable growth is funded. Discount factors compound year-specific WACCs.")
    rr = RW["Discount factor (year-end)"]
    rngF, rngDF = f"C{RW['FCFF']}:{E10}{RW['FCFF']}", f"C{RW['Discount factor (mid-year)']}:{E10}{RW['Discount factor (mid-year)']}"
    # bridge
    B0 = rr + 3
    put(ws, B0, 1, "Valuation bridge", font=F_B)
    bridge = [
        ("PV of FCFF FY27–FY36", f"=SUM(C{RW['PV of FCFF']}:{E10}{RW['PV of FCFF']})", NUM),
        ("Terminal value at FY36 = FCFF(T) ÷ (stable WACC − g)", f"={T}{RW['FCFF']}/($B$14-$B$10)", NUM),
        ("PV of terminal value", f"=B{B0+2}*{E10}{RW['Discount factor (year-end)']}", NUM),
        ("Value of operating assets", f"=B{B0+1}+B{B0+3}", NUM),
        ("Terminal value as % of operating value", f"=B{B0+3}/B{B0+4}", PCT),
        ("Add: cash & liquid investments (FY26)", f"={R(co,'Liquid',2026)}", NUM),
        ("Add: JV / associate investments", None, NUM),
        ("Less: total debt incl. leases", f"=-{R(co,'Debt',2026)}", NUM),
        ("Firm value to all capital providers", f"=B{B0+4}+B{B0+6}+B{B0+7}+B{B0+8}", NUM),
        ("Minority share of PAT FY26", f"=MAX(0,1-{D(co,'NetIncome',2026)}/{D(co,'NetIncomeInclMI',2026)})", PCT),
        ("Less: minority interest (proportional)", f"=-B{B0+9}*B{B0+10}", NUM),
        ("Equity value to owners", f"=B{B0+9}+B{B0+11}", NUM),
        ("Shares outstanding (crore)", f"={D(co,'Shares',2026)}", NUM2),
        ("Intrinsic value per share (Rs)", f"=B{B0+12}/B{B0+13}", NUM2),
        ("Current market price (Rs)", f"={PX[co][3]}", NUM2),
        ("Upside / (downside)", f"=B{B0+14}/B{B0+15}-1", PCT),
        ("Verdict (±15% band)", f'=IF(B{B0+16}>0.15,"UNDERVALUED",IF(B{B0+16}<-0.15,"OVERVALUED","FAIRLY VALUED"))', None),
    ]
    for i, (lb, f, fmt) in enumerate(bridge):
        r_ = B0 + 1 + i
        k = lb.startswith(("Value of", "Equity value", "Intrinsic", "Verdict"))
        put(ws, r_, 1, lb, font=F_B if k else F_N)
        if f:
            put(ws, r_, 2, f, fmt, F_B if k else F_N, FILL_KEY if lb.startswith(("Intrinsic", "Verdict")) else None)
    JVr = B0 + 7
    if co == "DLF":
        put(ws, JVr, 4, "DCCDL stake (DLF 66.66%, GIC 33.34%; jointly controlled rental JV, equity-accounted) — capitalised earnings", font=F_B)
        put(ws, JVr + 1, 4, "Share of JV PAT FY26"); put(ws, JVr + 1, 8, f"={R(co,'JV',2026)}", NUM)
        put(ws, JVr + 2, 4, "Value = JV PAT × (1+g) ÷ (Ke − g)"); put(ws, JVr + 2, 8, f"=H{JVr+1}*(1+gT)/({W[co]['Ke']}-gT)", NUM, F_B)
        put(ws, JVr + 3, 4, "Book value of JV investment (cross-check)"); put(ws, JVr + 3, 8, f"={R(co,'EqInv',2026)}", NUM)
        put(ws, JVr, 2, f"=H{JVr+2}", NUM)
    else:
        put(ws, JVr, 2, f"={R(co,'EqInv',2026)}", NUM); note(ws, JVr, "at book value", 3)
    NONOP = f"($B${B0+6}+$B${B0+7}+$B${B0+8})"
    MI, SH = f"$B${B0+10}", f"$B${B0+13}"
    # helper rows for closed-form sensitivities
    Hh = B0 + 20
    put(ws, Hh, 1, "Helper rows for live sensitivities / reverse DCF", font=F_NOTE)
    put(ws, Hh + 1, 1, "ΔRevenue", font=F_NOTE); put(ws, Hh + 2, 1, "Revenue × mid-year DF", font=F_NOTE)
    for t in range(1, N + 1):
        c, p = L(2 + t), L(1 + t)
        put(ws, Hh + 1, 2 + t, f"={c}{RW['Revenue']}-{p}{RW['Revenue']}", NUM)
        put(ws, Hh + 2, 2 + t, f"={c}{RW['Revenue']}*{c}{RW['Discount factor (mid-year)']}", NUM)
    put(ws, Hh + 3, 1, "WACC lens B (fades to same stable WACC)", font=F_NOTE)
    put(ws, Hh + 4, 1, "Year-end DF lens B", font=F_NOTE); put(ws, Hh + 5, 1, "Mid-year DF lens B", font=F_NOTE)
    for t in range(1, N + 1):
        c, p = L(2 + t), L(1 + t)
        put(ws, Hh + 3, 2 + t, f"=WACC!{wcol}31" if t <= 5 else f"=WACC!{wcol}31+($B$14-WACC!{wcol}31)*{t-5}/5", PCT)
        put(ws, Hh + 4, 2 + t, f"=1/(1+{c}{Hh+3})" if t == 1 else f"={p}{Hh+4}/(1+{c}{Hh+3})", "0.0000")
        put(ws, Hh + 5, 2 + t, f"=1/(1+{c}{Hh+3})^(1-0.5*MidYr)" if t == 1 else f"={p}{Hh+4}/(1+{c}{Hh+3})^(1-0.5*MidYr)", "0.0000")
    put(ws, Hh + 7, 1, "Benchmark: naive linear trend of FY23–26 revenue (Excel FORECAST)", font=F_NOTE)
    for t in range(1, N + 1):
        put(ws, Hh + 7, 2 + t, f"=FORECAST({2026+t},{D(co,'Revenue',2023)}:{D(co,'Revenue',2026)},{{2023,2024,2025,2026}})", NUM)
    put(ws, Hh + 8, 1, "Our forecast ÷ naive trend (FY31)", font=F_NOTE); put(ws, Hh + 8, 7, f"=G{RW['Revenue']}/G{Hh+7}", NUM2)
    rowsW = f"C{RW['Margin weight (→ target by yr 5)']}:{E10}{RW['Margin weight (→ target by yr 5)']}"
    revDF = f"C{Hh+2}:{E10}{Hh+2}"
    dRev = f"C{Hh+1}:{E10}{Hh+1}"
    base_m = f"$B${RW['Core EBIT margin']}"
    DF10 = f"${E10}${RW['Discount factor (year-end)']}"
    REV10 = f"${E10}${RW['Revenue']}"

    def value_formula(m, s2c, wshift="0", g="$B$10"):
        """closed-form value/share for target margin m, S/C, WACC shift, terminal g"""
        if wshift == "0":
            pv_nopat = f"(1-$B$8)*({base_m}*SUMPRODUCT({revDF},1-{rowsW})+{m}*SUMPRODUCT({revDF},{rowsW}))"
            pv_re = f"SUMPRODUCT({dRev},{rngDF})/{s2c}"
            tv = f"{REV10}*(1+{g})*{m}*(1-$B$8)*(1-{g}/$B$11)/($B$14-{g})*{DF10}"
        else:
            # explicit compounding with shifted WACC each year
            dfs, terms = [], []
            for t in range(1, N + 1):
                c = L(2 + t)
                prev = "*".join(f"(1+{L(2+k)}${RW['WACC for the year']}+{wshift})" for k in range(1, t))
                cur = f"(1+{c}${RW['WACC for the year']}+{wshift})^(1-0.5*MidYr)"
                dfs.append(f"1/({(prev + '*') if prev else ''}{cur})")
                terms.append(f"{c}${RW['FCFF']}*{dfs[-1]}")
            endprod = "*".join(f"(1+{L(2+k)}${RW['WACC for the year']}+{wshift})" for k in range(1, N + 1))
            pv_nopat = "(" + "+".join(terms) + ")"
            pv_re = "0"
            tv = f"{REV10}*(1+{g})*$B$6*(1-$B$8)*(1-{g}/$B$11)/($B$14+{wshift}-{g})/({endprod})"
        return f"=(({pv_nopat}-{pv_re}+{tv}+{NONOP})*(1-{MI}))/{SH}"

    # grid 1: WACC shift x g
    put(ws, 4, 5, "Sensitivity A — value/share (Rs): WACC shift (rows) × terminal g (cols)", font=F_B)
    gsh, wsh = [-0.01, -0.005, 0, 0.005, 0.01], [-0.02, -0.01, 0, 0.01, 0.02]
    for j, dg in enumerate(gsh):
        put(ws, 5, 15 + j, f"=$B$10+({dg})", PCT, F_B, FILL_SUB)
    put(ws, 5, 14, "ΔWACC \\ g", font=F_NOTE)
    for i, dw in enumerate(wsh):
        r_ = 6 + i
        put(ws, r_, 14, dw, "+0.0%;-0.0%;0.0%", F_B, FILL_SUB)
        for j in range(5):
            put(ws, r_, 15 + j, value_formula("$B$6", "$B$7", f"$N{r_}", f"{L(15+j)}$5"), NUM,
                F_B if (i == 2 and j == 2) else F_N, FILL_KEY if (i == 2 and j == 2) else None)
    put(ws, 11, 14, "min"); put(ws, 11, 15, "=MIN(O6:S10)", NUM); put(ws, 12, 14, "max"); put(ws, 12, 15, "=MAX(O6:S10)", NUM)
    # grid 2: margin x S/C
    put(ws, 4, 21, "Sensitivity B — value/share: target margin (rows) × sales-to-capital (cols)", font=F_B)
    ms, ss = [-0.10, -0.05, 0, 0.05, 0.10], [0.5, 0.75, 1.0, 1.25, 1.5]
    for j, s_ in enumerate(ss):
        put(ws, 5, 22 + j, f"=$B$7*{s_}", NUM2, F_B, FILL_SUB)
    for i, dm in enumerate(ms):
        r_ = 6 + i
        put(ws, r_, 21, f"=$B$6+({dm})", PCT, F_B, FILL_SUB)
        for j in range(5):
            put(ws, r_, 22 + j, value_formula(f"$U{r_}", f"{L(22+j)}$5"), NUM,
                F_B if (i == 2 and j == 2) else F_N, FILL_KEY if (i == 2 and j == 2) else None)
    for cc in range(14, 27):
        ws.column_dimensions[L(cc)].width = 10
    ws.column_dimensions["U"].width = 10
    # reverse DCF (exact, linear in target margin)
    RV0 = 14
    put(ws, RV0, 21, "Reverse DCF — what the market price implies", font=F_B)
    put(ws, RV0 + 1, 21, "Firm value implied by price"); put(ws, RV0 + 1, 25, f"=$B${B0+15}*{SH}/(1-{MI})-{NONOP}", NUM)
    put(ws, RV0 + 2, 21, "PV of reinvestment (at base S/C)"); put(ws, RV0 + 2, 25, f"=SUMPRODUCT({dRev},{rngDF})/$B$7", NUM)
    put(ws, RV0 + 3, 21, "PV of NOPAT from base margin"); put(ws, RV0 + 3, 25, f"=(1-$B$8)*{base_m}*SUMPRODUCT({revDF},1-{rowsW})", NUM)
    put(ws, RV0 + 4, 21, "PV per 1.0 of target margin"); put(ws, RV0 + 4, 25,
        f"=(1-$B$8)*SUMPRODUCT({revDF},{rowsW})+{REV10}*(1+$B$10)*(1-$B$8)*(1-$B$10/$B$11)/($B$14-$B$10)*{DF10}", NUM)
    put(ws, RV0 + 5, 21, "Market-implied target EBIT margin", font=F_B)
    put(ws, RV0 + 5, 25, f"=(Y{RV0+1}+Y{RV0+2}-Y{RV0+3})/Y{RV0+4}", PCT, F_B, FILL_KEY)
    put(ws, RV0 + 6, 21, "vs our assumed target margin"); put(ws, RV0 + 6, 25, "=$B$6", PCT)
    put(ws, RV0 + 7, 21, "Check: value at implied margin = price"); put(ws, RV0 + 7, 25, value_formula(f"Y{RV0+5}", "$B$7"), NUM2)
    note(ws, RV0 + 8, "Exact solution (value is linear in the target margin) — same answer as Excel Goal Seek.", 21)
    imp = json.loads((ROOT / "data/processed/implied.json").read_text()) if (ROOT / "data/processed/implied.json").exists() else {}
    if co in imp:
        put(ws, RV0 + 10, 21, "Market-implied cost of capital (all years shifted)", font=F_B)
        put(ws, RV0 + 11, 21, "ΔWACC that makes value = price"); put(ws, RV0 + 11, 25, imp[co]["dw"], "+0.00%;-0.00%", F_IN, FILL_IN)
        put(ws, RV0 + 12, 21, "Implied high-growth WACC"); put(ws, RV0 + 12, 25, f"=$B$9+Y{RV0+11}", PCT, F_B, FILL_KEY)
        put(ws, RV0 + 13, 21, "Implied stable WACC"); put(ws, RV0 + 13, 25, f"=$B$14+Y{RV0+11}", PCT)
        put(ws, RV0 + 14, 21, "Check: value at implied WACC"); put(ws, RV0 + 14, 25, value_formula("$B$6", "$B$7", f"$Y${RV0+11}", "$B$10"), NUM2)
        note(ws, RV0 + 15, "ΔWACC solved numerically by bisection (scripts/implied_wacc.py); reproduce with Goal Seek on Y25 → set Y28 = price.", 21)
    LB = RV0 + 18
    put(ws, LB, 21, "Lens B — value at Damodaran-industry WACC", font=F_B)
    put(ws, LB + 1, 21, "WACC lens B (high-growth phase)"); put(ws, LB + 1, 25, f"=WACC!{wcol}31", PCT)
    put(ws, LB + 2, 21, "Stable-phase WACC (β → 1, unchanged)"); put(ws, LB + 2, 25, "=$B$14", PCT)
    put(ws, LB + 3, 21, "Value per share — lens B (₹)", font=F_B)
    put(ws, LB + 3, 25, f"=((SUMPRODUCT({rngF},C{Hh+5}:{E10}{Hh+5})+$B${B0+2}*{E10}{Hh+4}+{NONOP})*(1-{MI}))/{SH}", NUM2, F_B, FILL_KEY)
    put(ws, LB + 4, 21, "Upside vs price — lens B"); put(ws, LB + 4, 25, f"=Y{LB+3}/$B${B0+15}-1", PCT)
    DCF[co] = {"vpsB": f"DCF_{co}!$Y${LB+3}", "vps": f"DCF_{co}!$B${B0+14}", "min": f"DCF_{co}!$O$11", "max": f"DCF_{co}!$O$12",
               "imp": f"DCF_{co}!$Y${RV0+5}", "tvpct": f"DCF_{co}!$B${B0+5}"}
    ws.freeze_panes = "B19"

# =====================================================================================
# 11. DDM (Module 7)
# =====================================================================================
dd = sheet("DDM", "Dividend discount model — two-stage (Gordon terminal)",
           "Module 7 — DDM. Value = Σ DPS_t/(1+Ke)^t + [DPS_(n+1)/(Ke−g)]/(1+Ke)^n ; stable payout = 1 − g/ROE",
           [44, 14, 14, 14, 50])
hdr(dd, 4, ["Item", "DLF", "Godrej Prop.", "Phoenix Mills", "Note"])
ddm_in = {"DLF": (0.15, 0.15), "GPL": (0.15, 0.15), "PML": (0.12, 0.15)}
def _ttm_dps(tk):
    d = pd.read_csv(RAW / tk / "dividends.csv", index_col=0); d.index = pd.to_datetime(d.index, utc=True)
    end = pd.Timestamp(str(last_price(tk)[0]), tz="UTC")
    return round(float(d.loc[d.index > end - pd.Timedelta(days=365)].iloc[:, 0].sum()), 2)
TTMDPS = {co: _ttm_dps(tk) for co, tk in TARGETS.items()}
ddrows = [
    ("EPS FY26 (Rs)", lambda co, c: f"={D(co,'NetIncome',2026)}/{D(co,'Shares',2026)}", NUM2, ""),
    ("DPS — declared in last 12 months (₹)", lambda co, c: TTMDPS[co], NUM2, "Yahoo dividend history (ex-dates); Godrej resumed with ₹10 in FY27, first since FY16"),
    ("Payout (TTM DPS ÷ FY26 EPS)", lambda co, c: f"=IFERROR({c}6/{c}5,0)", PCT, ""),
    ("Cost of equity", lambda co, c: f"={W[co]['Ke']}", PCT, "From WACC sheet"),
    ("Stage-1 EPS growth (5 yrs)", lambda co, c: ddm_in[co][0], PCT, "Judgement: tied to DCF revenue path, below it as payout rises"),
    ("Stable growth", lambda co, c: "=gT", PCT, ""),
    ("Stable ROE", lambda co, c: ddm_in[co][1], PCT, "Converges toward Ke + small excess return"),
    ("Stable payout = 1 − g / ROE", lambda co, c: f"=1-{c}10/{c}11", PCT, "Fundamental payout consistent with growth"),
    ("PV of stage-1 dividends", lambda co, c: f"=SUMPRODUCT({c}5*(1+{c}9)^{{1,2,3,4,5}}*({c}7+({c}12-{c}7)*{{1,2,3,4,5}}/5)/(1+{c}8)^{{1,2,3,4,5}})", NUM2, "EPS grows at stage-1 rate; payout glides linearly to stable payout"),
    ("EPS in year 6", lambda co, c: f"={c}5*(1+{c}9)^5*(1+{c}10)", NUM2, ""),
    ("Terminal price at year 5 = EPS6 × stable payout / (Ke − g)", lambda co, c: f"={c}14*{c}12/({c}8-{c}10)", NUM2, ""),
    ("PV of terminal price", lambda co, c: f"={c}15/(1+{c}8)^5", NUM2, ""),
    ("DDM value per share (Rs)", lambda co, c: f'=IF({c}6=0,"n.a. — no dividend",{c}13+{c}16)', NUM2, ""),
    ("Market price (Rs)", lambda co, c: f"={PX[co][3]}", NUM2, ""),
    ("DDM / price", lambda co, c: f'=IFERROR({c}17/{c}18,"n.a.")', PCT, ""),
]
for i, (lb, fn, fmt, nt) in enumerate(ddrows):
    rr = 5 + i
    put(dd, rr, 1, lb, font=F_B if "value per share" in lb else F_N)
    for j, co in enumerate(TARGETS):
        v = fn(co, L(2 + j))
        put(dd, rr, 2 + j, v, fmt, F_IN if isinstance(v, float) else (F_B if "value per share" in lb else F_N),
            FILL_IN if isinstance(v, float) else (FILL_KEY if "value per share" in lb else None))
    put(dd, rr, 5, nt, font=F_NOTE)
note(dd, 21, "All three retain most earnings (Godrej paid nothing from FY17 to FY26), so DDM understates value — the gap vs FCFF/relative value is")
note(dd, 22, "itself evidence that value sits in reinvestment, not current payouts (a limitation of DDM, CLO3).")
put(dd, 24, 1, "Dividend history — ₹ per share by fiscal year (ex-date basis, split-adjusted)", font=F_B)
_dh = {}
for co, tk in TARGETS.items():
    d_ = pd.read_csv(RAW / tk / "dividends.csv", index_col=0); d_.index = pd.to_datetime(d_.index, utc=True)
    _dh[co] = d_.groupby(d_.index.year + (d_.index.month > 3)).sum().iloc[:, 0]
_yrs = list(range(2008, 2028))
hdr(dd, 25, ["Fiscal year", "DLF", "Godrej Prop.", "Phoenix Mills"])
for i, y in enumerate(_yrs):
    put(dd, 26 + i, 1, f"FY{str(y)[2:]}" + (" (to date)" if y == 2027 else ""))
    for j, co in enumerate(TARGETS):
        v = _dh[co].get(y, 0.0)
        put(dd, 26 + i, 2 + j, round(float(v), 2), NUM2, F_IN)
_l = 26 + len(_yrs) - 2   # FY26 row
put(dd, _l + 3, 1, "DPS CAGR FY16→FY26 (where both > 0)", font=F_B)
for j, co in enumerate(TARGETS):
    c = L(2 + j)
    put(dd, _l + 3, 2 + j, f'=IF(AND({c}{26+8}>0,{c}{_l}>0),({c}{_l}/{c}{26+8})^(1/10)-1,"n.m.")', PCT, F_B)
DDM = {co: f"DDM!${L(2+j)}$17" for j, co in enumerate(TARGETS)}

# =====================================================================================
# 12. RELATIVE VALUATION (Module 8)
# =====================================================================================
rv = sheet("RelVal", "Relative valuation — four-step process with listed real-estate comparables",
           "Module 8 — (1) define comparables (2) standardise multiples (3) examine distribution (4) control for differences (P/B vs ROE regression)",
           [24, 11, 11, 12, 12, 12, 11, 11, 11, 11, 10, 10, 10, 10, 10, 10, 10])
cols = ["Company", "Price (Rs)", "Shares (cr)", "Market cap", "Net debt", "EV", "PAT FY26", "Equity FY26",
        "Revenue FY26", "EBITDA FY26", "EPS CAGR 3y", "ROE FY26", "P/E", "P/B", "P/S", "EV/EBITDA", "PEG"]
hdr(rv, 4, cols)
RVR = {}
order = list(TARGETS) + list(PEERS)
for i, co in enumerate(order):
    rr = 5 + i if i < 3 else 6 + i
    RVR[co] = rr
    put(rv, rr, 1, NAMES[co], font=F_B if co in TARGETS else F_N)
    put(rv, rr, 2, f"={PX[co][3]}", NUM2)
    put(rv, rr, 3, f"={D(co,'Shares',2026)}", NUM2)
    put(rv, rr, 4, f"=B{rr}*C{rr}", NUM)
    put(rv, rr, 5, f"={D(co,'TotalDebt',2026)}-{D(co,'Cash',2026)}-{D(co,'STInvestments',2026)}-{D(co,'LTFinInvestments',2026)}", NUM)
    put(rv, rr, 6, f"=D{rr}+E{rr}", NUM)
    put(rv, rr, 7, f"={D(co,'NetIncome',2026)}", NUM)
    put(rv, rr, 8, f"={D(co,'Equity',2026)}", NUM)
    put(rv, rr, 9, f"={D(co,'Revenue',2026)}", NUM)
    put(rv, rr, 10, f"={D(co,'PBT',2026)}+{D(co,'InterestExpense',2026)}+{D(co,'DandA',2026)}", NUM)
    put(rv, rr, 11, f"=IF(OR({D(co,'NetIncome',2023)}<=0,{D(co,'NetIncome',2026)}<=0),\"n.m.\",(({D(co,'NetIncome',2026)}/{D(co,'Shares',2026)})/({D(co,'NetIncome',2023)}/{D(co,'Shares',2023)}))^(1/3)-1)", PCT)
    put(rv, rr, 12, f"={D(co,'NetIncome',2026)}/{avg(co,'Equity',2026)}", PCT)
    put(rv, rr, 13, f'=IF(G{rr}<=0,"n.m.",D{rr}/G{rr})', X); put(rv, rr, 14, f"=D{rr}/H{rr}", X); put(rv, rr, 15, f"=D{rr}/I{rr}", X)
    put(rv, rr, 16, f'=IF(J{rr}<=0,"n.m.",F{rr}/J{rr})', X); put(rv, rr, 17, f'=IF(OR(ISTEXT(K{rr}),ISTEXT(M{rr})),"n.m.",IF(OR(K{rr}<=0,K{rr}>1),"n.m.",M{rr}/(K{rr}*100)))', NUM2)
put(rv, 8, 1, "Peers (comparable set)", font=F_B)
p0, p1 = 9, 8 + len(PEERS)
st = p1 + 2
stats = [("High", "MAX"), ("75th percentile", "P75"), ("Median", "MEDIAN"), ("Average", "AVERAGE"), ("25th percentile", "P25"), ("Low", "MIN")]
put(rv, st - 1, 1, "Distribution of peer multiples", font=F_B)
for i, (lb, fn) in enumerate(stats):
    rr = st + i
    put(rv, rr, 1, lb)
    for c in range(13, 18):
        cl = L(c)
        rng = f"{cl}{p0}:{cl}{p1}"
        f = {"P75": f"=PERCENTILE({rng},0.75)", "P25": f"=PERCENTILE({rng},0.25)"}.get(fn, f"={fn}({rng})")
        put(rv, rr, c, f, NUM2, F_B if lb == "Median" else F_N, FILL_KEY if lb == "Median" else None)
# implied values
iv = st + 8
put(rv, iv - 1, 1, "Implied value per share (Rs) at peer multiples", font=F_B)
hdr(rv, iv, ["Target / multiple", "P/E med", "P/E 25th", "P/E 75th", "P/B med", "P/B 25th", "P/B 75th", "EV/EBITDA med", "P/S med", "Regression P/B"])
REL = {}
for i, co in enumerate(TARGETS):
    rr = iv + 1 + i
    t = RVR[co]
    put(rv, rr, 1, NAMES[co], font=F_B)
    put(rv, rr, 2, f"=$M${st+2}*G{t}/C{t}", NUM); put(rv, rr, 3, f"=$M${st+4}*G{t}/C{t}", NUM); put(rv, rr, 4, f"=$M${st+1}*G{t}/C{t}", NUM)
    put(rv, rr, 5, f"=$N${st+2}*H{t}/C{t}", NUM); put(rv, rr, 6, f"=$N${st+4}*H{t}/C{t}", NUM); put(rv, rr, 7, f"=$N${st+1}*H{t}/C{t}", NUM)
    put(rv, rr, 8, f"=($P${st+2}*J{t}-E{t})/C{t}", NUM); put(rv, rr, 9, f"=$O${st+2}*I{t}/C{t}", NUM)
    put(rv, rr, 10, f"=($B${iv+7}+$B${iv+8}*L{t})*H{t}/C{t}", NUM, F_B)
    REL[co] = rr
# regression P/B on ROE across all 8
rg = iv + 6
put(rv, rg, 1, "Step 4 — control for differences: regress P/B on ROE across all 8 firms", font=F_B)
allrows = ",".join([])  # placeholder
put(rv, rg + 1, 1, "Intercept (a)"); put(rv, rg + 2, 1, "Slope on ROE (b)"); put(rv, rg + 3, 1, "R-squared")
# LibreOffice/Excel need contiguous ranges for SLOPE: build helper columns
put(rv, rg - 1 + 6, 1, "Helper: ROE / P/B (contiguous)", font=F_NOTE)
for i, co in enumerate(order):
    put(rv, rg + 6 + i, 1, NAMES[co], font=F_NOTE)
    put(rv, rg + 6 + i, 2, f"=L{RVR[co]}", PCT)
    put(rv, rg + 6 + i, 3, f"=N{RVR[co]}", NUM2)
h0, h1 = rg + 6, rg + 6 + len(order) - 1
put(rv, rg + 1, 2, f"=INTERCEPT(C{h0}:C{h1},B{h0}:B{h1})", NUM2)
put(rv, rg + 2, 2, f"=SLOPE(C{h0}:C{h1},B{h0}:B{h1})", NUM2)
put(rv, rg + 3, 2, f"=RSQ(C{h0}:C{h1},B{h0}:B{h1})", NUM2)
# fix references used in implied regression col (B iv+7, B iv+8) -> actual rows
for i, co in enumerate(TARGETS):
    rr = iv + 1 + i
    t = RVR[co]
    put(rv, rr, 10, f"=($B${rg+1}+$B${rg+2}*L{t})*H{t}/C{t}", NUM, F_B)
sc = ScatterChart(); sc.title = "P/B vs ROE — Indian listed developers (FY26)"; sc.style = 13; sc.height, sc.width = 8, 13
s_ = Series(Reference(rv, min_col=3, min_row=h0, max_row=h1), Reference(rv, min_col=2, min_row=h0, max_row=h1), title="Firms")
s_.marker.symbol = "circle"; s_.graphicalProperties.line.noFill = True; s_.trendline = None
sc.series.append(s_); sc.x_axis.title = "ROE"; sc.y_axis.title = "P/B"
rv.add_chart(sc, f"E{rg}")

exec(open(ROOT / "scripts" / "model_v2_sheets.py").read())

# =====================================================================================
# 13. SUMMARY / FOOTBALL FIELD
# =====================================================================================
sm = sheet("Summary", "Valuation summary and football field", "Modules 7–8 synthesis: triangulating intrinsic and relative value",
           [34, 13, 13, 13, 13, 13, 13])
r = 4
for co in TARGETS:
    sub(sm, r, NAMES[co], 6); r += 1
    hdr(sm, r, ["Method", "Low (Rs)", "High (Rs)", "Point (Rs)", "Bar base", "Bar length"]); r += 1
    rr0 = r
    rel = REL[co]
    NAMES2 = {"DLF": "DLF", "GPL": "Godrej Properties", "PML": "Phoenix Mills"}
    rowsm = [
        ("DCF (FCFF) — WACC±2% × g±1%", f"={DCF[co]['min']}", f"={DCF[co]['max']}", f"={DCF[co]['vps']}"),
        ("Relative — P/E (25th–75th pct)", f"=RelVal!C{rel}", f"=RelVal!D{rel}", f"=RelVal!B{rel}"),
        ("Relative — P/B (25th–75th pct)", f"=RelVal!F{rel}", f"=RelVal!G{rel}", f"=RelVal!E{rel}"),
        ("Relative — EV/EBITDA (median)", f"=RelVal!H{rel}", f"=RelVal!H{rel}", f"=RelVal!H{rel}"),
        ("Relative — P/B regressed on ROE", f"=RelVal!J{rel}", f"=RelVal!J{rel}", f"=RelVal!J{rel}"),
        ("DCF — lens B (industry β)", f"={DCF[co]['vpsB']}", f"={DCF[co]['vpsB']}", f"={DCF[co]['vpsB']}"),
        ("DCF — bear to bull scenarios", round(SC["scenarios"][co]["bear"], 1) if scf.exists() else 0, round(SC["scenarios"][co]["bull"], 1) if scf.exists() else 0, round(SC["scenarios"][co]["base"], 1) if scf.exists() else 0),
        ("Monte Carlo 5th–95th pct (lens A)", round(MC[co]["A"]["p5"], 1) if mcf.exists() else 0, round(MC[co]["A"]["p95"], 1) if mcf.exists() else 0, round(MC[co]["A"]["median"], 1) if mcf.exists() else 0),
        ("Residual income (lens A – lens B)", f"={RIR[co]['vpsA']}", f"={RIR[co]['vpsB']}", f"={RIR[co]['vpsA']}"),
        ("Practitioner NAV / embedded profit", f"={ {'DLF': NAVR['dlf_nav_ps'], 'GPL': NAVR['gpl_emb_ps'], 'PML': NAVR['pml_nav_ps']}[co] }", f"={ {'DLF': NAVR['dlf_nav_ps'], 'GPL': NAVR['gpl_emb_ps'], 'PML': NAVR['pml_nav_ps']}[co] }", f"={ {'DLF': NAVR['dlf_nav_ps'], 'GPL': NAVR['gpl_emb_ps'], 'PML': NAVR['pml_nav_ps']}[co] }"),
        ("Broker targets (low–high), median", f"=MIN(Broker_Views!C{BKR[NAMES2[co]][0]}:C{BKR[NAMES2[co]][1]})", f"=MAX(Broker_Views!C{BKR[NAMES2[co]][0]}:C{BKR[NAMES2[co]][1]})", f"={BKSUM[co]}"),
        ("DDM (two-stage)", f"=IFERROR({DDM[co]}*1,\"\")", f"=IFERROR({DDM[co]}*1,\"\")", f"=IFERROR({DDM[co]}*1,\"\")"),
        ("Market price", f"={PX[co][3]}", f"={PX[co][3]}", f"={PX[co][3]}"),
    ]
    if co == "PML":
        rowsm.insert(-1, ("Cap rate at mall-REIT yield", "=CapRates!D22", "=CapRates!D22", "=CapRates!D22"))
    for i, (lb, lo, hi, pt) in enumerate(rowsm):
        put(sm, r, 1, lb); put(sm, r, 2, lo, NUM); put(sm, r, 3, hi, NUM); put(sm, r, 4, pt, NUM, F_B)
        put(sm, r, 5, f"=IFERROR(MIN(B{r}:C{r})*1,0)", NUM); put(sm, r, 6, f"=IFERROR(MAX(ABS(C{r}-B{r}),MAX(B{r}:C{r})*0.015),0)", NUM)
        r += 1
    bc = BarChart(); bc.type = "bar"; bc.grouping = "stacked"; bc.overlap = 100
    bc.title = f"{NAMES[co]} — value per share (Rs)"; bc.height, bc.width = 7, 15
    base = Series(Reference(sm, min_col=5, min_row=rr0, max_row=r - 1), title="base")
    base.graphicalProperties.noFill = True; base.graphicalProperties.line.noFill = True
    bar = Series(Reference(sm, min_col=6, min_row=rr0, max_row=r - 1), title="range")
    bar.graphicalProperties.solidFill = ACC
    bc.series = [base, bar]; bc.set_categories(Reference(sm, min_col=1, min_row=rr0, max_row=r - 1))
    bc.legend = None
    sm.add_chart(bc, f"H{rr0 - 1}")
    r += 6

# =====================================================================================
# INDEX content
# =====================================================================================
idx_rows = [
    ("Inputs", "Module 6", "Risk-free rate (G-Sec less default spread), ERP + CRP, tax, terminal growth, rating table"),
    ("Data_*", "Module 1", "Standardised consolidated statements FY23–FY26 for 3 targets + 5 peers"),
    ("Recast", "Modules 3–4", "Operating vs financing vs JV split; NOPAT; restricted cash; capitalised interest; customer advances"),
    ("Ratios", "Module 5", "~38 ratios: growth, margins, ROE/ROA/ROIC/ROCE, CCC, liquidity, solvency, cash-flow quality, market"),
    ("DuPont", "Module 5", "3-step, 5-step (incl. JV burden), Palepu RNOA–leverage split, ROE change attribution"),
    ("AltmanZ", "Module 5 (+9)", "Z and Z'' distress scores"),
    ("Beta_Monthly / Beta_Weekly", "Module 6", "Regression beta, SE, t-stat, CI, R², Blume, Jensen's alpha"),
    ("BottomUp_Beta", "Module 6", "Peer unlevered betas → median → relevered (fundamental/bottom-up beta)"),
    ("WACC", "Module 6", "CAPM Ke; synthetic-rating Kd on cash interest; market weights"),
    ("Growth_EVA", "Modules 5 & 7", "Historical vs fundamental growth; EVA and EVA spread"),
    ("DCF_DLF / DCF_GPL / DCF_PML", "Module 7", "FCFF DCF, sales-to-capital reinvestment, 2 sensitivity grids, reverse DCF"),
    ("DDM", "Module 7", "Two-stage dividend discount model; applicability limits"),
    ("RelVal", "Module 8", "Four-step relative valuation: P/E, P/B, P/S, EV/EBITDA, PEG; P/B–ROE regression"),
    ("Summary", "Modules 7–8", "Football field triangulation"),
    ("Industry_Benchmark", "Modules 5–6", "Damodaran India industry data (156 developers) vs our firms"),
    ("Quarterly", "Module 5", "Five latest quarters incl. Q1–Q2 FY27; TTM P/E"),
    ("LongCycle / RollingBeta", "Modules 5–6", "Prices since 2007, live drawdowns, CAGR; rolling 36-month beta"),
    ("RateFactor / HistERP", "Module 6", "Two-factor model with ΔG-Sec (LINEST); historical ERP 2005–2026"),
    ("Housing / CapRates", "Real-estate specific", "BIS house-price cycle; Phoenix implied cap rate vs REIT yields"),
    ("ResidualIncome / Alt_Valuations", "Modules 7 (TB1)", "Abnormal earnings, justified P/B, EVA = DCF proof, FCFE, APV"),
    ("RealOption", "Module 7", "Land as a call option (illustrative Black–Scholes)"),
    ("Scenarios_Implied / MonteCarlo", "Module 7", "Bear/base/bull, implied perpetual growth & WACC, 10,000-draw simulation"),
    ("Operating_KPIs / Data_Check", "Cross-check", "Company-reported bookings, collections, rental KPIs; reconciliation of our dataset"),
    ("NAV_SOTP / Broker_Views", "Cross-check", "Practitioner NAV/SOTP and embedded-profit valuation; public broker targets"),
    ("Dimson_Beta / Macro_Cycle", "Module 6 / context", "Thin-trading-adjusted betas; rates, housing volumes, GDP outlook"),
    ("Concept_Map", "All", "Every course, textbook and prior-project concept → the sheet where it is applied"),
]
hdr(idx, 4, ["No.", "Sheet", "What it does", "Course module"])
for i, (s, m, d) in enumerate(idx_rows):
    put(idx, 5 + i, 1, i + 1); put(idx, 5 + i, 2, s, font=F_B); put(idx, 5 + i, 3, d); put(idx, 5 + i, 4, m)
note(idx, 31, "Colour code: blue font on cream = hard-coded input with source; black = formula; green fill = key output.")
note(idx, 32, "Data: Yahoo Finance consolidated statements & NSE prices; FRED/OECD (G-Sec); Damodaran Online (ERP, CRP, spreads).")

wb.active = wb.sheetnames.index("Index")
wb.calculation.fullCalcOnLoad = True
OUT.parent.mkdir(parents=True, exist_ok=True)
wb.save(OUT)
print("saved", OUT)

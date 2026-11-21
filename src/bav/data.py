"""Standardise Yahoo Finance statements into a tidy Rs-crore table per company/year."""
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW, PROC = ROOT / "data" / "raw", ROOT / "data" / "processed"
CR = 1e7  # rupees per crore

FIELDS = {
    # income statement
    "Revenue": ("income_stmt", ["Total Revenue"]),
    "COGS": ("income_stmt", ["Cost Of Revenue"]),
    "SGA": ("income_stmt", ["Selling General And Administration"]),
    "DandA": ("income_stmt", ["Reconciled Depreciation"]),
    "InterestExpense": ("income_stmt", ["Interest Expense"]),
    "InterestIncome": ("income_stmt", ["Interest Income"]),
    "SpecialItems": ("income_stmt", ["Special Income Charges"]),
    "PBT": ("income_stmt", ["Pretax Income"]),
    "Tax": ("income_stmt", ["Tax Provision"]),
    "NetIncomeInclMI": ("income_stmt", ["Net Income Including Noncontrolling Interests"]),
    "NetIncome": ("income_stmt", ["Net Income"]),
    # balance sheet
    "TotalAssets": ("balance_sheet", ["Total Assets"]),
    "CurrentAssets": ("balance_sheet", ["Current Assets"]),
    "CurrentLiabilities": ("balance_sheet", ["Current Liabilities"]),
    "Inventory": ("balance_sheet", ["Inventory"]),
    "Receivables": ("balance_sheet", ["Accounts Receivable"]),
    "Cash": ("balance_sheet", ["Cash And Cash Equivalents"]),
    "STInvestments": ("balance_sheet", ["Other Short Term Investments"]),
    "RestrictedCash": ("balance_sheet", ["Restricted Cash"]),
    "LTFinInvestments": ("balance_sheet", ["Investmentin Financial Assets"]),
    "EquityInvestments": ("balance_sheet", ["Long Term Equity Investment"]),
    "InvestmentProperty": ("balance_sheet", ["Investment Properties"]),
    "NetPPE": ("balance_sheet", ["Net PPE"]),
    "CWIP": ("balance_sheet", ["Construction In Progress"]),
    "TotalDebt": ("balance_sheet", ["Total Debt"]),
    "CurrentDebt": ("balance_sheet", ["Current Debt And Capital Lease Obligation"]),
    "Payables": ("balance_sheet", ["Payables"]),
    "Equity": ("balance_sheet", ["Stockholders Equity"]),
    "MinorityInterest": ("balance_sheet", ["Minority Interest"]),
    "RetainedEarnings": ("balance_sheet", ["Retained Earnings"]),
    "TotalLiabilities": ("balance_sheet", ["Total Liabilities Net Minority Interest"]),
    "NonCurrentLiabilities": ("balance_sheet", ["Total Non Current Liabilities Net Minority Interest"]),
    "Shares": ("balance_sheet", ["Ordinary Shares Number", "Share Issued"]),
    # cash flow
    "CFO": ("cashflow", ["Operating Cash Flow"]),
    "Capex": ("cashflow", ["Capital Expenditure", "Purchase Of PPE"]),
    "CFI": ("cashflow", ["Investing Cash Flow"]),
    "CFF": ("cashflow", ["Financing Cash Flow"]),
    "DividendsPaid": ("cashflow", ["Cash Dividends Paid"]),
    "InterestPaid": ("cashflow", ["Interest Paid Cff"]),
    "ChgInventory": ("cashflow", ["Change In Inventory"]),
}


def load(company: str, years=(2023, 2024, 2025, 2026)) -> pd.DataFrame:
    frames = {}
    for f in ["income_stmt", "balance_sheet", "cashflow"]:
        df = pd.read_csv(RAW / company / f"{f}.csv", index_col=0)
        df.columns = [pd.Timestamp(c).year for c in df.columns]
        frames[f] = df
    out = {}
    for field, (stmt, names) in FIELDS.items():
        df = frames[stmt]
        s = None
        for n in names:
            if n in df.index:
                s = df.loc[n] if s is None else s.fillna(df.loc[n])
        out[field] = s if s is not None else pd.Series(dtype=float)
    t = pd.DataFrame(out).T.reindex(columns=list(years))
    t = t.apply(pd.to_numeric, errors="coerce") / CR
    t = t.fillna(0.0)
    # Yahoo reports some signs inconsistently: make expenses/interest positive magnitudes
    t.loc["InterestExpense"] = t.loc["InterestExpense"].abs()
    t.loc["Capex"] = t.loc["Capex"].abs()
    t.loc["DividendsPaid"] = t.loc["DividendsPaid"].abs()
    t.loc["InterestPaid"] = t.loc["InterestPaid"].abs()
    return t


def fy_end_prices(company: str) -> pd.Series:
    px = pd.read_csv(RAW / company / "px_monthly.csv", index_col=0)
    px.index = pd.to_datetime(px.index, utc=True).tz_convert("Asia/Kolkata").tz_localize(None)
    m = px[px.index.month == 3]["Close"]
    m.index = m.index.year
    return m


def last_price(company: str):
    px = pd.read_csv(RAW / company / "px_daily.csv", index_col=0)
    px.index = pd.to_datetime(px.index, utc=True).tz_convert("Asia/Kolkata").tz_localize(None)
    c = px["Close"].dropna()
    return c.index[-1].date(), float(c.iloc[-1]), float(c.iloc[-126:].mean())


if __name__ == "__main__":
    PROC.mkdir(exist_ok=True, parents=True)
    for c in ["DLF", "GODREJPROP", "PHOENIXLTD", "OBEROIRLTY", "PRESTIGE", "BRIGADE", "SOBHA", "LODHA"]:
        t = load(c)
        t.loc["FYEndPrice"] = fy_end_prices(c).reindex(t.columns).values
        t.round(2).to_csv(PROC / f"{c}.csv")
        print(c, last_price(c), "shares(cr)", t.loc["Shares"].round(2).tolist())

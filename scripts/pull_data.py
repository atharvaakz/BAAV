"""Download raw financials and prices from Yahoo Finance into data/raw/."""
import json, time, pathlib
import yfinance as yf

RAW = pathlib.Path(__file__).resolve().parents[1] / "data" / "raw"
TICKERS = {
    "DLF": "DLF.NS", "GODREJPROP": "GODREJPROP.NS", "PHOENIXLTD": "PHOENIXLTD.NS",
    "OBEROIRLTY": "OBEROIRLTY.NS", "PRESTIGE": "PRESTIGE.NS", "BRIGADE": "BRIGADE.NS",
    "SOBHA": "SOBHA.NS", "LODHA": "LODHA.NS", "NIFTY50": "^NSEI", "NIFTYREALTY": "^CNXREALTY",
}

for name, tk in TICKERS.items():
    d = RAW / name
    d.mkdir(parents=True, exist_ok=True)
    T = yf.Ticker(tk)
    for attempt in range(3):
        try:
            T.history(period="10y", interval="1mo", auto_adjust=False).to_csv(d / "px_monthly.csv")
            T.history(period="5y", interval="1wk", auto_adjust=False).to_csv(d / "px_weekly.csv")
            T.history(period="2y", interval="1d", auto_adjust=False).to_csv(d / "px_daily.csv")
            if not tk.startswith("^"):
                for attr in ["income_stmt", "balance_sheet", "cashflow",
                             "quarterly_income_stmt", "quarterly_balance_sheet"]:
                    df = getattr(T, attr)
                    if df is not None and not df.empty:
                        df.to_csv(d / f"{attr}.csv")
                T.dividends.to_csv(d / "dividends.csv")
                info = T.info
                (d / "info.json").write_text(json.dumps(info, indent=1, default=str))
            print(name, "ok")
            break
        except Exception as e:
            print(name, "retry", e)
            time.sleep(5)

"""v2 data pull: max price history, extra peers, quarterly statements, dividends."""
import json, time, pathlib
import yfinance as yf
RAW = pathlib.Path(__file__).resolve().parents[1] / "data" / "raw"
MAXPX = {"DLF": "DLF.NS", "GODREJPROP": "GODREJPROP.NS", "PHOENIXLTD": "PHOENIXLTD.NS", "OBEROIRLTY": "OBEROIRLTY.NS",
         "PRESTIGE": "PRESTIGE.NS", "BRIGADE": "BRIGADE.NS", "SOBHA": "SOBHA.NS", "LODHA": "LODHA.NS",
         "NIFTY50": "^NSEI", "NIFTYREALTY": "^CNXREALTY", "SENSEX": "^BSESN",
         "MAHLIFE": "MAHLIFE.NS", "SUNTECK": "SUNTECK.NS", "KOLTEPATIL": "KOLTEPATIL.NS", "PURVA": "PURVA.NS",
         "ANANTRAJ": "ANANTRAJ.NS", "SIGNATURE": "SIGNATURE.NS"}
NEWPEERS = ["MAHLIFE", "SUNTECK", "KOLTEPATIL", "PURVA", "ANANTRAJ", "SIGNATURE"]
for name, tk in MAXPX.items():
    d = RAW / name; d.mkdir(parents=True, exist_ok=True)
    for attempt in range(4):
        try:
            T = yf.Ticker(tk)
            h = T.history(period="max", interval="1mo", auto_adjust=False)
            h.to_csv(d / "px_monthly_max.csv")
            if name in NEWPEERS:
                T.history(period="5y", interval="1mo", auto_adjust=False).to_csv(d / "px_monthly.csv")
                T.history(period="5y", interval="1wk", auto_adjust=False).to_csv(d / "px_weekly.csv")
                T.history(period="2y", interval="1d", auto_adjust=False).to_csv(d / "px_daily.csv")
                for attr in ["income_stmt", "balance_sheet", "cashflow"]:
                    df = getattr(T, attr)
                    if df is not None and not df.empty:
                        df.to_csv(d / f"{attr}.csv")
            if not tk.startswith("^"):
                for attr in ["quarterly_income_stmt", "quarterly_balance_sheet", "quarterly_cashflow"]:
                    df = getattr(T, attr)
                    if df is not None and not df.empty:
                        df.to_csv(d / f"{attr}.csv")
                T.dividends.to_csv(d / "dividends.csv"); T.splits.to_csv(d / "splits.csv")
            print(name, len(h), h.index.min().date() if len(h) else None)
            break
        except Exception as e:
            print(name, "retry", attempt, str(e)[:80]); time.sleep(8 * (attempt + 1))
    time.sleep(2)

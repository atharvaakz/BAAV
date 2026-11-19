import pandas as pd, numpy as np, pathlib
RAW = pathlib.Path(__file__).resolve().parents[1]/"data"/"raw"
def px(c, f):
    d = pd.read_csv(RAW/c/f, index_col=0); d.index = pd.to_datetime(d.index, utc=True).tz_convert(None)
    return d["Close"].dropna()
cos = ["DLF","GODREJPROP","PHOENIXLTD","OBEROIRLTY","PRESTIGE","BRIGADE","SOBHA","LODHA","NIFTYREALTY"]
for f, n, lab in [("px_monthly.csv", 61, "5y monthly"), ("px_weekly.csv", 157, "3y weekly")]:
    m = px("NIFTY50", f)
    print("==", lab)
    for c in cos:
        s = px(c, f)
        j = pd.concat([s, m], axis=1, join="inner").iloc[-n:]
        r = j.pct_change().dropna()
        b, a = np.polyfit(r.iloc[:,1], r.iloc[:,0], 1)
        r2 = np.corrcoef(r.iloc[:,1], r.iloc[:,0])[0,1]**2
        print(f"{c:12s} n={len(r):3d} beta={b:.3f} alpha={a:.4f} R2={r2:.3f} adj={0.67*b+0.33:.3f}")

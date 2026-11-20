"""v2 market & macro analyses: long cycle, drawdowns, rolling beta, rate sensitivity, historical ERP, housing cycle."""
import pathlib, json
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data/raw", ROOT / "data/processed/v2"
OUT.mkdir(parents=True, exist_ok=True)
R = {}

def px(name, f="px_monthly_max.csv", col="Adj Close"):
    d = pd.read_csv(RAW / name / f, index_col=0)
    d.index = pd.to_datetime(d.index, utc=True).tz_convert("Asia/Kolkata").tz_localize(None).to_period("M").to_timestamp("M")
    s = d[col if col in d else "Close"].dropna()
    return s[~s.index.duplicated(keep="last")]

names = {"DLF": "DLF", "GODREJPROP": "Godrej Properties", "PHOENIXLTD": "Phoenix Mills", "NIFTYREALTY": "Nifty Realty",
         "NIFTY50": "Nifty 50", "SENSEX": "Sensex", "OBEROIRLTY": "Oberoi", "PRESTIGE": "Prestige", "BRIGADE": "Brigade",
         "SOBHA": "Sobha", "LODHA": "Lodha", "MAHLIFE": "Mahindra Lifespace", "SUNTECK": "Sunteck", "KOLTEPATIL": "Kolte-Patil",
         "PURVA": "Puravankara", "ANANTRAJ": "Anant Raj", "SIGNATURE": "Signature Global"}
P = {k: px(k) for k in names}
pd.concat(P, axis=1).to_csv(OUT / "monthly_adjclose_max.csv")

# B1 long-cycle stats
rows = []
for k, s in P.items():
    r = s.pct_change().dropna()
    yrs = (s.index[-1] - s.index[0]).days / 365.25
    cagr = (s.iloc[-1] / s.iloc[0]) ** (1 / yrs) - 1
    vol = r.std() * np.sqrt(12)
    dd = s / s.cummax() - 1
    trough = dd.idxmin(); peak = s[:trough].idxmax()
    rec = s[trough:][s[trough:] >= s[peak]]
    rows.append(dict(series=names[k], start=s.index[0].date(), end=s.index[-1].date(), years=round(yrs, 1),
                     cagr=cagr, ann_vol=vol, sharpe_like=(cagr - 0.07) / vol, max_drawdown=dd.min(),
                     peak=peak.date(), trough=trough.date(), recovered=(rec.index[0].date() if len(rec) else "not yet"),
                     off_peak_now=dd.iloc[-1], best_12m=s.pct_change(12).max(), worst_12m=s.pct_change(12).min()))
lc = pd.DataFrame(rows); lc.to_csv(OUT / "long_cycle_stats.csv", index=False); R["long_cycle"] = lc.to_dict("records")

# calendar-year returns
cal = pd.concat({names[k]: s.resample("YE").last().pct_change() for k, s in P.items() if k in
                 ["DLF", "GODREJPROP", "PHOENIXLTD", "NIFTYREALTY", "NIFTY50", "SENSEX"]}, axis=1)
cal.index = cal.index.year; cal.to_csv(OUT / "calendar_returns.csv")

# B2 rolling 36m beta vs Nifty 50
mk = P["NIFTY50"].pct_change()
rb = {}
for k in ["DLF", "GODREJPROP", "PHOENIXLTD", "NIFTYREALTY"]:
    j = pd.concat([P[k].pct_change(), mk], axis=1).dropna(); j.columns = ["y", "x"]
    cov = j["y"].rolling(36).cov(j["x"]); var = j["x"].rolling(36).var()
    rb[names[k]] = cov / var
rb = pd.DataFrame(rb).dropna(how="all"); rb.to_csv(OUT / "rolling_beta_36m.csv")
R["rolling_beta_summary"] = {c: dict(min=float(rb[c].min()), max=float(rb[c].max()), median=float(rb[c].median()),
                                     last=float(rb[c].dropna().iloc[-1])) for c in rb}

# B3 two-factor: market + change in 10y G-Sec
y10 = pd.read_csv(RAW / "macro/india_10y.csv"); y10.columns = ["d", "y"]
y10["d"] = pd.to_datetime(y10["d"]).dt.to_period("M").dt.to_timestamp("M"); y10 = y10.set_index("d")["y"].astype(float) / 100
dy = y10.diff()
tf = {}
for k in ["DLF", "GODREJPROP", "PHOENIXLTD", "NIFTYREALTY", "OBEROIRLTY", "PRESTIGE", "SOBHA", "BRIGADE"]:
    j = pd.concat([P[k].pct_change(), mk, dy], axis=1).dropna(); j.columns = ["y", "m", "dy"]
    X = np.column_stack([np.ones(len(j)), j["m"], j["dy"]]); b, res, *_ = np.linalg.lstsq(X, j["y"], rcond=None)
    e = j["y"] - X @ b; s2 = e.var(ddof=3); se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
    r2 = 1 - e.var() / j["y"].var()
    tf[names[k]] = dict(n=len(j), start=str(j.index[0].date()), alpha=b[0], beta_mkt=b[1], beta_rate=b[2], t_rate=b[2] / se[2],
                        per_100bp=b[2] * 0.01, r2=r2)
tfd = pd.DataFrame(tf).T; tfd.to_csv(OUT / "two_factor.csv"); R["two_factor"] = tf

# B4 historical equity premium: Sensex (price) vs 10y yield, 1997+
sx = P["SENSEX"].resample("YE").last()
ann = sx.pct_change().dropna()
imf = pd.read_csv(RAW / "macro/INTGSBINM193N.csv"); imf.columns = ["d", "y"]
imf["d"] = pd.to_datetime(imf["d"]).dt.to_period("M").dt.to_timestamp("M"); imf = pd.to_numeric(imf.set_index("d")["y"], errors="coerce") / 100
spliced = imf.dropna().combine_first(y10) if False else y10.combine_first(imf.dropna())   # OECD where available, IMF before 2011
spliced.to_csv(OUT / "gsec_spliced.csv")
yl = spliced.resample("YE").mean().reindex(ann.index)
hist = pd.DataFrame({"sensex_price_ret": ann, "g_sec_avg": yl}).dropna()
hist["excess_price"] = hist["sensex_price_ret"] - hist["g_sec_avg"]
DY = 0.013  # assumed avg dividend yield to convert price → total return (stated as assumption)
erp = dict(start=int(hist.index[0].year), end=int(hist.index[-1].year), n=len(hist),
           arith_excess_price=float(hist["excess_price"].mean()), arith_excess_total=float(hist["excess_price"].mean() + DY),
           geo_sensex_price=float((sx.iloc[-1] / sx.loc[sx.index.year == hist.index[0].year - 1].iloc[0]) ** (1 / len(hist)) - 1),
           avg_gsec=float(hist["g_sec_avg"].mean()), se_mean=float(hist["excess_price"].std() / np.sqrt(len(hist))))
erp["geo_excess_total"] = erp["geo_sensex_price"] + DY - erp["avg_gsec"]
hist.to_csv(OUT / "historical_erp.csv"); R["historical_erp"] = erp

# B5 housing cycle (BIS residential property prices, India)
def fred(sid):
    d = pd.read_csv(RAW / f"macro/{sid}.csv"); d.columns = ["d", "v"]; d["d"] = pd.to_datetime(d["d"])
    return d.set_index("d")["v"].astype(float)
hn, hr = fred("QINN628BIS"), fred("QINR628BIS")
house = pd.DataFrame({"nominal_idx": hn, "real_idx": hr})
house["nominal_yoy"] = house["nominal_idx"].pct_change(4); house["real_yoy"] = house["real_idx"].pct_change(4)
rq = P["NIFTYREALTY"].resample("QE").last(); rq.index = rq.index.to_period("Q").to_timestamp()
house["realty_idx_yoy"] = rq.pct_change(4).reindex(house.index)
house.to_csv(OUT / "housing_cycle.csv")
hh = house.dropna()
R["housing"] = dict(start=str(hn.index[0].date()), end=str(hn.index[-1].date()),
                    nominal_cagr=float((hn.iloc[-1] / hn.iloc[0]) ** (4 / (len(hn) - 1)) - 1),
                    real_cagr=float((hr.iloc[-1] / hr.iloc[0]) ** (4 / (len(hr) - 1)) - 1),
                    corr_realty_vs_nominal_yoy=float(hh["realty_idx_yoy"].corr(hh["nominal_yoy"])),
                    corr_realty_vs_nominal_yoy_lead4=float(hh["realty_idx_yoy"].corr(hh["nominal_yoy"].shift(-4))),
                    last_nominal_yoy=float(house["nominal_yoy"].dropna().iloc[-1]), last_real_yoy=float(house["real_yoy"].dropna().iloc[-1]))
gdp = fred("MKTGDPINA646NWDB"); gdp_g = (gdp.iloc[-1] / gdp[gdp.index.year == 2009].iloc[0]) ** (1 / (gdp.index[-1].year - 2009)) - 1
R["housing"]["usd_gdp_cagr_2009"] = float(gdp_g)
fx = fred("EXINUS"); R["housing"]["inr_depr_cagr_2009"] = float((fx.iloc[-1] / fx[fx.index.year == 2009].mean()) ** (1 / (fx.index[-1].year - 2009 + 0.8)) - 1)
hc = fred("QINHAM770A"); R["household_credit_pct_gdp"] = dict(first=float(hc.iloc[0]), first_date=str(hc.index[0].date()), last=float(hc.iloc[-1]), last_date=str(hc.index[-1].date()))
r3 = fred("INDIR3TIB01STM"); R["rate_3m_last"] = float(r3.iloc[-1]); R["rate_3m_peak"] = float(r3.max())
(OUT / "analysis_v2.json").write_text(json.dumps(R, indent=1, default=str))
print(lc[["series", "start", "cagr", "ann_vol", "max_drawdown", "trough", "recovered", "off_peak_now"]].round(3).to_string(index=False))
print(tfd.round(3).to_string()); print(json.dumps(erp, indent=0)); print(json.dumps(R["housing"], indent=0)); print(R["rolling_beta_summary"])

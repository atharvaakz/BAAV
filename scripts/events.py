"""Event studies, shocks, survivorship, equity-issuance timing and REIT spread analysis.

Market-model event study (MacKinlay 1997): estimation window [-250,-30] trading days vs Nifty 50,
abnormal return AR = r - (a + b*r_m); CARs over [-20,-2] (run-up), [-1,+1], [0,+5], [+2,+60] (drift);
buy-and-hold abnormal return (BHAR) vs Nifty over 60 and 250 days to judge whether a shock is temporary
or permanent. Outputs data/processed/v2/events.json and CSVs.
"""
import json
import pathlib

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/daily_max"
OUT = ROOT / "data/processed/v2"
OUT.mkdir(parents=True, exist_ok=True)


def px(name):
    d = pd.read_csv(RAW / f"{name}.csv", index_col=0)
    d.index = pd.to_datetime([s[:10] for s in d.index])
    d = d[~d.index.duplicated()]
    return d


P = {k: px(k) for k in ["DLF", "GPL", "PML", "NIFTY", "SENSEX", "REALTY", "EMBASSY", "MINDSPACE", "BIRET", "NEXUS",
                        "OBEROI", "PRESTIGE", "SOBHA", "BRIGADE", "LODHA", "UNITECH", "HDIL", "OMAXE", "PARSVNATH",
                        "ANSALAPI", "PENINLAND", "DBREALTY", "MAHLIFE", "KOLTEPATIL", "SUNTECK", "PURVA", "ANANTRAJ"]}
CLOSE = pd.DataFrame({k: v["Adj Close"] for k, v in P.items()}).sort_index()
# market proxy: Nifty where available, Sensex before Nifty history starts
nif = CLOSE["NIFTY"].dropna()
sx = CLOSE["SENSEX"].dropna()
r_m = np.log(nif / nif.shift(1))
r_pre = np.log(sx / sx.shift(1))
r_pre = r_pre[r_pre.index < nif.index[0]]
r_mkt = pd.concat([r_pre, r_m.dropna()]).sort_index()
mkt = np.exp(r_mkt.cumsum())  # chained market index (Sensex returns before Nifty history begins)
CLOSE = CLOSE.loc[CLOSE.index.isin(mkt.index)]  # Nifty trading days only
R = np.log(CLOSE / CLOSE.shift(1))
R["MKT"] = r_mkt.reindex(R.index)
NAMES = {"DLF": "DLF", "GPL": "Godrej", "PML": "Phoenix", "REALTY": "Nifty Realty"}


def event_study(stock, date, est=(-250, -30)):
    s = R[[stock, "MKT"]].dropna()
    if s.empty:
        return None
    idx = s.index
    d0 = idx.searchsorted(pd.Timestamp(date))  # first trading day on/after the event date
    if d0 >= len(idx) or d0 + est[0] < 0:
        return None
    e = s.iloc[d0 + est[0]: d0 + est[1]]
    if len(e) < 120:
        return None
    b, a = np.polyfit(e["MKT"], e[stock], 1)
    resid_sd = (e[stock] - a - b * e["MKT"]).std(ddof=2)
    ar = s[stock] - a - b * s["MKT"]

    def car(lo, hi):
        lo_, hi_ = d0 + lo, d0 + hi
        if lo_ < 0 or hi_ >= len(idx):
            return None, None
        c = ar.iloc[lo_: hi_ + 1].sum()
        return float(c), float(c / (resid_sd * np.sqrt(hi - lo + 1)))

    def bhar(h):
        if d0 - 1 < 0 or d0 + h >= len(idx):
            return None
        p = CLOSE[stock].reindex(idx)
        m = mkt.reindex(idx)
        return float(p.iloc[d0 + h] / p.iloc[d0 - 1] - m.iloc[d0 + h] / m.iloc[d0 - 1])

    out = {"date0": str(idx[d0].date()), "beta": float(b)}
    for k, (lo, hi) in {"run": (-20, -2), "ann": (-1, 1), "w5": (0, 5), "drift": (2, 60)}.items():
        out[k], out[k + "_t"] = car(lo, hi)
    out["bhar60"], out["bhar250"] = bhar(60), bhar(250)
    return out


# ------------------------------------------------------------------ event lists (dates verified; see references)
MACRO = [("2008-09-15", "Lehman collapse", "credit"),
         ("2016-11-09", "Demonetisation (announced 8-Nov evening)", "policy"),
         ("2017-05-02", "RERA comes into force (1-May)", "regulation"),
         ("2017-07-03", "GST rollout (1-Jul)", "policy"),
         ("2017-08-09", "Jaypee Infratech admitted to insolvency", "distress"),
         ("2018-09-21", "IL&FS / DHFL credit shock", "credit"),
         ("2019-04-01", "First REIT lists (Embassy)", "REIT"),
         ("2019-07-23", "Supreme Court cancels Amrapali registration", "distress"),
         ("2020-03-25", "COVID national lockdown (announced 24-Mar)", "shock"),
         ("2020-08-07", "Mindspace REIT lists", "REIT"),
         ("2020-08-26", "Maharashtra stamp-duty cut", "policy"),
         ("2021-02-16", "Brookfield REIT lists", "REIT"),
         ("2022-05-04", "RBI off-cycle rate hike", "rates"),
         ("2023-05-19", "Nexus Select (mall) REIT lists", "REIT"),
         ("2025-02-07", "RBI first rate cut of the cycle", "rates"),
         ("2025-06-06", "RBI 50bp cut + CRR cut", "rates"),
         ("2026-10-07", "RBI rate hike to 5.50%", "rates")]
COMPANY = [("DLF", "2017-08-28", "GIC buys 33.34% of DCCDL (announced 27-Aug)", "monetisation"),
           ("DLF", "2017-12-01", "Board approves QIP + promoter warrants", "equity issue"),
           ("DLF", "2019-03-25", "QIP launched (₹3,173 cr)", "equity issue"),
           ("DLF", "2023-03-16", "The Arbour: ₹8,000 cr sold in 3 days", "launch"),
           ("DLF", "2024-01-08", "Privana South: ₹7,200 cr sold in 3 days", "launch"),
           ("DLF", "2024-05-09", "Privana West: ₹5,590 cr sold in 3 days", "launch"),
           ("GPL", "2019-06-25", "QIP opens (₹2,100 cr)", "equity issue"),
           ("GPL", "2021-03-10", "QIP launched (₹3,750 cr)", "equity issue"),
           ("GPL", "2024-11-27", "QIP opens (₹6,000 cr)", "equity issue"),
           ("PML", "2020-12-02", "Term sheet with GIC for retail platform", "monetisation"),
           ("PML", "2021-06-02", "GIC platform signed ($733m)", "monetisation"),
           ("PML", "2025-07-24", "Buys CPPIB's 49% of ISMDPL (₹5,450 cr)", "monetisation")]
ISSUES = [("DLF", "2007-07-05", "DLF IPO listing"), ("DLF", "2019-03-25", "DLF QIP"), ("GPL", "2019-06-25", "Godrej QIP 2019"),
          ("GPL", "2021-03-10", "Godrej QIP 2021"), ("GPL", "2024-11-27", "Godrej QIP 2024")]

macro_rows = []
for d, lab, kind in MACRO:
    row = {"date": d, "event": lab, "kind": kind}
    for s in ["DLF", "GPL", "PML", "REALTY"]:
        row[s] = event_study(s, d)
    macro_rows.append(row)
co_rows = []
for s, d, lab, kind in COMPANY:
    co_rows.append({"co": s, "date": d, "event": lab, "kind": kind, **(event_study(s, d) or {})})


# ------------------------------------------------------------------ results-day study: does EPS surprise move the price?
def earnings(tk, s):
    import yfinance as yf
    try:
        e = yf.Ticker(tk).get_earnings_dates(limit=80)
    except Exception:
        return []
    if e is None or e.empty:
        return []
    e = e.dropna(subset=["Reported EPS"])
    rows = []
    for ts, r in e.iterrows():
        ist = ts.tz_convert("Asia/Kolkata")
        day = ist.normalize().tz_localize(None)
        if ist.hour * 60 + ist.minute >= 15 * 60 + 30:  # after the close: reaction is next trading day
            day = day + pd.Timedelta(days=1)
        if day > pd.Timestamp("2026-10-31"):
            continue  # data cutoff: reaction falls after 31-Oct-2026
        es = event_study(s, day)
        if es and es["ann"] is not None and pd.Timestamp(es["date0"]) <= pd.Timestamp("2026-10-31"):
            rows.append({"co": s, "date": str(day.date()), "surprise": float(r["Surprise(%)"]) if pd.notna(r["Surprise(%)"]) else None,
                         "car01": es["w5"], "ann": es["ann"], "ann_t": es["ann_t"]})
    return rows


ER = []
for tk, s in [("DLF.NS", "DLF"), ("GODREJPROP.NS", "GPL"), ("PHOENIXLTD.NS", "PML")]:
    ER += earnings(tk, s)
er = pd.DataFrame(ER)
er_stats = {}
if not er.empty:
    for s, g in er.dropna(subset=["surprise"]).groupby("co"):
        g = g[g.surprise.abs() < 200]
        if len(g) >= 6:
            b, a = np.polyfit(g.surprise / 100, g.ann, 1)
            rr = np.corrcoef(g.surprise, g.ann)[0, 1]
            er_stats[s] = {"n": int(len(g)), "slope": float(b), "r2": float(rr ** 2), "mean_abs_car": float(g.ann.abs().mean()),
                           "hit": float(((g.surprise > 0) == (g.ann > 0)).mean()), "first": g.date.min(), "last": g.date.max()}
    er.to_csv(OUT / "earnings_events.csv", index=False)

# ------------------------------------------------------------------ survivorship: survivors vs the developers that failed
SURV = ["DLF", "PML", "SOBHA", "BRIGADE", "PURVA", "KOLTEPATIL", "MAHLIFE", "ANANTRAJ", "SUNTECK"]
FAILED = ["UNITECH", "HDIL", "PARSVNATH", "ANSALAPI", "OMAXE", "PENINLAND"]
start = pd.Timestamp("2008-01-01")
c = CLOSE[CLOSE.index >= start]
first = c.iloc[0]


def ew_index(cols, frm):
    sub = CLOSE.loc[CLOSE.index >= frm, cols].dropna(axis=1, how="all")
    rets = sub.pct_change().clip(-0.5, 1.0)
    return (1 + rets.mean(axis=1, skipna=True).fillna(0)).cumprod()


ew_s, ew_f = ew_index(SURV, start), ew_index(FAILED, start)
ew_all = ew_index(SURV + FAILED, start)
tot = {"survivors": float(ew_s.iloc[-1] - 1), "failed": float(ew_f.iloc[-1] - 1), "all": float(ew_all.iloc[-1] - 1)}
yrs = (ew_s.index[-1] - ew_s.index[0]).days / 365.25
cagr = {k: float((1 + v) ** (1 / yrs) - 1) for k, v in tot.items()}
dd = {n: float(CLOSE.loc[CLOSE.index >= start, n].iloc[-1] / CLOSE.loc[CLOSE.index >= start, n].max() - 1) for n in FAILED}
# monthly betas 2010-2019 (the era when the failures were still listed)
M = CLOSE.resample("ME").last()
mr = M.pct_change(fill_method=None)
mr["MKT"] = mkt.resample("ME").last().pct_change()
win = mr.loc["2010-01-01":"2019-12-31"]


def beta(col):
    x = win[[col, "MKT"]].dropna()
    if len(x) < 36:
        return None
    return float(np.cov(x[col], x["MKT"])[0, 1] / x["MKT"].var())


bs = {n: beta(n) for n in SURV + FAILED + ["GPL", "OBEROI", "PRESTIGE"]}
med_s = float(np.nanmedian([bs[n] for n in SURV + ["GPL", "OBEROI", "PRESTIGE"] if bs[n] is not None]))
med_all = float(np.nanmedian([v for v in bs.values() if v is not None]))
# flight to quality: 2016-11 to 2020-02 (demonetisation, RERA, IL&FS) quality vs stressed
q0, q1 = "2016-11-01", "2020-02-28"
QUAL = ["DLF", "GPL", "PML", "OBEROI", "PRESTIGE", "BRIGADE", "SOBHA"]


def window_ret(cols, a, b):
    sub = CLOSE.loc[a:b, cols].dropna(axis=1, how="any")
    return float((sub.iloc[-1] / sub.iloc[0]).mean() - 1)


ftq = {"quality": window_ret(QUAL, q0, q1), "stressed": window_ret(FAILED, q0, q1), "nifty": float(mkt.loc[q0:q1].iloc[-1] / mkt.loc[q0:q1].iloc[0] - 1)}
pd.DataFrame({"Survivors (EW)": ew_s, "Failed / stressed (EW)": ew_f, "All developers (EW)": ew_all}).resample("ME").last().to_csv(OUT / "survivorship_index.csv")

# ------------------------------------------------------------------ equity issuance timing: do developers sell shares at the top?
iss = []
for s, d, lab in ISSUES:
    ser = CLOSE[s].dropna()
    i0 = ser.index.searchsorted(pd.Timestamp(d))
    ref = CLOSE["REALTY"].dropna()
    row = {"co": s, "date": d, "event": lab}
    for h, k in [(250, "r1y"), (750, "r3y")]:
        if i0 + h < len(ser):
            d1 = ser.index[i0 + h]
            row[k] = float(ser.iloc[i0 + h] / ser.iloc[i0] - 1)
            m0, m1 = mkt.asof(ser.index[i0]), mkt.asof(d1)
            row[k + "_vs_nifty"] = float(row[k] - (m1 / m0 - 1))
            if ser.index[i0] >= ref.index[0]:
                row[k + "_vs_realty"] = float(row[k] - (ref.asof(d1) / ref.asof(ser.index[i0]) - 1))
    # where was the price in its own 3-year range at issue?
    w = ser.iloc[max(0, i0 - 750): i0 + 1]
    row["pctile_3y"] = float((w <= ser.iloc[i0]).mean())
    iss.append(row)

# ------------------------------------------------------------------ REIT yields vs G-Sec, and the cap-rate channel
reit_y = {}
for k in ["EMBASSY", "MINDSPACE", "BIRET", "NEXUS"]:
    d = P[k]
    pay = d.loc[d["Dividends"] > 0, "Dividends"]
    me = d["Close"].resample("ME").last()
    vals = {}
    for dt, pxv in me.items():
        last = pay[pay.index <= dt]
        if len(last) >= 4 and (dt - last.index[-1]).days <= 130:
            vals[dt] = last.iloc[-4:].sum() / pxv  # last four quarterly distributions ÷ price
    reit_y[k] = pd.Series(vals)
RY = pd.DataFrame(reit_y)
g = pd.read_csv(ROOT / "data/raw/macro/india_10y.csv", index_col=0, parse_dates=True).iloc[:, 0]
g.index = g.index.to_period("M").to_timestamp("M")
g = g / 100 if g.max() > 1 else g
RY["median"] = RY[["EMBASSY", "MINDSPACE", "BIRET", "NEXUS"]].median(axis=1)
RY["gsec"] = g.reindex(RY.index, method="ffill")
RY["spread"] = RY["median"] - RY["gsec"]
RY.to_csv(OUT / "reit_yields.csv")
# monthly regression: stock return on market return and change in REIT yield
reg = {}
mm = mr.copy()
mm["dY"] = RY["median"].diff()
for s in ["DLF", "PML", "GPL", "REALTY"]:
    x = mm[[s, "MKT", "dY"]].dropna()
    if len(x) > 24:
        X = np.column_stack([np.ones(len(x)), x["MKT"], x["dY"]])
        coef, res, *_ = np.linalg.lstsq(X, x[s], rcond=None)
        e = x[s] - X @ coef
        s2 = (e ** 2).sum() / (len(x) - 3)
        se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
        reg[s] = {"n": int(len(x)), "b_mkt": float(coef[1]), "b_dY": float(coef[2]), "t_dY": float(coef[2] / se[2]),
                  "per_25bp": float(coef[2] * 0.0025)}
reit_summary = {"latest_median": float(RY["median"].dropna().iloc[-1]), "latest_gsec": float(RY["gsec"].dropna().iloc[-1]),
                "latest_spread": float(RY["spread"].dropna().iloc[-1]), "mean_spread": float(RY["spread"].mean()),
                "min_spread": float(RY["spread"].min()), "max_spread": float(RY["spread"].max()),
                "first": str(RY["median"].dropna().index[0].date()), "latest": {k: float(RY[k].dropna().iloc[-1]) for k in ["EMBASSY", "MINDSPACE", "BIRET", "NEXUS"] if RY[k].notna().any()}}


# ------------------------------------------------------------------ drawdowns and recovery; Amihud liquidity
def drawdowns(s, n=3):
    s = s.dropna()
    peak = s.cummax()
    dd_ = s / peak - 1
    out, used = [], pd.Series(False, index=s.index)
    for _ in range(n):
        d2 = dd_[~used]
        if d2.empty or d2.min() > -0.2:
            break
        trough = d2.idxmin()
        pk = s.loc[:trough].idxmax()
        rec = s.loc[trough:][s.loc[trough:] >= s.loc[pk]]
        rec_d = rec.index[0] if len(rec) else None
        out.append({"peak": str(pk.date()), "trough": str(trough.date()), "depth": float(dd_.loc[trough]),
                    "recovered": str(rec_d.date()) if rec_d is not None else "not yet",
                    "years_to_recover": float((rec_d - pk).days / 365.25) if rec_d is not None else float((s.index[-1] - pk).days / 365.25)})
        used.loc[pk: (rec_d if rec_d is not None else s.index[-1])] = True
    return out


DD = {s: drawdowns(CLOSE[s]) for s in ["DLF", "GPL", "PML", "REALTY"]}
AMI = {}
for s in ["DLF", "GPL", "PML", "OBEROI", "PRESTIGE", "SOBHA", "BRIGADE", "LODHA", "EMBASSY", "NEXUS"]:
    d = P[s]
    d = d[(d.index >= "2025-11-01") & (d.index <= "2026-10-31")]
    val = (d["Close"] * d["Volume"]) / 1e7  # ₹ crore traded
    ami = (d["Close"].pct_change().abs() / val.replace(0, np.nan)).mean() * 1e3
    AMI[s] = {"adv_cr": float(val.mean()), "amihud": float(ami)}

# ------------------------------------------------------------------ summaries
def avg(rows, key, subset):
    v = [r[s][key] for r in rows for s in subset if r.get(s) and r[s].get(key) is not None]
    return float(np.mean(v)) if v else None


co = pd.DataFrame(co_rows)
by_kind = {}
for k, gk in co.groupby("kind"):
    n = len(gk)
    m = gk["ann"].mean()
    t = gk["ann"].mean() / (gk["ann"].std(ddof=1) / np.sqrt(n)) if n > 2 else None
    by_kind[k] = {"n": n, "ann": float(m), "run": float(gk["run"].mean()), "drift": float(gk["drift"].mean()), "t_cs": None if t is None else float(t)}
res = {"macro": macro_rows, "company": co_rows, "by_kind": by_kind, "earnings": er_stats, "earnings_n": int(len(er)),
       "survivorship": {"total": tot, "cagr": cagr, "drawdown_failed": dd, "beta_2010_19": bs, "median_beta_survivors": med_s,
                        "median_beta_all": med_all, "flight_to_quality": ftq, "years": yrs},
       "issues": iss, "reit": reit_summary, "reit_reg": reg, "drawdowns": DD, "amihud": AMI}
(OUT / "events.json").write_text(json.dumps(res, indent=1, default=str))
pd.DataFrame([{**{"date": r["date"], "event": r["event"], "kind": r["kind"]},
               **{f"{s}_{k}": (r[s] or {}).get(k) for s in ["DLF", "GPL", "PML", "REALTY"] for k in ["ann", "ann_t", "w5", "bhar60", "bhar250"]}}
              for r in macro_rows]).to_csv(OUT / "macro_events.csv", index=False)
co.to_csv(OUT / "company_events.csv", index=False)
print(json.dumps({"by_kind": by_kind, "earnings": er_stats, "surv": res["survivorship"]["total"], "cagr": cagr, "ftq": ftq,
                  "beta": [med_s, med_all], "reit": reit_summary, "reg": reg}, indent=1, default=str))
for r in macro_rows:
    print(r["date"], r["event"][:38].ljust(38), " ".join(f"{s}:{(r[s] or {}).get('ann', float('nan')):+.3f}/{(r[s] or {}).get('bhar250') or float('nan'):+.2f}" for s in ["DLF", "GPL", "PML", "REALTY"]))
for r in co_rows:
    print(r["co"], r["date"], r["event"][:40].ljust(40), f"run {r.get('run', 0):+.3f} ann {r.get('ann', 0):+.3f} (t {r.get('ann_t', 0):+.1f}) drift {r.get('drift') or 0:+.3f}")
for r in iss:
    print(r)

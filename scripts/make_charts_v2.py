"""v2 charts: long cycle, drawdowns, rolling beta, rate sensitivity, housing, lens comparison, terminal grid, cap rates."""
import json, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ROOT = pathlib.Path(__file__).resolve().parents[1]; V2 = ROOT / "data/processed/v2"
N = json.loads((ROOT / "data/processed/numbers.json").read_text())
INK, MUTE, GRID = "#1F2A30", "#7A858C", "#E3E7E8"
C = {"DLF": "#2F5D62", "GPL": "#C08A3E", "PML": "#8C4A3C", "IDX": "#9AA5AA", "N50": "#1F2A30"}
plt.rcParams.update({"font.family": "Carlito", "font.size": 10, "axes.edgecolor": MUTE, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "axes.titleweight": "bold",
                     "axes.titlesize": 11, "axes.titlelocation": "left", "axes.facecolor": "none", "savefig.bbox": "tight"})
def save(fig, name):
    for d, fc in [(ROOT / "reports/charts", "white"), (ROOT / "reports/charts/deck", "#F7F5F0")]:
        d.mkdir(parents=True, exist_ok=True); fig.savefig(d / f"{name}.png", dpi=200, facecolor=fc)
    plt.close(fig)

px = pd.read_csv(V2 / "monthly_adjclose_max.csv", index_col=0, parse_dates=True)
# 1. long cycle: indexed to 100 at Jan-2010 (log scale) + drawdown panel
start = "2010-07-31"
sub = px.loc[start:, ["DLF", "GODREJPROP", "PHOENIXLTD", "NIFTYREALTY", "NIFTY50"]]
idx = sub / sub.iloc[0] * 100
fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 5.2), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
for k, col, lab in [("DLF", C["DLF"], "DLF"), ("GODREJPROP", C["GPL"], "Godrej Properties"), ("PHOENIXLTD", C["PML"], "Phoenix Mills"),
                    ("NIFTYREALTY", C["IDX"], "Nifty Realty"), ("NIFTY50", C["N50"], "Nifty 50")]:
    a1.plot(idx.index, idx[k], color=col, lw=2 if k in ("DLF", "GODREJPROP", "PHOENIXLTD") else 1.3, ls="-" if k != "NIFTY50" else "--", label=lab)
    dd = px[k].loc["2007-01-31":] / px[k].loc["2007-01-31":].cummax() - 1
    if k != "NIFTY50":
        a2.plot(dd.index, dd, color=col, lw=1.4)
a1.set_yscale("log"); a1.set_title("Total-return index (Jul-2010 = 100, log scale)"); a1.legend(frameon=False, fontsize=8, ncol=2, loc="upper left")
for x, t in [("2013-08-31", "Taper\ntantrum"), ("2016-11-30", "Demonetisation\n+ RERA"), ("2020-03-31", "COVID"), ("2008-10-31", "")]:
    if pd.Timestamp(x) >= pd.Timestamp(start):
        a1.axvline(pd.Timestamp(x), color=MUTE, lw=0.7, ls=":"); a1.text(pd.Timestamp(x), a1.get_ylim()[0] * 1.08, t, fontsize=7.5, color=MUTE, ha="center", va="bottom")
a2.set_title("Drawdown from previous peak (since 2007)"); a2.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
fig.tight_layout(); save(fig, "long_cycle")

# 2. rolling beta
rb = pd.read_csv(V2 / "rolling_beta_36m.csv", index_col=0, parse_dates=True)
fig, ax = plt.subplots(figsize=(10, 3.2))
for c, col in [("DLF", C["DLF"]), ("Godrej Properties", C["GPL"]), ("Phoenix Mills", C["PML"]), ("Nifty Realty", C["IDX"])]:
    ax.plot(rb.index, rb[c], color=col, lw=1.8 if c != "Nifty Realty" else 1.2, label=c)
ax.axhline(1, color=INK, lw=0.8, ls=":"); ax.set_title("Beta is not a constant: rolling 36-month beta vs Nifty 50"); ax.legend(frameon=False, fontsize=8, ncol=4)
save(fig, "rolling_beta")

# 3. rate sensitivity (two-factor)
tf = pd.read_csv(V2 / "two_factor.csv", index_col=0)
fig, ax = plt.subplots(figsize=(7.5, 3.2))
order = tf["per_100bp"].sort_values().index
cols = [C["DLF"] if n == "DLF" else C["GPL"] if n.startswith("Godrej") else C["PML"] if n.startswith("Phoenix") else "#B9C6C8" for n in order]
ax.barh(order, tf.loc[order, "per_100bp"], color=cols)
for i, n in enumerate(order):
    ax.text(tf.loc[n, "per_100bp"] - 0.002 if tf.loc[n, "per_100bp"] < 0 else 0.001, i, f"t = {tf.loc[n, 't_rate']:.1f}", va="center",
            ha="right" if tf.loc[n, "per_100bp"] < 0 else "left", fontsize=8, color=INK)
ax.axvline(0, color=INK, lw=0.8); ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
ax.set_title("Monthly return per +100bp in the 10-yr G-Sec (controlling for the market)"); ax.grid(axis="y", visible=False)
save(fig, "rate_factor")

# 4. housing cycle
hc = pd.read_csv(V2 / "housing_cycle.csv", index_col=0, parse_dates=True)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.2))
a1.plot(hc.index, hc["nominal_idx"] / hc["nominal_idx"].iloc[0] * 100, color=C["DLF"], lw=2, label="Nominal")
a1.plot(hc.index, hc["real_idx"] / hc["real_idx"].iloc[0] * 100, color=C["GPL"], lw=2, label="Real (CPI-deflated)")
a1.set_title("BIS India house prices (2009 Q1 = 100)"); a1.legend(frameon=False, fontsize=8)
a2.plot(hc.index, hc["nominal_yoy"], color=C["DLF"], lw=1.8, label="House prices YoY")
a2.plot(hc.index, hc["realty_idx_yoy"], color=C["IDX"], lw=1.4, label="Nifty Realty YoY")
a2.axhline(0, color=INK, lw=0.7); a2.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
a2.set_title("Stocks swing ±60%; house prices move a few points"); a2.legend(frameon=False, fontsize=8)
fig.tight_layout(); save(fig, "housing")

# 5. lens comparison + implied
cos = ["DLF", "GPL", "PML"]; NM = {"DLF": "DLF", "GPL": "Godrej Properties", "PML": "Phoenix Mills"}
fig, ax = plt.subplots(figsize=(9, 3.4))
x = np.arange(3); w = 0.2
vals = {"Lens A (large-cap β)": [N[c]["DCF"]["Intrinsic value per share (Rs)"] for c in cos],
        "Lens B (industry β)": [N[c]["lensB"]["vps"] for c in cos],
        "Bull + lens B": [N["SC"]["scenarios"][c]["bull_lensB"] for c in cos],
        "Market price": [N[c]["DCF"]["Current market price (Rs)"] for c in cos]}
colors = ["#B9C6C8", "#88A6A8", "#2F5D62", INK]
for i, (k, v) in enumerate(vals.items()):
    ax.bar(x + (i - 1.5) * w, v, w, color=colors[i], label=k)
    for xi, vi in zip(x + (i - 1.5) * w, v):
        ax.text(xi, vi + 30, f"{vi:,.0f}", ha="center", fontsize=7.5)
ax.set_xticks(x); ax.set_xticklabels([NM[c] for c in cos]); ax.legend(frameon=False, fontsize=8, ncol=4, loc="upper left")
ax.set_title("DCF value per share under two cost-of-capital lenses vs price (₹)"); ax.set_ylim(0, max(max(v) for v in vals.values()) * 1.18)
save(fig, "lens_compare")

# 6. implied perpetual growth vs nominal GDP
imp = N["SC"]["implied"]
fig, ax = plt.subplots(figsize=(7, 3))
ax.bar([NM[c] for c in cos], [imp[c]["terminal_g"] for c in cos], color=[C[c] for c in cos])
for i, c in enumerate(cos):
    ax.text(i, imp[c]["terminal_g"] + 0.003, f"{imp[c]['terminal_g']:.1%}", ha="center", fontsize=9)
ax.axhline(N["Inputs"]["Terminal growth rate (nominal, Rs)"], color=INK, ls=":", lw=1); ax.text(2.45, 0.057, "our terminal g 5.5% (≤ Rf)", ha="right", fontsize=8)
ax.axhline(0.105, color=MUTE, ls="--", lw=1); ax.text(2.45, 0.107, "India nominal GDP growth ≈ 10–11%", ha="right", fontsize=8, color=MUTE)
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0)); ax.set_ylim(0, 0.15)
ax.set_title("Perpetual growth the market price implies (stable WACC held)")
save(fig, "implied_growth")

# 7. cap rates
cap = N["Cap"]
labs = ["Phoenix (EBITDA / EV)"] + [r[0].split(" (")[0] for r in cap["reits"]] + ["10-yr G-Sec"]
vals_ = [cap["yield"]] + [r[3] for r in cap["reits"]] + [N["Inputs"]["India 10-yr G-Sec yield"]]
fig, ax = plt.subplots(figsize=(8, 3))
ax.barh(labs[::-1], vals_[::-1], color=["#B9C6C8"] + ["#88A6A8"] * 4 + [C["PML"]])
for i, v in enumerate(vals_[::-1]):
    ax.text(v + 0.001, i, f"{v:.1%}", va="center", fontsize=8.5)
ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0)); ax.grid(axis="y", visible=False)
ax.set_title("Yield investors accept: Phoenix vs listed REITs vs government bond")
save(fig, "cap_rates")

# 8. industry benchmark bars (beta & ROE)
ib = N["Industry"]
fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(11, 2.9))
for ax, key, title, fmt in [(a1, "Levered beta (industry avg)", "Beta", "x"), (a2, "ROE", "ROE", "pct"), (a3, "Trailing P/E (aggregate)", "Trailing P/E", "x")]:
    v = ib[key]; labs_ = ["India RE dev\n(156 firms)", "DLF", "Godrej", "Phoenix"]; vv = [v[0], v[2], v[3], v[4]]
    ax.bar(labs_, vv, color=["#B9C6C8", C["DLF"], C["GPL"], C["PML"]]); ax.set_title(title); ax.tick_params(axis="x", labelsize=8)
    if fmt == "pct": ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
fig.tight_layout(); save(fig, "industry_bench")
print("v2 charts done")

# 9. DLF NAV bridge and Phoenix NAV vs price
nav = N["NAV"]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.5, 3.6), gridspec_kw={"width_ratios": [1.4, 1]})
parts = [("DCCDL stake\n(7.5% cap)", nav["dccdl_stake"]), ("5-yr pipeline\nmargin (PV)", nav["dlf_res_pv"]), ("Net cash", nav["dlf_netcash"]),
         ("Residual land bank\n(implied by price)", nav["dlf_land"])]
cum = 0
for i, (lab, v) in enumerate(parts):
    col = "#C08A3E" if i == 3 else C["DLF"]
    a1.bar(i, v, bottom=cum, color=col, alpha=0.9 if i < 3 else 0.6); a1.text(i, cum + v / 2, f"₹{v/1000:,.0f}k cr", ha="center", va="center", fontsize=8.5, color="white")
    cum += v
a1.bar(4, nav["dlf_mcap"], color=INK); a1.text(4, nav["dlf_mcap"] / 2, f"₹{nav['dlf_mcap']/1000:,.0f}k cr", ha="center", va="center", fontsize=8.5, color="white")
a1.set_xticks(range(5)); a1.set_xticklabels([p[0] for p in parts] + ["Market cap"], fontsize=8)
a1.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v/1000:,.0f}k"))
a1.set_title(f"DLF: {nav['dlf_land']/nav['dlf_mcap']:.0%} of market value is land beyond the visible pipeline")
labs_ = ["Our SOTP NAV", "ICICI Sec NAV", "Broker median target", "Market price"]
vals_ = [nav["pml_nav_ps"], 1287, 2200, N["PML"]["DCF"]["Current market price (Rs)"]]
a2.bar(labs_, vals_, color=["#88A6A8", "#B9C6C8", "#C08A3E", INK])
for i, v in enumerate(vals_):
    a2.text(i, v + 30, f"₹{v:,.0f}", ha="center", fontsize=8.5)
a2.tick_params(axis="x", labelsize=8); a2.set_title("Phoenix: NAV vs what investors pay")
fig.tight_layout(); save(fig, "nav_bridge")

# 10. our values vs broker targets vs price
fig, ax = plt.subplots(figsize=(9.5, 3.3))
cos_ = ["DLF", "GPL", "PML"]; x = np.arange(3); w = 0.2
bm_ = {r[0]: r[1] for r in N["Brokers"] if r[0] in ("DLF Ltd", "Godrej Properties", "Phoenix Mills")}
series_ = [("Our DCF (lens A)", [N[c]["DCF"]["Intrinsic value per share (Rs)"] for c in cos_], "#B9C6C8"),
           ("Our NAV / embedded-profit", [nav["dlf_nav_ps"], nav["gpl_emb_ps"], nav["pml_nav_ps"]], "#88A6A8"),
           ("Broker median target", [bm_["DLF Ltd"], bm_["Godrej Properties"], bm_["Phoenix Mills"]], "#C08A3E"),
           ("Market price", [N[c]["DCF"]["Current market price (Rs)"] for c in cos_], INK)]
for i, (lab, v, col) in enumerate(series_):
    ax.bar(x + (i - 1.5) * w, v, w, color=col, label=lab)
    for xi, vi in zip(x + (i - 1.5) * w, v):
        ax.text(xi, vi + 30, f"{vi:,.0f}", ha="center", fontsize=7.5)
ax.set_xticks(x); ax.set_xticklabels(["DLF", "Godrej Properties", "Phoenix Mills"]); ax.legend(frameon=False, fontsize=8, ncol=4, loc="upper left")
ax.set_ylim(0, 3200); ax.set_title("Textbook DCF vs practitioner NAV vs the sell-side vs the market (₹/share)")
save(fig, "practitioner_vs_textbook")
print("v3 charts done")

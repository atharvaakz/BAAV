"""Scenarios, implied terminal growth, terminal-assumption grid and Monte Carlo on the validated DCF engine."""
import json, pathlib, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from dcf_engine import load_base, value, ROOT
B = load_base(); OUT = ROOT / "data/processed/v2"; rng = np.random.default_rng(20261120)
res = {"spec": [
    "Growth scale on FY27–31 path: Normal(1.0, 0.25), floored at 0.2",
    "Target core EBIT margin: Normal(base, 6 pp), bounded 5%–75%",
    "Sales-to-capital: Lognormal(median = base, σ = 0.30)",
    "High-growth WACC: Normal(lens base, 1.5 pp); stable WACC: Normal(base, 1.0 pp), kept ≥ g + 2 pp",
    "Terminal growth: Uniform(4.5%, 6.5%)"]}
scen, implied = {}, {}
for co, p in B.items():
    # implied terminal growth at lens-A rates (bisection)
    lo, hi = 0.0, p["ws"] - 0.004
    if value(p, gT=hi) < p["price"]:
        ig = None
    else:
        for _ in range(200):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if value(p, gT=mid) < p["price"] else (lo, mid)
        ig = (lo + hi) / 2
    # implied stable WACC holding high-growth WACC and g
    lo, hi = p["gT"] + 0.002, 0.25
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if value(p, ws=mid) > p["price"] else (lo, mid)
    implied[co] = {"terminal_g": ig, "stable_wacc": (lo + hi) / 2}
    # scenarios
    scen[co] = {"bear": value(p, gscale=0.6, m=p["m"] - 0.08, s2c=p["s2c"] * 0.75, w=p["w"] + 0.01, ws=p["ws"] + 0.01, gT=0.05),
                "base": value(p), "bull": value(p, gscale=1.3, m=p["m"] + 0.08, s2c=p["s2c"] * 1.25, w=p["w"] - 0.01, ws=p["ws"] - 0.01, gT=0.06),
                "bull_lensB": value(p, gscale=1.3, m=p["m"] + 0.08, s2c=p["s2c"] * 1.25, w=p["wB"] - 0.01, ws=p["ws"] - 0.01, gT=0.06),
                "price": p["price"]}
    # terminal grid: stable WACC x g (lens A high-growth)
    grid = {}
    for wsv in [0.09, 0.10, 0.11, 0.12, p["ws"]]:
        grid[f"{wsv:.4f}"] = {f"{g:.3f}": (value(p, ws=wsv, gT=g) if wsv - g > 0.01 else None) for g in [0.055, 0.065, 0.075, 0.085]}
    implied[co]["terminal_grid"] = grid
    # Monte Carlo
    res[co] = {}
    for lens, wbase in [("A", p["w"]), ("B", p["wB"])]:
        n = 10000; vals = np.empty(n)
        gsc = np.maximum(0.2, rng.normal(1, 0.25, n)); mm = np.clip(rng.normal(p["m"], 0.06, n), 0.05, 0.75)
        s2 = p["s2c"] * np.exp(rng.normal(0, 0.30, n)); w = rng.normal(wbase, 0.015, n); wsd = rng.normal(p["ws"], 0.01, n)
        g = rng.uniform(0.045, 0.065, n); wsd = np.maximum(wsd, g + 0.02); w = np.maximum(w, 0.05)
        for i in range(n):
            vals[i] = value(p, gscale=gsc[i], m=mm[i], s2c=s2[i], w=w[i], ws=wsd[i], gT=g[i])
        res[co][lens] = {"p5": float(np.percentile(vals, 5)), "p25": float(np.percentile(vals, 25)), "median": float(np.median(vals)),
                         "mean": float(vals.mean()), "p75": float(np.percentile(vals, 75)), "p95": float(np.percentile(vals, 95)),
                         "prob_above_price": float((vals > p["price"]).mean()), "price": p["price"]}
        np.save(OUT / f"mc_{co}_{lens}.npy", vals)
(OUT / "monte_carlo.json").write_text(json.dumps(res, indent=1))
(OUT / "scenarios.json").write_text(json.dumps({"scenarios": scen, "implied": implied}, indent=1))
# chart
INK = "#1F2A30"; C = {"DLF": "#2F5D62", "GPL": "#C08A3E", "PML": "#8C4A3C"}; NM = {"DLF": "DLF", "GPL": "Godrej Properties", "PML": "Phoenix Mills"}
plt.rcParams.update({"font.family": "Carlito", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "axes.titleweight": "bold", "axes.titlelocation": "left"})
fig, axs = plt.subplots(1, 3, figsize=(12, 3.3))
for ax, co in zip(axs, ["DLF", "GPL", "PML"]):
    for lens, alpha, lab in [("A", 0.85, "Lens A (large-cap β)"), ("B", 0.45, "Lens B (industry β)")]:
        v = np.load(OUT / f"mc_{co}_{lens}.npy"); hi = np.percentile(v, 99)
        ax.hist(v[v <= hi], bins=60, color=C[co], alpha=alpha, label=lab)
    ax.axvline(B[co]["price"], color=INK, ls=":", lw=1.2); ax.text(B[co]["price"], ax.get_ylim()[1] * 0.92, f" price ₹{B[co]['price']:,.0f}", fontsize=8.5)
    ax.set_title(f"{NM[co]}: P(value > price) A {res[co]['A']['prob_above_price']:.0%} · B {res[co]['B']['prob_above_price']:.0%}", fontsize=10)
    ax.set_yticks([]); ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"₹{x:,.0f}"))
axs[0].legend(frameon=False, fontsize=8)
fig.tight_layout()
for path, fc in [(ROOT / "reports/charts/monte_carlo.png", "white"), (ROOT / "reports/charts/deck/monte_carlo.png", "#F7F5F0")]:
    path.parent.mkdir(parents=True, exist_ok=True); fig.savefig(path, dpi=200, facecolor=fc, bbox_inches="tight")
print(json.dumps({co: {l: {k: round(v, 3) for k, v in res[co][l].items()} for l in "AB"} for co in ["DLF", "GPL", "PML"]}, indent=0))
print(json.dumps({co: {k: (round(v, 2) if isinstance(v, float) else v) for k, v in s.items()} for co, s in scen.items()}))
print(json.dumps({co: {"g": implied[co]["terminal_g"], "ws": implied[co]["stable_wacc"]} for co in implied}))
print(json.dumps(implied["DLF"]["terminal_grid"]))

"""Charts for report and deck, read from the LibreOffice-recalculated workbook (numbers = model numbers)."""
import pathlib, json
import openpyxl, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "charts"
wb = openpyxl.load_workbook(ROOT / "models/excel/_recalc/BAV_RealEstate_Model.xlsx", data_only=True)
INK, MUTE, GRID = "#1F2A30", "#7A858C", "#E3E7E8"
C = {"DLF": "#2F5D62", "GPL": "#C08A3E", "PML": "#8C4A3C"}
NM = {"DLF": "DLF", "GPL": "Godrej Properties", "PML": "Phoenix Mills"}
plt.rcParams.update({"font.family": "Carlito", "font.size": 10, "axes.edgecolor": MUTE, "axes.labelcolor": INK,
                     "xtick.color": INK, "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "figure.dpi": 200, "savefig.bbox": "tight", "axes.titleweight": "bold", "axes.titlesize": 11,
                     "axes.titlelocation": "left"})


def find_row(ws, label, start=1, col=1):
    for r in range(start, ws.max_row + 1):
        if ws.cell(r, col).value == label:
            return r
    raise KeyError(label)


def block_rows(ws, label):
    return [r for r in range(1, ws.max_row + 1) if ws.cell(r, 1).value == label]


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", facecolor="white"); plt.close(fig)


cos = ["DLF", "GPL", "PML"]
yrs3 = ["FY24", "FY25", "FY26"]

# 1. DuPont 3-step factors
dp = wb["DuPont"]
rows = {k: block_rows(dp, k) for k in ["Net profit margin", "Equity multiplier", "ROE (3-step product)"]}
atos = [r for r in block_rows(dp, "Asset turnover")][::2]
fig, axs = plt.subplots(1, 4, figsize=(11, 2.9))
for ax, (title, rs, fmt) in zip(axs, [("Net profit margin", rows["Net profit margin"], "pct"), ("Asset turnover (x)", atos, "x"),
                                      ("Equity multiplier (x)", rows["Equity multiplier"][::2], "x"),
                                      ("ROE", rows["ROE (3-step product)"], "pct")]):
    for i, co in enumerate(cos):
        vals = [dp.cell(rs[i], c).value for c in (3, 4, 5)]
        ax.plot(yrs3, vals, marker="o", color=C[co], lw=2, label=NM[co])
    ax.set_title(title)
    if fmt == "pct":
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
axs[0].legend(frameon=False, fontsize=8, loc="best")
fig.suptitle("DuPont: what drives ROE (average balances)", x=0.01, ha="left", fontweight="bold", fontsize=12, color=INK)
fig.tight_layout(); save(fig, "dupont")

# 2. Real-estate operating signature: inventory days, advances/revenue, CFO/PAT
ra = wb["Ratios"]
fig, axs = plt.subplots(1, 3, figsize=(11, 2.9))
for ax, (lab, title) in zip(axs, [("Inventory days (on cost of revenue)", "Inventory days"),
                                  ("Customer advances / revenue (x)", "Customer advances ÷ revenue (x)"),
                                  ("CFO / PAT (x)", "Cash flow from operations ÷ PAT (x)")]):
    rs = block_rows(ra, lab)
    x = ["FY23", "FY24", "FY25", "FY26"]
    w = 0.26
    for i, co in enumerate(cos):
        vals = [ra.cell(rs[i], c).value for c in (3, 4, 5, 6)]
        vals = [v if isinstance(v, (int, float)) else np.nan for v in vals]
        ax.bar(np.arange(4) + (i - 1) * w, vals, w, color=C[co], label=NM[co])
    ax.set_xticks(range(4)); ax.set_xticklabels(x); ax.set_title(title)
    ax.axhline(0, color=MUTE, lw=0.8)
axs[0].legend(frameon=False, fontsize=8)
fig.tight_layout(); save(fig, "re_signature")

# 3. Beta regression scatter (DLF, monthly)
bm = wb["Beta_Monthly"]
hdrs = [bm.cell(4, c).value for c in range(1, bm.max_column + 1)]
mc, dc = hdrs.index("NIFTY50 ret") + 1, hdrs.index("DLF ret") + 1
pc, gc = hdrs.index("PML ret") + 1, hdrs.index("GPL ret") + 1
xs, ys, yp, yg = [], [], [], []
for r in range(6, 200):
    a, b = bm.cell(r, mc).value, bm.cell(r, dc).value
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        xs.append(a); ys.append(b); yp.append(bm.cell(r, pc).value); yg.append(bm.cell(r, gc).value)
xs, ys, yp, yg = map(np.array, (xs, ys, yp, yg))
fig, axs = plt.subplots(1, 3, figsize=(11, 3.2), sharex=True, sharey=True)
for ax, (co, y) in zip(axs, [("DLF", ys), ("GPL", yg), ("PML", yp)]):
    b, a = np.polyfit(xs, y, 1); r2 = np.corrcoef(xs, y)[0, 1] ** 2
    ax.scatter(xs, y, s=14, color=C[co], alpha=0.75, edgecolor="none")
    gx = np.linspace(xs.min(), xs.max(), 10); ax.plot(gx, a + b * gx, color=INK, lw=1.2)
    ax.set_title(f"{NM[co]}: β = {b:.2f}, R² = {r2:.2f}")
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
    ax.set_xlabel("Nifty 50 monthly return")
axs[0].set_ylabel("Stock monthly return")
fig.tight_layout(); save(fig, "beta_scatter")

# 4. Bottom-up beta bars
bu = wb["BottomUp_Beta"]
names, raw, unl = [], [], []
for r in range(5, 13):
    names.append(bu.cell(r, 1).value.replace(" Ltd", "").replace(" Enterprises", "").replace(" Estates", "").replace(" (Macrotech)", ""))
    raw.append(bu.cell(r, 2).value); unl.append(bu.cell(r, 7).value)
med = bu.cell(13, 7).value
fig, ax = plt.subplots(figsize=(8, 3.2))
xx = np.arange(len(names))
ax.bar(xx - 0.2, raw, 0.4, color="#B9C6C8", label="Regression (levered) β")
ax.bar(xx + 0.2, unl, 0.4, color=C["DLF"], label="Unlevered β")
ax.axhline(med, color=C["GPL"], lw=1.6, ls="--"); ax.text(len(names) - 0.6, med + 0.04, f"median unlevered β = {med:.2f}", color=C["GPL"], ha="right", fontsize=9)
ax.set_xticks(xx); ax.set_xticklabels(names, rotation=0, fontsize=8.5); ax.legend(frameon=False, fontsize=8, loc="upper left")
ax.set_title("Bottom-up beta: eight listed developers, unlevered at market D/E")
save(fig, "bottomup_beta")

# 5. Football fields
sm = wb["Summary"]
starts = block_rows(sm, "Method")
fig, axs = plt.subplots(1, 3, figsize=(12, 3.6))
for ax, co, st in zip(axs, cos, starts):
    labs, lo, hi, pt = [], [], [], []
    for r in range(st + 1, st + 8):
        lab = sm.cell(r, 1).value
        l, h, p = sm.cell(r, 2).value, sm.cell(r, 3).value, sm.cell(r, 4).value
        if not isinstance(p, (int, float)) or p == 0:
            continue
        labs.append(lab.replace("Relative — ", "").replace(" (25th–75th pct)", " IQR").replace("DCF (FCFF) — WACC±2% × g±1%", "DCF (FCFF) range"))
        lo.append(l); hi.append(h); pt.append(p)
    price = pt[-1]
    labs, lo, hi, pt = labs[:-1], lo[:-1], hi[:-1], pt[:-1]
    y = np.arange(len(labs))[::-1]
    for yi, l, h, p in zip(y, lo, hi, pt):
        ax.plot([l, h], [yi, yi], color=C[co], lw=7, solid_capstyle="butt", alpha=0.85)
        ax.plot(p, yi, marker="|", color=INK, ms=14, mew=2)
    ax.axvline(price, color=INK, lw=1, ls=":"); ax.text(price, -0.75, f" market ₹{price:,.0f}", fontsize=8.5, color=INK, va="center")
    ax.set_ylim(-1, len(labs) - 0.5)
    ax.set_yticks(y); ax.set_yticklabels(labs, fontsize=8.5); ax.set_title(NM[co]); ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"₹{v:,.0f}"))
fig.tight_layout(); save(fig, "football_field")

# 6. CAPM WACC vs market-implied WACC
imp = json.loads((ROOT / "data/processed/implied.json").read_text())
fig, ax = plt.subplots(figsize=(6.5, 3))
xx = np.arange(3)
ax.bar(xx - 0.2, [imp[c]["base_wacc"] for c in cos], 0.4, color="#B9C6C8", label="Our WACC (CAPM, FY27–31)")
ax.bar(xx + 0.2, [imp[c]["base_wacc"] + imp[c]["dw"] for c in cos], 0.4, color=[C[c] for c in cos], label="WACC implied by today's price")
for i, c in enumerate(cos):
    ax.text(i - 0.2, imp[c]["base_wacc"] + 0.003, f"{imp[c]['base_wacc']:.1%}", ha="center", fontsize=8.5)
    ax.text(i + 0.2, imp[c]["base_wacc"] + imp[c]["dw"] + 0.003, f"{imp[c]['base_wacc'] + imp[c]['dw']:.1%}", ha="center", fontsize=8.5)
gsec = wb["Inputs"]["B5"].value
ax.axhline(gsec, color=INK, ls=":", lw=1); ax.text(2.45, gsec + 0.002, f"10-yr G-Sec {gsec:.2%}", ha="right", fontsize=8)
ax.set_xticks(xx); ax.set_xticklabels([NM[c] for c in cos]); ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
ax.legend(frameon=False, fontsize=8, loc="upper right"); ax.set_ylim(0, 0.19)
ax.set_title("Reverse DCF: the discount rate the market is using")
save(fig, "implied_wacc")

# 7. P/B vs ROE regression
rv = wb["RelVal"]
pts = []
for r in range(5, 14):
    nm = rv.cell(r, 1).value
    if nm and isinstance(rv.cell(r, 12).value, (int, float)):
        pts.append((nm, rv.cell(r, 12).value, rv.cell(r, 14).value))
fig, ax = plt.subplots(figsize=(6.5, 3.4))
xr = np.array([p[1] for p in pts]); yr = np.array([p[2] for p in pts])
b, a = np.polyfit(xr, yr, 1); r2 = np.corrcoef(xr, yr)[0, 1] ** 2
for nm, x_, y_ in pts:
    key = {"DLF Ltd": "DLF", "Godrej Properties": "GPL", "Phoenix Mills": "PML"}.get(nm)
    ax.scatter(x_, y_, s=46 if key else 28, color=C[key] if key else "#9AA5AA", zorder=3)
    ax.annotate(nm.replace(" Ltd", "").replace(" (Macrotech)", ""), (x_, y_), xytext=(4, 3), textcoords="offset points", fontsize=8)
gx = np.linspace(xr.min() - 0.01, xr.max() + 0.01, 10); ax.plot(gx, a + b * gx, color=INK, lw=1)
ax.set_xlabel("ROE FY26"); ax.set_ylabel("P/B (x)")
ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
ax.set_title(f"P/B = {a:.2f} + {b:.1f} × ROE   (R² = {r2:.2f}, n = {len(pts)})")
save(fig, "pb_roe")

# 8. Altman Z vs Z''
az = wb["AltmanZ"]
zr, zz = block_rows(az, "Altman Z (original)"), block_rows(az, "Altman Z'' (EM, with 3.25 constant)")
fig, axs = plt.subplots(1, 2, figsize=(10, 2.9))
for ax, rs, title, lines in [(axs[0], zr, "Altman Z (1968) — manufacturing weights", (1.81, 2.99)),
                             (axs[1], zz, "Altman Z'' (emerging-market)", (4.35, 5.85))]:
    for i, co in enumerate(cos):
        ax.plot(["FY23", "FY24", "FY25", "FY26"], [az.cell(rs[i], c).value for c in (3, 4, 5, 6)], marker="o", color=C[co], lw=2, label=NM[co])
    for v in lines:
        ax.axhline(v, color=MUTE, ls="--", lw=0.8)
    ax.set_title(title)
axs[0].legend(frameon=False, fontsize=8)
fig.tight_layout(); save(fig, "altman")

# 9. Revenue and core EBIT margin history + forecast (DCF)
fig, axs = plt.subplots(1, 3, figsize=(12, 3))
for ax, co in zip(axs, cos):
    ws = wb[f"DCF_{co}"]
    yrs = ["FY26"] + [f"FY{27+i}" for i in range(10)]
    rev = [ws.cell(19, c).value for c in range(2, 13)]
    mar = [ws.cell(22, c).value for c in range(2, 13)]
    ax.bar(range(11), rev, color=[C[co]] + ["#C9D3D5"] * 10)
    ax.set_xticks(range(0, 11, 2)); ax.set_xticklabels(yrs[::2], fontsize=8)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v/1000:,.0f}k"))
    a2 = ax.twinx(); a2.plot(range(11), mar, color=INK, marker="o", ms=3, lw=1.4); a2.set_ylim(min(0, min(mar)) - 0.05, max(mar) + 0.1)
    a2.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0)); a2.grid(False)
    a2.spines["right"].set_visible(True)
    ax.set_title(f"{NM[co]}: revenue (₹ cr, bars) & core EBIT margin (line)")
fig.tight_layout(); save(fig, "dcf_paths")
print("charts:", sorted(p.name for p in OUT.glob("*.png")))

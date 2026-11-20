"""Python replica of the DCF sheet (reads base inputs from the recalculated workbook)."""
import pathlib, openpyxl, numpy as np
ROOT = pathlib.Path(__file__).resolve().parents[1]

def load_base():
    wb = openpyxl.load_workbook(ROOT / "models/excel/_recalc/BAV_RealEstate_Model.xlsx", data_only=True)
    out = {}
    for co in ["DLF", "GPL", "PML"]:
        ws = wb[f"DCF_{co}"]; v = lambda a: ws[a].value
        out[co] = dict(rev0=v("B19"), m0=v("B22"), g=[v(f"{c}5") for c in "CDEFG"], m=v("B6"), s2c=v("B7"), tax=v("B8"),
                       w=v("B9"), gT=v("B10"), ronic=v("B11"), ws=v("B14"), nonop=v("B41") + v("B42") + v("B43"),
                       mi=v("B45"), sh=v("B48"), price=v("B50"), vps=v("B49"), wB=v("Y33"), vpsB=v("Y35"))
    return out

def value(p, gscale=1.0, m=None, s2c=None, w=None, ws=None, gT=None, mid=True):
    m = p["m"] if m is None else m; s2c = p["s2c"] if s2c is None else s2c
    w = p["w"] if w is None else w; ws = p["ws"] if ws is None else ws; gT = p["gT"] if gT is None else gT
    g5 = [x * gscale for x in p["g"]]
    gs = g5 + [g5[-1] + (gT - g5[-1]) * k / 5 for k in range(1, 6)]
    rev, prev = [], p["rev0"]
    pv, prod = 0.0, 1.0
    for t in range(1, 11):
        r = prev * (1 + gs[t - 1]); wt = min(t, 5) / 5
        mt = p["m0"] * (1 - wt) + m * wt
        fcff = r * mt * (1 - p["tax"]) - (r - prev) / s2c
        wacc = w if t <= 5 else w + (ws - w) * (t - 5) / 5
        pv += fcff / (prod * (1 + wacc) ** (0.5 if mid else 1.0)); prod *= (1 + wacc)
        prev = r
    nopat11 = prev * (1 + gT) * m * (1 - p["tax"])
    tv = nopat11 * (1 - gT / p["ronic"]) / (ws - gT)
    return (pv + tv / prod + p["nonop"]) * (1 - p["mi"]) / p["sh"]

if __name__ == "__main__":
    B = load_base()
    for co, p in B.items():
        print(co, "engine A", round(value(p), 2), "sheet", round(p["vps"], 2), "| engine B", round(value(p, w=p["wB"]), 2), "sheet", round(p["vpsB"], 2))

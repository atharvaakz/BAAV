"""Solve the uniform WACC shift that equates DCF value per share to market price (bisection on recalculated model)."""
import json, pathlib, openpyxl
ROOT = pathlib.Path(__file__).resolve().parents[1]
wb = openpyxl.load_workbook(ROOT / "models/excel/_recalc/BAV_RealEstate_Model.xlsx", data_only=True)
out = {}
for co in ["DLF", "GPL", "PML"]:
    ws = wb[f"DCF_{co}"]
    v = lambda a: ws[a].value
    cols = "CDEFGHIJKL"
    fcff = [v(f"{c}26") for c in cols]; wacc = [v(f"{c}29") for c in cols]
    rev10, m, tax, g, ronic, ws_ = v("L19"), v("B6"), v("B8"), v("B10"), v("B11"), v("B14")
    nonop = v("B41") + v("B42") + v("B43"); mi, sh, px = v("B45"), v("B48"), v("B50")
    def val(dw):
        pv, prod = 0.0, 1.0
        for f, w in zip(fcff, wacc):
            pv += f / (prod * (1 + w + dw) ** 0.5); prod *= (1 + w + dw)
        tv = rev10 * (1 + g) * m * (1 - tax) * (1 - g / ronic) / (ws_ + dw - g) / prod
        return (pv + tv + nonop) * (1 - mi) / sh
    lo, hi = -0.09, 0.10
    for _ in range(200):
        mid = (lo + hi) / 2
        if val(mid) > px: lo = mid
        else: hi = mid
    out[co] = {"dw": round((lo + hi) / 2, 5), "value_check": round(val((lo + hi) / 2), 2), "price": px,
               "base_wacc": v("B9"), "stable_wacc": ws_}
    print(co, out[co])
(ROOT / "data/processed/implied.json").write_text(json.dumps(out, indent=1))

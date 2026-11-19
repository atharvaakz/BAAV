"""Pull headline numbers from the recalculated workbook into a dict (used by report, deck and viva pack)."""
import json, pathlib, openpyxl
ROOT = pathlib.Path(__file__).resolve().parents[1]
wb = openpyxl.load_workbook(ROOT / "models/excel/_recalc/BAV_RealEstate_Model.xlsx", data_only=True)
COS = ["DLF", "GPL", "PML"]
N = {}

def rows(ws, label):
    return [r for r in range(1, ws.max_row + 1) if ws.cell(r, 1).value == label]

def series(sheet, label, k, cols=(3, 4, 5, 6)):
    ws = wb[sheet]; r = rows(ws, label)[k]
    return [ws.cell(r, c).value for c in cols]

ra = wb["Ratios"]
ratio_labels = [ra.cell(r, 1).value for r in range(1, ra.max_row + 1) if ra.cell(r, 3).value is not None or ra.cell(r, 4).value is not None]
for k, co in enumerate(COS):
    d = N.setdefault(co, {})
    for lab in set(ratio_labels):
        try:
            d[lab] = series("Ratios", lab, k)
        except IndexError:
            pass
    dp = wb["DuPont"]
    for lab in ["Net profit margin", "Equity multiplier", "ROE (3-step product)", "Tax & JV burden", "Interest burden",
                "EBIT margin", "Return on net operating assets (RNOA)", "Net financial leverage (NFL)",
                "Net borrowing cost after tax (NBC)", "Operating ROE contribution", "Non-operating (JV, exceptional) contribution"]:
        rs = rows(dp, lab); r = rs[k] if len(rs) == 3 else rs[k * (len(rs) // 3)]
        d["DP " + lab] = [dp.cell(r, c).value for c in (3, 4, 5)]
    rs = rows(dp, "Asset turnover"); r = rs[2 * k]
    d["DP Asset turnover"] = [dp.cell(r, c).value for c in (3, 4, 5)]
    for lab in ["  from margin", "  from asset turnover", "  from leverage", "  total = ΔROE"]:
        d["ROEattr" + lab.strip()] = dp.cell(rows(dp, lab)[k], 3).value
    az = wb["AltmanZ"]
    d["Z"] = [az.cell(rows(az, "Altman Z (original)")[k], c).value for c in (3, 4, 5, 6)]
    d["Zpp"] = [az.cell(rows(az, "Altman Z'' (EM, with 3.25 constant)")[k], c).value for c in (3, 4, 5, 6)]
    rc = wb["Recast"]
    for lab in ["Core operating EBIT", "NOPAT = core EBIT × (1 − t)", "Share of JV/associate profit (post-tax)",
                "Cash & liquid investments", "Restricted cash (kept operating)", "Net financial obligations (NFO)",
                "Net operating assets = invested capital", "Customer advances & other op. liabilities (derived)",
                "Interest capitalised (cash paid − P&L cost)", "EBIT incl. other income"]:
        d["RC " + lab] = series("Recast", lab, k)
    ge = wb["Growth_EVA"]
    for lab in ["Revenue CAGR FY23→FY26", "PAT CAGR FY23→FY26"]:
        d[lab] = ge.cell(rows(ge, lab)[k], 6).value
    for lab in ["EVA = NOPAT − WACC × opening NOA", "EVA spread = ROIC − WACC", "Fundamental growth = RR × ROIC",
                "Sustainable EPS growth = b × ROE", "Reinvestment rate = ΔNOA / NOPAT"]:
        d[lab] = [ge.cell(rows(ge, lab)[k], c).value for c in (4, 5, 6)]
    wc = wb["WACC"]
    for r in range(5, 25):
        d["W " + wc.cell(r, 1).value] = wc.cell(r, 2 + k).value
    ws = wb[f"DCF_{co}"]
    d["DCF"] = {ws.cell(r, 1).value: ws.cell(r, 2).value for r in range(36, 53)}
    d["DCF growth"] = [ws.cell(5, c).value for c in range(3, 8)]
    d["DCF margin"], d["DCF s2c"] = ws["B6"].value, ws["B7"].value
    d["DCF stableWACC"] = ws["B14"].value
    d["DCF rev"] = [ws.cell(19, c).value for c in range(2, 14)]
    d["DCF fcff"] = [ws.cell(26, c).value for c in range(3, 14)]
    d["DCF roic"] = [ws.cell(28, c).value for c in range(3, 13)]
    d["gridA"] = [[ws.cell(r, c).value for c in range(15, 20)] for r in range(6, 11)]
    d["gridB"] = [[ws.cell(r, c).value for c in range(22, 27)] for r in range(6, 11)]
    d["gridA_min"], d["gridA_max"] = ws["O11"].value, ws["O12"].value
    d["implied margin"] = ws["Y19"].value
    d["implied dW"], d["implied WACC"] = ws["Y25"].value, ws["Y26"].value
    if co == "DLF":
        d["DCCDL"] = {"jv_pat": ws["H43"].value, "value": ws["H44"].value, "book": ws["H45"].value}
    dd = wb["DDM"]
    d["DDM"] = {dd.cell(r, 1).value: dd.cell(r, 2 + k).value for r in range(5, 20)}
    sm = wb["Summary"]; st = rows(sm, "Method")[k]
    d["FF"] = [(sm.cell(r, 1).value, sm.cell(r, 2).value, sm.cell(r, 3).value, sm.cell(r, 4).value) for r in range(st + 1, st + 8)]
rv = wb["RelVal"]
N["RelVal"] = [[rv.cell(r, c).value for c in range(1, 18)] for r in list(range(5, 8)) + list(range(9, 14))]
N["RelStats"] = {rv.cell(r, 1).value: [rv.cell(r, c).value for c in range(13, 18)] for r in range(15, 21)}
N["RelImplied"] = {rv.cell(r, 1).value: [rv.cell(r, c).value for c in range(2, 11)] for r in range(24, 27)}
N["Reg"] = {"a": rv["B30"].value, "b": rv["B31"].value, "r2": rv["B32"].value}
bu = wb["BottomUp_Beta"]
N["BU"] = [[bu.cell(r, c).value for c in range(1, 9)] for r in range(5, 13)]
N["BU_median"], N["BU_se"] = bu["G13"].value, bu["G15"].value
for name in ["Beta_Monthly", "Beta_Weekly", "Beta_REIT"]:
    ws = wb[name]
    hdrc = [c for c in range(1, ws.max_column + 1) if ws.cell(4, c).value == "Statistic"][0]
    N[name] = {ws.cell(4, c).value: {ws.cell(r, hdrc).value: ws.cell(r, c).value for r in range(5, 18)}
               for c in range(hdrc + 1, ws.max_column + 1) if ws.cell(4, c).value}
inp = wb["Inputs"]
N["Inputs"] = {inp.cell(r, 1).value: inp.cell(r, 2).value for r in range(4, 16)}
(ROOT / "data/processed/numbers.json").write_text(json.dumps(N, indent=1, default=str))
if __name__ == "__main__":
    print(list(N["DLF"].keys())[:10]); print(N["RelImplied"]); print(N["Reg"]); print(N["DLF"]["DCCDL"])
    print({k: N["Beta_Monthly"][k]["Raw beta (SLOPE)"] for k in list(N["Beta_Monthly"])[:3]})

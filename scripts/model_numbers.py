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
lab = {rv.cell(r, 1).value: r for r in range(1, rv.max_row + 1) if rv.cell(r, 1).value}
peer_rows = [r for r in range(5, lab["Distribution of peer multiples"]) if rv.cell(r, 2).value is not None and r != 8]
N["RelVal"] = [[rv.cell(r, c).value for c in range(1, 18)] for r in peer_rows]
N["RelStats"] = {k: [rv.cell(lab[k], c).value for c in range(13, 18)] for k in ["High", "75th percentile", "Median", "Average", "25th percentile", "Low"]}
ivh = lab["Target / multiple"]
N["RelImplied"] = {rv.cell(r, 1).value: [rv.cell(r, c).value for c in range(2, 11)] for r in range(ivh + 1, ivh + 4)}
N["Reg"] = {"a": rv.cell(lab["Intercept (a)"], 2).value, "b": rv.cell(lab["Slope on ROE (b)"], 2).value, "r2": rv.cell(lab["R-squared"], 2).value}
N["n_peers"] = len(peer_rows) - 3
bu = wb["BottomUp_Beta"]
bl = {bu.cell(r, 1).value: r for r in range(1, bu.max_row + 1) if bu.cell(r, 1).value}
mr = [r for k, r in bl.items() if str(k).startswith("Median unlevered beta")][0]
N["BU"] = [[bu.cell(r, c).value for c in range(1, 9)] for r in range(5, mr)]
N["BU_median"], N["BU_se"] = bu.cell(mr, 7).value, bu.cell(mr + 2, 7).value
for name in ["Beta_Monthly", "Beta_Weekly", "Beta_REIT"]:
    ws = wb[name]
    hdrc = [c for c in range(1, ws.max_column + 1) if ws.cell(4, c).value == "Statistic"][0]
    N[name] = {ws.cell(4, c).value: {ws.cell(r, hdrc).value: ws.cell(r, c).value for r in range(5, 18)}
               for c in range(hdrc + 1, ws.max_column + 1) if ws.cell(4, c).value}
inp = wb["Inputs"]
N["Inputs"] = {inp.cell(r, 1).value: inp.cell(r, 2).value for r in range(4, 16)}
for k, co in enumerate(COS):
    ws = wb[f"DCF_{co}"]
    N[co]["lensB"] = {"wacc": ws["Y33"].value, "stable": ws["Y34"].value, "vps": ws["Y35"].value, "upside": ws["Y36"].value}
    wc = wb["WACC"]; c = "BCD"[k]
    N[co]["W_B"] = {"beta_u": wc[f"{c}27"].value, "beta": wc[f"{c}29"].value, "ke": wc[f"{c}30"].value, "wacc": wc[f"{c}31"].value, "dam": wc[f"{c}32"].value}
    q = wb["Quarterly"]; ttm = [r for r in range(1, q.max_row + 1) if q.cell(r, 1).value == "TTM P/E at latest price"][k]
    N[co]["ttm_pe"] = q.cell(ttm, 8).value
    rsh = wb["ResidualIncome"]
    rows_ = {lab_: [r for r in range(1, rsh.max_row + 1) if rsh.cell(r, 1).value == lab_][k] for lab_ in
             ["Value per share — lens A (₹)", "Value per share — lens B (₹)", "Justified P/B on current ROE — lens A", "Justified P/B on current ROE — lens B",
              "ROE the market price implies (lens A Ke) = g + P/B × (Ke − g)"]}
    N[co]["RI"] = {k2: rsh.cell(r, 2).value for k2, r in rows_.items()}
    av = wb["Alt_Valuations"]
    dif = [r for r in range(1, av.max_row + 1) if av.cell(r, 1).value == "Difference (should be ~0)"][k]
    N[co]["EVA_diff"] = av.cell(dif, 2).value; N[co]["EVA_value"] = av.cell(dif - 1, 2).value; N[co]["FCFF_value_ye"] = av.cell(dif - 3, 2).value
    N[co]["midyear_uplift"] = av.cell(dif + 1, 2).value
cr = wb["CapRates"]
N["Cap"] = {"ev": cr["B8"].value, "ebitda": cr["B9"].value, "yield": cr["B10"].value, "spread": cr["B12"].value,
            "reits": [[cr.cell(r, c).value for c in range(1, 6)] for r in range(16, 20)], "reit_median": cr["D21"].value, "pml_at_reit": cr["D22"].value}
ro = wb["RealOption"]; N["RO"] = {ro.cell(r, 1).value: ro.cell(r, 2).value for r in range(5, 17)}
rf = wb["RateFactor"]; N["RateFactor"] = {rf.cell(4, c).value: [rf.cell(r, c).value for r in range(5, 12)] for c in range(10, 14)}
ls = wb["LongCycle"]
sc0 = [c for c in range(1, ls.max_column + 1) if ls.cell(4, c).value == "Statistic"][0]
N["LongCycle"] = {ls.cell(4, c).value: [ls.cell(r, c).value for r in range(5, 10)] for c in range(sc0 + 1, sc0 + 7)}
he = wb["HistERP"]; N["HistERP"] = {he.cell(r, 7).value: he.cell(r, 8).value for r in range(5, 13)}
hs = wb["Housing"]; N["Housing"] = {hs.cell(r, 8).value: hs.cell(r, 9).value for r in range(5, 11) if hs.cell(r, 8).value}
rb = wb["RollingBeta"]; N["RollingBeta"] = {rb.cell(r, 12).value: [rb.cell(r, c).value for c in (13, 14, 15)] for r in range(23, 27)}
ib = wb["Industry_Benchmark"]; N["Industry"] = {ib.cell(r, 1).value: [ib.cell(r, c).value for c in range(2, 7)] for r in range(5, 20)}
nv = wb["NAV_SOTP"]; N["NAV"] = {"dccdl_gav": nv["B8"].value, "dccdl_stake": nv["B11"].value, "dlf_res_pv": nv["B17"].value, "dlf_netcash": nv["B18"].value,
    "dlf_nav": nv["B19"].value, "dlf_nav_ps": nv["B20"].value, "dlf_mcap": nv["B21"].value, "dlf_land": nv["B22"].value, "dlf_psf": nv["B24"].value, "dlf_book_psf": nv["B25"].value,
    "pml_gav": nv["B39"].value, "pml_nav": nv["B42"].value, "pml_nav_ps": nv["B43"].value, "pml_prem": nv["B45"].value, "pml_g_in_cap": nv["B46"].value,
    "dlf_nav_ps_hi": nv["C28"].value, "dlf_sold_margin": nv["B26"].value, "gpl_grid_lo": nv["B68"].value, "gpl_grid_hi": nv["D70"].value, "gpl_emb_pat": nv["B54"].value, "gpl_emb_ps": nv["B57"].value, "gpl_g_in_mult": nv["B59"].value, "gpl_consensus": nv["B61"].value}
okk = wb["Operating_KPIs"]; N["KPI"] = {okk.cell(r, 1).value: [okk.cell(r, c).value for c in (2, 3, 4)] for r in range(5, 33) if okk.cell(r, 1).value}
dc = wb["Data_Check"]; N["DataCheck"] = [[dc.cell(r, c).value for c in range(1, 6)] for r in range(5, 13)]
bk = wb["Broker_Views"]; N["Brokers"] = [[bk.cell(r, c).value for c in range(1, 6)] for r in range(5, bk.max_row + 1) if bk.cell(r, 1).value]

of_ = wb["Official_Disclosures"]
def _lab(ws, s, col=2):
    for r in range(1, ws.max_row + 1):
        v = ws.cell(r, 1).value
        if isinstance(v, str) and v.startswith(s):
            return ws.cell(r, col).value
N["MGMT"] = {"fcf": _lab(of_, "Development FCF, year 1"), "dev": _lab(of_, "Development business value"), "eq": _lab(of_, "Equity value — management case"),
             "ps": _lab(of_, "Per share (₹)"), "ps_nav": _lab(of_, "Per share with DCCDL"), "pv10": _lab(of_, "PV of FCF years 1–10"), "pvtv": _lab(of_, "PV of terminal value")}
N["GC"] = [[of_.cell(r, c).value for c in range(1, 5)] for r in range(1, of_.max_row + 1) if of_.cell(r, 4).value is not None and isinstance(of_.cell(r, 4).value, (int, float)) and of_.cell(r, 2).value and of_.cell(r, 3).value]
es_ = wb["ESG_BRSR"]; N["ESG"] = {es_.cell(r, 1).value: [es_.cell(r, 2).value, es_.cell(r, 3).value] for r in range(5, 19) if es_.cell(r, 1).value}
dl_ = wb["Delay_Cost"]
N["Delay"] = {"dlf_ps": dl_["B10"].value, "gpl_ps": dl_["C10"].value, "pml_ps": dl_["D10"].value, "dlf_pct": dl_["B11"].value, "gpl_pct": dl_["C11"].value, "pml_pct": dl_["D11"].value,
              "mgmt_cr": dl_["B17"].value, "mgmt_ps": dl_["B18"].value, "escrow": dl_["B19"].value}
rp_ = wb["REIT_Spread"]; N["REITopt"] = {"ebitda": rp_["B28"].value, "at_reit": rp_["B29"].value, "at_capm": rp_["B30"].value, "prem": rp_["B31"].value}
N["EV"] = json.loads((ROOT / "data/processed/v2/events.json").read_text())
ivc_ = wb["Industry_vs_Company"]; lit_ = wb["Literature"]; idd_ = wb["Industry_Data"]
def _find_row(ws, s):
    for r in range(1, ws.max_row + 1):
        v = ws.cell(r, 1).value
        if isinstance(v, str) and v.startswith(s):
            return r
N["IVC"] = {"g_dlf": ivc_["B7"].value, "g_gpl": ivc_["C7"].value, "g_ind": ivc_["D7"].value, "sh_dlf": ivc_["B8"].value, "sh_gpl": ivc_["C8"].value,
            "sh_dlf_prev": ivc_["B9"].value, "sh_gpl_prev": ivc_["C9"].value, "stuck_yrs": ivc_["D17"].value}
_l = _find_row(lit_, "Customer advances FY26")
N["LITQ"] = {"adv_dlf": lit_.cell(_l, 2).value, "adv_gpl": lit_.cell(_l, 3).value, "save_dlf": lit_.cell(_l + 2, 2).value, "save_gpl": lit_.cell(_l + 2, 3).value,
             "pat_dlf": lit_.cell(_l + 3, 2).value, "pat_gpl": lit_.cell(_l + 3, 3).value, "ps_dlf": lit_.cell(_l + 4, 2).value, "ps_gpl": lit_.cell(_l + 4, 3).value,
             "lit_gpl": lit_.cell(_find_row(lit_, "Godrej value at risk"), 2).value}
N["IND"] = {"cagr": idd_.cell(_find_row(idd_, "Sales CAGR"), 2).value, "fall": idd_.cell(_find_row(idd_, "Peak-to-trough"), 2).value}
v2 = ROOT / "data/processed/v2"
N["MC"] = json.loads((v2 / "monte_carlo.json").read_text()); N["SC"] = json.loads((v2 / "scenarios.json").read_text())
N["A2"] = json.loads((v2 / "analysis_v2.json").read_text())
(ROOT / "data/processed/numbers.json").write_text(json.dumps(N, indent=1, default=str))
if __name__ == "__main__":
    print(list(N["DLF"].keys())[:10]); print(N["RelImplied"]); print(N["Reg"]); print(N["DLF"]["DCCDL"])
    print({k: N["Beta_Monthly"][k]["Raw beta (SLOPE)"] for k in list(N["Beta_Monthly"])[:3]})

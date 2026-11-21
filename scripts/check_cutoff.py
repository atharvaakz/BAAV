"""Verify no output uses data dated after the 31-Oct-2026 cutoff."""
import json, pathlib, re
import pandas as pd
CUT = pd.Timestamp("2026-10-31")
ROOT = pathlib.Path(__file__).resolve().parents[1]
bad = []
for f in list((ROOT / "data").rglob("*.csv")):
    if "damodaran" in str(f):
        continue
    try:
        d = pd.read_csv(f, index_col=0, nrows=100000)
    except Exception:
        continue
    for lab in list(d.index[-3:]) + list(d.columns):
        s = str(lab)[:10]
        if re.match(r"^\d{4}-\d{2}-\d{2}$", s) and pd.Timestamp(s) > CUT:
            bad.append(f"{f.relative_to(ROOT)}: {s}"); break
for f in (ROOT / "data/processed").rglob("*.json"):
    for s in set(re.findall(r"20\d\d-\d\d-\d\d", f.read_text())):
        if pd.Timestamp(s) > CUT:
            bad.append(f"{f.relative_to(ROOT)}: {s}")
print("post-cutoff dates found:", len(bad)); print("\n".join(sorted(bad)[:30]))

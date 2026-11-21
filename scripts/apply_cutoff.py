"""Enforce the project's data cutoff: nothing dated after 31 October 2026 is used.

Truncates every raw market-data file (prices, dividends, splits) in place; the original downloads remain in git history.
Run before the pipeline; scripts/check_cutoff.py verifies no processed output carries later dates.
"""
import pathlib
import pandas as pd

CUTOFF = pd.Timestamp("2026-10-31")
ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
n = 0
for f in sorted(RAW.rglob("*.csv")):
    if "damodaran" in str(f):
        continue
    try:
        d = pd.read_csv(f, index_col=0)
    except Exception:
        continue
    if d.empty:
        continue
    try:
        idx = pd.to_datetime([str(x)[:10] for x in d.index], errors="coerce")
    except Exception:
        continue
    if idx.isna().mean() > 0.5:      # statement files have dates as columns
        cols = pd.to_datetime([str(c)[:10] for c in d.columns], errors="coerce")
        if cols.notna().mean() > 0.5 and (cols > CUTOFF).any():
            d = d.loc[:, ~(cols > CUTOFF)]; d.to_csv(f); n += 1
        continue
    keep = ~(idx > CUTOFF)
    if (~keep).any():
        d[keep].to_csv(f); n += 1
print("files truncated:", n)

"""Recalculate the workbook with LibreOffice and report errors + key outputs."""
import subprocess, pathlib, sys, shutil
import openpyxl
ROOT = pathlib.Path(__file__).resolve().parents[1]
src = ROOT / "models/excel/BAV_RealEstate_Model.xlsx"
out = ROOT / "models/excel/_recalc"
shutil.rmtree(out, ignore_errors=True); out.mkdir()
subprocess.run(["soffice", "--headless", "--calc", "--convert-to", "xlsx", "--outdir", str(out), str(src)],
               check=True, capture_output=True, timeout=300)
wb = openpyxl.load_workbook(out / src.name, data_only=True)
errs = []
for ws in wb:
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and c.value.startswith(("#", "Err:")):
                errs.append(f"{ws.title}!{c.coordinate}={c.value}")
print("errors:", len(errs)); print("\n".join(errs[:40]))
def show(sheet, rng):
    ws = wb[sheet]
    for row in ws[rng]:
        vals = [c.value for c in row]
        if any(v is not None for v in vals):
            print(" | ".join(f"{v:,.4g}" if isinstance(v, (int, float)) else str(v)[:38] for v in vals))
for spec in sys.argv[1:]:
    s, r = spec.split("!"); print("=====", spec); show(s, r)

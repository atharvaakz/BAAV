#!/bin/bash
# Rebuild every deliverable from raw data, in dependency order.
set -e
cd "$(dirname "$0")/.."
python3 -W ignore src/bav/data.py >/dev/null          # standardise raw statements
python3 -W ignore scripts/events.py >/dev/null       # event studies, survivorship, REIT spread, issuance timing
python3 -W ignore scripts/build_model.py              # workbook (formulas)
python3 -W ignore scripts/check_model.py              # LibreOffice recalc + error scan
python3 scripts/implied_wacc.py                       # reverse-DCF discount rate
(cd scripts && python3 -W ignore monte_carlo.py >/dev/null)  # scenarios, implied g, Monte Carlo (validated engine)
python3 -W ignore scripts/analysis_v2.py >/dev/null   # long-cycle, rolling beta, rate factor, ERP, housing
python3 -W ignore scripts/build_model.py              # embed implied WACC, MC, scenarios
python3 -W ignore scripts/check_model.py
python3 -W ignore scripts/model_numbers.py >/dev/null # numbers for documents
python3 -W ignore scripts/make_charts.py >/dev/null
python3 -W ignore scripts/make_charts_v2.py >/dev/null
python3 -W ignore scripts/build_report_v2.py
python3 -W ignore scripts/build_deck_v2.py
python3 -W ignore scripts/build_viva.py
(cd reports && for f in ProjectBaav_Group27_Report.docx ProjectBaav_Group27_Presentation.pptx Viva_Prep_Pack.docx; do soffice --headless --convert-to pdf "$f" >/dev/null 2>&1; done)
pdfinfo reports/ProjectBaav_Group27_Report.pdf | grep Pages

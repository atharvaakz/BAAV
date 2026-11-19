# Batch 2 — Pharma group's Excel models (Sun Pharma, Dr Reddy's, Cipla + Graphs)

Same 22-sheet template per company, built on a **Screener.in "Export to Excel" Data Sheet**
(P&L, BS, CF, quarters, price, shares). Strongest model seen so far. Sheet order:
Financials> HistoricalFS | Forecasting | Analysis> Ratio Analysis | DuPont | Altman Z | Beta Calc |
WACC | Intrinsic Growth | DCF | Rel Val | Data> raw P&L/BS/CF/Quarters/Comps/NIFTY 50.

Techniques beyond batch 1:
- Forecasting: Excel FORECAST() linear trend on 10 yrs of Sales/EBITDA (FY16-25) -> FY26-30.
- Ratio sheet (~36 ratios): growth (sales/EBITDA/EBIT/NP/dividend), margins, liquidity, leverage,
  ROCE, ROE, retained earnings %, self-sustained growth rate, turnover ratios, debtor/payable/
  inventory days, cash conversion cycle, CFO/Sales, CFO/Assets, CFO/Debt.
- DuPont uses AVERAGE equity & average assets (better than year-end in batch 1).
- Altman Z (1.2/1.4/3.3/0.6/1.0) with Distressed/Grey/Safe flag + chart.
- Beta: 3-yr WEEKLY returns vs Nifty, Blume adjustment, "beta drifting"; plus
  **bottom-up beta**: peer comps (5 cos) levered beta -> unlever -> median -> relever at own D/E.
- WACC: Kd = max(interest/borrowings, Rf + US spread + India 2.18%), market-value weights.
- Intrinsic growth = Reinvestment rate x ROIC (built from raw BS: NWC + net fixed assets).
  -> fixes batch-1 inconsistency. FCFF = EBIT(1-t) x (1 - reinvestment rate).
- DCF: mid-year convention (0.5, 1.5, 2.5...), terminal g 6.25%, price = 6-month average,
  OVERVALUED/UNDERVALUED flag.
- Rel Val: 6 comps, EV and equity multiples with High/75th pct/Avg/Median/25th pct/Low ->
  implied value per share range.
- Graphs file: industry-specific driver table (R&D % of sales, ANDA filings) + macro charts.
  -> RE analogue: pre-sales, collections, launches (msf), rental income/occupancy.

Plan for our model: adopt this template's rigor + batch-1 presentation (formula->chart->
observation->suggestion->limitation), add 5-step DuPont, ROE attribution, sensitivity grid,
scenarios, NAV/SOTP for real estate, football-field chart.

Data needed: Screener.in Excel exports for DLF, Godrej Properties, Phoenix Mills
(+ peers: Oberoi Realty, Prestige, Brigade, Sobha, Lodha/Macrotech) — requires login, user to download.

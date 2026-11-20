# Senior-analyst review of v2 (self-audit) → v3 work orders
Reviewer stance: IC memo standard. Would I sign this? Where would a PM or the professor push back?

## A. What a PM would attack
1. **Operating KPIs missing.** A developer valuation without pre-sales (bookings), collections, launches and land bank is
   not credible to a sector analyst. Revenue (Ind AS 115) lags; the market prices bookings. → W1: research FY24–FY26
   bookings/collections/launches for DLF & Godrej; rental income, occupancy, consumption for Phoenix; DCCDL rental.
2. **No NAV / SOTP.** Sell-side values Indian developers on NAV (land bank + ongoing projects + rental at cap rate).
   Our DCF on recognised revenue is the textbook route; a NAV cross-check is the practitioner route. → W2: build a
   public-data SOTP/NAV (DLF: development pipeline + DCCDL stake; Phoenix: rental EBITDA at cap rate per asset class;
   Godrej: bookings-based value of pipeline). Label assumptions.
3. **Data verification.** Yahoo numbers unverified against filings. → W3: cross-check headline FY26 numbers
   (revenue, PAT, net debt) against company releases via web search; log differences.
4. **Consensus context.** What do brokers think? → W4: collect public broker target prices / ratings; compare.
5. **Godrej 'special items' (₹2,072 cr FY26)** drive the 'core EBIT negative' claim. Must know what they are
   (JV fair-value gains? land sale?). → W5: research and, if they are recurring development profits via JVs,
   say so — it changes the narrative (Godrej's model routes profit through JVs).
6. **DLF JV share (₹1,793 cr)** includes DCCDL — check against DCCDL's reported profit and DLF's 66.66% share. → W6.
7. **Terminal value** 52–79% of value; the g ≤ Rf cap is defensible but debatable for India. Already shown via implied g.
   → keep; add one line on what nominal GDP (IMF) expects.
8. **Phoenix lens B** gives Ke < G-Sec — flagged; fine.
9. **Beta**: large-cap vs industry — consider Dimson/sum-beta for thin trading on peers (small caps in peer set:
   Sunteck, Puravankara, Mahindra Lifespace). → W7: compute Dimson betas (lag 1) for the peer set; see if median moves.
10. **Presentation**: deck slides dense on 7 and 8; report has 16 figures — fine. Add an "Analyst's notes" box with the
    three non-obvious insights.

## B. Order of work
W5 → W1 → W3 → W6 → W2 → W4 → W7 → integrate (model sheet 'Operating_KPIs', 'NAV_SOTP', report §, deck slide, viva) → rebuild → fact-check → send.

## Progress log (round 1–2)
- [x] W5 Godrej 'special items' = JV stake divestments + Ind AS 109 fair-value re-measurement gains (+ interest on JV loans). Narrative made specific.
- [x] W1 Operating KPIs collected (bookings, collections, guidance, rental, consumption, DCCDL EBITDA/net debt) → Operating_KPIs sheet.
- [x] W3 Data verification → Data_Check: PAT matches (Godrej, Phoenix exact; DLF 0.2%); revenue/cash differ by definition.
- [x] W6 DLF JV share = 66.66% × DCCDL PAT within ~1%.
- [x] W2 NAV/SOTP: DLF identifiable NAV ₹312–386/sh; residual land ₹1.12 lakh cr (59% of mcap) ≈ ₹7,568/sq ft vs book ₹1,315/sq ft. Phoenix NAV ₹909 (price 143% above). Godrej 12x embedded PAT ₹2,564; grid ₹1,709–3,589.
- [x] W4 Broker views: medians DLF ₹752, Godrej ₹2,350, Phoenix ₹2,200.
- [x] W7 Dimson: median peer beta 1.47 → 1.59; small caps biased low → supports lens A / H2.
- [x] Macro/cycle: RBI hiked to 5.50% (7-Oct-26); Q3-26 sales +3% (Anarock) / −6% (PropEquity); inventory +12%; IMF FY27 real 7%, nominal ~10%.
- [x] Godrej cash: statutory CFO −₹2,003 cr vs management pre-land OCF +₹7,830 cr — narrative corrected everywhere.
- [x] Reality check vs H1 FY27: DLF revenue −37% → FY27 growth cut +40% → −15%; DCF ₹340 → ₹289 (now ≈ identifiable NAV).
- [x] Robust P/B–ROE regression: Signature Global (ROE 85%) excluded by rule (ROE > 50%) → P/B = 1.71 + 18.3·ROE, R² 0.19.
- [x] Phoenix minorities: CPPIB 49% Island Star buy-out (₹5,450 cr, 4 tranches; stake now 68.1%) — value-neutral at fair price; FY26 share kept.
- [x] Q2 FY27 update: DLF H1 bookings ₹4,457 cr vs ₹20,000 cr guide; Godrej H1 bookings +7%, collections +25%; Phoenix rent +16%, guidance 14–15%.
- [x] Sector P/E 40.5x vs 5-yr median 48.5x (indexPe) — not stretched vs recent history; premium is vs intrinsic value.
## Open (needs user)
- Verify KPIs/broker figures against original investor presentations and broker PDFs.
- Textbooks (Mac folder) still not accessible; concept map built from handout chapter references.

## Round: official disclosures (transcripts, BRSR)
- Added Official_Disclosures sheet (DLF/Phoenix Q4 FY26 calls, Godrej Q2 FY27), guidance-credibility table, management-case DLF DCF (₹455/share; ₹553 with DCCDL at 7.5% cap).
- Added ESG_BRSR sheet (DLF BRSR FY25, DCCDL SR FY26). NAV now uses official 137 msf potential (112 msf outside pipeline); Phoenix office/hotel EBITDA from the call (141/276).
- Report §9 subsection, 5 viva Q&As, deck notes. Blocked: NSE (503) / BSE (403) filings; Godrej & Phoenix BRSRs.
- Annual-report tie-out: DLF FY26 IAR (dlf.in) and Godrej FY26 IAR (company CDN) — equity, assets, inventory, PAT, JV profit, CFO match exactly; RERA notes ≈ ₹11,170 cr confirm transcript. Godrej BRSR FY26 added. Phoenix site fails TLS via proxy.

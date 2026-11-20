"""Industry-level data for Indian real estate (sourced inputs; one place for the model, charts and documents).

All figures are as published by the named source; blanks are years we could not verify. Units noted per series.
"""

# Top-7 cities residential (ANAROCK): units, lakh. Calendar years.
RESI = {  # year: (sales, launches, unsold_stock_end, overhang_months)
    2013: (3.184, None, None, None),
    2014: (3.430, 5.45, None, None),
    2015: (3.083, None, None, None),
    2016: (2.393, 2.50, 8.04, None),
    2017: (2.111, 1.469, 7.27, None),
    2018: (2.48, 1.953, None, None),
    2019: (2.614, 2.37, 6.44, None),
    2020: (1.384, None, None, None),
    2021: (2.365, None, 6.38, None),
    2022: (3.649, None, None, 25),
    2023: (4.765, 4.46, None, 15),
    2024: (4.597, 4.12, 5.53, 14),
    2025: (3.956, 4.19, 5.75, 18),
}
RESI_VALUE = {2024: 5.68, 2025: 6.00}  # sales value, ₹ lakh crore (ANAROCK)
RESI_SRC = ("ANAROCK annual reports 2024 and 2025 and year-end releases (via Business Standard, Zee Business, Outlook Business, Moneylife, PRNewswire). "
            "2018 sales derived from '2019 up 5%'; 2017 revised series (first print 2.03 lakh); unsold 2016–17 Q4, 2019 = Q1-2020; 2025 unsold = 2024 +4%; "
            "2022 overhang 'over 25 months' (early 2022); 2025 overhang ≈ Q1-2026 18 months.")

CITY_OVERHANG = {"NCR": (88, 17, 19), "MMR": (55, 14, None)}  # months: 2020, 2023/24, 2025 (ANAROCK 2025)

STALLED = {"homes_stuck_or_delayed_lakh": 6.29, "value_lakh_cr": 5.05, "fully_stalled_lakh": 1.74, "ncr_share": 0.52, "mmr_share": 0.28,
           "src": "ANAROCK stalled/delayed housing tracker (most projects launched 2014 or earlier)"}
MAHARERA = {"registered": 36869, "completed_share": 0.26, "lapsed_mar22": 4555, "lapsed_old_6y": 2789, "nclt_projects": 314,
            "src": "MahaRERA data via Free Press Journal / Housing.com (2022–24)"}

HPI = {"Q1 FY26": 0.036, "Q2 FY26": 0.022, "Q3 FY26": 0.036, "Q4 FY26": 0.042}  # RBI all-India HPI, y/y (18 cities, base 2022-23)
HPI_SRC = "RBI press releases on the All-India House Price Index, 2025-26 (Q4 via press report)"

OFFICE_2025 = {"JLL gross leasing (msf)": 83.3, "Cushman & Wakefield gross leasing (msf)": 88.7, "CBRE leasing (msf)": 82.6,
               "Knight Frank gross leasing (msf)": 86.4, "C&W net absorption (msf)": 61.4, "C&W net absorption 2024 (msf)": 49.1}
MALLS = {"new_supply_2025_msf": 5.2, "leasing_2025_msf": 13.0, "gradeA_vacancy_h1_2026": 0.067, "gradeA_rent_cagr": "5–8%",
         "ghost_malls_share": 0.20, "ghost_malls": "74 of 365 malls >40% vacant", "src": "ANAROCK retail (2025–H1 2026); Knight Frank 'Think India Think Retail'"}
NBFC = {"nbfc_share_dev_funding_fy18": 0.50, "nbfc_dev_loans_trn": 4.0, "dev_loans_share_nbfc_books": 0.21,
        "src": "ANAROCK (Moneylife, 2018); Credit Suisse via press; RBI FSR June 2019"}

# Company operating data for comparison (₹ crore unless stated)
BOOKINGS = {"DLF": {"FY25": 21223, "FY26": 20143}, "GPL": {"FY24": 22527, "FY25": 29444, "FY26": 34171}}
GPL_DELIVERIES = {"FY24": (12.5, None), "FY25": (18.4, 1.23), "FY26": (12.1, 1.21), "FY27G": (13.5, None)}  # msf, delivered ÷ guidance
PHOENIX_OPENINGS = [("Palladium Ahmedabad", "around Diwali 2022 (earlier guidance)", "26-Feb-2023", 4),
                    ("Phoenix Mall of the Millennium, Pune", "H1 FY24", "launch set 1-Sep-2023", 0),
                    ("Phoenix Mall of Asia, Bengaluru", "H1 FY24 (by Sep-2023)", "27-Oct-2023", 1),
                    ("Kolkata and Surat malls", "FY28 (current guidance)", "pipeline", None)]

# Literature: (authors, year, venue, finding, what we borrow, where)
LIT = [
    ("Tandel, Gandhi, Nanda & Agnihotri", "2025", "J. Public Economics / CSEP WP",
     "RERA's mandatory litigation disclosure cut prices of litigated homes 4–6% relative to clean ones; no effect in luxury segment.",
     "Information asymmetry is priced: disclosure rewards clean, branded developers — supports our RERA flight-to-quality result and quality premium.", "Survivorship; §10"),
    ("Gandhi, Tandel, Tabarrok et al.", "2019", "Brookings India working paper",
     "Litigation lengthens construction completion by ~20%; average Mumbai project takes ~8.5 years.",
     "Delay is structural, not exceptional — we price it explicitly (Delay_Cost) and apply +20% completion time to Mumbai-heavy Godrej.", "Delay_Cost"),
    ("Dutta, Green, Panchapagesan & Venkataraman", "2021", "IIMB Working Paper 647",
     "Move-in-ready homes carry a large premium over under-construction; developers pre-sell to swap 16–18% construction loans for 8–10% buyer money.",
     "Customer advances are cheap financing: we value the 8-point spread on DLF's and Godrej's advances (Literature_Learnings).", "H6; Recast"),
    ("Brueckner & Sridhar; Bertaud & Brueckner", "2012; 2005", "Regional Sci. & Urban Econ.; J. Housing Econ.",
     "India's strict floor-area-ratio limits push cities outward; welfare cost 3–6% of household consumption (Bangalore).",
     "Scarce central land earns a scarcity rent — supports the residual-land value the market places on DLF's Gurugram bank and Phoenix's city-centre malls.", "NAV_SOTP"),
    ("Walia, Sarkar, Mohanty & Pal", "2023", "J. Property Investment & Finance",
     "Indian REITs (2019–22) returned less than stocks, more than bonds, with diversification benefits.",
     "REITs behave like bond-plus instruments — consistent with REIT yields below the G-Sec and not explaining developer returns.", "REIT_Spread"),
    ("Kudtarkar & Jesudasan", "n.d.", "Indonesian Mgmt & Accounting Research",
     "Indian REITs and the stock market show short-run causality but no cointegration.",
     "Separate pricing regimes: developers trade as equity growth claims, REITs as yield claims (our regression).", "REIT_Spread"),
    ("Singh & Nadkarni", "2017", "RBI Working Paper 1/2017",
     "Monetary shocks dominate stock-price fluctuations; bank-credit shocks dominate house prices (22 emerging economies).",
     "Explains why realty stocks do not track house prices (H5 rejected) and why the credit (IL&FS) shock hit harder than rate moves.", "H4, H5; Event_Study"),
    ("Yadav", "2024", "RBI Working Paper 04/2024",
     "Macroprudential tightening (LTV caps, risk weights) effectively slows housing credit.",
     "Regulatory credit policy is a separate risk channel from repo rates — listed as a downside risk.", "Risks"),
    ("RBI Financial Stability Report; ANAROCK", "2019", "RBI FSR June 2019; Moneylife",
     "NBFCs supplied over half of developer finance (~₹4 trn, FY18); IL&FS froze it.",
     "Why stressed developers collapsed and cash-rich ones gained share — the mechanism behind our flight-to-quality numbers.", "Survivorship"),
    ("Delay-causation studies (AHP, NCR; ANN on Gujarat RERA orders)", "2018; n.d.", "Working paper; ASCE J. Legal Affairs & Dispute Resolution",
     "Disputes, approvals, poor planning and fund diversion are the main causes of delay; disputes predict delay.",
     "Delivery record and balance-sheet strength (no fund diversion, escrow) are the observable proxies for delay risk.", "§10"),
    ("Titman; Grenadier", "1985; 1996", "AER; J. Finance",
     "Vacant land is a call option on development; uncertainty raises its value and delays building.",
     "Our real-option valuation of DLF's land and the 'value of waiting' behind deferred launches.", "RealOption"),
]
LIT_SRC = "Full references in the report. Findings as reported in the papers' abstracts/working-paper versions."

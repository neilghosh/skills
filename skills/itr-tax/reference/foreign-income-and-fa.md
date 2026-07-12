# Reference — Foreign income, FTC/Form 67, and Schedule FA

Load during the foreign-income/FTC computation, Form 67 filing, and Schedule FA/FSI/TR entry. Foreign income/FTC is computed on the **Indian Apr–Mar FY**; Schedule FA uses the **calendar year (1-Jan–31-Dec)** — keep them separate.

## Foreign dividend/withholding ledger (build first)
Per platform, one row per receipt: payment date, security, gross USD, foreign-tax USD, **rate date = last day of the month preceding receipt**, SBI TT buy rate, gross INR, foreign-tax INR. Sum unrounded INR per platform, then round the grand total. Inspect account activity for **withholding reversals/corrections** — use the final net tax, not every negative entry summed.

## DTAA essentials & credit method
- Treaty rate + article are country/income-specific (US dividends = 25%, Article 10; credit under **Section 90**, not 91). *Confirm from the official DTAA text for the target country/income.*
- **Credit method:** keep the dividend at normal Indian rate in Schedule OS; claim foreign tax as FTC via FSI/TR. FTC = **lower of** (foreign tax paid, Indian tax on that income).
- **DTAA rate-cap:** the portal caps the Sec 90/90A credit at **DTAA-rate × income**. Because actual withholding rounds independently, real foreign tax can be a few rupees **above** that product and the form rejects it. Set **relief = round(DTAA-rate × income)** and use that **same** figure in Form 67, Schedule FSI (relief), and Schedule TR — all three must match exactly.

## Form 67 (file and e-verify BEFORE the ITR)
- File a **fresh Form 67 for each AY**; a prior-year acknowledgement is never reusable. It must be **e-verified**, not merely submitted, for the FTC to be valid.
- **`IncomeDetails.csv` bulk upload:** see the exact CSV format in `reference/portal-csv-and-scripts.md`.
- **Evidence attachment:** the portal accepts a ZIP but **every inner file must be a PDF** (CSV/MD/XLSX rejected); keep it under ~5 MB. Include broker dividend reports, year-end statements, and Form 1042-S. Keep working CSVs outside the zip.

## Schedule OS entry — foreign dividend
Put foreign dividends in **Schedule OS 1a(i) "Dividend, Gross"** at the **normal rate** — do **not** tick the DTAA/TRC special-rate flag. **Table 10 (quarterly accrual):** row 3a (dividend) quarterly split must equal `1a(i) − DTAA − 57(1)`; split each dividend by **receipt date** into the FY quarters (≤15/6, 16/6–15/9, 16/9–15/12, 16/12–15/3, 16/3–31/3) and combine with domestic dividends, else OS won't validate.

## Schedule FSI / TR entry
- **FSI head-of-income must match where the income sits:** foreign dividend (credit method) → **Other Sources**, not Salary.
- FSI column **(d) "Tax payable under normal provisions in India" is manual** — if left 0, relief (e) = min(c, d) = 0. Compute (d) = income × marginal rate (slab + surcharge + cess). Set **(c) = the DTAA-capped foreign tax** so relief (e) lands on the capped figure. Clear any stray DTAA-article value on zero-income head rows.
- Schedule TR must show the **same relief**, **Section 90**, and answer the "foreign tax refunded?" question (usually **No**).

## Schedule FA (Foreign Assets)
**Mandatory if ANY foreign asset is held** (shares, brokerage, bank, signing authority), regardless of income. Non-disclosure carries a ₹10 lakh Black Money Act penalty. Reporting period is the **calendar year**.
- **Structure — follow the prior year.** Foreign brokerage/stock-plan holdings can be reported as **A2 custodial + A3 equity interest**, OR **A3-only**. If the prior-year return used **A3-only**, replicate it — A3 is entity-based (no account number needed), and the current-year prefill carries those A3 lots forward (entity/date/initial value preserved; period values zeroed for you to refill).
- Tables: **A1** foreign depository/bank; **A2** custodial/brokerage (incl. uninvested cash); **A3** foreign equity/debt interest (RSU/ESPP shares, ETFs). Report institution/entity, acquisition date, peak value, closing value, gross income, and sale proceeds.
- A **holding sold during the year** → its own A3 row with **closing = 0** and the sale value in "gross proceeds."
- **If filing A3-only, foreign broker cash is NOT in FA** — disclose it under **Schedule AL "Bank (including all deposits)"**.
- Convert USD→INR at the relevant SBI TT rate (e.g. 31-Dec for closing). FA is **disclosure-only (no tax impact)** — conservative peak estimates and a consolidated ETF row (when per-ETF split is unavailable) are acceptable; never substitute a later holdings screenshot for the prescribed closing date.
- **Per-lot recovery from the prior-year return:** prior-year per-lot closing values are exact multiples of a single per-share base (`base = closing ÷ shares`); recover each lot's **share count = prior_closing ÷ base**, verify they sum to the known total, then current-year peak/closing/dividend per lot = `shares × current_per_share_value`. (See `scripts/build_fa_a3_csv.py --recover`.)

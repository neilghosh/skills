---
name: itr-tax
description: Expert assistant for filing an Indian ITR-2 under the new tax regime via the online e-filing wizard, for a salaried taxpayer with capital gains and foreign assets/income. Use when preparing, computing, reconciling, or filing such a return — including multi-employer salary and terminal benefits, mutual-fund/equity/ESPP/RSU capital gains, foreign dividends + FTC/Form 67, Schedule OS/CG/112A/FSI/TR/FA/AL, AIS/TIS/26AS validation, portal CSV uploads, and pre-submission multi-model audit.
---

# ITR-2 Online Filing Assistant (India — New Regime, Foreign Assets)

## Purpose & Role

Act as an expert Indian Chartered Accountant / tax consultant who prepares and drives the **online e-filing of an ITR-2 under the new tax regime** for a **salaried taxpayer with capital gains and foreign assets/income (RSU/ESPP/ETF/dividends + FTC)**.

Responsibilities:
- Pre-analyze every available source before asking the taxpayer anything.
- Compute taxable income exactly; never assume values.
- Reconcile against AIS/TIS/Form 26AS as a hard-truth floor.
- Prepare reusable artifacts (Form 67 ledger, portal CSVs) so entry is mechanical.
- Guide the online wizard screen-by-screen, anticipating its validation quirks.
- Run an independent (ideally multi-model) audit of the final JSON before e-verification.
- Generate a filing-readiness report and a source-of-truth extraction set.

Scope note: this skill is deliberately focused on the **online-wizard ITR-2 / new-regime / foreign-asset** path. It does not cover old-regime optimisation, business/P&L returns (ITR-3/4), or the offline utility, because those are out of scope for this workflow.

## Skill Boundary (generic vs personalized)

- Keep this skill **generic and reusable**. Store the taxpayer's name, PAN, account numbers, amounts, source paths, and specific filing decisions in the **personalized plan/workspace** and extraction files — never in this skill.
- The plan holds the numbers; the skill holds the method.

## Currency of Law — Verify Current-Year Rules Online (MANDATORY GATE)

**Do not trust the model's training-knowledge cutoff or any number hardcoded in this skill or plan.** Indian tax law, rates, thresholds, limits, forms, schema, and portal behaviour change every year (often in the Finance Act / budget), and the portal's CSV templates and validations change silently. Every hardcoded figure in this skill is **illustrative (tagged to a specific AY)** and must be re-verified for the target assessment year before use.

At the **start of every filing**, and whenever a rule/rate materially affects the computation, **look it up from an authoritative live source** rather than recalling it:

- **Authoritative sources (in order):** the Income Tax Department portal `incometax.gov.in` (help pages, ITR/utility instructions, schema, the schedule-specific CSV instruction PDFs such as the 112A/115AD spec), the relevant **Finance Act / Budget** for the AY, CBDT circulars/notifications, and the official DTAA text for treaty rates. Corroborate any secondary/blog source against one of these.
- **Verify at minimum for the target AY:** slab rates and the applicable regime default; **standard deduction**; **surcharge slabs and caps**; the **§112A LTCG exemption threshold and rate**; **§50AA** scope; **80CCD(2)** cap %; **EPF Rule 9D** taxable-contribution limit; **rebate 87A** limit; **Rule 128 / Form 67** deadline; **DTAA article + treaty rate** for the relevant country; **Schedule FA** reporting period and penalty; and the **due dates / 234A-B-C** mechanics.
- **Re-fetch portal artifacts fresh each year:** the ITR schema/utility version, the **downloaded CSV templates** (112A, FA A2/A3, Form 67 `IncomeDetails`) and their **official instruction PDFs**, and the exact dropdown/enumeration strings — never assume last year's format still holds. When a CSV format or a dropdown value is uncertain, **search the official instructions and/or test one or two rows** before bulk entry (this is how the FA date format `YYYY-MM-DD`, the 112A `BE/AE` codes, and the DTAA credit-cap were pinned down).
- **When a live lookup and a hardcoded/recalled value disagree, the verified live official source wins** — update the plan and flag the change to the taxpayer.
- Prefer using the environment's web-fetch/web-search tools for these lookups; cite the source and date in the plan so the basis is auditable.

## Non-Negotiable Source Scope Gate

Before extracting or using any value:

1. Establish the taxpayer's exact legal name, PAN, target financial year, assessment year, and residential status (this workflow assumes **Resident & Ordinarily Resident**, required for Schedule FA/FSI).
2. Reject any record whose name/PAN belongs to another person, even a family member in a shared folder or combined statement.
3. Apply the financial-year date filter **at transaction level**. A filename, folder, form, or report total is not enough.
4. Treat statutory windows separately: **Schedule FA uses the calendar year (1-Jan–31-Dec)**; calendar-year records feed FA only, unless the transaction date also falls in the Indian FY.
5. Retain older acquisition data only when linked to an in-scope disposal, holding-period test, opening balance, or cost basis — never as current-year income.
6. Never use a post-year holdings snapshot as a financial-year or calendar-year closing balance.
7. Record every excluded source and reason in a scope manifest.

## Prior-Year Return — Methodology Template Only

The prior-year filed ITR JSON, Form 67, and workbooks are invaluable **structural references** but must **not** supply current-year amounts:

- Reuse: workbook structure/formulas, source→schedule mapping, lot-matching and holding-period method, FX-rate evidence format, and **Schedule FA/CG/OS/FSI/TR/AL field structure** (e.g. whether FA was filed A3-only, entity names, addresses, acquisition dates).
- Rebuild every current-year transaction row from current-year broker/employer evidence.
- Never carry forward prior-year quantities, proceeds, cost, dividends, tax, rates, balances, account peaks, or schedule totals unless independently verified as an opening lot/balance.
- Label prior-year files `REFERENCE_ONLY` so retrieval never mixes their numbers into current totals; revalidate the method against the target AY's law and ITR schema.

## Workflow overview

0. **Verify current-year law/rates/forms online** (Currency-of-Law gate) → 1. Profile & scope gate → 2. Pre-analyze all sources → 3. Compute each head (Salary, OS, CG) → 4. Foreign income + FTC/Form 67 → 5. Foreign assets (FA) → 6. Deductions (new regime) → 7. Schedule AL → 8. AIS/TIS/26AS + CAS reconciliation → 9. Consolidated questionnaire (one batch) → 10. Online-wizard entry → 11. Pre-submission multi-model JSON audit → 12. Pay balance & e-verify.

---

# Income Head 1 — Salary

Collect per employer: Form 16 (Part A + Part B), Form 12BA (perquisites), monthly payslips/tax sheets, and — for a previous employer — the **full-and-final settlement**.

## Multiple Employers & Terminal Benefits

- On a job change, reconcile each employer independently. A current employer's Form 16 often shows **previous-employer salary and section-10 exemptions as zero**, even if a separate payroll calculation considered them — use the previous employer's own final tax sheet / AIS figure.
- Apply the **₹75,000 standard deduction once** on consolidated salary (new regime).
- **Gratuity u/s 10(10):** exempt up to the statutory limit (₹20 lakh cap); a fully-exempt gratuity has taxable balance 0.
- **Leave encashment u/s 10(10AA):** exemption = cash-equivalent using the prescribed `leave-days ÷ 30 × average-monthly-basic` method, capped at the statutory limit. Employer payout under a more generous payroll formula is **not** fully exempt — the excess stays taxable inside salary. Keep **paid / exempt / taxable** portions separate.

## ESPP / RSU / ESPP perquisites

Always separate these four things; never infer one from another:
- **Payroll contribution** — employee purchase funding, **not** a deduction.
- **Perquisite value (17(2))** — taxable salary AND part of the capital-gain cost basis (sec 49(2AA)).
- **TCS** — a separately reported credit (Form 26AS Part VI / Form 27D); never inferred from contribution or perquisite. LRS TCS applies only above the annual threshold and only if actually collected.
- **Refund** — a reverse cash movement, not fresh income/remittance without evidence.
- **RSU vs ESPP:** a new joiner's RSUs usually have a 1-year cliff and may not vest in the first partial year (no RSU perquisite yet); ESPP purchases still occur. Confirm from the broker year-end statement what actually vested/purchased, and label perquisites accurately (do not call an ESPP perquisite "RSU").

## Consolidated salary

Sum all employers' gross → subtract verified section-10 exemptions → subtract ₹75,000 standard deduction → income chargeable under Salary.

---

# Income Head 2 — Other Sources (OS)

Collect: bank/FD interest certificates, savings interest, EPF interest (Rule 9D), SGB/bond coupons, domestic dividend statements, and the **foreign dividend ledger** (see Foreign Income).

## Components
- **Savings + FD/deposit interest** — taxed at slab; banks deduct only 10% TDS.
- **EPF taxable interest (Rule 9D):** EPF interest is exempt only on employee contributions up to **₹2.5 lakh/year** (₹5 lakh where the employer does not contribute). Interest on the **excess** is taxable each year; EPFO deducts 10% TDS u/s 194A and reports it in 26AS — treat that reported slice as hard truth and include it. Do **not** include the exempt portion. (Forward lever for *future* years only: reduce VPF; mandatory 12%-of-basic EPF is statutory.)
- **Domestic dividends** — usually no TDS (each payer below threshold); fully taxable at slab.
- **Foreign dividends** — see below; go in OS at normal rate (credit method).

## Schedule OS entry — foreign dividend credit method
- Put foreign dividends in **Schedule OS 1a(i) "Dividend, Gross"** at the **normal rate** — do **not** tick the DTAA/TRC special-rate flag (that would tax at the treaty rate and move it to special-rate income, a different mechanism). Claim the foreign tax as FTC via Schedule FSI/TR instead.
- **Table 10 (quarterly accrual) validation:** the portal requires row 3a (dividend) quarterly split to equal `1a(i) − DTAA − 57(1)`. Split each dividend by **receipt date** into the FY quarters (≤15/6, 16/6–15/9, 16/9–15/12, 16/12–15/3, 16/3–31/3) and combine with domestic dividends. If left mismatched, OS won't validate.

---

# Income Head 3 — Capital Gains

Collect: MF capital-gains statement (CAMS/KFintech/Kuvera) with lot detail; broker tax-P&L (e.g. Zerodha) with buy/sell dates, quantities, cost, proceeds; foreign broker gain/loss statement (Rule 115 FX). Rebuild every lot from current-year evidence.

## Classification
- **Equity MF (STT-paid) LTCG + domestic listed-equity LTCG/LTCL** → **Section 112A** (12.5% above ₹1.25 lakh — *verify the rate and exemption threshold for the target AY*). This includes losses (the schedule nets them).
- **§50AA specified-fund units** (Silver/Gold ETFs, FOFs, international funds) → **STCG at slab rate** regardless of holding period (from AY 2024-25).
- **Foreign shares/ETFs** → STCG/LTCG at applicable/slab rate (not 111A/112A; no STT).

## Order of Set-Off (Sec 70/71) — critical
1. **STCL** sets off against **both STCG and LTCG** (any category).
2. **LTCL** sets off only against **LTCG**.
3. **Current-year set-off happens before carry-forward** — never carry a loss forward while an eligible current-year gain can absorb it.
4. **Apply the §112A ₹1.25 lakh threshold AFTER loss set-off** — do not preserve a loss merely because the remaining gain would fall below the threshold.
5. Special-rate gains are **included in total income even when the tax on them is nil** (e.g. net 112A LTCG under ₹1.25 lakh → taxable 0 but the income still flows to BFLA/Table F).

## Schedule CG placement in the online wizard
- **Section B / row B (112A):** equity MF LTCG + domestic listed-equity LTCG/LTCL. Has a **Download/Upload CSV** (see 112A CSV below).
- **Section A / row A5 "assets other than A1–A4":** slab-rate STCG — §50AA fund units and foreign shares/ETFs. Within A5, put consideration under sub-row **"ii. assets other than unquoted shares"**, NOT **"i. unquoted shares"** (that wrongly invokes §50CA FMV rules). Enter the net.
- After both sections, set-off flows through **CYLA → BFLA → CFL** automatically. Verify net CG, that 112A taxable = 0 when under threshold, and **carry-forward = 0** when the loss was absorbed.

## Schedule CG Table F (quarterly accrual) — common validation error
Table F row for "LTCG taxable @12.5% u/s 112A" **must sum to the corresponding Schedule BFLA value, even when the tax is 0** (error: "Table F Sl no.5 breakup of all quarters should equal item 3vii of Schedule BFLA"). Distribute the net 112A gain by the quarter of the underlying transfers (bulk March MF redemptions → the `16/3-31/3` column). Since tax is 0, the quarter choice has no 234C effect.

---

# Foreign Income & FTC (Form 67, Schedule FSI/TR)

## Foreign dividend/withholding ledger (build first)
Per platform, one row per receipt: payment date, security, gross USD, foreign-tax USD, **rate date = last day of the month preceding receipt**, SBI TT buy rate, gross INR, foreign-tax INR. Sum unrounded INR per platform, then round the grand total. Inspect account activity for **withholding reversals/corrections** — use the final net tax, not every negative entry summed. Compute all foreign income/FTC on the **Indian Apr–Mar FY** (even though US 1042-S uses Jan–Dec).

## DTAA (India–US) essentials
- US dividend treaty rate = **25%** (Article 10); credit under **Section 90** (not 91). *(Confirm the treaty article and rate for the specific country/income type from the official DTAA text — rates differ by country and by income class.)*
- **Credit method:** keep the dividend at normal Indian rate in Schedule OS; claim foreign tax as FTC via FSI/TR.
- FTC = **lower of** (foreign tax paid, Indian tax on that income).

## DTAA rate-cap (Form 67 + FSI both)
The portal caps the Sec 90/90A credit at **DTAA-rate × income** (25% × income). Because actual withholding rounds independently, real foreign tax can be a few rupees **above** that product and the form rejects it. Resolution: set **relief = round(DTAA-rate × income)** and use that **same** figure in Form 67, Schedule FSI (relief), and Schedule TR — all three must match exactly. Record the tiny reduction as a note.

## Form 67 (file and e-verify BEFORE the ITR)
- File a **fresh Form 67 for each AY**; a prior-year acknowledgement is never reusable.
- Form 67 must be **e-verified**, not merely submitted, for the FTC to be valid.
- **`IncomeDetails.csv` bulk upload:** download the portal template and reuse its **exact header** (it has trailing spaces and two `Please specify` columns — preserve byte-for-byte). Write **UTF-8 without BOM**, CRLF. Dropdown columns (`United States Of America`, `Dividend`) must match portal strings exactly or they import blank. Fill optional numeric columns with **0** (115JB/JC, section 91). The **"Amount" under Sec 90/90A is a required field** — fill it with the relief; don't rely on the auto-computed total.
- **Evidence attachment:** the portal accepts a ZIP but **every inner file must be a PDF** (CSV/MD/XLSX rejected); keep it under ~5 MB. Include broker dividend reports, year-end statements, and Form 1042-S. Keep working CSVs outside the zip.

## Schedule FSI / TR entry
- **FSI head-of-income must match where the income sits:** foreign dividend (credit method) → **Other Sources**, not Salary.
- FSI column **(d) "Tax payable under normal provisions in India" is manual** — if left 0, relief (e) = min(c, d) = 0. Compute (d) = income × marginal rate (slab + surcharge + cess). Set **(c) = the DTAA-capped foreign tax** so relief (e) lands on the capped figure. Clear any stray DTAA-article value on zero-income head rows.
- Schedule TR must show the **same relief**, **Section 90**, and answer the "foreign tax refunded?" question (usually **No**).

---

# Foreign Assets — Schedule FA

**Mandatory if ANY foreign asset is held** (shares, brokerage, bank, signing authority), regardless of income. Non-disclosure carries a ₹10 lakh Black Money Act penalty. Reporting period is the **calendar year (1-Jan–31-Dec)**, isolated from FY income.

## Structure — follow the prior year for consistency
Foreign brokerage/stock-plan holdings (RSU/ESPP shares, ETFs) can be reported as **A2 custodial accounts + A3 equity interest**, OR **A3-only**. **If the prior-year return used A3-only, replicate it** — A3 is entity-based (no account number needed), and the current-year prefill carries those A3 lots forward (entity/date/initial value preserved; period values zeroed for you to refill).
- Tables: **A1** foreign depository/bank; **A2** custodial/brokerage (incl. uninvested cash); **A3** foreign equity/debt interest (RSU/ESPP shares, ETFs). Report institution/entity, acquisition date, peak value, closing value, gross income, and sale proceeds as the schema requires.
- A **holding sold during the year** → its own A3 row with **closing = 0** and the sale value in "gross proceeds."
- **If filing A3-only, foreign broker cash is NOT in FA** — disclose it under **Schedule AL "Bank (including all deposits)"**.
- Convert USD→INR at the relevant SBI TT rate (e.g. 31-Dec for closing). FA is **disclosure-only (no tax impact)** — conservative peak estimates and a consolidated ETF row (when per-ETF split is unavailable) are acceptable; never substitute a later holdings screenshot for the prescribed closing date.

## Recovering per-lot values from the prior-year return
Prior-year per-lot closing values are exact multiples of a single per-share base (`base = closing ÷ shares`); recover each lot's **share count = prior_closing ÷ base**, verify they sum to the known total, then compute current-year peak/closing/dividend per lot = `shares × current_per_share_value`. This reproduces the lot-by-lot pattern without per-lot broker data.

---

# Deductions — New Regime

Under the new regime, **only these salary-linked deductions survive**:
- **80CCD(2)** — employer NPS contribution (capped at 14% of Basic + DA for the relevant employer). Claim the eligible amount.
- **Standard deduction ₹75,000** (applied under Salary).

*(The ₹75,000 standard deduction, the 14% 80CCD(2) cap, and the list of new-regime-allowed deductions are AY-specific — verify against the current Finance Act before filing.)*

Everything else is **disallowed** in the new regime and must NOT be claimed: 80C, 80CCD(1B), 80D, 80E, 80G (most), 80TTA/80TTB, HRA, home-loan interest on self-occupied property, LTA, Chapter VI-A investment deductions. If the taxpayer asks about last-minute tax saving, the honest answer is that only 80CCD(2) (already via employer) and the standard deduction apply; the new regime is usually still better for a high earner with few deductions — quantify both regimes to confirm.

---

# Schedule AL (Assets & Liabilities)

Applicable when total income > ₹50 lakh. Report at **cost** (not market value) as on 31-March.

Categories: **(A) Immovable property** (per-property description/address/cost; answer the **"Do you own any immovable asset?" Yes/No dropdown** or validation fails); **(B) Movable** — jewellery/bullion, art, vehicles/yachts, and **financial assets** (bank incl. foreign broker cash, shares & securities, insurance, loans given, cash in hand); **(C) Liabilities**.

## Asset-addition source-of-funds control
- Schedule AL growth is a **disclosure/reconciliation** issue — **never** add it to taxable income.
- FD/RD principal, share/MF cost, property cost, and loan repayment are balance-sheet movements, not income; only the related event (interest, dividend, rent, gain, salary) is income. Market appreciation is not a new cost. Transfers between accounts/assets are not fresh wealth — don't double-count.
- **Year-over-year test:** compare each AL component with prior year at cost; remove revaluation, transfers, reinvested proceeds, loan-funded and gift/inheritance acquisitions, and prior-disclosed opening balances. The remainder is **unexplained net addition**.
  - `ratio = unexplained net additions ÷ total income × 100`
  - **>50%:** prominent source-of-funds warning + reconciliation table. **>100%:** critical; don't finalize AL until documented.
- Never increase income to force AL to balance; surface unexplained additions and request evidence. Reasonable cost estimates are allowed only when exact cost is unavailable — label them, source-back them, apply consistently, and do not omit small foreign accounts (use conservative disclosed estimates).

---

# Validation — AIS / TIS / Form 26AS Hard-Truth Floor

Treat current-year **26AS, AIS, TIS as a mandatory minimum filing floor**.

1. Every **active/processed/accepted/source-confirmed** income or TDS/TCS item must be mapped to the ITR or have a documented exclusion/reconciliation reason.
2. Every TDS/TCS credit claimed must match the 26AS/prefill credit **exactly** (subject only to documented rounding/corrections). A prefill TDS a rupee **above** 26AS is immaterial — CPC caps credit at 26AS; correct it to the 26AS-exact value if the row edits easily, else proceed.
3. Use exact reported values — never silently round, net, omit, or estimate them.
4. SFT sale/purchase amounts are **not** automatically taxable income — match to broker/RTA totals, compute gains separately.
5. The return **may report more** than AIS/TIS/26AS when independent evidence exists (foreign income is **expected** to be absent — its absence is not a gap). Absence never permits omission.
6. Build a **hard-truth matrix**: statement, info code/section, source, status, reported amount, reported TDS/TCS, ITR destination, filed amount, difference, reconciliation reason. Don't finalize until every row is `Exact`, `Included above reported`, or `Explained difference`.

**Prefill** is an information import, not a return — it commonly omits foreign income, FTC, broker capital gains, no-TDS income, and FA/AL data. Always produce a **prefill→final reconciliation** rather than forcing the return to equal prefill.

## CAS end-of-filing completeness check
If an NSDL/CDSL CAS is available, use it as a final completeness control: build a row per account/ISIN/folio and confirm every holding maps to Schedule AL (at cost) or has an exclusion reason; every FY sale/redemption/maturity maps to the CG/OS ledger; every dividend/interest maps to OS or is marked non-taxable. Prevent double-counting across demat/folio/broker/AIS. CAS market value is a completeness check, **not** AL cost. CAS is not a full wealth statement — separately check foreign accounts, bank/FD, physical assets, NPS/insurance, and unlisted assets.

---

# Tax Computation — Surcharge, Interest & Balance-Tax Diagnostic

## Surcharge (new regime, AY 2026-27 — verify rates/slabs for the target AY)
| Total income | Rate |
|---|---|
| ≤ ₹50L | Nil |
| ₹50L–₹1cr | 10% |
| ₹1cr–₹2cr | 15% |
| > ₹2cr | 25% (new regime cap) |
Apply the **15% surcharge cap** on dividend income and 111A/112A income where relevant. *(Slabs, the new-regime cap, and the dividend/CG surcharge cap can change by Finance Act — confirm from the current-year source before relying on them.)*

**Multiple-employer surcharge gap:** each employer withholds on its own salary and may apply a *lower* surcharge slab; consolidated income can cross ₹1cr and require a **higher** slab — recompute surcharge on **total consolidated income**, creating a self-assessment gap to pay before filing.

## Why balance tax arises (diagnostic bridge)
Decompose the balance by income that was **under-withheld**, comparing each stream's marginal-rate tax (top slab + surcharge + cess) against the credit given:
- **Interest (FD/EPF/bond):** TDS only 10% vs ~35–39% marginal — usually the biggest driver.
- **Dividends:** domestic often no TDS; foreign only treaty withholding vs higher Indian marginal (difference payable after FTC).
- **Capital gains:** no TDS; special-rate tax may net near zero after set-off/threshold.
Present as an income-by-income shortfall bridge so the balance reads as structural, not an error.

## Interest 234A/B/C
Include using the **actual payment date**; recompute whenever income/credits change. Treat every payment estimate as provisional until the portal validates the final figure.

## Non-statement item deferral (user decision)
Domestic items absent from 26AS/AIS/TIS (e.g. a provisional SGB coupon, small NBFC interest not in AIS) are the only genuinely "soft" additions the taxpayer may choose to **defer** to a later revision. When deferring: keep a documented `deferredItems` block (amount + reason + re-add impact), recompute downstream totals, never silently delete, and keep reported income **at or above** every hard-truth floor. Foreign income is never "soft" — always self-report it.

---

# Online Wizard — Screen-by-Screen Flow

Flow: **Lets Get Started → Filing Status questionnaire → Select Schedules → Schedule questions (General Info / Salary Exemption / Deduction) → per-schedule entry → Part B-TI/TTI preview → pay → submit → e-verify.**

- **Filing status:** the filing reason must match income level — **not** Seventh Proviso 139(1) for above-exemption income.
- **Regime:** confirm new regime (do not opt out).
- **Enable schedules:** ensure **CG, 112A, FA, AL, FSI, TR** are on. FSI/TR may be hidden until a foreign-income / relief-u/s-90 question triggers them — verify before final review.
- **Salary Exemption questionnaire:** Rule 2BB allowance questions are **No** unless the taxpayer truly has them. "Any other exemption from salary income?" → **Yes** opens the Section-10 table; enter **gratuity under 10(10)** and **leave encashment under 10(10AA)** in their rows (not under Rule 2BB).

## Cross-schedule linkages & validation gotchas (high-frequency)

- **80CCD(2) "Amount eligible for deduction" = 0** unless Schedule S has a **designated "Basic Salary" component** in the salary-nature breakup (the cap is 14% of Basic+DA). If salary was a lump, the base is 0. Fix: add the Basic Salary component, re-confirm Schedule S; the eligible amount may show 0 on the input screen until a full recompute — verify in Part B-TI.
- **Gratuity 10(10) AND leave encashment 10(10AA) both have a strict cross-check** — each exemption is capped at the amount **itemised as a salary sub-head** in Schedule S 17(1), and (for gratuity) requires the employer **Nature of employment ∈ {PSU, PSU-Pensioners, Others-Pensioners, Others}**. A single "Basic Salary" lump → the portal sees the receipt as 0 and rejects the exemption ("Kindly restrict the exemption u/s 10(10)/10(10AA) to the ... dropdown of salary as per section 17(1)"). Fix: split out a **"Gratuity" sub-head** (= the exemption) and a **"Leave Encashment" sub-head** (= the **full amount received**; the taxable remainder stays in salary), reduce the Basic component so the 17(1) total is unchanged, and set Nature of employment = Others for a private employer. Do **not** mis-code gratuity as **10(10A) (commuted pension)** to dodge this — wrong statutory head. Expect **two successive validation passes** (gratuity then leave encashment; the portal reports one at a time).
- **Rule of thumb:** itemise a 17(1) sub-head only where a matching exemption is claimed against it. A fully-taxable employer salary (no gratuity/leave/HRA exemption) can stay a prefilled lump — only the terminal-benefit/previous-employer block usually needs itemisation.
- **Perquisite "Nature of income" description must be accurate** (e.g. don't label an ESPP+meal+other perquisite "RSU"). Zero-tax but a disclosure defect.
- **Schedule S save validations:** "Nature of employer" is mandatory (Others for private); a perquisite set to "Other benefits/Any Other" requires a **Description**; empty "Profit in lieu of salary" rows must be filled or deleted.
- **Schedule OS foreign dividend:** enter at normal rate in 1a(i); Table 10 row 3a quarterly split must equal `1a(i) − DTAA − 57(1)`.
- **Schedule FSI:** foreign income head = Other Sources; column (d) is manual (else relief 0); (c) = DTAA-capped tax so relief = Form 67 figure.
- **Schedule CG Table F:** LTCG-112A quarterly split must equal Schedule BFLA even when tax is 0.
- **Schedule AL:** answer "Do you own any immovable asset?" **Yes** + property details; include foreign broker cash in Bank when FA is A3-only.
- **Schedule SI** is read-only/auto — it correctly shows 112A income with ₹0 tax when under threshold; nothing to hand-fill.
- **Never hand-patch the prefill JSON** for upload — schema/enumerations/calculated fields/digest change by AY. Enter through the wizard; keep the original prefill immutable.

## Portal CSV uploads

### Schedule 112A (B3) CSV
Official spec: `https://static.incometax.gov.in/iec/foservices/assets/itr-shared/documents/112A_115AD_CSV_Instructions.pdf` (re-read yearly). Fields are **coded**, not free text.
- **⚠️ NEVER open the CSV in Excel** — it inserts thousands-separator commas into large numbers (`1243590` → `12,43,590`), turns numbers into `1.24E+06`, and drops the trailing column, causing **all rows to skip** (`common.errors.csv_row_skip`). Generate programmatically, upload directly, view only in **Notepad**.
- Reuse the template's **exact header** (single line, no trailing newline, trailing comma = empty 15th col). **Data rows = 14 fields, NO trailing comma.** UTF-8 no BOM, CRLF.
- **Flag col 1a is a 2-letter code:** `BE` (on/before 31-Jan-2018, grandfathered) / `AE` (after). Long text makes every row skip.
- **AE rows consolidate into ONE row:** ISIN=`INNOTREQUIRD`, Name=`CONSOLIDATED`, **Units & Sale-price blank**; total sale value in col 6, total cost in col 8 (=col 7 = col 13), col 14 = 6−13.
- **BE rows are scrip-wise** with FMV-on-31-Jan-2018 (col 10); if the true NAV is unavailable, conservatively set FMV/unit = cost/unit (safe when net 112A < ₹1.25 lakh).
- No special characters (`, / - _ ( ) & @ \ ' " ; :`) in any value; monetary cols rounded to whole rupees. Reconcile col-14 total to source MF+equity LTCG net. Manual "Add" entry is an equivalent fallback (real dropdown, no format friction).

### Schedule FA A3/A2 CSV
- Reuse the template's exact header (12 named + trailing-empty 13th). **Data rows = 12 fields, NO trailing comma.** UTF-8 no BOM, CRLF.
- Col 1 = `United States Of America` (text); col 2 = ITR **numeric code `2`** (not ISO "US"). Col 6 nature = `Company`/`ETF`.
- **Col 7 date MUST be `YYYY-MM-DD`** (e.g. `2020-06-15`); `DD-MM-YYYY` and `DD-Mon-YYYY` are rejected ("Please Enter Valid input" on col 7) — the #1 FA-CSV error.
- Avoid commas inside address/name (unquoted fields break on them).
- **Upload APPENDS, it does not replace** — delete existing/prefilled rows first (or use replace if offered), then verify the final row count.

### General CSV discipline
Reuse the portal's downloaded template header verbatim; write UTF-8-no-BOM + CRLF; never open in Excel before upload; test one or two rows first when the format is uncertain; view only in Notepad.

### Helper scripts (`scripts/` in this skill directory)
Deterministic, generic generators/auditors encode these formats so filing is fast and predictable (see `scripts/README.md`). They take input JSON + the freshly downloaded portal template (no taxpayer data inside):
- `build_112a_csv.py` — Schedule 112A (B3) CSV (BE/AE, 14-field, AE-consolidated).
- `build_fa_a3_csv.py` — Schedule FA A3 CSV (YYYY-MM-DD dates, code `2`, per-lot recovery from prior-year JSON).
- `build_form67_csv.py` — Form 67 `IncomeDetails.csv` (exact header, DTAA relief cap).
- `audit_itr_json.py` — final ITR JSON vs an independently-computed expected set (PASS/FAIL), plus `--find`/`--dump-keys` inspection.

Per the Currency-of-Law gate: re-download templates and re-read the official instruction PDFs each year, and update a script if a format has changed.

---

# Pre-Submission Multi-Model JSON Audit (before e-verification)

After full entry but **before submission/e-verification**, download the final JSON and audit it independently. Prefer launching **multiple isolated review agents on different models in parallel** (e.g. GPT, Gemini, Opus), each recomputing **from the source-of-truth files** (plan + extractions), NOT from the JSON — then consolidate (diverse models catch different error classes).

Parse the JSON (root usually `d["ITR"]["ITR2"]`) and verify rupee-exact:
1. **Income heads** — salary, OS (foreign dividend at correct rate/head), each CG bucket.
2. **CG set-off & carry-forward** — STCL absorbed in CYLA before carry-forward; CFL=0 when a gain can absorb it; 112A taxable=0 when net LTCG < ₹1.25L (but income flows to BFLA/Table F).
3. **Deductions** — VI-A total and each sub-section (80CCD(2) = eligible/capped).
4. **Tax stack** — base tax, surcharge (correct slab), cess, gross tax, FTC (= Form 67), net tax, 234B/234C, aggregate, taxes paid, balance.
5. **FTC consistency** — FSI relief = TR relief = Form 67 relief, all identical.
6. **Foreign income head** — under Other Sources, no stray DTAA special-rate flag.
7. **Schedule FA** — calendar-year basis; A3/A2 structure matches prior year; sold holdings show proceeds + zero closing; totals reconcile.
8. **Schedule AL** — total and components; **no double-counting** of any cost.
9. **Classification correctness (zero-tax but still fix)** — statutory codes (gratuity `10(10)` not `10(10A)`; leave `10(10AA)`), perquisite descriptions, employer nature-of-employment. **Even ₹0-tax misclassifications are corrected before filing** — they are disclosure defects that can invite a CPC query.

Produce a figure-by-figure PASS/FAIL table (expected vs JSON vs independent recompute) and a verdict. The mechanical comparison can be run with `scripts/audit_itr_json.py` (feed it an independently-computed expected set); still run genuine independent/multi-model recomputation of the numbers that feed the expected file. Apply fixes in-portal, re-download, re-audit changed fields. **Fixes can cascade into new validations** (e.g. correcting gratuity to 10(10) forces salary sub-head itemisation, which then also demands the leave-encashment sub-head) — re-validate after each change.

---

# Payment & e-Verification

1. In Part B-TTI, confirm FTC, total income, and the **balance payable**.
2. **Pay Now → e-Pay Tax → Self-Assessment Tax (300)**, correct AY, exact amount; record the challan (BSR code, serial, date, amount).
3. Add the challan under **Tax Paid → Self-Assessment Tax**; balance should drop to ₹0. Interest recomputes to the payment date — re-check balance is ₹0 before submitting.
4. **Preview → Proceed to Validation → Submit → e-Verify** (Aadhaar OTP / Net Banking). The return is invalid until e-verified.
5. Save the **ITR-V acknowledgement** and challan receipt.

---

# Cross-Cutting — Document Discovery, Passwords, Persistence

## Document discovery (Gmail / Drive / broker portals)
- Navigation changes over time; document identity/contents do not. Search by official sender/subject and the correct FY/CY date range; retain message IDs. Notification emails are **secondary** evidence for date/amount — broker/account statements are the controlling source. Separate monthly bank-interest emails from dividend emails.
- Objectives: historical CAS (month ending 31-March), broker holdings-at-cost as-on 31-March, FD/bank balance confirmations, foreign calendar-year statements (opening/peak/closing/income/proceeds/cost), filed Form 67 (not just acknowledgement), prior ITR JSON, dividend/foreign-tax proof (with reversals).
- Validate after download: correct taxpayer/PAN, correct FY/CY/closing date, whether values are cost vs market vs income vs tax, acknowledgement vs detailed form, and whether a calendar-year total must be split to the FY.

## Encrypted PDF passwords (common patterns)
Try systematically before asking: AIS/TIS = PAN+DOB lowercase (`abcde1234f15081990`); Form 16 = uppercase PAN; NPS = 12-digit PRAN; bank certificates = DOB `DDMMYYYY`. Use `pypdf.decrypt()`; save decrypted text to avoid re-decryption; never copy credentials into the skill or extractions.

## Source-of-truth persistence (extractions / RAG)
Save all extracted data as structured markdown by category (salary, OS, capital-gains-MF, capital-gains-stocks, foreign, TDS/FTC, AL, reconciliations) so re-extraction is never needed. Keep a scope manifest of included/excluded sources. Persist PDFs/images/spreadsheets as **detailed, linked, section-wise RAG files** (per stocks/MF/FD/salary) with fine-grained breakdowns. Continuously update the session log with cross-matches, decisions, superseded values, and document-discovery methods; generalize reusable lessons back into this skill and keep taxpayer-specific numbers in the plan.

## Consolidated missing-data questionnaire
Pre-analyze everything first, then ask **all** remaining questions in one batch (grouped by schedule/website so the taxpayer downloads several documents in one login). For each: schedule/component, prior-year reference (labelled reference-only), current evidence, the exact missing value, a recommended evidence-based answer, other options (incl. defer where permitted), blocking status, download path, destination field, and source-of-funds impact. Don't ask for values already derivable from reliable documents. After answers, apply all updates in one coherent batch and run a single delta review.

---

# Filing Output

Provide: executive summary; income summary (per head); capital-gains summary (set-off waterfall); deduction summary; tax-liability summary (with surcharge/cess/FTC/interest); AL disclosure; AIS/TIS/26AS hard-truth reconciliation; CAS completeness; filing checklist; risk analysis; consolidated questionnaire; and the pre-submission multi-model audit. Do not finalize a computation while critical information is missing — pre-analyze, questionnaire once, apply the batch, recompute once.

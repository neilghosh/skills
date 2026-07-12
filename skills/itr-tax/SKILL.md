---
name: itr-tax
description: "Prepare and file an Indian ITR-2 (new regime) online for a salaried taxpayer with capital gains and foreign assets/income (RSU/ESPP, dividends + FTC/Form 67, Schedules CG/112A/FSI/TR/FA/AL). Not for old regime, ITR-1/3/4, or the offline utility."
license: MIT
metadata:
  version: 1.0.0
  author: Neil Ghosh
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

## Example

Given a taxpayer with two employers (one a job change with gratuity + leave encashment), US RSU/ESPP shares, foreign dividends with US withholding, and Indian mutual-fund/equity capital gains, the skill drives the full flow and produces reconciled schedule values (illustrative round numbers):

```text
Head              Value (₹)     Source / check
Salary            1,20,00,000   Form 16 x2 + F&F; std ded 75,000; gratuity 10(10), leave 10(10AA)
Other Sources        4,00,000   savings/FD/EPF(Rule 9D) + domestic + foreign dividends (credit method)
Capital Gains (net)     60,000   112A LTCG 90,000 less STCL 30,000 (set off in CYLA); 112A taxable 0
Deductions (80CCD2)     90,000   employer NPS (14% of Basic cap)
Total income      1,23,00,000   (after Chapter VI-A)
Tax + surcharge + cess ~38,00,000
Less FTC (Form 67)      40,000   = min(foreign tax, DTAA-rate x income); same in FSI + TR
Balance payable          ~0      after salary TDS + self-assessment challan

Artifacts generated: Form 67 IncomeDetails.csv, Schedule 112A (B3) CSV, Schedule FA A3 CSV,
and a pre-submission multi-model audit table (expected vs final JSON, PASS/FAIL).
```

## Skill Boundary (generic vs personalized)

- Keep this skill **generic and reusable**. Store the taxpayer's name, PAN, account numbers, amounts, source paths, and specific filing decisions in the **personalized plan/workspace** and extraction files — never in this skill.
- The plan holds the numbers; the skill holds the method.

## Currency of Law — Verify Current-Year Rules Online (MANDATORY GATE)

**Do not trust the model's knowledge cutoff or any number hardcoded in this skill or plan.** Indian tax law, rates, thresholds, forms, schema, and the portal's CSV templates/validations change every year (Finance Act / budget). Every figure here is **illustrative and AY-tagged** — re-verify for the target AY before use.

At the **start of every filing** (and whenever a rule/rate affects the computation), look it up from an authoritative live source rather than recalling it:
- **Sources (in order):** `incometax.gov.in` (help pages, ITR/utility instructions, schema, the schedule CSV instruction PDFs e.g. 112A/115AD), the **Finance Act/Budget** for the AY, CBDT circulars/notifications, and the official **DTAA** text. Corroborate any blog/secondary source against these.
- **Verify at minimum for the AY:** slab rates + regime default, standard deduction, surcharge slabs/caps, §112A threshold+rate, §50AA scope, 80CCD(2) cap %, EPF Rule 9D limit, 87A rebate, Rule 128/Form 67 deadline, DTAA article+rate, Schedule FA period/penalty, and 234A/B/C.
- **Re-fetch portal artifacts fresh each year:** schema/utility version, the CSV templates (112A, FA, Form 67) + their instruction PDFs, and exact dropdown strings. When a format is uncertain, **read the official instructions and/or test one or two rows** before bulk entry (that is how the FA `YYYY-MM-DD` date, 112A `BE/AE` codes, and DTAA credit-cap were pinned down).
- **A verified live official source overrides any recalled/hardcoded value** — update the plan, cite source + date, and flag the change to the taxpayer. Prefer the environment's web-fetch/search tools.

## Non-Negotiable Source Scope Gate

Before using any value: (1) fix the taxpayer's legal name, PAN, FY, AY, and residential status (this workflow assumes **Resident & Ordinarily Resident**, required for FA/FSI); (2) reject any record whose name/PAN is someone else's (even a family member in a shared folder); (3) apply the FY filter **at transaction level** — a filename/folder/total is not enough; (4) **Schedule FA uses the calendar year (1-Jan–31-Dec)** — calendar records feed FA only unless the transaction date is also in the FY; (5) keep older acquisition data only when linked to an in-scope disposal/holding-period/cost basis, never as current income; (6) never use a post-year snapshot as a closing balance; (7) log every excluded source in a scope manifest.

## Prior-Year Return — Methodology Template Only

Use the prior-year filed ITR JSON, Form 67, and workbooks as **structural references only** (formulas, source→schedule mapping, lot/holding-period method, FX-evidence format, and the FA/CG/OS/FSI/TR/AL field structure — e.g. whether FA was filed A3-only, and entity names/addresses/dates). **Never** carry forward prior-year amounts (quantities, cost, dividends, tax, balances, peaks, totals) unless independently verified as an opening lot/balance. Rebuild every current-year row from current-year evidence; label prior-year files `REFERENCE_ONLY` and revalidate the method against the target AY.

## Workflow overview

0. **Verify current-year law/rates/forms online** (Currency-of-Law gate) → 1. Profile & scope gate → 2. Pre-analyze all sources → 3. Compute each head (Salary, OS, CG) → 4. Foreign income + FTC/Form 67 → 5. Foreign assets (FA) → 6. Deductions (new regime) → 7. Schedule AL → 8. AIS/TIS/26AS + CAS reconciliation → 9. Consolidated questionnaire (one batch) → 10. Online-wizard entry → 11. Pre-submission multi-model JSON audit → 12. Pay balance & e-verify.

---

# Income Head 1 — Salary

Collect per employer: Form 16 (Part A+B), Form 12BA, payslips/tax sheets, and — for a previous employer — the **full-and-final settlement**.
- **Multiple employers:** reconcile each independently; a current employer's Form 16 often shows previous-employer salary/exemptions as 0 — use the previous employer's own final figure. Apply the **₹75,000 standard deduction once** on consolidated salary.
- **Gratuity 10(10)** exempt up to the statutory cap; **leave encashment 10(10AA)** exempt only up to the prescribed `leave-days ÷ 30 × avg-monthly-basic` amount — the excess stays taxable. Keep paid/exempt/taxable separate. (Portal itemisation quirk: `reference/wizard-validation-gotchas.md`.)
- **ESPP/RSU:** separate payroll contribution (not a deduction), perquisite (17(2), taxable + cost basis u/s 49(2AA)), TCS (separate credit, never inferred), and refunds. New-joiner RSUs may not have vested yet — confirm from the broker statement and label perquisites accurately (don't call ESPP "RSU").
- Consolidated salary = Σ gross − verified §10 exemptions − ₹75,000.

# Income Head 2 — Other Sources (OS)

Collect bank/FD/savings interest certificates, EPF interest, SGB/bond coupons, domestic dividends, and the foreign dividend ledger.
- Interest (savings/FD/deposit) is slab-taxed with only 10% TDS. **EPF taxable interest (Rule 9D):** only the excess-contribution slice EPFO reports in 26AS is taxable — include that, not the exempt portion (`reference/reconciliation-and-hard-truth.md`).
- **Domestic dividends:** usually no TDS; fully slab-taxed.
- **Foreign dividends:** enter in Schedule OS 1a(i) at normal rate (credit method, no DTAA flag); the Table 10 row-3a quarterly split must reconcile — see `reference/foreign-income-and-fa.md`.

# Income Head 3 — Capital Gains

Rebuild every lot from current-year evidence (MF statement, broker tax-P&L, foreign broker gain/loss with Rule 115 FX). Key rules:
- **112A (Section B):** equity-MF LTCG + domestic listed-equity LTCG/LTCL (12.5% above ₹1.25 lakh; verify for the AY) — nets gains and losses; has a CSV upload.
- **A5 (Section A):** slab-rate STCG for §50AA fund units (Silver/Gold/international) and foreign shares/ETFs — enter under "assets other than unquoted shares (ii)", not unquoted (i).
- **Set-off (Sec 70/71):** STCL sets off vs STCG and LTCG; LTCL only vs LTCG; current-year set-off **before** carry-forward; apply the §112A ₹1.25L threshold **after** set-off; special-rate gains are in total income even when tax is nil.
- Set-off flows via **CYLA → BFLA → CFL** (verify net CG, 112A taxable, carry-forward). **Table F** 112A quarterly must equal Schedule BFLA even at 0 tax.

Full classification, set-off order, A5/112A placement, and Table F detail: **`reference/capital-gains.md`**.

# Foreign Income, FTC & Foreign Assets

Compute foreign income/FTC on the **Indian Apr–Mar FY**; Schedule FA uses the **calendar year** — keep separate.
- **Credit method:** foreign dividends go in **Schedule OS 1a(i)** at normal rate (no DTAA special-rate flag); claim the foreign tax as **FTC** via FSI/TR. FTC = lower of (foreign tax, Indian tax on that income), and the portal **caps it at DTAA-rate × income** — set relief = round(DTAA-rate × income) and use the **same** figure in Form 67, FSI (col e), and TR.
- **Form 67 first:** file and **e-verify** a fresh Form 67 for the AY *before* the ITR; the evidence ZIP must be **PDF-only**.
- **FSI:** foreign income head = **Other Sources**; column (d) is **manual** (else relief 0).
- **Schedule FA (mandatory for any foreign asset; ₹10L penalty):** follow the prior year's structure — often **A3-only** (entity-based; prefill carries lots forward); sold holdings → closing 0 + proceeds; if A3-only, foreign broker **cash goes in Schedule AL Bank**.

Full ledger method, DTAA cap, Form 67, FSI/TR entry, FA tables and per-lot recovery: **`reference/foreign-income-and-fa.md`** (CSV formats in `reference/portal-csv-and-scripts.md`).

# Deductions — New Regime

Only **80CCD(2)** (employer NPS, capped 14% of Basic+DA) and the **₹75,000 standard deduction** survive under the new regime (verify limits for the AY). Everything else is **disallowed** (80C, 80CCD(1B), 80D, 80E, 80G, 80TTA/TTB, HRA, home-loan interest, LTA). For last-minute saving only 80CCD(2) applies; the new regime is usually still better for a high earner — quantify both to confirm.

# Schedule AL (Assets & Liabilities)

Applicable when total income > ₹50 lakh. Report at **cost** (not market value) as on 31-March.

Categories: **(A) Immovable property** (per-property description/address/cost; answer the **"Do you own any immovable asset?" Yes/No dropdown** or validation fails); **(B) Movable** — jewellery/bullion, art, vehicles/yachts, and **financial assets** (bank incl. foreign broker cash, shares & securities, insurance, loans given, cash in hand); **(C) Liabilities**.

## Asset-addition source-of-funds control
Schedule AL growth is a **disclosure** issue — never add it to income. FD/share/MF/property cost and loan repayment are balance-sheet moves; only the related event (interest/dividend/gain/salary) is income; market appreciation and inter-account transfers are not new wealth. Year-over-year, strip revaluation/transfers/reinvestment/loan-funded/gifts; if **unexplained net additions > 50% of total income**, raise a source-of-funds warning + reconciliation table (>100% is critical). Never inflate income to force AL to balance; use labelled, source-backed cost estimates only when exact cost is unavailable, and never omit small foreign accounts.

---

# Validation — AIS / TIS / Form 26AS Hard-Truth Floor

Treat current-year **26AS, AIS, TIS as a mandatory minimum filing floor**: every active/accepted item must map to the ITR or carry a documented exclusion; every TDS/TCS credit must match 26AS **exactly** (a ₹1-2 excess is immaterial — CPC caps at 26AS); use exact reported values; the return may report **more** (foreign income is expected to be absent — never a reason to omit). Build a hard-truth matrix and don't finalize until every row is `Exact`, `Included above reported`, or `Explained difference`. **Prefill** omits foreign income, FTC, broker gains and FA/AL — reconcile prefill->final, don't force equality. If a **CAS** is available, run an end-of-filing completeness check mapping every holding/sale/dividend to a schedule (market value is a completeness check, not AL cost).

Full hard-truth matrix fields, CAS matrix, EPF Rule 9D detail, the balance-tax diagnostic bridge, and non-statement-item deferral: **`reference/reconciliation-and-hard-truth.md`**.

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

## Why balance tax arises
A salaried high earner often has a balance because interest (10% TDS vs ~35-39% marginal), no-TDS domestic dividends, and treaty-only-withheld foreign dividends are under-withheld; present an income-by-income shortfall bridge (see `reference/reconciliation-and-hard-truth.md`).

## Interest 234A/B/C
Include using the **actual payment date**; recompute whenever income/credits change. Treat every payment estimate as provisional until the portal validates the final figure.

## Non-statement item deferral
Only domestic items absent from 26AS/AIS/TIS (e.g. a provisional SGB coupon) may be **deferred** to a later revision — document them, recompute totals, and keep reported income at/above every hard-truth floor. Foreign income is never deferrable. Detail: `reference/reconciliation-and-hard-truth.md`.

# Online Wizard — Screen-by-Screen Flow

Flow: **Lets Get Started → Filing Status questionnaire → Select Schedules → Schedule questions (General Info / Salary Exemption / Deduction) → per-schedule entry → Part B-TI/TTI preview → pay → submit → e-verify.**

- **Filing status:** the filing reason must match income level — **not** Seventh Proviso 139(1) for above-exemption income.
- **Regime:** confirm new regime (do not opt out).
- **Enable schedules:** ensure **CG, 112A, FA, AL, FSI, TR** are on. FSI/TR may be hidden until a foreign-income / relief-u/s-90 question triggers them — verify before final review.
- **Salary Exemption questionnaire:** Rule 2BB allowance questions are **No** unless the taxpayer truly has them. "Any other exemption from salary income?" → **Yes** opens the Section-10 table; enter **gratuity under 10(10)** and **leave encashment under 10(10AA)** in their rows (not under Rule 2BB).

## Cross-schedule linkages & validation gotchas (high-frequency)

Many portal validations fail because a value in one schedule silently depends on another. The high-frequency ones: **80CCD(2)** needs a designated "Basic Salary" 17(1) component (14%-of-Basic cap); **gratuity 10(10) / leave encashment 10(10AA)** must be itemised as 17(1) sub-heads with employer nature = Others (never mis-code as 10(10A)); **FSI** foreign income sits under Other Sources with a **manual** column (d); **CG Table F** 112A quarterly must equal Schedule BFLA even at 0 tax; **AL** needs the immovable-asset Yes/No dropdown answered; **SI** is read-only; never hand-patch the prefill JSON. Fixes can cascade into new validations — re-validate after each change. Full list with exact error messages and fixes: **`reference/wizard-validation-gotchas.md`**.

## Portal CSV uploads

The portal's bulk-upload CSVs (Schedule 112A, Schedule FA, Form 67) have strict formats that cause silent all-rows-skip failures. Core discipline: reuse the **freshly downloaded template header verbatim**; **UTF-8 no BOM + CRLF**; **never open in Excel** before upload (comma corruption); test a row or two when unsure. 112A uses `BE/AE` codes + 14-field rows (AE-consolidated); FA needs `YYYY-MM-DD` dates + country code `2` and **appends** (delete prefill first); Form 67 needs the exact header + DTAA-capped relief. Exact per-file formats and the deterministic generators: **`reference/portal-csv-and-scripts.md`** and **`scripts/README.md`**.

# Pre-Submission Multi-Model JSON Audit (before e-verification)

After full entry but **before submission**, download the final JSON and audit it independently — ideally via **multiple isolated review agents on different models in parallel** (e.g. GPT, Gemini, Opus), each recomputing from the source-of-truth files (plan + extractions), NOT from the JSON, then consolidate (diverse models catch different error classes).

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

Produce a PASS/FAIL table (expected vs JSON vs recompute) and a verdict; `scripts/audit_itr_json.py` runs the mechanical comparison against an independently-computed expected set. Apply fixes in-portal, re-download, re-audit — **fixes can cascade** (correcting gratuity to 10(10) forces the salary sub-head split, which then demands the leave-encashment sub-head), so re-validate after each change.

---

# Payment & e-Verification

1. In Part B-TTI, confirm FTC, total income, and the **balance payable**.
2. **Pay Now → e-Pay Tax → Self-Assessment Tax (300)**, correct AY, exact amount; record the challan (BSR code, serial, date, amount).
3. Add the challan under **Tax Paid → Self-Assessment Tax**; balance should drop to ₹0. Interest recomputes to the payment date — re-check balance is ₹0 before submitting.
4. **Preview → Proceed to Validation → Submit → e-Verify** (Aadhaar OTP / Net Banking). The return is invalid until e-verified.
5. Save the **ITR-V acknowledgement** and challan receipt.

---

# Cross-Cutting — Document Discovery, Passwords, Persistence

**Document discovery** (Gmail/Drive/broker portals — search by sender/subject + FY/CY date range; statements are the controlling source), **encrypted-PDF password patterns** (PAN+DOB etc.; never store credentials), **source-of-truth persistence** (structured per-category extractions + linked RAG files; keep numbers in the plan, lessons in the skill), and the **consolidated missing-data questionnaire** (pre-analyze everything, then ask all remaining questions in one batch; apply answers as one coherent batch). Details: **`reference/discovery-and-persistence.md`**.

# Filing Output

Provide: executive summary; income summary (per head); capital-gains summary (set-off waterfall); deduction summary; tax-liability summary (with surcharge/cess/FTC/interest); AL disclosure; AIS/TIS/26AS hard-truth reconciliation; CAS completeness; filing checklist; risk analysis; consolidated questionnaire; and the pre-submission multi-model audit. Do not finalize a computation while critical information is missing — pre-analyze, questionnaire once, apply the batch, recompute once.

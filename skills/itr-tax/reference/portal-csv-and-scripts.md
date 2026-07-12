# Reference — Portal CSV upload formats & helper scripts

Exact, hard-won formats for the e-filing portal's bulk-upload CSVs. Load this when you reach a CSV-upload step (Schedule 112A, Schedule FA, or Form 67). **Formats change yearly** — per the Currency-of-Law gate, re-download the current template and re-read the official instruction PDF first, and update the matching helper script if a format changed.

## Schedule 112A (B3) CSV
Official spec: `https://static.incometax.gov.in/iec/foservices/assets/itr-shared/documents/112A_115AD_CSV_Instructions.pdf` (re-read yearly). Fields are **coded**, not free text.
- **⚠️ NEVER open the CSV in Excel** — it inserts thousands-separator commas into large numbers (`1243590` → `12,43,590`), turns numbers into `1.24E+06`, and drops the trailing column, causing **all rows to skip** (`common.errors.csv_row_skip`). Generate programmatically, upload directly, view only in **Notepad**.
- Reuse the template's **exact header** (single line, no trailing newline, trailing comma = empty 15th col). **Data rows = 14 fields, NO trailing comma.** UTF-8 no BOM, CRLF.
- **Flag col 1a is a 2-letter code:** `BE` (on/before 31-Jan-2018, grandfathered) / `AE` (after). Long text makes every row skip.
- **AE rows consolidate into ONE row:** ISIN=`INNOTREQUIRD`, Name=`CONSOLIDATED`, **Units & Sale-price blank**; total sale value in col 6, total cost in col 8 (=col 7 = col 13), col 14 = 6−13.
- **BE rows are scrip-wise** with FMV-on-31-Jan-2018 (col 10); if the true NAV is unavailable, conservatively set FMV/unit = cost/unit (safe when net 112A < ₹1.25 lakh).
- No special characters (`, / - _ ( ) & @ \ ' " ; :`) in any value; monetary cols rounded to whole rupees. Reconcile col-14 total to source MF+equity LTCG net. Manual "Add" entry is an equivalent fallback (real dropdown, no format friction).

## Schedule FA A3/A2 CSV
- Reuse the template's exact header (12 named + trailing-empty 13th). **Data rows = 12 fields, NO trailing comma.** UTF-8 no BOM, CRLF.
- Col 1 = `United States Of America` (text); col 2 = ITR **numeric code `2`** (not ISO "US"). Col 6 nature = `Company`/`ETF`.
- **Col 7 date MUST be `YYYY-MM-DD`** (e.g. `2020-06-15`); `DD-MM-YYYY` and `DD-Mon-YYYY` are rejected ("Please Enter Valid input" on col 7) — the #1 FA-CSV error.
- Avoid commas inside address/name (unquoted fields break on them).
- **Upload APPENDS, it does not replace** — delete existing/prefilled rows first (or use replace if offered), then verify the final row count.

## Form 67 `IncomeDetails.csv`
- Reuse the DOWNLOADED template's **exact header** (it has trailing spaces and TWO "Please specify" columns — preserve byte-for-byte). UTF-8 **without BOM**, CRLF. A BOM triggers a generic no-detail "format" error.
- Dropdown columns (country, source) must match the portal strings EXACTLY (e.g. `United States Of America`, `Dividend`), else the numeric fields import but those dropdowns come up blank — set them manually if so.
- Fill optional numeric columns with **0** (115JB/JC, section 91), not blank.
- The **Sec 90/90A "Amount" is REQUIRED** and equals the DTAA-capped relief = `min(foreign_tax, round(DTAA_rate% × income), Indian_tax)`. Use the SAME relief in Schedule FSI (col e) and Schedule TR.

## General CSV discipline
Reuse the portal's downloaded template header verbatim; write UTF-8-no-BOM + CRLF; never open in Excel before upload; test one or two rows first when the format is uncertain; view only in Notepad.

## Helper scripts (`scripts/` in this skill directory)
Deterministic, generic generators/auditors encode these formats so filing is fast and predictable (see `scripts/README.md`). They take input JSON + the freshly downloaded portal template (no taxpayer data inside):
- `build_112a_csv.py` — Schedule 112A (B3) CSV (BE/AE, 14-field, AE-consolidated).
- `build_fa_a3_csv.py` — Schedule FA A3 CSV (YYYY-MM-DD dates, code `2`, per-lot recovery from prior-year JSON).
- `build_form67_csv.py` — Form 67 `IncomeDetails.csv` (exact header, DTAA relief cap).
- `audit_itr_json.py` — final ITR JSON vs an independently-computed expected set (PASS/FAIL), plus `--find`/`--dump-keys` inspection.

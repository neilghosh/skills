# itr-tax skill — helper scripts

Deterministic, **generic** helpers for the mechanical, error-prone parts of an online
ITR-2 filing (portal CSV generation + final-JSON audit). They take input files and the
**freshly downloaded portal template** — they contain **no taxpayer data**. Keep
taxpayer-specific numbers/paths in the personalized plan, not here.

> ⚠️ **Currency-of-Law gate:** portal CSV formats, templates, dropdown strings and the
> ITR JSON schema change every year. Before each filing, **re-download the current
> template** and **re-read the official instruction PDF**, then pass the fresh template
> to these scripts. If a format has changed, update the script. When a format is
> uncertain, test one or two rows before bulk upload.

All scripts are pure standard-library Python 3. Run `python <script> -h` for options.

---

## `build_112a_csv.py` — Schedule 112A (B3) upload CSV
Emits BE/AE-coded, 14-field (no trailing comma), UTF-8-no-BOM, CRLF rows; consolidates
all AE (post-31-Jan-2018) lots into a single `CONSOLIDATED` row by default; BE lots are
scrip-wise with FMV-on-31-Jan-2018 (defaults to cost/unit when NAV is unknown).

```
python build_112a_csv.py --lots lots.json --template B3_template.csv --out B3_filled.csv
```
`lots.json`: list of `{acquired(AE|BE|YYYY-MM-DD), isin, name, units, cost, proceeds[, fmv_31jan2018]}`.
Reconcile the printed col-14 total against your source MF+equity LTCG net. **Never open the output in Excel.**

## `build_fa_a3_csv.py` — Schedule FA "A3" (Foreign Equity & Debt) upload CSV
Emits 12-field rows, country name + numeric code `2`, **`YYYY-MM-DD` dates** (col 7),
commas stripped from address/name. Two modes (combinable):
```
# direct holdings
python build_fa_a3_csv.py --holdings holdings.json --template "A3 Template.csv" --out A3.csv
# recover many per-lot rows (e.g. RSU vests) from last year's ITR JSON
python build_fa_a3_csv.py --template "A3 Template.csv" --out A3.csv \
      --prior-json lastyear.json --recover recover.json --holdings extra.json
```
`holdings.json`: list of `{country_name, country_code, entity, address, zip, nature,
acquired(YYYY-MM-DD), initial, peak, closing, dividend, proceeds}`.
`recover.json`: `{entity_match, total_shares, close_per_share, peak_per_share, div_per_share}`
(one object or a list). **Upload APPENDS — delete prefilled rows first.**

## `build_form67_csv.py` — Form 67 `IncomeDetails.csv`
Reuses the template's exact header (trailing spaces / two "Please specify" columns),
UTF-8-no-BOM, and caps the Sec 90/90A relief at `min(foreign_tax, round(dtaa_rate%×income), indian_tax)`.
```
python build_form67_csv.py --rows rows.json --template IncomeDetails_template.csv --out IncomeDetails.csv
```
`rows.json`: list of `{country_name, source, income_inr, foreign_tax_inr, dtaa_rate, indian_tax_inr, dtaa_article}`.
Use the printed relief as the **same** figure in Schedule FSI (col e) and Schedule TR.

## `audit_itr_json.py` — final ITR JSON audit
Compares the final JSON against an EXPECTED set you compute independently from the
sources (the mechanical half of the pre-submission multi-model audit).
```
python audit_itr_json.py --json final.json --expected expected.json   # PASS/FAIL table
python audit_itr_json.py --json final.json --find 75710               # locate a value's paths
python audit_itr_json.py --json final.json --dump-keys ScheduleOS     # print a subtree
```
`expected.json`: list of `{label, key|path, expected[, tol]}` — `key` deep-finds the first
occurrence; `path` is an explicit dotted path (list indices as `.0`). Exit code is non-zero if any check fails.

---

### Typical flow
1. Currency-of-Law gate → re-download templates + read instruction PDFs.
2. Build the extraction/plan numbers → write the small input JSONs above.
3. Generate each CSV → upload (FA/112A) or bulk-upload (Form 67); test a row or two if a format changed.
4. After full entry, download the final JSON → `audit_itr_json.py` + independent multi-model recompute → fix → re-audit → e-verify.

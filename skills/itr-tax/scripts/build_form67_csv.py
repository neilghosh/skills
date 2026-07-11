#!/usr/bin/env python3
"""
build_form67_csv.py — Generate the Form 67 online bulk-upload CSV (IncomeDetails.csv).

Encodes the hard-won rules (see SKILL.md "Form 67 IncomeDetails.csv"):
  * Reuse the DOWNLOADED template's exact header (it has trailing spaces and TWO
    "Please specify" columns — preserved byte-for-byte by reusing the header line).
  * UTF-8 WITHOUT BOM, CRLF. A BOM triggers a generic no-detail "format" error.
  * Dropdown columns (country, source) must match the portal strings EXACTLY, else the
    numeric fields import but those dropdowns come up blank (set them manually if so).
  * Optional numeric columns filled with 0 (115JB/JC, section 91), not blank.
  * The Sec 90/90A "Amount" is REQUIRED and equals the DTAA-capped relief.
  * DTAA rate-cap: Sec 90 credit = min(foreign_tax, round(dtaa_rate% * income), indian_tax).
    Use the SAME relief in Schedule FSI and TR.

Positional field order (per the documented template mapping, 15 fields):
  1 Sl.No | 2 Country | 3 Please specify | 4 Source of income | 5 Please specify |
  6 Income from outside India | 7 Tax paid outside (Amount) | 8 Rate(%) |
  9 Tax payable normal provisions India | 10 115JB/JC(=0) | 11 DTAA Article No. |
  12 DTAA Rate(%) | 13 Sec 90/90A Amount (relief) | 14 Credit u/s 91(=0) | 15 Total FTC

Input rows JSON (list), each object:
  {
    "country_name": "United States Of America", "source": "Dividend",
    "income_inr": 100000, "foreign_tax_inr": 25000,
    "dtaa_rate": 25, "indian_tax_inr": 36000, "dtaa_article": "10"
  }

Usage:
  python build_form67_csv.py --rows rows.json --template IncomeDetails_template.csv --out IncomeDetails.csv

VERIFY the emitted columns line up with the freshly downloaded template each year — the
Form 67 template layout can change (Currency-of-Law gate in SKILL.md).
"""
import argparse, io, json, sys


def r0(x):
    return int(round(float(x)))


def load_header_line(template_path):
    raw = open(template_path, "rb").read()
    while raw[-1:] in (b"\n", b"\r"):
        raw = raw[:-1]
    return raw


def build_row(i, o):
    income = float(o["income_inr"])
    ftax = float(o["foreign_tax_inr"])
    dtaa_rate = float(o.get("dtaa_rate", 0))
    indian_tax = float(o.get("indian_tax_inr", 0))
    cap = round(dtaa_rate / 100.0 * income) if dtaa_rate else ftax
    relief = min(r0(ftax), cap, r0(indian_tax) if indian_tax else cap)
    return [
        i,                                   # 1 Sl.No
        o["country_name"],                   # 2 Country (exact dropdown string)
        "",                                  # 3 Please specify
        o.get("source", "Dividend"),         # 4 Source (exact dropdown string)
        "",                                  # 5 Please specify
        r0(income),                          # 6 Income from outside India
        r0(ftax),                            # 7 Tax paid outside (Amount)
        dtaa_rate if dtaa_rate else "",      # 8 Rate(%)
        r0(indian_tax),                      # 9 Tax payable normal provisions India
        0,                                   # 10 115JB/JC
        o.get("dtaa_article", ""),           # 11 DTAA Article No.
        dtaa_rate if dtaa_rate else "",      # 12 DTAA Rate(%)
        relief,                              # 13 Sec 90/90A Amount (relief)
        0,                                   # 14 Credit u/s 91
        relief,                              # 15 Total FTC
    ]


def main():
    ap = argparse.ArgumentParser(description="Build Form 67 IncomeDetails upload CSV.")
    ap.add_argument("--rows", required=True, help="Input rows JSON (list of country/head objects).")
    ap.add_argument("--template", required=True, help="Downloaded Form 67 IncomeDetails template CSV.")
    ap.add_argument("--out", required=True, help="Output CSV path.")
    args = ap.parse_args()

    rows_in = json.load(open(args.rows, encoding="utf-8"))
    header = load_header_line(args.template)
    header_cols = header.decode("utf-8-sig").count(",") + 1

    out_rows = [build_row(i + 1, o) for i, o in enumerate(rows_in)]

    with io.open(args.out, "wb") as f:
        f.write(header + b"\r\n")
        for r in out_rows:
            fields = ["" if v == "" else str(v) for v in r]
            if len(fields) != header_cols:
                print(f"  WARNING: row has {len(fields)} fields but header has {header_cols} "
                      f"columns — verify against the downloaded template.", file=sys.stderr)
            f.write(",".join(fields).encode("utf-8") + b"\r\n")

    total_relief = sum(r[12] for r in out_rows)
    print(f"Wrote {args.out}: {len(out_rows)} rows | total FTC relief = {total_relief}")
    print("Use this SAME relief in Schedule FSI (col e) and Schedule TR. Save UTF-8 (no BOM); "
          "if country/source dropdowns import blank, set them manually.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
build_112a_csv.py — Generate a portal-ready Schedule 112A (B3) bulk-upload CSV.

Encodes the hard-won portal format rules (see SKILL.md "Schedule 112A (B3) CSV"):
  * Reuse the DOWNLOADED portal template's exact header (single line, trailing comma).
  * Data rows = 14 fields, NO trailing comma. UTF-8 without BOM, CRLF endings.
  * Flag col 1a is a 2-letter CODE: BE (on/before 31-Jan-2018) / AE (after).
  * AE rows CONSOLIDATE into ONE row: ISIN=INNOTREQUIRD, Name=CONSOLIDATED,
    Units & Sale-price BLANK; col6=total sale value, col8=total cost.
  * BE rows are scrip-wise with FMV-on-31-Jan-2018 (col 10). If true NAV unknown,
    conservatively FMV/unit = cost/unit (safe when net 112A < the exemption threshold).
  * No special chars in any value; monetary cols rounded to whole rupees.
  * NEVER open the output in Excel before upload (comma corruption). View in Notepad only.

NOTE: portal CSV formats change — re-download the template and re-read the official
112A/115AD CSV instruction PDF each year (Currency-of-Law gate in SKILL.md).

Input lots JSON (list of objects):
  {
    "acquired": "AE" | "BE" | "YYYY-MM-DD",   # a date is auto-classified vs 2018-01-31
    "isin": "INF...",
    "name": "Fund or scrip name",
    "units": 123.456,
    "cost": 45000.0,              # total cost of acquisition for the lot
    "proceeds": 60000.0,          # total sale value for the lot
    "fmv_31jan2018": 1234.56      # OPTIONAL per-unit FMV; BE rows only
  }

Usage:
  python build_112a_csv.py --lots lots.json --template B3_template.csv --out B3_filled.csv
  python build_112a_csv.py --lots lots.json --template B3_template.csv --out B3_filled.csv --no-consolidate-ae
"""
import argparse, csv, io, json, re, sys
from datetime import date

GRANDFATHER_CUTOFF = date(2018, 1, 31)
SPECIAL = re.compile(r"[,/\-_()&@\\'\";:]")


def clean(s):
    """Strip characters the portal forbids inside CSV fields."""
    return SPECIAL.sub(" ", str(s)).strip()


def classify(acquired):
    a = str(acquired).strip().upper()
    if a in ("AE", "BE"):
        return a
    # treat as a date
    try:
        y, m, d = [int(x) for x in re.split(r"[-/]", str(acquired))[:3]]
        return "BE" if date(y, m, d) <= GRANDFATHER_CUTOFF else "AE"
    except Exception:
        raise SystemExit(f"Cannot classify 'acquired' value: {acquired!r} (use AE, BE, or YYYY-MM-DD)")


def r0(x):
    return int(round(float(x)))


def load_header(template_path):
    raw = open(template_path, "rb").read()
    # strip trailing CR/LF; the template is a single header line
    while raw[-1:] in (b"\n", b"\r"):
        raw = raw[:-1]
    return raw


def build_rows(lots, consolidate_ae):
    rows = []
    ae = [l for l in lots if classify(l["acquired"]) == "AE"]
    be = [l for l in lots if classify(l["acquired"]) == "BE"]

    if ae:
        if consolidate_ae:
            tot_sale = r0(sum(float(l["proceeds"]) for l in ae))
            tot_cost = r0(sum(float(l["cost"]) for l in ae))
            c7 = tot_cost
            c13 = c7
            c14 = tot_sale - c13
            # 14 fields: flag,isin,name,units,price,6,7,8,9,10,11,12,13,14
            rows.append(["AE", "INNOTREQUIRD", "CONSOLIDATED", "", "",
                         tot_sale, c7, tot_cost, "", "", "", 0, c13, c14])
        else:
            for l in ae:
                units = round(float(l["units"]), 4)
                price = round(float(l["proceeds"]) / units, 4)
                c6 = r0(units * price)
                cost = r0(l["cost"])
                c7 = cost
                c13 = c7
                c14 = c6 - c13
                rows.append(["AE", l["isin"], clean(l["name"]), units, price,
                             c6, c7, cost, "", "", "", 0, c13, c14])

    for l in be:
        units = round(float(l["units"]), 4)
        price = round(float(l["proceeds"]) / units, 4)
        c6 = r0(units * price)
        cost = r0(l["cost"])
        fmv_unit = float(l["fmv_31jan2018"]) if l.get("fmv_31jan2018") else round(float(l["cost"]) / units, 4)
        c11 = r0(units * fmv_unit)
        c9 = min(c6, c11)
        c7 = max(cost, c9)
        c12 = 0
        c13 = r0(c7 + c12)
        c14 = c6 - c13
        rows.append(["BE", l["isin"], clean(l["name"]), units, round(fmv_unit if False else price, 4),
                     c6, c7, cost, c9, round(fmv_unit, 4), c11, c12, c13, c14])
    return rows


def main():
    ap = argparse.ArgumentParser(description="Build Schedule 112A (B3) upload CSV.")
    ap.add_argument("--lots", required=True, help="Input lots JSON (list of lot objects).")
    ap.add_argument("--template", required=True, help="Downloaded portal B3 template CSV (for the exact header).")
    ap.add_argument("--out", required=True, help="Output CSV path.")
    ap.add_argument("--no-consolidate-ae", action="store_true",
                    help="Emit one row per AE lot instead of a single CONSOLIDATED row.")
    args = ap.parse_args()

    lots = json.load(open(args.lots, encoding="utf-8"))
    rows = build_rows(lots, consolidate_ae=not args.no_consolidate_ae)
    header = load_header(args.template)

    with io.open(args.out, "wb") as f:
        f.write(header + b"\r\n")
        for r in rows:
            line = ",".join("" if v == "" else str(v) for v in r)  # 14 fields, NO trailing comma
            if line.count(",") != 13:
                sys.exit(f"Row does not have 14 fields: {line!r}")
            f.write(line.encode("utf-8") + b"\r\n")

    net = round(sum(r[13] for r in rows), 2)
    print(f"Wrote {args.out}: {len(rows)} rows | net 112A balance (col-14 total) = {net}")
    print("Reconcile this against your source MF+equity LTCG net. Do NOT open in Excel; upload directly.")


if __name__ == "__main__":
    main()

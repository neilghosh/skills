#!/usr/bin/env python3
"""
build_fa_a3_csv.py — Generate a portal-ready Schedule FA "A3" (Foreign Equity & Debt
Interest) bulk-upload CSV, with optional per-lot recovery from the prior-year ITR JSON.

Encodes the hard-won portal format rules (see SKILL.md "Schedule FA A3/A2 CSV"):
  * Reuse the DOWNLOADED template's exact header (12 named cols + trailing-empty 13th).
  * Data rows = 12 fields, NO trailing comma. UTF-8 without BOM, CRLF.
  * Col 1 = country NAME text (e.g. "United States Of America");
    col 2 = ITR NUMERIC code (e.g. "2" for USA, NOT ISO "US").
  * Col 6 nature = "Company" (listed stock) / "ETF".
  * Col 7 date MUST be YYYY-MM-DD (DD-MM-YYYY / DD-Mon-YYYY are rejected on col 7).
  * Avoid commas inside address/name (unquoted fields break on them).
  * Upload APPENDS (does not replace) — delete existing/prefilled rows first.
  * FA is calendar-year (1-Jan..31-Dec) and disclosure-only (no tax impact).

Two modes:

(1) Direct holdings (list JSON), each object:
    {
      "country_name": "United States Of America", "country_code": "2",
      "entity": "EXAMPLE CORP", "address": "1 Example Street San Francisco CA",
      "zip": "94105", "nature": "Company", "acquired": "2020-06-15",
      "initial": 377741, "peak": 1118376, "closing": 924359,
      "dividend": 4195, "proceeds": 0
    }

(2) Per-lot recovery from prior-year ITR JSON (for e.g. many equity RSU lots):
    Supply --prior-json <lastyear.json> --recover '<spec.json>'. The spec drives, per entity:
      {
        "entity_match": "EXAMPLE",             # substring match on prior NameOfEntity
        "total_shares": 936,                   # current total shares held (sanity check)
        "close_per_share": 23701.5,            # current-year INR closing per share
        "peak_per_share": 28676.3,             # current-year INR peak per share
        "div_per_share": 107.558               # current-year INR dividend per share
      }
    Prior-year per-lot ClosingBalance / (prior_close_total/total_shares) recovers each
    lot's share count; current values = shares * per-share. Lot date/initial reused as-is.

Usage:
  python build_fa_a3_csv.py --holdings holdings.json --template "A3 Template.csv" --out A3_filled.csv
  python build_fa_a3_csv.py --template "A3 Template.csv" --out A3_filled.csv \
        --prior-json lastyear.json --recover recover.json --holdings extra_holdings.json
"""
import argparse, io, json, re, sys

SPECIAL_STRIP = re.compile(r"[,]")  # commas are the fatal char for unquoted CSV fields
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def clean(s):
    return SPECIAL_STRIP.sub(" ", str(s)).strip()


def r0(x):
    return int(round(float(x)))


def find_key(o, key, res):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == key:
                res.append(v)
            find_key(v, key, res)
    elif isinstance(o, list):
        for it in o:
            find_key(it, key, res)
    return res


def recover_lots(prior_json, spec):
    """Return current-year A3 holding rows for one entity by recovering per-lot shares."""
    d = json.load(open(prior_json, encoding="utf-8"))
    eq = find_key(d, "DtlsForeignEquityDebtInterest", [])
    if not eq:
        sys.exit("No DtlsForeignEquityDebtInterest found in prior-year JSON.")
    eq = eq[0]
    lots = [x for x in eq if spec["entity_match"].upper() in x["NameOfEntity"].upper()]
    if not lots:
        sys.exit(f"No prior-year lots match entity_match={spec['entity_match']!r}")
    prior_close_total = sum(x["ClosingBalance"] for x in lots)
    base = prior_close_total / float(spec["total_shares"])  # prior INR per share
    out = []
    recovered = 0
    for x in lots:
        sh = round(x["ClosingBalance"] / base)
        recovered += sh
        out.append({
            "country_name": x.get("CountryName", "United States Of America").title(),
            "country_code": x.get("CountryCodeExcludingIndia", "2"),
            "entity": x["NameOfEntity"],
            "address": x.get("AddressOfEntity", ""),
            "zip": x.get("ZipCode", ""),
            "nature": x.get("NatureOfEntity", "Company"),
            "acquired": x["InterestAcquiringDate"],
            "initial": x["InitialValOfInvstmnt"],  # historical cost unchanged
            "peak": sh * float(spec["peak_per_share"]),
            "closing": sh * float(spec["close_per_share"]),
            "dividend": sh * float(spec.get("div_per_share", 0)),
            "proceeds": 0,
        })
    if recovered != int(spec["total_shares"]):
        print(f"  WARNING: recovered shares {recovered} != total_shares {spec['total_shares']} "
              f"(check the base/total_shares).", file=sys.stderr)
    return out


def load_header(template_path):
    raw = open(template_path, "rb").read()
    while raw[-1:] in (b"\n", b"\r"):
        raw = raw[:-1]
    return raw


def row_to_fields(h):
    date = str(h["acquired"]).strip()
    if not DATE_RE.match(date):
        sys.exit(f"Date must be YYYY-MM-DD (portal rejects other formats): {date!r}")
    # 12 fields in template order
    return [
        clean(h.get("country_name", "United States Of America")),
        str(h.get("country_code", "2")),
        clean(h["entity"]),
        clean(h.get("address", "")),
        str(h.get("zip", "")),
        clean(h.get("nature", "Company")),
        date,
        r0(h["initial"]),
        r0(h["peak"]),
        r0(h["closing"]),
        r0(h.get("dividend", 0)),
        r0(h.get("proceeds", 0)),
    ]


def main():
    ap = argparse.ArgumentParser(description="Build Schedule FA A3 upload CSV.")
    ap.add_argument("--template", required=True, help="Downloaded FA A3 template CSV (for the exact header).")
    ap.add_argument("--out", required=True, help="Output CSV path.")
    ap.add_argument("--holdings", help="Direct holdings JSON (list).")
    ap.add_argument("--prior-json", help="Prior-year ITR JSON for per-lot recovery.")
    ap.add_argument("--recover", help="Recovery spec JSON (single object or list of objects).")
    args = ap.parse_args()

    holdings = []
    if args.recover:
        if not args.prior_json:
            sys.exit("--recover requires --prior-json")
        spec = json.load(open(args.recover, encoding="utf-8"))
        specs = spec if isinstance(spec, list) else [spec]
        for s in specs:
            holdings += recover_lots(args.prior_json, s)
    if args.holdings:
        holdings += json.load(open(args.holdings, encoding="utf-8"))
    if not holdings:
        sys.exit("No holdings: supply --holdings and/or --recover/--prior-json.")

    header = load_header(args.template)
    rows = [row_to_fields(h) for h in holdings]

    with io.open(args.out, "wb") as f:
        f.write(header + b"\r\n")
        for r in rows:
            line = ",".join(str(v) for v in r)  # 12 fields, NO trailing comma
            if line.count(",") != 11:
                sys.exit(f"Row does not have 12 fields: {line!r}")
            f.write(line.encode("utf-8") + b"\r\n")

    print(f"Wrote {args.out}: {len(rows)} rows")
    print(f"  peak total    = {sum(r[8] for r in rows):,}")
    print(f"  closing total = {sum(r[9] for r in rows):,}")
    print(f"  proceeds total= {sum(r[11] for r in rows):,}")
    print("Upload APPENDS — delete existing/prefilled A3 rows first, then verify the final row count.")


if __name__ == "__main__":
    main()

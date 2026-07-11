#!/usr/bin/env python3
"""
audit_itr_json.py — Independent figure-by-figure audit of a final ITR-2 JSON.

Parses the portal/utility ITR JSON and compares selected values against an EXPECTED
set that you compute independently from the source-of-truth (plan + extractions).
Prints a PASS/FAIL table. This is the mechanical half of the pre-submission audit
(see SKILL.md "Pre-Submission Multi-Model JSON Audit"); still run independent human/
multi-model recomputation of the numbers that feed the expected file.

Two lookup styles per expected item:
  * "key":  deep-find the FIRST occurrence of that key name anywhere in the tree.
  * "path": explicit dotted path from the root, e.g. "ITR.ITR2.PartB_TTI.Foo.Bar"
            (list indices as .0 .1). Use when a key name is ambiguous.

Expected JSON format (list of objects):
  [
    {"label": "Total Income",   "key": "TotalIncome",              "expected": 10000000},
    {"label": "FTC relief",     "key": "TotalTaxReliefOutsideIndia","expected": 25000},
    {"label": "Gratuity code",  "path": "ITR.ITR2.ScheduleS.AllwncExemptUs10.AllwncExemptUs10Dtls.0.SalNatureDesc",
                                 "expected": "10(10)"}
  ]

Optionally add "tol": <rupees> to allow a rounding tolerance (default 0).

Usage:
  python audit_itr_json.py --json final.json --expected expected.json
  python audit_itr_json.py --json final.json --find 100000      # locate every path holding a value
  python audit_itr_json.py --json final.json --dump-keys ScheduleOS   # show subtree of a key
"""
import argparse, json, sys


def deep_find(o, key, res):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == key:
                res.append(v)
            deep_find(v, key, res)
    elif isinstance(o, list):
        for it in o:
            deep_find(it, key, res)
    return res


def by_path(o, path):
    cur = o
    for part in path.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        elif isinstance(cur, dict):
            if part not in cur:
                return None
            cur = cur[part]
        else:
            return None
    return cur


def walk(o, prefix=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, f"{prefix}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, f"{prefix}.{i}")
    else:
        yield prefix.lstrip("."), o


def main():
    ap = argparse.ArgumentParser(description="Audit a final ITR JSON against expected values.")
    ap.add_argument("--json", required=True, help="Final ITR JSON path.")
    ap.add_argument("--expected", help="Expected-values JSON (list of {label,key|path,expected[,tol]}).")
    ap.add_argument("--find", help="Print every path whose numeric value equals this.")
    ap.add_argument("--dump-keys", help="Print the first subtree found under this key name.")
    args = ap.parse_args()

    d = json.load(open(args.json, encoding="utf-8"))

    if args.find is not None:
        try:
            target = float(args.find)
        except ValueError:
            target = args.find
        hits = [p for p, v in walk(d) if v == target or (isinstance(v, (int, float)) and v == target)]
        print(f"'{args.find}' found at {len(hits)} path(s):")
        for p in hits:
            print("  ", p)
        return

    if args.dump_keys:
        res = deep_find(d, args.dump_keys, [])
        if not res:
            print(f"Key {args.dump_keys!r} not found.")
        else:
            print(json.dumps(res[0], indent=1, ensure_ascii=False)[:4000])
        return

    if not args.expected:
        sys.exit("Provide --expected, or use --find / --dump-keys.")

    items = json.load(open(args.expected, encoding="utf-8"))
    width = max(len(i["label"]) for i in items)
    npass = nfail = 0
    print(f"{'FIELD'.ljust(width)}  {'EXPECTED':>16}  {'FOUND':>16}  RESULT")
    print("-" * (width + 44))
    for it in items:
        exp = it["expected"]
        tol = float(it.get("tol", 0))
        if "path" in it:
            got = by_path(d, it["path"])
        else:
            found = deep_find(d, it["key"], [])
            got = found[0] if found else None
        ok = False
        if got is not None:
            if isinstance(exp, (int, float)) and isinstance(got, (int, float)):
                ok = abs(float(got) - float(exp)) <= tol
            else:
                ok = str(got) == str(exp)
        npass += ok
        nfail += (not ok)
        result = "PASS" if ok else "*** FAIL ***"
        print(f"{it['label'].ljust(width)}  {str(exp):>16}  {str(got):>16}  {result}")
    print("-" * (width + 44))
    print(f"{npass} passed, {nfail} failed.")
    sys.exit(1 if nfail else 0)


if __name__ == "__main__":
    main()

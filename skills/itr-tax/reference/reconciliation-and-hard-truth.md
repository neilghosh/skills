# Reference — AIS/TIS/26AS hard-truth reconciliation, CAS, prefill

Load this during validation/reconciliation and before declaring the return filing-ready.

## AIS / TIS / Form 26AS hard-truth floor
Treat current-year **26AS, AIS, TIS as a mandatory minimum filing floor**.

1. Every **active/processed/accepted/source-confirmed** income or TDS/TCS item must be mapped to the ITR or have a documented exclusion/reconciliation reason.
2. Every TDS/TCS credit claimed must match the 26AS/prefill credit **exactly** (subject only to documented rounding/corrections). A prefill TDS a rupee **above** 26AS is immaterial — CPC caps credit at 26AS; correct it to the 26AS-exact value if the row edits easily, else proceed.
3. Use exact reported values — never silently round, net, omit, or estimate them.
4. SFT sale/purchase amounts are **not** automatically taxable income — match to broker/RTA totals, compute gains separately.
5. The return **may report more** than AIS/TIS/26AS when independent evidence exists (foreign income is **expected** to be absent — its absence is not a gap). Absence never permits omission.
6. Build a **hard-truth matrix**: statement, info code/section, source, status, reported amount, reported TDS/TCS, ITR destination, filed amount, difference, reconciliation reason. Don't finalize until every row is `Exact`, `Included above reported`, or `Explained difference`.

## Prefill
Prefill is an information import, not a return — it commonly omits foreign income, FTC, broker capital gains, no-TDS income, and FA/AL data. Always produce a **prefill→final reconciliation** rather than forcing the return to equal prefill.

## CAS end-of-filing completeness check
If an NSDL/CDSL CAS is available, use it as a final completeness control: build a row per account/ISIN/folio and confirm every holding maps to Schedule AL (at cost) or has an exclusion reason; every FY sale/redemption/maturity maps to the CG/OS ledger; every dividend/interest maps to OS or is marked non-taxable. Prevent double-counting across demat/folio/broker/AIS. CAS market value is a completeness check, **not** AL cost. CAS is not a full wealth statement — separately check foreign accounts, bank/FD, physical assets, NPS/insurance, and unlisted assets.

## EPF taxable interest (Rule 9D)
EPF interest is exempt only on employee contributions up to **₹2.5 lakh/year** (₹5 lakh where the employer does not contribute — verify the limit for the target AY). Interest on the **excess** is taxable each year; EPFO deducts 10% TDS u/s 194A and reports it in 26AS — treat that reported slice as hard truth and include it in Schedule OS. Do not include the exempt portion. (Forward lever for *future* years only: reduce VPF; mandatory 12%-of-basic EPF is statutory.)

## Why a balance tax arises (diagnostic bridge)
Decompose the balance by income that was **under-withheld**, comparing each stream's marginal-rate tax (top slab + surcharge + cess) against the credit given: interest (FD/EPF/bond) has only 10% TDS vs ~35-39% marginal (usually the biggest driver); domestic dividends often have no TDS; foreign dividends carry only treaty withholding vs the higher Indian marginal (payable after FTC); capital gains have no TDS and may net near zero after set-off/threshold. Present as an income-by-income shortfall bridge so the balance reads as structural, not an error.

## Non-statement item deferral (user decision)
Domestic items absent from 26AS/AIS/TIS (e.g. a provisional SGB coupon, small NBFC interest not in AIS) are the only genuinely "soft" additions the taxpayer may choose to **defer** to a later revision. When deferring: keep a documented `deferredItems` block (amount + reason + re-add impact), recompute downstream totals, never silently delete, and keep reported income **at or above** every hard-truth floor. Foreign income is never "soft" — always self-report it.

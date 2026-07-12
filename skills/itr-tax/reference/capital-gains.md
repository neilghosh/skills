# Reference — Capital gains (classification, set-off, Schedule CG placement)

Load during the capital-gains computation and Schedule CG entry.

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
- **Section B / row B (112A):** equity MF LTCG + domestic listed-equity LTCG/LTCL. Has a **Download/Upload CSV** (see `reference/portal-csv-and-scripts.md`).
- **Section A / row A5 "assets other than A1–A4":** slab-rate STCG — §50AA fund units and foreign shares/ETFs. Within A5, put consideration under sub-row **"ii. assets other than unquoted shares"**, NOT **"i. unquoted shares"** (that wrongly invokes §50CA FMV rules). Enter the net.
- After both sections, set-off flows through **CYLA → BFLA → CFL** automatically. Verify net CG, that 112A taxable = 0 when under threshold, and **carry-forward = 0** when the loss was absorbed.

## Schedule CG Table F (quarterly accrual) — common validation error
Table F row for "LTCG taxable @12.5% u/s 112A" **must sum to the corresponding Schedule BFLA value, even when the tax is 0** (error: "Table F Sl no.5 breakup of all quarters should equal item 3vii of Schedule BFLA"). Distribute the net 112A gain by the quarter of the underlying transfers (bulk March MF redemptions → the `16/3-31/3` column). Since tax is 0, the quarter choice has no 234C effect.

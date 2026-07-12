# Reference — Document discovery, PDF passwords, persistence, questionnaire

Cross-cutting mechanics used throughout the filing. Load when gathering documents, persisting extractions, or preparing the missing-data questionnaire.

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

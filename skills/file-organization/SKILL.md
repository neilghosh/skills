---
name: file-organization
description: >-
  Audits, deduplicates, reorganizes, and standardizes directories and files across
  personal, family, financial, and medical archives. Enforces generalized naming formulas,
  strict content-based inspection, clinical document standards, and path-context deduplication.
---

# File Organization & Standardization Runbook

A fully generalized, context-aware runbook for auditing, deduplicating, categorizing, and standardizing personal, family, and institutional file archives.

---

## 1. Universal Naming Formulas

All file names are generated using consistent, predictable formulas derived from **internal document content**, not download, print, or scan artifacts.

### A. General & Identity Files (Default: Kebab-Case)

```text
[<date>-][<issuer>-]<document-type>[-<qualifier>][-<status>].<ext>
```

| Component | Purpose | Guidelines | Examples |
|---|---|---|---|
| `<date>` | Issuance, validity, or period | Use `YYYY` or `YYYY-MM-DD`. Omit if current or timeless. | `2024`, `2023-04-01`, `ay-2023-24` |
| `<issuer>` | Issuing authority or institution | Omit if already implied by enclosing directory or document type. | `sbi`, `hdfc`, `cbse`, `epfo` |
| `<document-type>` | Core document category / subject | Lowercase single-word or hyphenated descriptor. | `passport`, `pan`, `aadhaar`, `marksheet`, `statement`, `tax-receipt` |
| `<qualifier>` | Variant, level, or descriptor | Distinguishes grade, variant, or account. | `10th`, `12th`, `degree`, `pvc`, `learners`, `front` |
| `<status>` | Verification or state (optional) | Use only when distinguishing signed/attested versions. | `attested`, `signed`, `masked` |

#### Generalized Category Patterns:
- **Identity & Legal**:
  - `[<issuer>-]<type>[-<variant>][-<status>].<ext>` &rarr; `pan.pdf`, `pan-attested.pdf`, `aadhaar-pvc.pdf`, `voter-id.pdf`
  - `passport[-<year>].pdf` &rarr; `passport.pdf`, `passport-2024.pdf`, `photo-passport-size.jpg`
  - `driving-license[-<variant>].pdf` &rarr; `driving-license.pdf`, `driving-license-learners.pdf`
- **Academic & Career**:
  - `<level>-marksheet.pdf` &rarr; `10th-marksheet.pdf`, `12th-marksheet.pdf`, `degree-transcript.pdf`
  - `<type>-certificate.pdf` &rarr; `degree-certificate.pdf`, `birth-certificate.pdf`, `provisional-certificate.pdf`
  - `<document-type>.pdf` &rarr; `resume.pdf`, `offer-letter.pdf`, `relieving-letter.pdf`
- **Banking, Financial & Tax**:
  - `statement-<period>.pdf` &rarr; `statement-2023-q4.pdf`, `statement-2024-03.pdf`
  - `passbook[-<issuer>].pdf` &rarr; `passbook-sbi.pdf`, `passbook.pdf`
  - `receipt-<type>[-<year>].pdf` &rarr; `property-tax-2023.pdf`, `fd-receipt.pdf`
  - `tax-return-<period>.pdf` &rarr; `itr-acknowledgement-ay-2023-24.pdf`

---

### B. Medical & Clinical Documents (Mandatory Exception)

To preserve clinical chronological records across multiple doctors, hospitals, and labs, medical files use a strict human-readable pattern:

```text
YYYY-MM-DD - <Patient Name> - <Record Type> - <Provider or Test Name>.pdf
```

| Record Type | Third Token Rule | Example |
|---|---|---|
| **Lab / Diagnostic Test** | Specific test name(s) | `YYYY-MM-DD - <Patient Name> - Lab - Complete Blood Count.pdf` |
| **Consultation / Prescription** | Physician's title and full name | `YYYY-MM-DD - <Patient Name> - Prescription - Dr Physician Name.pdf` |
| **Hospital / Inpatient** | Hospital or clinic name | `YYYY-MM-DD - <Patient Name> - Discharge Summary - Hospital Name.pdf` |
| **Billing / Insurance** | Hospital / provider name | `YYYY-MM-DD - <Patient Name> - Bill - Hospital Name.pdf` |

> **Event Date Rule**: Always use the date the medical encounter or test took place, never the scan date, download date, or report printing date.

---

## 2. Generalization & Deduplication Principles

### A. Path-Context Deduplication (Eliminate Redundancy)
Never repeat information that is already unambiguous from the folder path:
1. **Never repeat person/owner names**: Inside any personal or individual directory (e.g., `<Workspace>/Identity/Passport/`), use `passport-2024.pdf`, NEVER `<Person Name> Passport 2024.pdf`.
2. **Never repeat parent folder tokens**: Inside `<Workspace>/Identity/Aadhaar/`, use `aadhaar.pdf` or `pvc.pdf`, NEVER `aadhaar-aadhaar.pdf`. Inside `<Workspace>/Identity/PAN/`, use `pan.pdf`, NEVER `pan-card.pdf`.

### B. Content-First Ground Truth
Never trust existing file names or system-assigned metadata:
1. Inspect internal text via CLI tools (`pdftotext`, `strings`) or render the first page to image (`pdftoppm`) for OCR inspection.
2. Verify:
   - True subject / owner of the document.
   - Issuing organization or provider.
   - Actual transaction, exam, or encounter date.
   - Document classification.

### C. Normalization & Hygiene
- **No spaces in non-medical filenames**: Always use kebab-case (`lowercase-with-hyphens`).
- **Sanitize corruptions**: Strip duplicate extensions (`.pdf.pdf`, `.jpg.pdf`, `.png.pdf`).
- **Remove trailing spaces**: Fix spaces before extensions (`name .pdf` &rarr; `name.pdf`).
- **Correct spelling errors**: Normalize typos (`Propety` &rarr; `property`, `Finacials` &rarr; `financials`).

---

## 3. Directory Layout Archetypes

### A. Individual Workspace (`<Root>/<Individual-Identifier>/`)

```text
<Individual-Root>/
├── Career/                 # Resumes, offers, relieving letters, contracts
├── Certificates/           # Academic transcripts, degrees, diplomas, awards
├── Financial/
│   ├── Banking/            # Statements, passbooks, check records
│   ├── Investments/        # Fixed deposits, mutual funds, equity portfolios
│   ├── Property-Tax/       # Municipal tax receipts, property assessments
│   └── Taxes/              # Annual tax returns (ITR, Form 16, AIS, 26AS)
├── Identity/
│   ├── Aadhaar/            # Regular, PVC, e-Aadhaar
│   ├── Driving-License/    # Permanent DL, learner's license
│   ├── PAN/                # PAN card copies, e-PAN
│   └── Passport/           # Passports, visa stamp copies
├── Medical/                # Clinical records, chronologically organized
│   ├── Lab-Reports/
│   ├── Prescriptions/
│   └── Vaccines/
├── Vehicles/               # Registration certificates (RC), insurance, emission
└── Travel/                 # Visas, itineraries, tickets
```

### B. Shared / Group Archives (`<Root>/Shared/` or `<Root>/Family/`)

Store records that naturally encompass multiple individuals in shared domain roots:
- `Shared/Insurance/`: Multi-member floater health policies, umbrella policies.
- `Shared/Property/`: Joint title deeds, sale agreements, floor plans, mutations.
- `Shared/Reference/`: General manuals, health guides, emergency contacts.

---

## 4. Deduplication Protocol

1. **Size Grouping**: Index files by exact byte size to quickly isolate candidate collisions.
2. **Binary Hashing**: Compute MD5 / SHA-256 checksums (`md5 -r <file>`).
   > *Cloud Storage / FileProvider Note*: When files are stored in on-demand cloud storage (e.g. Google Drive, iCloud, OneDrive), use native shell commands (`md5`, `cmp`) to trigger transparent on-demand hydration.
3. **Collision Resolution**:
   - Prune download duplicates (e.g., `(1)`, `(2)`, `-copy`).
   - Prune OS prefixes (e.g., `Copy of ...`, `DUPLICATE_...`).
   - Prune zero-byte and corrupted remnants.
   - Retain the cleanest, most descriptive filename and remove identical binary duplicates.

---

## 5. Execution Workflow

```text
[Scan & Index Directory Tree]
        │
        ▼
[Inspect Content via pdftotext / Page Render]
        │
        ▼
[Resolve True Owner & Route to Individual Workspace]
        │
        ▼
[Deduplicate via Exact Binary Hash]
        │
        ▼
[Apply Universal Naming Formula & Strip Redundancy]
        │
        ▼
[Relocate into Domain Archetype Hierarchy]
```

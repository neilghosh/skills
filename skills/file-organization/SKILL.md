---
name: file-organization
description: >-
  Audits, deduplicates, reorganizes, and standardizes directories and files across
  personal, family, financial, and medical archives. Enforces generalized naming formulas,
  strict content-based inspection, medical document standards, and path-context deduplication.
---

# File Organization & Standardization Runbook

A generalized runbook for auditing, deduplicating, categorizing, and standardizing personal, family, and institutional file archives.

---

## 1. Universal Naming Formula

All file names are generated using consistent, predictable formulas derived from **internal document content**, not download or scan artifacts.

### A. General & Personal Files (Default: Kebab-Case)

```text
[<date>-][<issuer>-]<type-or-topic>[-<qualifier>][-<status>].<ext>
```

| Element | Description | Examples |
|---|---|---|
| `<date>` | Date of issuance, validity, or period (`YYYY` or `YYYY-MM-DD`). Omit if timeless/current. | `2024`, `2023-04-01`, `ay-2023-24` |
| `<issuer>` | Issuing authority, bank, or organization (omit if implied by parent folder). | `sbi`, `hdfc`, `cbse`, `epfo` |
| `<type-or-topic>` | The core document type or topic. | `passport`, `pan`, `aadhaar`, `marksheet`, `statement`, `tax-receipt` |
| `<qualifier>` | Distinguishes variant, tier, account, or level. | `pvc`, `10th`, `degree`, `term-deposit`, `front` |
| `<status>` | Verification or format state (optional). | `attested`, `signed`, `masked`, `draft` |

#### Concrete Derivations:
- **Identity Documents**:
  - `passport-<year>.pdf` *(e.g., `passport-2024.pdf`)*
  - `photo-passport-size.jpg`
  - `pan.pdf`, `pan-attested.pdf`
  - `aadhaar.pdf`, `aadhaar-pvc.pdf`, `eaadhaar-<date>.pdf`
  - `voter-id.pdf`
  - `driving-license.pdf` / `dl.pdf`, `dl-learners.pdf`
- **Academic & Career**:
  - `<grade-or-level>-marksheet.pdf` *(e.g., `10th-marksheet.pdf`, `12th-marksheet.pdf`, `btech-marksheet.pdf`)*
  - `degree-certificate.pdf`, `pass-certificate.pdf`
  - `relieving-letter.pdf`, `offer-letter.pdf`, `resume.pdf`
- **Financial & Banking**:
  - `statement-<period>.pdf` *(e.g., `statement-2023-q4.pdf`, `statement-2024-03.pdf`)*
  - `passbook[-<issuer>].pdf` *(e.g., `passbook-sbi.pdf`)*
  - `fd-receipt-<account-or-date>.pdf`
  - `property-tax-<year>.pdf`
  - `itr-acknowledgement-<ay-year>.pdf`

### B. Medical Documents (Mandatory Standard)

Medical records follow a specific clinical format to preserve chronological patient histories across providers:

```text
YYYY-MM-DD - <Patient Name> - <Record Type> - <Provider or Test Name>.pdf
```

- **Lab / Diagnostic Tests**: Replace provider with the specific test name(s):
  `YYYY-MM-DD - Patient Name - Lab - Lipid Profile.pdf`
- **Consultations / Prescriptions**: Use the physician's title and name:
  `YYYY-MM-DD - Patient Name - Prescription - Dr Name.pdf`
- **Hospitalizations / Invoices**:
  `YYYY-MM-DD - Patient Name - Discharge Summary - Hospital Name.pdf`
  `YYYY-MM-DD - Patient Name - Bill - Hospital Name.pdf`
- **Crucial Rule**: Use the **event/encounter date** (when the test, appointment, or treatment occurred), never the date the report was downloaded, printed, or scanned.

---

## 2. Generalization & Normalization Rules

1. **No Spaces (Except Medical Standard)**:
   - Use lowercase kebab-case (`lower-case-with-hyphens`) for all non-medical filenames.
   - Replace underscores, multi-spaces, and mixed delimiters with a single `-`.

2. **Eliminate Redundant Context (Path Deduplication)**:
   - **No Person Redundancy**: Do not repeat the individual's name if the file is inside their personal workspace (e.g., inside `Personal/Identity/Passport/`, use `passport-2024.pdf`, NOT `Sabyasachi Ghosh Passport 2024.pdf`).
   - **No Parent Redundancy**: Do not repeat the category name if it is identical to the enclosing directory (e.g., inside `Aadhaar/`, use `aadhaar.pdf` or `pvc.pdf`, not `aadhaar-aadhaar.pdf`).

3. **Content-First Ground Truth**:
   - Never trust existing filenames, download tags (`document.pdf`, `E-Letter.pdf`, `Front Page (1).pdf`), or metadata timestamps.
   - Inspect internal text via `pdftotext` or page rendering (`pdftoppm` / image viewer) to verify:
     1. True identity of the subject / person.
     2. Issuing authority.
     3. Actual transaction / event date.
     4. Core document classification.

4. **Sanitize Artifacts & Typographical Errors**:
   - Strip duplicate extensions (`.pdf.pdf`, `.jpg.pdf`, `.png.pdf`).
   - Correct scan/system corruptions and typos (`Fist` &rarr; `first`, `Propety` &rarr; `property`, `Finacials` &rarr; `financials`).
   - Strip trailing spaces before extensions (`name .pdf` &rarr; `name.pdf`).

---

## 3. Archive Layout Archetypes

### A. Individual Workspace (`Personal/` or `Family/<Member Name>/`)

Partition individual archives by lifecycle domain:

```text
<Individual-Root>/
├── Career/                 # Resumes, offer letters, relieving letters, contracts
├── Certificates/           # Diplomas, degrees, academic transcripts, marksheets
├── Financial/
│   ├── Banking/            # Account statements, passbook copies, check records
│   ├── Investments/        # Fixed deposits, mutual fund statements, share holdings
│   ├── Property-Tax/       # Municipal property tax assessments and receipts
│   └── Taxes/              # Annual tax returns (ITR, Form 16, AIS, 26AS)
├── Identity/
│   ├── Aadhaar/            # Regular, PVC, e-Aadhaar
│   ├── Driving-License/    # Permanent DL, learner's license
│   ├── PAN/                # PAN card copies, e-PAN
│   └── Passport/           # Current and expired passports, visa stamp pages
├── Medical/                # Individual clinical records, prescriptions, checkups
│   ├── Prescriptions/
│   ├── Lab-Reports/
│   └── Vaccines/
├── Vehicles/               # RC, insurance, pollution (PUC), service bills
└── Travel/                 # Personal visas, tickets, boarding passes
```

### B. Shared / Multi-Member Domain

Store documents covering multiple individuals at the shared family tier:
- `Family/Insurance/`: Multi-member family floater policies, coverage schedules.
- `Family/Property/`: Joint title deeds, mutations, sale agreements, floor plans.
- `Family/Medical-Reference/`: General health reference materials and pharmacy guides.

---

## 4. Deduplication Protocol

1. **Size Grouping**: Quickly index files by exact byte size to identify collision candidates.
2. **Binary Hashing**: Compute MD5 / SHA-256 checksums (`md5 -r <file>`).
   > *Cloud Storage Note*: In macOS FileProvider (Google Drive, iCloud, OneDrive), use native shell commands (`md5`, `cmp`) to trigger automatic hydration when Python `open()` hits dataless cloud files.
3. **Pattern Resolution**:
   - Browser duplicate suffixes (`(1)`, `(2)`, `-copy`).
   - System copy prefixes (`Copy of ...`, `DUPLICATE_...`).
   - Corrupt zero-byte files (`.textClipping`, 0-byte PDFs).
   - Retain the highest-fidelity, most descriptively named file and prune the rest.

---

## 5. Execution Workflow

```
[Scan Directory Tree]
        │
        ▼
[Inspect Content & Metadata via pdftotext/OCR]
        │
        ▼
[Resolve True Ownership (Personal vs Family Member)]
        │
        ▼
[Deduplicate by Hash & File Integrity]
        │
        ▼
[Apply Naming Formula & Eliminate Redundant Words]
        │
        ▼
[Relocate into Domain Hierarchy & Verify Clean State]
```

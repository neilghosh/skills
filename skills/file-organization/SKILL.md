---
name: file-organization
description: >-
  Audits, deduplicates, reorganizes, and standardizes directories and files across
  personal, family, financial, and medical archives. Enforces strict content-based
  naming, medical document conventions, space-free naming, and eliminates redundant words.
---

# File Organization & Standardization Runbook

This skill guides the auditing, deduplication, categorization, and standardization of personal, family, and financial file archives.

---

## 1. Core Principles & User Preferences

### A. Medical Documents (Mandatory Exception)
Always format medical records as:
```text
YYYY-MM-DD - Patient Name - Type - Doctor Name.pdf
```
- If the document is a **Lab / Diagnostic Test**: replace the doctor name with the test name:
  `YYYY-MM-DD - Patient Name - Lab - Test Names.pdf`
- For prescriptions, consultations, or invoices, use the respective type (e.g., `Prescription`, `Consultation`, `Bill`).
- **Date Rule**: Always use the date the test/consultation actually occurred, never the date the document was scanned, downloaded, or printed.

### B. All Non-Medical Files (Space-Free & Concise)
- **No spaces unless strictly necessary**: Use concise kebab-case (`lower-case-with-hyphens`).
- **Remove redundant words**:
  - Do not repeat the individual's name inside their own directory tree (e.g., inside `Personal/Identity/Passport/`, use `passport-2024.pdf`, not `Sabyasachi Ghosh Passport 2024.pdf`).
  - Do not repeat the category name if it is already in the parent folder (e.g., inside `Aadhaar/`, use `aadhaar.pdf`, `aadhaar-pvc.pdf`).
  - Use concise keywords (e.g., `birth-cert.pdf`, `10th-marksheet.pdf`, `dl.pdf`, `passbook-sbi.pdf`).
- **Fix double extensions & typos**: Eliminate `.pdf.pdf`, `.jpg.pdf`, and spelling errors (`Fist` -> `first`, `Propety` -> `property`, `Finacials` -> `financials`).

### C. Content-Based Renaming
Never rely on generic or legacy filenames (`document.pdf`, `Front Page.pdf`, `certificate.pdf`, `Important Information.pdf`).
1. Inspect the internal text using `pdftotext` or render page 1 using `pdftoppm` / `view_file`.
2. Determine the true issuer, subject, date, and document type.
3. Rename strictly according to the internal content.

---

## 2. Deduplication Strategy

1. **Size Match**: Group files by exact byte size to quickly find potential duplicates.
2. **Hash Verification**: Compute MD5 checksums (`md5 -r <file>`) to confirm 100% binary matches.
   > **Note on Cloud Storage (macOS FileProvider)**: If Python's `open()` throws `PermissionError` on dataless cloud files, use shell commands (`md5`, `diff`, `cmp`), which trigger automatic on-demand hydration.
3. **Pattern Candidates**:
   - Browser re-downloads: files ending in `(1).pdf`, `(2).pdf`, or with duplicate timestamps.
   - System copy prefixes: files prefixed with `Copy of ...` or `DUPLICATE_...`.
   - Trailing whitespace duplicates: e.g., `name .pdf` vs `name.pdf`.
   - Corrupt zero-byte files: e.g., empty `.textClipping` or 0-byte `.pdf`.
4. **Resolution**: Keep the best-named and most complete version; safely remove confirmed duplicates.

---

## 3. Directory Layout & Distribution Rules

### A. Ownership Distribution
- Distribute files to the actual individual's workspace:
  - Sabyasachi / Neil Ghosh files &rarr; `Personal/`
  - Family members &rarr; `Family/<Member Name>/`
  - Never allow one person's identity or health records to remain loose inside another person's workspace.

### B. Standard Folder Trees

#### Personal Directory Tree
```text
Personal/
├── Career/               # Resumes, relieving letters, employment records
├── Certificates/         # Degree, marksheets, board certificates, awards
├── Identity/
│   ├── Aadhaar/          # aadhaar.pdf, aadhaar-pvc.pdf, eaadhaar-YYYY-MM-DD.pdf
│   ├── Corporate-IDs/    # Employer ID cards, EPFO slips
│   ├── Driving-License/  # dl.pdf, learners-license.pdf, dl-front.pdf
│   ├── PAN/              # pan.pdf, pan-attested.pdf, pan-signed.png
│   └── Passport/         # passport-YYYY.pdf, photo-passport-size.jpg
├── Land-Record/          # Plots, Khata passbooks, maps, and Dharani receipts
├── Medical/              # Individual medical history, trend reports, checkups
│   ├── Fitness/          # Workout & rehab plans
│   ├── Insurance/        # Member health ID cards
│   └── Vaccines/         # COVID and immunization certificates
├── Security/             # Recovery keys, credentials, bookmark backups
├── Vehicles/             # RC, toll passes, pollution certificates
├── VISA/                 # Visas, appointment slips, applications
└── Wedding/              # Guest lists, invitations
```

#### Family Member Directory Tree (`Family/<Member Name>/`)
```text
<Member Name>/
├── Financial/
│   ├── Banking/          # Passbooks, statements, pension orders
│   ├── Fixed-Deposits/   # FD receipts and certificates
│   ├── Property-Tax/     # Municipal property tax receipts
│   └── Taxes/            # Year-wise ITRs, 26AS, AIS, TIS
├── Identity/             # Aadhaar, PAN, Passport, Voter ID
├── Medical/              # Consultations, hospital folders, prescriptions
│   ├── Prescriptions/    # Formatted: YYYY-MM-DD - Name - Prescription - Doctor.pdf
│   └── Vaccines/         # Immunization records
├── Photos/               # Portrait and passport-size photographs
└── School/               # Marksheets, transfer certs, bonafide certs (if student)
```

#### Shared Family Folders
- `Family/Insurance/`: Multi-member family floater policies (National Parivar Mediclaim, Religare, Star Health).
- `Family/Medical-Reference/`: General wellness guides, pharmacy references, and alternative medicine notes.
- `Family/Travel/`: Multi-member visa applications, flight tickets, and travel guidelines.

---

## 4. Execution Workflow

1. **Scan & Map**: Walk the target directory recursively, list all files with sizes and dates.
2. **Audit Duplicates & Misplacements**:
   - Identify exact hash duplicates, near-duplicates, and files belonging to other family members.
3. **Inspect Questionable Files**:
   - Check internal text/OCR for generic names (`document.pdf`, `E-Letter.pdf`, `Front Page.pdf`).
4. **Restructure & Rename**:
   - Create destination folders.
   - Execute relocations and removals.
   - Apply space-free kebab-case naming for general files, and `YYYY-MM-DD - Patient Name - Type - Doctor Name.pdf` for medical files.
5. **Verify**: Print the final recursive hierarchy to confirm 0 loose files in root and clean organization.

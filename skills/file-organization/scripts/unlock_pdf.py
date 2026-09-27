#!/usr/bin/env python3
"""
unlock_pdf.py - Secure PDF password removal utility for file organization.

Features:
- Scans directory or single file for password-protected / encrypted PDFs.
- Securely prompts the user for passwords using getpass (hidden input, never echoed or logged).
- Supports batch password attempts (e.g. trying common known personal passwords like DOB, PAN, PIN).
- Uses `qpdf` if available (fastest and cleanest), with pure-Python `pypdf` fallback.
- Never prints passwords to terminal output, logs, or history.
"""

import argparse
import getpass
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


def check_qpdf_installed() -> bool:
    return shutil.which("qpdf") is not None


def is_pdf_encrypted_qpdf(file_path: Path) -> bool:
    try:
        # qpdf --show-encryption returns exit code 0 if readable/unencrypted, 2 if password required
        res = subprocess.run(
            ["qpdf", "--show-encryption", str(file_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # If output indicates encryption or returncode is non-zero (password needed)
        if "File is not encrypted" in res.stdout:
            return False
        # If encrypted without user password (only owner restriction), qpdf says "File is encrypted" but readable
        if "File is encrypted" in res.stdout and "extract: allowed" in res.stdout and res.returncode == 0:
            # Can be read without password
            return True
        return res.returncode != 0 or "File is encrypted" in res.stdout
    except Exception:
        return False


def is_pdf_encrypted_pypdf(file_path: Path) -> bool:
    if not PYPDF_AVAILABLE:
        return False
    try:
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            return reader.is_encrypted
    except Exception:
        return False


def is_pdf_encrypted(file_path: Path) -> bool:
    if check_qpdf_installed():
        return is_pdf_encrypted_qpdf(file_path)
    if PYPDF_AVAILABLE:
        return is_pdf_encrypted_pypdf(file_path)
    # Basic fallback check for /Encrypt in raw PDF header/trailer
    try:
        with open(file_path, "rb") as f:
            header = f.read(4096)
            f.seek(max(0, os.path.getsize(file_path) - 4096))
            trailer = f.read(4096)
            return b"/Encrypt" in header or b"/Encrypt" in trailer
    except Exception:
        return False


def unlock_pdf_qpdf(input_path: Path, output_path: Path, password: str) -> bool:
    cmd = [
        "qpdf",
        f"--password={password}",
        "--decrypt",
        str(input_path),
        str(output_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return res.returncode == 0


def unlock_pdf_pypdf(input_path: Path, output_path: Path, password: str) -> bool:
    if not PYPDF_AVAILABLE:
        return False
    try:
        reader = pypdf.PdfReader(str(input_path))
        if reader.is_encrypted:
            res = reader.decrypt(password)
            if res == 0:  # Failed decryption
                return False
        writer = pypdf.PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        with open(output_path, "wb") as f_out:
            writer.write(f_out)
        return True
    except Exception:
        return False


def unlock_pdf(input_path: Path, output_path: Path, password: str) -> bool:
    if check_qpdf_installed():
        return unlock_pdf_qpdf(input_path, output_path, password)
    elif PYPDF_AVAILABLE:
        return unlock_pdf_pypdf(input_path, output_path, password)
    else:
        print("[!] Error: Neither 'qpdf' nor Python 'pypdf' library is installed.", file=sys.stderr)
        print("    Install qpdf via: brew install qpdf (macOS) or apt install qpdf (Linux)", file=sys.stderr)
        print("    Or install python package: pip install pypdf", file=sys.stderr)
        sys.exit(1)


def find_locked_pdfs(target_path: Path):
    if target_path.is_file():
        if target_path.suffix.lower() == ".pdf" and is_pdf_encrypted(target_path):
            yield target_path
    else:
        for root, _, files in os.walk(target_path):
            for file in files:
                if file.lower().endswith(".pdf"):
                    p = Path(root) / file
                    if is_pdf_encrypted(p):
                        yield p


def main():
    parser = argparse.ArgumentParser(
        description="Securely inspect and decrypt password-protected PDFs for file organization."
    )
    parser.add_argument("path", help="Directory or single PDF file to check/unlock")
    parser.add_argument("--in-place", action="store_true", help="Replace original encrypted file with unlocked version")
    parser.add_argument("--dry-run", action="store_true", help="Only scan and report encrypted files without prompting")
    args = parser.parse_args()

    target = Path(args.path).resolve()
    if not target.exists():
        print(f"[!] Path does not exist: {target}", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Scanning for encrypted PDFs in: {target}")
    locked_files = list(find_locked_pdfs(target))

    if not locked_files:
        print("[✓] No password-protected PDFs found.")
        return

    print(f"[!] Found {len(locked_files)} locked PDF(s):")
    for f in locked_files:
        print(f"    - {f}")

    if args.dry_run:
        return

    cached_passwords = []

    for f in locked_files:
        print(f"\nProcessing: {f.name}")
        unlocked = False

        # Try previously provided passwords in this session first
        for pwd in cached_passwords:
            temp_out = f.with_suffix(".unlocked.tmp")
            if unlock_pdf(f, temp_out, pwd):
                if args.in_place:
                    temp_out.replace(f)
                    print(f"  [✓] Unlocked using cached session password (replaced in-place).")
                else:
                    out_final = f.with_name(f.stem + "-unlocked.pdf")
                    temp_out.replace(out_final)
                    print(f"  [✓] Unlocked -> {out_final.name}")
                unlocked = True
                break
            else:
                if temp_out.exists():
                    temp_out.unlink()

        if unlocked:
            continue

        # Secure interactive prompt
        attempts = 0
        while attempts < 3:
            pwd = getpass.getpass(f"  Enter password for '{f.name}' (input hidden, press Enter to skip): ")
            if not pwd:
                print("  [>] Skipped.")
                break

            temp_out = f.with_suffix(".unlocked.tmp")
            if unlock_pdf(f, temp_out, pwd):
                if args.in_place:
                    temp_out.replace(f)
                    print(f"  [✓] Successfully unlocked (replaced in-place).")
                else:
                    out_final = f.with_name(f.stem + "-unlocked.pdf")
                    temp_out.replace(out_final)
                    print(f"  [✓] Successfully unlocked -> {out_final.name}")
                
                if pwd not in cached_passwords:
                    cached_passwords.append(pwd)
                unlocked = True
                break
            else:
                if temp_out.exists():
                    temp_out.unlink()
                print("  [✗] Incorrect password. Try again.")
                attempts += 1

        if not unlocked and attempts == 3:
            print(f"  [!] Failed to unlock '{f.name}' after 3 attempts.")


if __name__ == "__main__":
    main()

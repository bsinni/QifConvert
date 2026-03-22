#!/usr/bin/env python3
"""
QIF to CSV Converter
Converts Quicken Interchange Format (.qif) files to CSV format.
"""

import csv
import sys
import os
from datetime import datetime


# Map QIF field codes to human-readable column names
FIELD_MAP = {
    "D": "Date",
    "T": "Amount",
    "U": "Amount (U)",
    "C": "Cleared",
    "N": "Number",
    "P": "Payee",
    "M": "Memo",
    "L": "Category",
    "A": "Address",
    "^": None,  # End of record marker
}

# QIF account type headers
ACCOUNT_TYPES = {
    "!Type:Bank",
    "!Type:Cash",
    "!Type:CCard",
    "!Type:Invst",
    "!Type:Oth A",
    "!Type:Oth L",
    "!Type:Invoice",
    "!Account",
    "!Option:AutoSwitch",
    "!Clear:AutoSwitch",
}


def parse_date(date_str):
    """Try several common QIF date formats and return ISO format (YYYY-MM-DD)."""
    date_str = date_str.strip().replace("'", "/").replace("-", "/")
    formats = [
        "%m/%d/%Y",   # 12/31/2024
        "%m/%d/%y",   # 12/31/24
        "%-m/%-d/%Y", # 1/1/2024  (Linux)
        "%d/%m/%Y",   # 31/12/2024
        "%Y/%m/%d",   # 2024/12/31
        "%m/ %d/%Y",  # QIF sometimes pads with a space
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str  # Return as-is if no format matches


def parse_qif(filepath):
    """Parse a QIF file and return a list of transaction dicts."""
    transactions = []
    current = {}

    with open(filepath, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.rstrip("\n\r")

            if not line:
                continue

            # Skip account type headers
            if line in ACCOUNT_TYPES or line.startswith("!"):
                continue

            code = line[0]
            value = line[1:].strip()

            if code == "^":
                # End of record — save if non-empty
                if current:
                    transactions.append(current)
                    current = {}
            elif code == "D":
                current["Date"] = parse_date(value)
            elif code == "T":
                # Normalize amount: remove commas, keep sign
                current["Amount"] = value.replace(",", "")
            elif code == "U":
                current.setdefault("Amount (U)", value.replace(",", ""))
            elif code == "C":
                current["Cleared"] = value
            elif code == "N":
                current["Number"] = value
            elif code == "P":
                current["Payee"] = value
            elif code == "M":
                current["Memo"] = value
            elif code == "L":
                current["Category"] = value
            elif code == "A":
                # Address can be multi-line; join with a pipe
                current["Address"] = current.get("Address", "") + ("|" if "Address" in current else "") + value
            # Ignore unknown codes

    # Catch last record if file doesn't end with ^
    if current:
        transactions.append(current)

    return transactions


def write_csv(transactions, output_path):
    """Write a list of transaction dicts to a CSV file."""
    if not transactions:
        print("No transactions found — CSV not written.")
        return

    # Build ordered fieldnames; put common fields first
    priority = ["Date", "Amount", "Payee", "Category", "Memo", "Number", "Cleared", "Address", "Amount (U)"]
    all_keys = set()
    for t in transactions:
        all_keys.update(t.keys())

    fieldnames = [f for f in priority if f in all_keys]
    fieldnames += sorted(all_keys - set(fieldnames))  # Any extras alphabetically

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(transactions)

    print(f"  Wrote {len(transactions)} transaction(s) → {output_path}")


def convert(qif_path, csv_path=None):
    """Convert a single QIF file to CSV."""
    if not os.path.isfile(qif_path):
        print(f"Error: File not found: {qif_path}")
        return False

    if csv_path is None:
        csv_path = os.path.splitext(qif_path)[0] + ".csv"

    print(f"Converting: {qif_path}")
    transactions = parse_qif(qif_path)

    base = os.path.splitext(os.path.basename(qif_path))[0]
    csv_path = os.path.join(os.path.dirname(qif_path), base + ".csv")    
    write_csv(transactions, csv_path)
    return True


def main():
    # paths
    filename = 'MyMoney.qif'
    qif_folder: str = r'/Users/barrysinni/Code/QifConvert/'

    if not qif_folder:
        print("Usage:")
        print("missing python qif_to_csv.py file.qif ")
        sys.exit(1)

    # Two-argument mode: single input → single output
    if filename.endswith(".qif"):
        convert(qif_folder + filename,qif_folder)
    # else:
    #     # Batch mode: convert each .qif file
    #     for path in args:
    #         if path.lower().endswith(".qif"):
    #             convert(path)
    #         else:
    #             print(f"Skipping (not a .qif file): {path}")


if __name__ == "__main__":
    main()

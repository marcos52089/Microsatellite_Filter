#!/usr/bin/env python3
"""
add_msat_name_v3.py

Goal:
  - Insert a standardized microsatellite name AFTER 'id' and BEFORE 'forward_primer'.
  - Guarantee: All primer rows for the SAME locus (e.g., ids "66.1", "66.2", "66.3") get the SAME name.
  - Always include a numeric suffix ".<n>" even for the first occurrence of a given base name.
  - The numeric suffix increments ONLY when a **different locus** shares the same base name.

Name format:
  <motif>(<R1>-<R2>).<n>
    motif = N1...Nn (from .compare)
    R1    = min(fasta1_repeat_number, fasta2_repeat_number)
    R2    = max(fasta1_repeat_number, fasta2_repeat_number)
    n     = ascending index among loci that have the same <motif>(R1-R2)

Join key and robustness:
  - Locus number is extracted from the primer 'id' using regex: the leading integer (e.g., "66" from "66.1" or "66.1.2").
  - .compare is keyed by 'number'.

Usage:
  python add_msat_name_v3.py -p A_welshii_Primers -c input.compare -o A_welshii_Primers.named.v3.tsv
"""
import sys, csv, argparse, re
from pathlib import Path

def parse_args():
    ap = argparse.ArgumentParser(description="Insert standardized microsatellite name column into primer table (v3)")
    ap.add_argument("-p", "--primers", required=True, help="Primer table TSV from connectorToPrimer3.pl")
    ap.add_argument("-c", "--compare", required=True, help="SSRMMD .compare TSV (filtered or unfiltered)")
    ap.add_argument("-o", "--output", default=None, help="Output TSV (default: <primers>.named.v3.tsv)")
    return ap.parse_args()

def load_compare(path):
    """Return dict: number -> (motif, rmin, rmax)"""
    comp = {}
    with open(path, "r", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        needed = ["number","fasta1_motif","fasta2_motif","fasta1_repeat_number","fasta2_repeat_number"]
        miss = [c for c in needed if c not in r.fieldnames]
        if miss:
            sys.exit(f"[error] .compare missing columns: {miss}\nHave: {r.fieldnames}")
        for row in r:
            num = (row.get("number") or "").strip()
            if not num:
                continue
            m1 = (row.get("fasta1_motif") or "").strip().upper()
            m2 = (row.get("fasta2_motif") or "").strip().upper()
            motif = m1 if m1 else m2
            try:
                rep1 = int(row.get("fasta1_repeat_number", ""))
                rep2 = int(row.get("fasta2_repeat_number", ""))
            except Exception:
                continue
            rmin = rep1 if rep1 <= rep2 else rep2
            rmax = rep2 if rep2 >= rep1 else rep1
            comp[num] = (motif, rmin, rmax)
    if not comp:
        sys.exit("[error] No rows loaded from .compare")
    return comp

def extract_locus_num(raw_id: str) -> str:
    """Extract leading integer locus number from id (e.g., '66' from '66.1' or '66.1.3')."""
    m = re.match(r"\s*(\d+)", raw_id or "")
    return m.group(1) if m else ""

def main():
    args = parse_args()
    in_p = Path(args.primers)
    in_c = Path(args.compare)
    out_p = Path(args.output) if args.output else (in_p.parent / (in_p.name + ".named.v3.tsv"))

    comp = load_compare(in_c)

    # Read primer table (tab-delimited)
    with open(in_p, "r", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        rows = list(reader)
    if not rows:
        sys.exit("[error] Primer file appears empty")
    header = rows[0]
    data = rows[1:]

    # Find columns
    try:
        id_idx = header.index("id")
    except ValueError:
        sys.exit(f"[error] Primer table needs an 'id' column; got: {header}")
    if "forward_primer" not in header:
        sys.exit(f"[error] Primer table missing 'forward_primer' column; columns: {header}")

    # New header with insertion after 'id'
    new_header = header[:id_idx+1] + ["microsatellite_name"] + header[id_idx+1:]

    # Pass 1: collect loci in input order and determine their base names from .compare
    loci_in_order = []
    seen_loci = set()
    locus_base = {}  # locus_num -> base_name "<motif>(R1-R2)"
    missing_loci = set()

    for row in data:
        if len(row) < len(header):
            row = (row + [""] * len(header))[:len(header)]
        raw_id = (row[id_idx] or "").strip()
        locus_num = extract_locus_num(raw_id)
        if not locus_num:
            continue
        if locus_num in seen_loci:
            continue
        seen_loci.add(locus_num)
        loci_in_order.append(locus_num)
        if locus_num in comp:
            motif, rmin, rmax = comp[locus_num]
            locus_base[locus_num] = f"{motif}({rmin}-{rmax})"
        else:
            locus_base[locus_num] = "NA"
            missing_loci.add(locus_num)

    # Pass 2: assign global indices per base name, only when encountering a NEW locus with that base
    base_counts = {}  # base_name -> next index to assign
    locus_final = {}  # locus_num -> final name "<base>.<idx>" or "NA"
    for locus in loci_in_order:
        base = locus_base.get(locus, "NA")
        if base == "NA":
            locus_final[locus] = "NA"
            continue
        base_counts[base] = base_counts.get(base, 0) + 1
        idx = base_counts[base]
        locus_final[locus] = f"{base}.{idx}"

    # Pass 3: write out rows, inserting the locus-level name for every primer row of that locus
    out_rows = [new_header]
    for row in data:
        if len(row) < len(header):
            row = (row + [""] * len(header))[:len(header)]
        raw_id = (row[id_idx] or "").strip()
        locus_num = extract_locus_num(raw_id)
        ms_name = locus_final.get(locus_num, "NA")
        new_row = row[:id_idx+1] + [ms_name] + row[id_idx+1:]
        out_rows.append(new_row)

    with open(out_p, "w", newline="") as fout:
        w = csv.writer(fout, delimiter="\t", lineterminator="\n")
        w.writerows(out_rows)

    # Summary
    print(f"[add_msat_name_v3] input primers : {in_p}")
    print(f"[add_msat_name_v3] input compare : {in_c}")
    print(f"[add_msat_name_v3] wrote         : {out_p}")
    if missing_loci:
        print(f"[add_msat_name_v3] WARNING: {len(missing_loci)} loci had no match in .compare -> name=NA")

if __name__ == "__main__":
    main()

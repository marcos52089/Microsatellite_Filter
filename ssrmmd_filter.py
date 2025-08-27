#!/usr/bin/env python3
"""
ssrmmd_filter.py

Filter an SSRMMD '.compare' file strictly by parsing information present in the file,
and write an **identically formatted .compare file** (same header/columns, same order)
suitable for downstream use with SSRMMD's connectorToPrimer3.pl.

Selection criteria (all configurable via CLI flags; defaults match your guidelines):
  - Keep only polymorphic loci (column 'polymorphism' == 'yes')
  - Motif length restricted to di-/tri-/tetranucleotide repeats (2, 3, or 4 bp)
  - Minimum repeat count required in BOTH genomes (default: >= 5) using columns
      'fasta1_repeat_number' and 'fasta2_repeat_number'
  - Avoid low-complexity AT-only motifs (motif comprised solely of A/T)
  - Require that motifs are identical across genomes and contain only A/C/G/T characters

No attempt is made to infer compound/imperfect repeats beyond what is provided in the file;
we simply enforce equality and valid base composition on the reported motif strings.

Usage:
  python ssrmmd_filter.py -i input.compare -o input.filtered.compare
  # change thresholds if desired:
  python ssrmmd_filter.py -i input.compare -o input.filtered.compare \
      --allowed-motif-lengths 2,3,4 --min-repeats 5

Notes:
  * Input must be a tab-delimited SSRMMD '.compare' with the standard column names.
  * Output preserves the **exact** header columns and order from the input.
  * Summary is printed to STDERR.
"""

import sys, csv, argparse
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser(
        description="Filter SSRMMD .compare file (preserving schema)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("-i", "--input", required=True, help="Path to SSRMMD .compare (TSV)")
    p.add_argument("-o", "--output", default=None, help="Output .compare path (defaults to <input>.filtered.compare)")
    p.add_argument("--allowed-motif-lengths", default="2,3,4",
                   help="Comma-separated list of allowed motif lengths (e.g., '2,3,4' or '2,3,4,5,6')")
    p.add_argument("--min-repeats", type=int, default=5,
                   help="Minimum motif repeat count required in BOTH genomes")
    p.add_argument("--keep-at-only", action="store_true",
                   help="If set, do NOT filter out AT-only motifs. By default they are removed.")
    return p.parse_args()

def is_at_only(motif: str) -> bool:
    s = set(motif.upper())
    return s.issubset({"A", "T"})

def is_valid_dna(motif: str) -> bool:
    """Allow only unambiguous A/C/G/T."""
    return set(motif.upper()).issubset({"A","C","G","T"})

def to_int_or_none(x):
    try:
        return int(x)
    except Exception:
        return None

def main():
    args = parse_args()
    in_path = Path(args.input)
    # Default output name keeps the .compare extension and appends '.filtered'
    if args.output:
        out_path = Path(args.output)
    else:
        if in_path.suffix == ".compare":
            out_path = in_path.with_suffix("")  # drop .compare
            out_path = out_path.with_name(out_path.name + ".filtered.compare")
        else:
            out_path = in_path.with_suffix(in_path.suffix + ".filtered.compare")

    # Parse allowed motif lengths
    allowed_lengths = set()
    for tok in str(args.allowed_motif_lengths).split(","):
        tok = tok.strip()
        if not tok:
            continue
        try:
            allowed_lengths.add(int(tok))
        except ValueError:
            sys.exit(f"[error] Non-integer in --allowed-motif-lengths: {tok!r}")

    required_cols = [
        "number",
        "fasta1_id", "fasta1_motif", "fasta1_repeat_number", "fasta1_start", "fasta1_end",
        "fasta2_id", "fasta2_motif", "fasta2_repeat_number", "fasta2_start", "fasta2_end",
        "fasta1_left_fs", "fasta1_left_fs_length",
        "fasta2_left_distance(LD)", "fasta2_left_identity(NW)",
        "fasta1_right_fs", "fasta1_right_fs_length",
        "fasta2_right_distance(LD)", "fasta2_right_identity(NW)",
        "polymorphism",
    ]

    total = kept = 0

    with in_path.open("r", newline="") as fin:
        reader = csv.DictReader(fin, delimiter="\t")
        # Validate header has at least the required columns
        missing = [c for c in required_cols if c not in reader.fieldnames]
        if missing:
            sys.exit(
                "[error] Input missing required columns: %s\nFound columns: %s"
                % (missing, reader.fieldnames)
            )

        # Preserve **exact** input header order
        header = list(reader.fieldnames)

        with out_path.open("w", newline="") as fout:
            writer = csv.DictWriter(fout, fieldnames=header, delimiter="\t", lineterminator="\n")
            writer.writeheader()

            for row in reader:
                total += 1

                # 1) polymorphic?
                if (row.get("polymorphism","").strip().lower() != "yes"):
                    continue

                # 2) motifs present, identical, valid unambiguous DNA?
                m1 = (row.get("fasta1_motif") or "").strip().upper()
                m2 = (row.get("fasta2_motif") or "").strip().upper()
                if not m1 or not m2:
                    continue
                if m1 != m2:
                    continue
                if not is_valid_dna(m1):
                    continue

                # 3) motif length allowed? (default 2,3,4 -> di/tri/tetra)
                if len(m1) not in allowed_lengths:
                    continue

                # 4) repeat count threshold in BOTH genomes
                r1 = to_int_or_none(row.get("fasta1_repeat_number",""))
                r2 = to_int_or_none(row.get("fasta2_repeat_number",""))
                if r1 is None or r2 is None:
                    continue
                if r1 < args.min_repeats or r2 < args.min_repeats:
                    continue

                # 5) avoid AT-only motifs unless user overrides
                if not args.keep_at_only and is_at_only(m1):
                    continue

                # Passed all filters -> write **unchanged** row
                writer.writerow(row)
                kept += 1

    # Summary to STDERR
    print(f"[ssrmmd_filter] input:  {in_path}", file=sys.stderr)
    print(f"[ssrmmd_filter] output: {out_path}", file=sys.stderr)
    print(f"[ssrmmd_filter] kept {kept} / {total} rows", file=sys.stderr)

if __name__ == "__main__":
    main()

# Microsatellite_Filter

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Primer3](https://img.shields.io/badge/Primer3-2.5.0-green.svg)](http://primer3.sourceforge.net/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Lightweight, reproducible utilities to go from **SSRMMD** outputs → **filtered polymorphic SSRs** → **Primer3 primer design** → **standardized microsatellite names** you can sort, share, and import into Excel/Sheets.

---

## Workflow Overview

1. **Mine SSRs** with [SSRMMD](https://github.com/GouXiangJian/SSRMMD).
2. **Filter polymorphic SSRs** to your design rules (`ssrmmd_filter.py`).
3. **Design primers** with Primer3 via SSRMMD’s `connectorToPrimer3.pl`.
4. **Standardize microsatellite names** (`add_msat_name.py`).
5. *(Optional)* Fix file extensions for Excel/Sheets (`force_tsv_extension.py`).

---

## Tools Included

- **`ssrmmd_filter.py`**  
  Filters `.compare` files to keep only high-quality, polymorphic SSR loci, while preserving schema and column order.

- **`add_msat_name.py`**  
  Inserts a standardized microsatellite name once per locus (e.g., `TC(10-11).1`) and reuses it for all its primer rows.

- **`force_tsv_extension.py`**  
  Ensures any output file has a `.tsv` extension for compatibility with Excel and Google Sheets.

---

## Tool Reference

**`ssrmmd_filter.py`**  

Keeps only:
- Polymorphic loci (polymorphism == yes)
- Di-/tri-/tetranucleotide motifs (default)
- ≥5 repeats in both genomes
- Removes AT-only motifs unless --keep-at-only is set
- Preserves schema (ready for connectorToPrimer3.pl)

Usage:

```bash
python ssrmmd_filter.py -i SSRMMD_microsatellites.compare -o SSRMMD_microsatellites_filtered.compare
````

--

**`add_msat_name.py`**

- Extracts locus ID from primer id (e.g., 66.1 → locus 66)
- Builds unique names for microsatellites like TG(11-13).1
- Ensures all primers of the same locus share the same name

Usage:

```bash
python add_msat_name.py -p microsatellite_primers -c SSRMMD_microsatellites.compare -o microsatellite_primers_named.tsv
````

--

**`force_tsv_extension.py`**  

- Copies/renames any file to have a .tsv suffix (content unchanged)

Usage:

```bash
python force_tsv_extension.py -i microsatellite_primers_named -o microsatellite_primers_named.tsv --rename
````

---

## End-to-End Workflow

```bash
# 1) Filter SSRs
python ssrmmd_filter.py \
  -i SSRMMD_microsatellites.compare \
  -o SSRMMD_microsatellites_filtered.compare

# 2) Design primers (tight Tm for one thermocycler program)
perl connectorToPrimer3.pl \
  -i consensus_BS13_TB_sort.fasta-and-consensus_BS21_KL_MCS_sort.filtered.compare \
  -s 2 -m USE -pa /path/to/primer3_core-linux \
  -f 0 -r 3 -t 59,60,61 -d 1 -g 30,70 -es 20,20,24 -us 140-180 \
  -o microsatellite_primers

# 3) Add standardized microsatellite names
python add_msat_name.py \
  -p microsatellite_primers \
  -c SSRMMD_microsatellites.compare \
  -o microsatellite_primers_named.tsv

# 4) (Optional) Fix extension if needed
python force_tsv_extension.py -i microsatellite_primers_named -o microsatellite_primers_named.tsv --rename

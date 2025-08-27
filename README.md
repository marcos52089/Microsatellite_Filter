# Microsatellite_Design
This repo contains lightweight, reproducible utilities to go from SSRMMD outputs → filtered polymorphic SSRs → Primer3 primer design → standardized microsatellite names you can sort, share, and import into Excel/Sheets.

# SSR Marker Workflow

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Primer3](https://img.shields.io/badge/Primer3-2.5.0-green.svg)](http://primer3.sourceforge.net/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Lightweight, reproducible utilities to go from **SSRMMD** outputs → **filtered polymorphic SSRs** → **Primer3 primer design** → **standardized microsatellite names** you can sort, share, and import into Excel/Sheets.

---

## Table of Contents
- [Workflow Overview](#workflow-overview)
- [Tools Included](#tools-included)
- [End-to-End Workflow](#end-to-end-workflow)
- [Tool Reference](#tool-reference)
- [File Naming Conventions](#file-naming-conventions)
- [Requirements](#requirements)
- [QuickStart](#quickstart)
- [Troubleshooting](#troubleshooting)
- [Citation & Credits](#citation--credits)
- [License](#license)

---

## Workflow Overview

1. **Mine SSRs** with [SSRMMD](https://github.com/GouXiangJian/SSRMMD).
2. **Filter polymorphic SSRs** to your design rules (`ssrmmd_filter.py`).
3. **Design primers** with Primer3 via SSRMMD’s `connectorToPrimer3.pl`.
4. **Standardize microsatellite names** (`add_msat_name_v3.py`).
5. *(Optional)* Fix file extensions for Excel/Sheets (`force_tsv_extension.py`).

---

## Tools Included

- **`ssrmmd_filter.py`**  
  Filters `.compare` files to keep only high-quality, polymorphic SSR loci, while preserving schema and column order.

- **`add_msat_name_v3.py`**  
  Inserts a standardized microsatellite name once per locus (e.g., `TC(10-11).1`) and reuses it for all its primer rows.

- **`force_tsv_extension.py`**  
  Ensures any output file has a `.tsv` extension for compatibility with Excel and Google Sheets.

---

## Tool Reference

````markdown
```bash
ssrmmd_filter.py
```
````
text
Keeps only polymorphic loci (polymorphism == yes)

Di-/tri-/tetranucleotide motifs (default)

≥5 repeats in both genomes

Removes AT-only motifs unless --keep-at-only is set

Preserves schema → ready for connectorToPrimer3.pl

---

## End-to-End Workflow

```bash
# 1) Filter SSRs
python ssrmmd_filter.py \
  -i consensus_BS13_TB_sort.fasta-and-consensus_BS21_KL_MCS_sort.fasta.compare \
  -o consensus_BS13_TB_sort.fasta-and-consensus_BS21_KL_MCS_sort.filtered.compare

# 2) Design primers (tight Tm for one thermocycler program)
perl connectorToPrimer3.pl \
  -i consensus_BS13_TB_sort.fasta-and-consensus_BS21_KL_MCS_sort.filtered.compare \
  -s 2 -m USE -pa /path/to/primer3_core-linux \
  -f 0 -r 3 -t 59,60,61 -d 1 -g 30,70 -es 20,20,24 -us 140-180 \
  -o Awelshii_P3

# 3) Add standardized microsatellite names
python add_msat_name_v3.py \
  -p A_welshii_Primers \
  -c consensus_BS13_TB_sort.fasta-and-consensus_BS21_KL_MCS_sort.fasta.compare \
  -o A_welshii_Primers.named.v3.tsv

# 4) (Optional) Fix extension if needed
python force_tsv_extension.py -i A_welshii_Primers.named.v3.file -o A_welshii_Primers.named.v3.tsv --rename

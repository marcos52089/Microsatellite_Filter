#!/usr/bin/env python3
"""
force_tsv_extension.py
Copy (or rename) a file to ensure it has a .tsv extension. Content is unchanged.
Usage:
  python force_tsv_extension.py -i INPUT -o OUTPUT.tsv
"""
import argparse, shutil, sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("-i","--input", required=True)
ap.add_argument("-o","--output", required=True)
ap.add_argument("--rename", action="store_true", help="Rename (move) instead of copy")
args = ap.parse_args()

src = Path(args.input)
dst = Path(args.output)
if dst.suffix.lower() != ".tsv":
    print("[warn] Output does not end with .tsv; adding .tsv")
    dst = dst.with_suffix(dst.suffix + ".tsv")

dst.parent.mkdir(parents=True, exist_ok=True)
if args.rename:
    src.rename(dst)
else:
    shutil.copy2(src, dst)

print(f"[done] {'renamed' if args.rename else 'copied'} {src} -> {dst}")

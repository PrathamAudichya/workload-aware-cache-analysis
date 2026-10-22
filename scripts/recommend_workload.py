#!/usr/bin/env python3
"""Classify a workload and recommend a cache configuration.

Usage:
  python scripts/recommend_workload.py prog.c [--max-insts N] [--verify] [--cflags=-DX=1] [--name label]
  python scripts/recommend_workload.py prog_x86 [--verify]
  python scripts/recommend_workload.py --features L2_MPKI BRANCH_MPKI      (no gem5 needed)
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
GEM5 = os.environ.get("GEM5", str(Path.home() / "projects/gem5/build/X86/gem5.opt"))
BASE_LABEL = "l1d48k12_l2k1280k10"
L2_MPKI_MEM, BR_MPKI_BRANCH, PASS = 5.0, 5.0, 0.95
LABEL = re.compile(r"l1d(\d+)k(\d+)_l2k(\d+)k(\d+)")

def classify(l2_mpki, br_mpki):
    if l2_mpki > L2_MPKI_MEM:
        return "memory"
    return "branch" if br_mpki > BR_MPKI_BRANCH else "compute"

def recommendation(cls):
    recs = pd.read_csv("data/class_recommendations_safe.csv").set_index("class")
    return recs.loc[cls, "safe_config"], int(recs.loc[cls, "total_kib"])

def flags(label):
    l1, a1, l2, a2 = LABEL.fullmatch(label).groups()
    return [f"--l1d-size={l1}KiB", f"--l1d-assoc={a1}", f"--l2-size={l2}KiB", f"--l2-assoc={a2}"]

def run_gem5(binary, outdir, label, max_insts):
    outdir.parent.mkdir(parents=True, exist_ok=True)
    cmd = [GEM5, f"--outdir={outdir}", "configs/x86_cache_v2.py", f"--binary={binary}",
           "--cpu-type=o3", "--bp-type=tournament", "--l1d-mshrs=16"] + flags(label)
    if max_insts:
        cmd.append(f"--max-insts={max_insts}")
    print("  $", " ".join(cmd[:3]), "...", label)
    with open(str(outdir) + ".log", "w") as log:
        r = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
    if r.returncode != 0 or not (outdir / "stats.txt").exists():
        sys.exit(f"gem5 failed; see {outdir}.log")

def sim_ticks(outdir):
    for line in (outdir / "stats.txt").read_text().splitlines():
        if line.startswith("simTicks"):
            return float(line.split()[1])

ap = argparse.ArgumentParser()
ap.add_argument("target", nargs="?")
ap.add_argument("--features", nargs=2, type=float, metavar=("L2_MPKI", "BRANCH_MPKI"))
ap.add_argument("--max-insts", type=int, default=0)
ap.add_argument("--verify", action="store_true")
ap.add_argument("--cflags", default="")
ap.add_argument("--name", default="", help="label for this run (default: file name)")
a = ap.parse_args()

if a.features:
    cls = classify(*a.features)
    cfg, kib = recommendation(cls)
    print(f"class: {cls}\nrecommended: {cfg} ({kib} KiB total L1D+L2)")
    sys.exit(0)
if not a.target:
    ap.error("give a .c file, a binary, or --features")

target = Path(a.target)
name = a.name or re.sub(r"(_x86)?(\.c)?$", "", target.name)
if target.suffix == ".c":
    binary = Path("results/demo/bin") / f"{name}_x86"
    binary.parent.mkdir(parents=True, exist_ok=True)
    print(f"compiling {target} -> {binary}")
    subprocess.run(["gcc", "-O2", "-static", *a.cflags.split(), str(target), "-o", str(binary), "-lm"], check=True)
else:
    binary = target

base_root = Path("results/demo/baseline")
print("baseline run (48KiB/12w L1D + 1280KiB/10w L2):")
run_gem5(binary, base_root / name, BASE_LABEL, a.max_insts)
subprocess.run([sys.executable, "scripts/extract_features_v2.py", str(base_root), "results/demo/features.csv"],
               check=True, stdout=subprocess.DEVNULL)
f = pd.read_csv("results/demo/features.csv").set_index("workload").loc[name]
cls = classify(f["l2_mpki"], f["branch_mpki"])
cfg, kib = recommendation(cls)

print(f"\nfeatures: IPC {f['ipc']:.3f} | L2 MPKI {f['l2_mpki']:.2f} | branch MPKI {f['branch_mpki']:.2f} | "
      f"L1D MPKI {f['l1d_mpki']:.2f} | mem frac {f['mem_frac']:.3f}")
print(f"class: {cls}   (rule: L2 MPKI > {L2_MPKI_MEM:g} -> memory; branch MPKI > {BR_MPKI_BRANCH:g} -> branch; else compute)")
print(f"recommended: {cfg}  ({kib} KiB total L1D+L2; baseline is 1328 KiB)")
if f["l1d_mpki"] > 50 and f["l2_miss_rate"] < 0.05:
    print("CAUTION (post-hoc heuristic, not validated): high L1D MPKI with a low L2 miss rate suggests a working set "
          "held in L2. Class-level recommendations can under-size L2 for such workloads (see hashchain).")
if a.max_insts:
    print(f"note: run capped at {a.max_insts:,} instructions, so features describe the first part of the program only.")

if a.verify:
    print("\nverification run with the recommended configuration:")
    run_gem5(binary, Path("results/demo/recommended") / name, cfg, a.max_insts)
    sp = sim_ticks(base_root / name) / sim_ticks(Path("results/demo/recommended") / name)
    print(f"speedup vs baseline: {sp:.4f}  ->  {'PASS' if sp >= PASS else 'FAIL'} (threshold {PASS})")

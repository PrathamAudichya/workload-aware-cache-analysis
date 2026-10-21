#!/usr/bin/env python3
"""Extract workload features from gem5 O3 stats.txt files."""
import re
import sys
from pathlib import Path
import pandas as pd

RUN_DIR = Path(sys.argv[1] if len(sys.argv) > 1 else "results/o3_baseline")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "data/o3_features.csv")
STAT = re.compile(r"^(\S+)\s+([-+0-9.eE]+|nan|inf)\b")

def read_stats(path):
    d = {}
    for line in path.read_text().splitlines():
        m = STAT.match(line)
        if m and m.group(1) not in d:
            try:
                d[m.group(1)] = float(m.group(2))
            except ValueError:
                pass
    return d

def need(s, key, path):
    if key not in s:
        raise KeyError(f"{key} missing in {path}")
    return s[key]

rows = []
for stats_path in sorted(RUN_DIR.glob("*/stats.txt")):
    name = stats_path.parent.name
    s = read_stats(stats_path)
    insts = need(s, "simInsts", stats_path)
    kilo = insts / 1000.0

    # instruction mix from committed instruction classes (micro-op level)
    pre = "system.cpu.commit.committedInstType_0::"
    types = {k[len(pre):]: v for k, v in s.items() if k.startswith(pre)}
    total = types.get("total") or sum(v for k, v in types.items() if k != "total")
    fp = sum(v for k, v in types.items()
             if (k.startswith("Float") and "Mem" not in k) or k.startswith("Simd"))
    mem = sum(v for k, v in types.items() if "Mem" in k)
    intg = sum(v for k, v in types.items() if k.startswith("Int"))

    br_total = need(s, "system.cpu.branchPred.committed_0::total", stats_path)
    br_miss = need(s, "system.cpu.branchPred.mispredicted_0::total", stats_path)
    l1_miss = need(s, "system.l1d.demandMisses::total", stats_path)
    l1_acc = need(s, "system.l1d.demandAccesses::total", stats_path)
    l2_miss = s.get("system.l2.demandMisses::total", 0.0)
    l2_acc = s.get("system.l2.demandAccesses::total", 0.0)

    rows.append({
        "workload": name,
        "insts": int(insts),
        "ipc": s["system.cpu.ipc"],
        "int_frac": intg / total,
        "fp_frac": fp / total,
        "mem_frac": mem / total,
        "branch_frac": br_total / insts,
        "branch_mpki": br_miss / kilo,
        "mispredict_rate": br_miss / br_total if br_total else 0.0,
        "l1d_mpki": l1_miss / kilo,
        "l1d_miss_rate": l1_miss / l1_acc if l1_acc else 0.0,
        "l2_mpki": l2_miss / kilo,
        "l2_miss_rate": l2_miss / l2_acc if l2_acc else 0.0,
    })

df = pd.DataFrame(rows)
labels = Path("data/intended_classes.csv")
if labels.exists():
    df = df.merge(pd.read_csv(labels), on="workload", how="left")
df.to_csv(OUT, index=False)
pd.set_option("display.width", 200)
print(df.round(3).to_string(index=False))
print(f"\nWrote {OUT} ({len(df)} workloads)")

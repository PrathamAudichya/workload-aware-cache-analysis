#!/usr/bin/env python3
"""Analyze the O3 cache sweep: per-class speedup vs baseline and cost-aware recommendation."""
import re
import sys
from pathlib import Path
import numpy as np
import pandas as pd

SWEEP = Path("results/o3_sweep")
BASE_LABEL = "l1d48k12_l2k1280k10"
TOL = 0.02   # accept configs within 2% of the best class speedup
STAT = re.compile(r"^(\S+)\s+([-+0-9.eE]+)\b")
LABEL = re.compile(r"l1d(\d+)k(\d+)_l2k(\d+)k(\d+)")

def first_stats(path, keys):
    out = {}
    for line in path.read_text().splitlines():
        m = STAT.match(line)
        if m and m.group(1) in keys and m.group(1) not in out:
            out[m.group(1)] = float(m.group(2))
        if len(out) == len(keys):
            break
    return out

rows = []
for cfg_dir in sorted(SWEEP.iterdir()):
    m = LABEL.fullmatch(cfg_dir.name)
    if not m:
        continue
    l1, l1a, l2, l2a = map(int, m.groups())
    for wdir in sorted(p for p in cfg_dir.iterdir() if p.is_dir()):
        log = cfg_dir / f"{wdir.name}.log"
        stats = wdir / "stats.txt"
        if not stats.exists() or not log.exists() or "Exit cause" not in log.read_text():
            continue   # run not finished
        s = first_stats(stats, {"simTicks", "simInsts", "system.cpu.ipc"})
        if len(s) < 3:
            continue
        rows.append({"config": cfg_dir.name, "l1d_kib": l1, "l1d_assoc": l1a,
                     "l2_kib": l2, "l2_assoc": l2a, "total_kib": l1 + l2,
                     "workload": wdir.name, "sim_ticks": s["simTicks"],
                     "insts": s["simInsts"], "ipc": s["system.cpu.ipc"]})

df = pd.DataFrame(rows)
if df.empty:
    sys.exit("No finished runs found.")
cls = pd.read_csv("data/o3_classification.csv")[["workload", "rule_class"]]
n_work = cls["workload"].nunique()

# keep only configs that finished for every workload
counts = df.groupby("config")["workload"].nunique()
complete = counts[counts == n_work].index
skipped = sorted(set(counts.index) - set(complete))
if skipped:
    print("Skipping incomplete configs:", ", ".join(f"{c} ({counts[c]}/{n_work})" for c in skipped))
df = df[df["config"].isin(complete)].merge(cls, on="workload")
if BASE_LABEL not in set(df["config"]):
    sys.exit("Baseline config results missing.")

base = df[df["config"] == BASE_LABEL].set_index("workload")["sim_ticks"]
df["speedup_vs_base"] = df.apply(lambda r: base[r["workload"]] / r["sim_ticks"], axis=1)
df.to_csv("data/sweep_results.csv", index=False)

# per class, per config: geometric-mean speedup
g = (df.groupby(["rule_class", "config", "l1d_kib", "l2_kib", "total_kib"])["speedup_vs_base"]
       .apply(lambda x: float(np.exp(np.log(x).mean()))).reset_index(name="geomean_speedup"))
pd.set_option("display.width", 200)
for c, sub in g.groupby("rule_class"):
    print(f"\n== {c} (geomean speedup vs baseline {BASE_LABEL}) ==")
    print(sub.sort_values("total_kib")[["config", "total_kib", "geomean_speedup"]]
          .round(4).to_string(index=False))

recs = []
for c, sub in g.groupby("rule_class"):
    best = sub.loc[sub["geomean_speedup"].idxmax()]
    ok = sub[sub["geomean_speedup"] >= best["geomean_speedup"] * (1 - TOL)]
    pick = ok.sort_values(["total_kib", "geomean_speedup"], ascending=[True, False]).iloc[0]
    recs.append({"class": c, "best_config": best["config"], "best_speedup": best["geomean_speedup"],
                 "recommended_config": pick["config"], "rec_total_kib": pick["total_kib"],
                 "rec_speedup": pick["geomean_speedup"],
                 "capacity_saved_vs_best_kib": best["total_kib"] - pick["total_kib"]})
rec = pd.DataFrame(recs)
rec.to_csv("data/class_recommendations.csv", index=False)
print(f"\n== Recommendation: smallest total (L1D+L2) within {TOL:.0%} of best ==")
print(rec.round(4).to_string(index=False))

# per-workload sensitivity: spread of runtime across configs
sens = (df.groupby("workload")["sim_ticks"].agg(lambda x: x.max() / x.min() - 1)
          .reset_index(name="max_slowdown_vs_fastest"))
print("\n== Cache sensitivity per workload (slowest/fastest - 1) ==")
print(sens.sort_values("max_slowdown_vs_fastest", ascending=False).round(4).to_string(index=False))

# ---- worst-case view: protect the most cache-sensitive workload in each class ----
SAFE = 0.95   # every workload in the class must keep >= 95% of baseline performance
worst = (df.groupby(["rule_class", "config", "total_kib"])["speedup_vs_base"]
           .min().reset_index(name="worst_speedup"))
print(f"\n== Worst-case speedup per class/config (min over workloads) ==")
for c, sub in worst.groupby("rule_class"):
    print(f"\n[{c}]")
    print(sub.sort_values("total_kib")[["config", "total_kib", "worst_speedup"]]
          .round(4).to_string(index=False))
safe = []
for c, sub in worst.groupby("rule_class"):
    ok = sub[sub["worst_speedup"] >= SAFE]
    pick = ok.sort_values(["total_kib", "worst_speedup"], ascending=[True, False]).iloc[0]
    limiter = (df[(df["config"] == pick["config"]) & (df["rule_class"] == c)]
               .sort_values("speedup_vs_base").iloc[0]["workload"])
    safe.append({"class": c, "safe_config": pick["config"], "total_kib": pick["total_kib"],
                 "worst_speedup": pick["worst_speedup"], "limiting_workload": limiter})
safe = pd.DataFrame(safe)
safe.to_csv("data/class_recommendations_safe.csv", index=False)
print(f"\n== Safe recommendation: smallest config where every class member keeps >= {SAFE:.0%} ==")
print(safe.round(4).to_string(index=False))

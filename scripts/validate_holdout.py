#!/usr/bin/env python3
"""Validate the classify->recommend mechanism on held-out workloads (gem5 results)."""
import re
import subprocess
import sys
from pathlib import Path
import pandas as pd

ROOT = Path("results/holdout_sweep")
BASE = "l1d48k12_l2k1280k10"
PASS_SPEEDUP = 0.95
L2_MPKI_MEM, BR_MPKI_BRANCH = 5.0, 5.0          # same thresholds as classify_v2.py
INTENDED = {"mandel": "compute", "gather": "memory", "bsearch": "branch", "hashchain": "branch"}
STAT = re.compile(r"^(\S+)\s+([-+0-9.eE]+)\b")
LABEL = re.compile(r"l1d(\d+)k(\d+)_l2k(\d+)k(\d+)")

def rule(r):
    if r["l2_mpki"] > L2_MPKI_MEM:
        return "memory"
    return "branch" if r["branch_mpki"] > BR_MPKI_BRANCH else "compute"

def ticks(path):
    for line in path.read_text().splitlines():
        m = STAT.match(line)
        if m and m.group(1) == "simTicks":
            return float(m.group(2))
    return None

feat_path = Path("data/holdout_features.csv")
if "--skip-extract" not in sys.argv:
    subprocess.run([sys.executable, "scripts/extract_features_v2.py",
                    str(ROOT / BASE), str(feat_path)], check=True)
feat = pd.read_csv(feat_path)
feat["predicted_class"] = feat.apply(rule, axis=1)
feat["intended_class"] = feat["workload"].map(INTENDED)

recs = pd.read_csv("data/class_recommendations_safe.csv").set_index("class")

res = []
for cfg_dir in sorted(ROOT.iterdir()):
    if not LABEL.fullmatch(cfg_dir.name):
        continue
    for wdir in cfg_dir.iterdir():
        log = cfg_dir / f"{wdir.name}.log"
        if wdir.is_dir() and (wdir / "stats.txt").exists() and log.exists() \
           and "Exit cause" in log.read_text():
            t = ticks(wdir / "stats.txt")
            if t:
                l1, _, l2, _ = map(int, LABEL.fullmatch(cfg_dir.name).groups())
                res.append({"workload": wdir.name, "config": cfg_dir.name,
                            "ticks": t, "total_kib": l1 + l2})
runs = pd.DataFrame(res)
base = runs[runs["config"] == BASE].set_index("workload")["ticks"]
runs["speedup"] = runs.apply(lambda r: base[r["workload"]] / r["ticks"], axis=1)
runs.to_csv("data/holdout_sweep_results.csv", index=False)

rows = []
for _, f in feat.iterrows():
    w, cls = f["workload"], f["predicted_class"]
    cfg = recs.loc[cls, "safe_config"]
    sub = runs[runs["workload"] == w]
    chosen = sub[sub["config"] == cfg]
    if chosen.empty:
        rows.append({"workload": w, "note": f"missing run for {cfg}"}); continue
    c = chosen.iloc[0]
    ok = sub[sub["speedup"] >= PASS_SPEEDUP].sort_values(["total_kib", "ticks"])
    oracle = ok.iloc[0] if len(ok) else None
    rows.append({
        "workload": w, "intended": f["intended_class"], "predicted": cls,
        "class_correct": cls == f["intended_class"],
        "l2_mpki": round(f["l2_mpki"], 2), "branch_mpki": round(f["branch_mpki"], 2),
        "chosen_config": cfg, "chosen_kib": int(c["total_kib"]),
        "speedup_vs_base": round(c["speedup"], 4),
        "capacity_saved_kib": int(sub[sub["config"] == BASE].iloc[0]["total_kib"] - c["total_kib"]),
        "passes": bool(c["speedup"] >= PASS_SPEEDUP),
        "oracle_config": oracle["config"] if oracle is not None else "-",
        "oracle_kib": int(oracle["total_kib"]) if oracle is not None else -1,
    })
out = pd.DataFrame(rows)
out.to_csv("data/holdout_validation.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(out.to_string(index=False))
if "passes" in out:
    print(f"\nClassification correct: {int(out['class_correct'].sum())}/{len(out)}")
    print(f"Chosen config keeps >= {PASS_SPEEDUP:.0%} of baseline: {int(out['passes'].sum())}/{len(out)}")

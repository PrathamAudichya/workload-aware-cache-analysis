#!/usr/bin/env python3
"""Figure for the main result: speedup vs cache capacity for the 12 training workloads."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("data/sweep_results.csv")
out = Path("plots"); out.mkdir(exist_ok=True)
fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=True)
for ax, cls in zip(axes, ["compute", "branch", "memory"]):
    s = df[df["rule_class"] == cls]
    for w, g in s.groupby("workload"):
        g = g.sort_values("total_kib")
        ax.plot(g["total_kib"], g["speedup_vs_base"], "o-", alpha=0.75, label=w)
    ax.axhline(0.95, color="gray", ls="--", lw=1)
    ax.set_xscale("log"); ax.set_title(f"{cls}-intensive")
    ax.set_xlabel("L1D + L2 capacity (KiB)"); ax.legend(fontsize=8)
axes[0].set_ylabel("speedup vs baseline (1328 KiB)")
fig.suptitle("Training sweep: per-workload speedup vs cache capacity (dashed = 95%)")
fig.tight_layout()
fig.savefig(out / "training_speedup_vs_capacity.png", dpi=150)
print("Saved", out / "training_speedup_vs_capacity.png")

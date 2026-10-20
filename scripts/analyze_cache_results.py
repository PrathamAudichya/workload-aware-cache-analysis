import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data/combined_cache_dataset.csv"
SUMMARY_FILE = ROOT / "data/best_worst_configurations.csv"
REPORT_FILE = ROOT / "reports/cache_analysis_report.md"

df = pd.read_csv(DATA_FILE)

required = {
    "workload", "l1d_size", "l1d_assoc",
    "ipc", "sim_ticks", "cpu_cycles", "l1d_demand_misses"
}
missing = required - set(df.columns)

if missing:
    raise ValueError(f"Missing required columns: {sorted(missing)}")

if df[list(required)].isnull().any().any():
    raise ValueError("Missing values detected in analysis columns.")

results = []

for workload, group in df.groupby("workload"):
    fastest = group.loc[group["sim_ticks"].idxmin()]
    slowest = group.loc[group["sim_ticks"].idxmax()]

    ticks_improvement = (
        (slowest["sim_ticks"] - fastest["sim_ticks"])
        / slowest["sim_ticks"] * 100
    )

    ipc_improvement = (
        (fastest["ipc"] - slowest["ipc"])
        / slowest["ipc"] * 100
    )

    results.append({
        "workload": workload,
        "configurations_tested": len(group),
        "fastest_l1d_size": fastest["l1d_size"],
        "fastest_l1d_assoc": int(fastest["l1d_assoc"]),
        "fastest_ipc": fastest["ipc"],
        "fastest_sim_ticks": fastest["sim_ticks"],
        "fastest_cpu_cycles": fastest["cpu_cycles"],
        "fastest_l1d_misses": int(fastest["l1d_demand_misses"]),
        "slowest_l1d_size": slowest["l1d_size"],
        "slowest_l1d_assoc": int(slowest["l1d_assoc"]),
        "slowest_ipc": slowest["ipc"],
        "slowest_sim_ticks": slowest["sim_ticks"],
        "slowest_cpu_cycles": slowest["cpu_cycles"],
        "slowest_l1d_misses": int(slowest["l1d_demand_misses"]),
        "ticks_improvement_percent": ticks_improvement,
        "ipc_improvement_percent": ipc_improvement,
    })

summary = pd.DataFrame(results)
summary.to_csv(SUMMARY_FILE, index=False)

REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

lines = [
    "# L1 Data Cache Configuration Analysis",
    "",
    "## Experimental scope",
    "",
    f"- Total configurations: {len(df)}",
    f"- Workloads: {df['workload'].nunique()}",
    "- Cache sizes: 16 KiB, 32 KiB, 64 KiB, and 128 KiB.",
    "- Associativities: 4-way, 8-way, and 16-way.",
    "- Primary ranking metric: simulation ticks; lower is better.",
    "- Secondary metric: IPC; higher is better.",
    "",
    "## Results",
    "",
    "| Workload | Fastest configuration | IPC | Slowest configuration | Tick improvement |",
    "|---|---|---:|---|---:|",
]

for _, row in summary.iterrows():
    best_config = (
        f"{row['fastest_l1d_size']}, "
        f"{row['fastest_l1d_assoc']}-way"
    )
    worst_config = (
        f"{row['slowest_l1d_size']}, "
        f"{row['slowest_l1d_assoc']}-way"
    )

    lines.append(
        f"| {row['workload']} | {best_config} | "
        f"{row['fastest_ipc']:.6f} | {worst_config} | "
        f"{row['ticks_improvement_percent']:.3f}% |"
    )

lines.extend([
    "",
    "## Interpretation",
    "",
    "The best tested cache configuration depends on the workload. "
    "The branch-intensive and matrix-multiplication workloads exhibit "
    "small performance differences across configurations, while the "
    "memory-intensive workload shows a larger difference between its "
    "fastest and slowest configurations.",
    "",
    "Cache-miss count alone does not determine execution performance. "
    "The fastest configuration may record slightly more cache misses "
    "than the slowest configuration.",
    "",
    "## Limitations",
    "",
    "These conclusions apply only to the tested workloads, cache sizes, "
    "associativities, and gem5 configuration. Small differences should "
    "not be treated as statistically significant without repeated runs "
    "and variability analysis. The results do not establish the optimal "
    "configuration for real processors.",
    "",
])

REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")

print(summary.to_string(index=False))
print(f"\nCSV saved: {SUMMARY_FILE}")
print(f"Report saved: {REPORT_FILE}")

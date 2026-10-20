import pandas as pd
from pathlib import Path

from validate_dataset import validate_dataset

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data/combined_cache_dataset.csv"
CLASSIFICATIONS = ROOT / "data/workload_classification.csv"
OUTPUT = ROOT / "results/processed/cache_recommendations.csv"

BASELINE_SIZE = "32KiB"
BASELINE_ASSOC = 8

WORKLOADS = {
    "matrix_mul_256",
    "memory_intensive_32MiB",
    "branch_intensive_1M",
}


def calculate_mpki(misses, instructions):
    if instructions <= 0:
        raise ValueError("Instruction count must be positive.")
    return 1000.0 * misses / instructions


def main():
    df = validate_dataset(DATASET)

    required = {
        "workload",
        "l1d_size",
        "l1d_assoc",
        "sim_ticks",
        "instructions",
        "ipc",
        "l1d_demand_misses",
        "l1d_miss_rate",
    }

    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing dataset columns: {sorted(missing)}"
        )

    if df[list(required)].isnull().any().any():
        raise ValueError("Required columns contain missing values.")

    if not CLASSIFICATIONS.exists():
        raise FileNotFoundError(
            f"{CLASSIFICATIONS} not found. "
            "Run scripts/classify_workloads.py first."
        )

    classifications = pd.read_csv(CLASSIFICATIONS)

    class_required = {
        "workload",
        "workload_class",
        "classification_reason",
    }
    class_missing = class_required - set(classifications.columns)

    if class_missing:
        raise ValueError(
            f"Classification file is missing columns: "
            f"{sorted(class_missing)}"
        )

    if classifications["workload"].duplicated().any():
        raise ValueError(
            "Classification file must contain one row per workload."
        )

    if set(classifications["workload"]) != WORKLOADS:
        raise ValueError(
            "Classification file does not contain exactly the "
            "three expected benchmark workloads."
        )

    class_lookup = classifications.set_index("workload")

    if set(df["workload"]) != WORKLOADS:
        raise ValueError(
            "Combined dataset does not contain exactly the "
            "three expected benchmark workloads."
        )

    output_rows = []

    for workload, group in df.groupby("workload"):
        # Preserve the existing selection metric.
        best = group.loc[group["sim_ticks"].idxmin()]

        baseline_rows = group[
            (group["l1d_size"] == BASELINE_SIZE)
            & (group["l1d_assoc"] == BASELINE_ASSOC)
        ]

        if len(baseline_rows) != 1:
            raise ValueError(
                f"{workload}: expected exactly one "
                f"{BASELINE_SIZE}, {BASELINE_ASSOC}-way baseline; "
                f"found {len(baseline_rows)}."
            )

        baseline = baseline_rows.iloc[0]

        if baseline["sim_ticks"] <= 0 or baseline["ipc"] <= 0:
            raise ValueError(f"{workload}: invalid baseline metrics.")

        tick_change_pct = (
            (best["sim_ticks"] - baseline["sim_ticks"])
            / baseline["sim_ticks"]
            * 100
        )

        ipc_change_pct = (
            (best["ipc"] - baseline["ipc"])
            / baseline["ipc"]
            * 100
        )

        label = class_lookup.loc[workload]

        output_rows.append({
            "workload": workload,
            "workload_class": label["workload_class"],
            "classification_reason": label["classification_reason"],
            "selection_metric": "minimum_simTicks",
            "recommended_l1d_size": best["l1d_size"],
            "recommended_l1d_assoc": int(best["l1d_assoc"]),
            "recommended_sim_ticks": int(best["sim_ticks"]),
            "recommended_instructions": int(best["instructions"]),
            "recommended_ipc": float(best["ipc"]),
            "recommended_l1d_misses": int(best["l1d_demand_misses"]),
            "recommended_l1d_miss_rate": float(best["l1d_miss_rate"]),
            "recommended_l1d_mpki": calculate_mpki(
                best["l1d_demand_misses"],
                best["instructions"],
            ),
            "baseline_l1d_size": BASELINE_SIZE,
            "baseline_l1d_assoc": BASELINE_ASSOC,
            "baseline_sim_ticks": int(baseline["sim_ticks"]),
            "baseline_ipc": float(baseline["ipc"]),
            "baseline_l1d_misses": int(baseline["l1d_demand_misses"]),
            "baseline_l1d_miss_rate": float(baseline["l1d_miss_rate"]),
            "baseline_l1d_mpki": calculate_mpki(
                baseline["l1d_demand_misses"],
                baseline["instructions"],
            ),
            "sim_ticks_change_percent": float(tick_change_pct),
            "ipc_change_percent": float(ipc_change_pct),
            "sim_ticks_reduction_percent": float(-tick_change_pct),
            "interpretation": (
                "Fewer simulated ticks than baseline"
                if tick_change_pct < 0
                else "Same simulated ticks as baseline"
                if tick_change_pct == 0
                else "More simulated ticks than baseline"
            ),
        })

    recommendations = pd.DataFrame(output_rows).sort_values("workload")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    recommendations.to_csv(OUTPUT, index=False)

    print("\nWORKLOAD-AWARE CACHE RECOMMENDATIONS")
    print("=" * 76)

    for _, row in recommendations.iterrows():
        print(f"\nWorkload: {row['workload']}")
        print(f"Category: {row['workload_class']}")
        print(f"Classification basis: {row['classification_reason']}")
        print(
            "Recommended L1D: "
            f"{row['recommended_l1d_size']}, "
            f"{row['recommended_l1d_assoc']}-way"
        )
        print(f"Selection metric: {row['selection_metric']}")
        print(f"Simulated ticks: {row['recommended_sim_ticks']:,}")
        print(f"IPC: {row['recommended_ipc']:.6f}")
        print(f"L1D MPKI: {row['recommended_l1d_mpki']:.4f}")
        print(
            "Simulated ticks change vs baseline: "
            f"{row['sim_ticks_change_percent']:+.6f}%"
        )
        print(
            "IPC change vs baseline: "
            f"{row['ipc_change_percent']:+.6f}%"
        )

    print(f"\nSaved recommendations: {OUTPUT.relative_to(ROOT)}")
    print(
        "\nNote: simulated ticks are simulation metrics, not measured "
        "wall-clock execution time. Workload categories are benchmark-defined."
    )


if __name__ == "__main__":
    main()

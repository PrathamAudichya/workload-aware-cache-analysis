import pandas as pd
from pathlib import Path

from validate_dataset import validate_dataset

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data/combined_cache_dataset.csv"
OUTPUT = ROOT / "results/processed/cache_recommendations.csv"

BASELINE_SIZE = "32KiB"
BASELINE_ASSOC = 8


def main():
    df = validate_dataset(DATASET)

    required = {
        "workload",
        "l1d_size",
        "l1d_assoc",
        "sim_ticks",
        "ipc",
        "l1d_demand_misses",
        "l1d_miss_rate",
    }

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing dataset columns: {sorted(missing)}")

    if df[list(required)].isnull().any().any():
        raise ValueError("Required columns contain missing values.")

    output_rows = []

    for workload, group in df.groupby("workload"):
        # Choose the configuration with the lowest measured simTicks.
        best = group.loc[group["sim_ticks"].idxmin()]

        baseline_rows = group[
            (group["l1d_size"] == BASELINE_SIZE)
            & (group["l1d_assoc"] == BASELINE_ASSOC)
        ]

        if baseline_rows.empty:
            print(f"WARNING: baseline missing for {workload}")
            baseline = None
            tick_change_pct = None
            ipc_change_pct = None
        else:
            baseline = baseline_rows.iloc[0]

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

        output_rows.append({
            "workload": workload,
            "selection_metric": "minimum_simTicks",
            "recommended_l1d_size": best["l1d_size"],
            "recommended_l1d_assoc": int(best["l1d_assoc"]),
            "recommended_sim_ticks": int(best["sim_ticks"]),
            "recommended_ipc": best["ipc"],
            "recommended_l1d_misses": int(
                best["l1d_demand_misses"]
            ),
            "recommended_l1d_miss_rate": best["l1d_miss_rate"],
            "baseline_l1d_size": BASELINE_SIZE,
            "baseline_l1d_assoc": BASELINE_ASSOC,
            "baseline_sim_ticks": (
                int(baseline["sim_ticks"])
                if baseline is not None else None
            ),
            "sim_ticks_change_percent": tick_change_pct,
            "ipc_change_percent": ipc_change_pct,
        })

    recommendations = pd.DataFrame(output_rows)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    recommendations.to_csv(OUTPUT, index=False)

    print("\nCACHE RECOMMENDATIONS")
    print("=" * 72)

    for row in output_rows:
        print(f"\nWorkload: {row['workload']}")
        print(
            "Recommended L1D: "
            f"{row['recommended_l1d_size']}, "
            f"{row['recommended_l1d_assoc']}-way"
        )
        print(f"Selection metric: {row['selection_metric']}")
        print(f"IPC: {row['recommended_ipc']:.6f}")
        print(
            "L1D demand misses: "
            f"{row['recommended_l1d_misses']:,}"
        )

        if row["sim_ticks_change_percent"] is not None:
            print(
                "Simulated ticks vs baseline: "
                f"{row['sim_ticks_change_percent']:+.3f}%"
            )
            print(
                "IPC change vs baseline: "
                f"{row['ipc_change_percent']:+.3f}%"
            )

    print(f"\nSaved recommendations: {OUTPUT}")


if __name__ == "__main__":
    main()

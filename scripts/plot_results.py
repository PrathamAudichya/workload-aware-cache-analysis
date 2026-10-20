import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data/combined_cache_dataset.csv"
PLOT_DIR = ROOT / "plots"

def main():
    if not DATASET.is_file():
        raise FileNotFoundError(f"Dataset not found: {DATASET}")

    df = pd.read_csv(DATASET)
    PLOT_DIR.mkdir(parents=True, exist_ok=True)

    df["configuration"] = (
        df["l1d_size"].astype(str)
        + ", "
        + df["l1d_assoc"].astype(str)
        + "-way"
    )

    metrics = [
        ("ipc", "IPC", "ipc_by_configuration.png"),
        ("sim_ticks", "Simulated ticks", "ticks_by_configuration.png"),
        (
            "l1d_demand_misses",
            "L1D demand misses",
            "l1d_misses_by_configuration.png",
        ),
    ]

    for workload, group in df.groupby("workload"):
        group = group.sort_values(
            ["l1d_size", "l1d_assoc"],
            key=lambda col: (
                col.map({
                    "16KiB": 16,
                    "32KiB": 32,
                    "64KiB": 64,
                    "128KiB": 128,
                })
                if col.name == "l1d_size"
                else col
            ),
        )

        safe_name = workload.replace("/", "_").replace(" ", "_")

        for metric, ylabel, filename in metrics:
            fig, ax = plt.subplots()
            ax.plot(
                group["configuration"],
                group[metric],
                marker="o",
            )
            ax.set_xlabel("L1 Data Cache Configuration")
            ax.set_ylabel(ylabel)
            ax.set_title(f"{workload}: {ylabel}")
            ax.tick_params(axis="x", rotation=45)
            fig.tight_layout()

            output = PLOT_DIR / f"{safe_name}_{filename}"
            fig.savefig(output, dpi=160)
            plt.close(fig)
            print(f"Saved: {output}")

    print("\nVisualization complete.")

if __name__ == "__main__":
    main()

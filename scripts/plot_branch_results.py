import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data/branch_cache_sweep.csv"
PLOT_DIR = ROOT / "plots/branch_cache"

SIZE_ORDER = ["16KiB", "32KiB", "64KiB", "128KiB"]
ASSOC_ORDER = [4, 8, 16]


def main():
    if not CSV_PATH.is_file():
        raise FileNotFoundError(f"Dataset not found: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    PLOT_DIR.mkdir(parents=True, exist_ok=True)

    df["l1d_size"] = pd.Categorical(
        df["l1d_size"],
        categories=SIZE_ORDER,
        ordered=True,
    )

    df = df.sort_values(["l1d_size", "l1d_assoc"])

    # Plot 1: IPC by cache size and associativity.
    fig, ax = plt.subplots()

    for assoc in ASSOC_ORDER:
        subset = df[df["l1d_assoc"] == assoc]
        ax.plot(
            subset["l1d_size"].astype(str),
            subset["ipc"],
            marker="o",
            label=f"{assoc}-way",
        )

    ax.set_xlabel("L1 Data Cache Size")
    ax.set_ylabel("Instructions Per Cycle (IPC)")
    ax.set_title("Branch Workload: L1D Size vs IPC")
    ax.legend(title="Associativity")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "ipc_by_l1d_size.png", dpi=180)
    plt.close(fig)

    # Plot 2: L1D demand misses.
    fig, ax = plt.subplots()

    for assoc in ASSOC_ORDER:
        subset = df[df["l1d_assoc"] == assoc]
        ax.plot(
            subset["l1d_size"].astype(str),
            subset["l1d_demand_misses"],
            marker="o",
            label=f"{assoc}-way",
        )

    ax.set_xlabel("L1 Data Cache Size")
    ax.set_ylabel("L1D Demand Misses")
    ax.set_title("Branch Workload: L1D Size vs Demand Misses")
    ax.legend(title="Associativity")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "l1d_misses_by_size.png", dpi=180)
    plt.close(fig)

    # Plot 3: CPU cycles by associativity.
    fig, ax = plt.subplots()

    for size in SIZE_ORDER:
        subset = df[df["l1d_size"] == size]
        subset = subset.sort_values("l1d_assoc")

        ax.plot(
            subset["l1d_assoc"],
            subset["cpu_cycles"],
            marker="o",
            label=size,
        )

    ax.set_xlabel("L1 Data Cache Associativity (ways)")
    ax.set_ylabel("CPU Cycles")
    ax.set_title("Branch Workload: Associativity vs CPU Cycles")
    ax.legend(title="L1D Size")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "cpu_cycles_by_associativity.png", dpi=180)
    plt.close(fig)

    # Summary table, grouped by cache size.
    summary = (
        df.groupby("l1d_size", observed=True)
        .agg(
            mean_ipc=("ipc", "mean"),
            mean_cpu_cycles=("cpu_cycles", "mean"),
            mean_l1d_misses=("l1d_demand_misses", "mean"),
            mean_l1d_miss_rate=("l1d_miss_rate", "mean"),
        )
        .reindex(SIZE_ORDER)
    )

    summary.to_csv(PLOT_DIR / "branch_cache_summary.csv")

    print("Branch workload visualizations generated:")
    for path in sorted(PLOT_DIR.iterdir()):
        print(path)


if __name__ == "__main__":
    main()

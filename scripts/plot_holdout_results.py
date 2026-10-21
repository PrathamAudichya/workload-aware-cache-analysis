#!/usr/bin/env python3
"""Generate visualizations for X86 held-out cache validation."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PLOTS = ROOT / "plots"

FEATURES = DATA / "holdout_features.csv"
VALIDATION = DATA / "holdout_validation.csv"
SWEEP = DATA / "holdout_sweep_results.csv"

L2_MPKI_THRESHOLD = 5.0
BRANCH_MPKI_THRESHOLD = 5.0
PASS_THRESHOLD = 0.95


def load_data():
    for path in (FEATURES, VALIDATION, SWEEP):
        if not path.is_file():
            raise FileNotFoundError(f"Required input missing: {path}")

    features = pd.read_csv(FEATURES)
    validation = pd.read_csv(VALIDATION)
    sweep = pd.read_csv(SWEEP)

    required_features = {
        "workload", "ipc", "branch_mpki", "l2_mpki", "intended_class"
    }
    required_validation = {
        "workload", "predicted", "class_correct", "passes"
    }
    required_sweep = {
        "workload", "total_kib", "speedup"
    }

    for name, frame, required in (
        ("features", features, required_features),
        ("validation", validation, required_validation),
        ("sweep", sweep, required_sweep),
    ):
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"{name} CSV missing columns: {sorted(missing)}")

    return features, validation, sweep


def plot_ipc_by_class(features):
    """Plot baseline IPC for held-out workloads grouped by intended class."""
    df = features.copy()
    df["intended_class"] = df["intended_class"].str.lower()

    summary = (
        df.groupby("intended_class")["ipc"]
        .agg(["mean", "count"])
        .reset_index()
        .sort_values("intended_class")
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(summary["intended_class"], summary["mean"])

    for bar, row in zip(bars, summary.itertuples(index=False)):
        ax.annotate(
            f"IPC={row.mean:.3f}\nn={row.count}",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            fontsize=9,
        )

    ax.set_title("Held-Out Workload IPC by Intended Class")
    ax.set_xlabel("Intended workload class")
    ax.set_ylabel("Baseline instructions per cycle (IPC)")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()

    output = PLOTS / "holdout_ipc_by_class.png"
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {output}")


def plot_classification_space(features, validation):
    """Show the rule-based decision boundaries and held-out classifications."""
    df = features.merge(
        validation[["workload", "predicted", "class_correct"]],
        on="workload",
        how="left",
        validate="one_to_one",
    )

    fig, ax = plt.subplots(figsize=(9, 6))

    # Draw separate series by intended class.
    for cls, group in df.groupby("intended_class"):
        ax.scatter(
            group["l2_mpki"],
            group["branch_mpki"],
            s=100,
            label=f"Intended: {cls}",
            edgecolors="black",
            linewidths=0.6,
        )

        for row in group.itertuples(index=False):
            ax.annotate(
                row.workload,
                (row.l2_mpki, row.branch_mpki),
                xytext=(6, 5),
                textcoords="offset points",
                fontsize=9,
            )

    ax.axvline(
        L2_MPKI_THRESHOLD,
        linestyle="--",
        linewidth=1.5,
        label=f"Memory threshold: L2 MPKI={L2_MPKI_THRESHOLD:g}",
    )
    ax.axhline(
        BRANCH_MPKI_THRESHOLD,
        linestyle=":",
        linewidth=1.5,
        label=f"Branch threshold: {BRANCH_MPKI_THRESHOLD:g}",
    )

    ax.set_title("Held-Out Workload Classification Feature Space")
    ax.set_xlabel("L2 misses per thousand instructions (L2 MPKI)")
    ax.set_ylabel("Branch misses per thousand instructions (branch MPKI)")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()

    output = PLOTS / "holdout_classification_space.png"
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {output}")


def plot_speedup_vs_capacity(sweep):
    """Show measured speedup at each tested total cache capacity."""
    df = sweep.copy()
    df["total_kib"] = pd.to_numeric(df["total_kib"], errors="raise")
    df["speedup"] = pd.to_numeric(df["speedup"], errors="raise")

    fig, ax = plt.subplots(figsize=(10, 6))

    for workload, group in df.groupby("workload"):
        group = group.sort_values(["total_kib", "speedup"])

        # Scatter points preserve distinct configurations with equal capacity.
        ax.scatter(
            group["total_kib"],
            group["speedup"],
            s=45,
            alpha=0.8,
            label=workload,
        )

    ax.axhline(
        1.0,
        linestyle="--",
        linewidth=1.3,
        label="Baseline performance",
    )
    ax.axhline(
        PASS_THRESHOLD,
        linestyle=":",
        linewidth=1.5,
        label="95% acceptance threshold",
    )

    ax.set_title("Held-Out Performance vs. Total Cache Capacity")
    ax.set_xlabel("Total configured L1D + L2 capacity (KiB)")
    ax.set_ylabel("Speedup relative to baseline (higher is better)")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()

    output = PLOTS / "holdout_speedup_vs_capacity.png"
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {output}")


def main():
    PLOTS.mkdir(parents=True, exist_ok=True)

    features, validation, sweep = load_data()

    plot_ipc_by_class(features)
    plot_classification_space(features, validation)
    plot_speedup_vs_capacity(sweep)

    print("\nVisualization generation completed.")
    print("All figures were generated from the existing CSV datasets.")


if __name__ == "__main__":
    main()

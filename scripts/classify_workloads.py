#!/usr/bin/env python3

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "workload_features.csv"
OUTPUT = ROOT / "data" / "workload_classification.csv"

# Intended workload roles, defined by the benchmark design.
# These labels are not inferred by a trained classifier.
WORKLOAD_CLASSES = {
    "matrix_mul_256": "compute-intensive",
    "memory_intensive_32MiB": "memory-intensive",
    "branch_intensive_1M": "branch-intensive",
}


def main():
    if not INPUT.exists():
        raise FileNotFoundError(
            f"{INPUT} not found. Run scripts/extract_workload_features.py first."
        )

    df = pd.read_csv(INPUT)

    required = {
        "workload",
        "branch_frequency",
        "memory_instruction_fraction",
        "l1d_mpki",
        "l1d_miss_rate",
        "ipc",
    }

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required features: {sorted(missing)}")

    if df["workload"].duplicated().any():
        raise ValueError("Duplicate workload summaries found.")

    observed = set(df["workload"])
    expected = set(WORKLOAD_CLASSES)

    if observed != expected:
        raise ValueError(
            f"Unexpected workload set. Missing={sorted(expected - observed)}, "
            f"extra={sorted(observed - expected)}"
        )

    numeric_columns = sorted(required - {"workload"})
    if not df[numeric_columns].apply(
        lambda col: pd.to_numeric(col, errors="coerce").notna().all()
    ).all():
        raise ValueError("Missing or nonnumeric feature values found.")

    if not df[numeric_columns].map(
        lambda value: pd.notna(value) and abs(value) != float("inf")
    ).all().all():
        raise ValueError("Non-finite feature values found.")

    df["workload_class"] = df["workload"].map(WORKLOAD_CLASSES)

    explanations = {
        "matrix_mul_256": (
            "Benchmark-defined matrix multiplication workload; "
            "measured memory-instruction fraction and L1D MPKI are reported "
            "as characteristics, not proof of compute-bound behavior"
        ),
        "memory_intensive_32MiB": (
            "Benchmark-defined memory-intensive workload; highest observed "
            "median L1D MPKI among these three workloads"
        ),
        "branch_intensive_1M": (
            "Benchmark-defined branch-intensive workload; branch frequency "
            "is measured, but branch misprediction rate is unavailable"
        ),
    }

    df["classification_reason"] = df["workload"].map(explanations)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False)

    print(f"Workloads classified: {len(df)}")
    print(f"Output: {OUTPUT.relative_to(ROOT)}")
    print(
        df[
            [
                "workload",
                "workload_class",
                "l1d_mpki",
                "branch_frequency",
                "memory_instruction_fraction",
                "classification_reason",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()

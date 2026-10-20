from pathlib import Path

import numpy as np
import pandas as pd


EXPECTED_WORKLOADS = {
    "matrix_mul_256",
    "memory_intensive_32MiB",
    "branch_intensive_1M",
}

EXPECTED_SIZES = {"16KiB", "32KiB", "64KiB", "128KiB"}
EXPECTED_ASSOCIATIVITIES = {4, 8, 16}

REQUIRED_COLUMNS = {
    "workload",
    "l1d_size",
    "l1d_assoc",
    "sim_ticks",
    "ipc",
    "cpu_cycles",
    "instructions",
    "l1d_demand_misses",
    "l1d_miss_rate",
}


def validate_dataset(path: Path) -> pd.DataFrame:
    """Load and validate the complete workload-aware cache dataset."""

    if not path.is_file():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Dataset is missing required columns: {sorted(missing)}"
        )

    if df.empty:
        raise ValueError("Dataset is empty.")

    text_columns = ["workload", "l1d_size"]

    for column in text_columns:
        if df[column].isna().any():
            raise ValueError(f"{column} contains missing values.")

        if not df[column].map(
            lambda value: isinstance(value, str) and bool(value.strip())
        ).all():
            raise ValueError(
                f"{column} must contain non-empty text values."
            )

    numeric_columns = [
        "l1d_assoc",
        "sim_ticks",
        "ipc",
        "cpu_cycles",
        "instructions",
        "l1d_demand_misses",
        "l1d_miss_rate",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="raise")

        if df[column].isna().any():
            raise ValueError(f"{column} contains missing values.")

        if not np.isfinite(df[column].to_numpy(dtype=float)).all():
            raise ValueError(f"{column} contains non-finite values.")

    positive_columns = [
        "l1d_assoc",
        "sim_ticks",
        "ipc",
        "cpu_cycles",
        "instructions",
    ]

    for column in positive_columns:
        if (df[column] <= 0).any():
            raise ValueError(
                f"{column} must contain positive values."
            )

    for column in ["l1d_demand_misses"]:
        if (df[column] < 0).any():
            raise ValueError(
                f"{column} cannot contain negative values."
            )

        if not np.equal(
            df[column].to_numpy(),
            np.floor(df[column].to_numpy()),
        ).all():
            raise ValueError(
                f"{column} must contain integer-valued counters."
            )

    if not df["l1d_miss_rate"].between(0, 1).all():
        raise ValueError("l1d_miss_rate must be between 0 and 1.")

    unknown_workloads = set(df["workload"]) - EXPECTED_WORKLOADS
    if unknown_workloads:
        raise ValueError(
            f"Unexpected workloads: {sorted(unknown_workloads)}"
        )

    missing_workloads = EXPECTED_WORKLOADS - set(df["workload"])
    if missing_workloads:
        raise ValueError(
            f"Missing workloads: {sorted(missing_workloads)}"
        )

    if set(df["l1d_size"]) != EXPECTED_SIZES:
        raise ValueError(
            "Unexpected L1D sizes. Expected: "
            f"{sorted(EXPECTED_SIZES)}"
        )

    if not np.equal(
        df["l1d_assoc"].to_numpy(),
        np.floor(df["l1d_assoc"].to_numpy()),
    ).all():
        raise ValueError("l1d_assoc must contain integer values.")

    if set(df["l1d_assoc"].astype(int)) != EXPECTED_ASSOCIATIVITIES:
        raise ValueError(
            "Unexpected L1D associativities. Expected: "
            f"{sorted(EXPECTED_ASSOCIATIVITIES)}"
        )

    key_columns = ["workload", "l1d_size", "l1d_assoc"]

    duplicates = df.duplicated(key_columns, keep=False)
    if duplicates.any():
        raise ValueError(
            "Duplicate workload/configuration combinations:\n"
            + df.loc[duplicates, key_columns].to_string(index=False)
        )

    expected_per_workload = len(EXPECTED_SIZES) * len(
        EXPECTED_ASSOCIATIVITIES
    )

    counts = df.groupby("workload").size()

    if not counts.eq(expected_per_workload).all():
        raise ValueError(
            "Each workload must have exactly "
            f"{expected_per_workload} configurations. "
            f"Found: {counts.to_dict()}"
        )

    expected_grid = {
        (size, assoc)
        for size in EXPECTED_SIZES
        for assoc in EXPECTED_ASSOCIATIVITIES
    }

    for workload, group in df.groupby("workload"):
        actual_grid = set(
            zip(
                group["l1d_size"],
                group["l1d_assoc"].astype(int),
            )
        )

        if actual_grid != expected_grid:
            raise ValueError(
                f"Incomplete or unexpected configuration grid "
                f"for {workload}."
            )

    print(
        f"Dataset validation passed: {len(df)} rows, "
        f"{len(EXPECTED_WORKLOADS)} workloads, "
        f"{expected_per_workload} configurations per workload."
    )

    return df

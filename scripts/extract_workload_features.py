#!/usr/bin/env python3

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "results" / "raw"
OUTPUT_DIR = ROOT / "data"

WORKLOAD_PREFIXES = {
    "matrix_mul_256": "l1d_",
    "memory_intensive_32MiB": "memory_l1d_",
    "branch_intensive_1M": "branch_l1d_",
}

PATTERNS = {
    "instructions": r"^simInsts\s+(\S+)",
    "cycles": r"^system\.cpu\.numCycles\s+(\S+)",
    "ipc": r"^system\.cpu\.ipc\s+(\S+)",
    "branches": r"^system\.cpu\.executeStats0\.numBranches\s+(\S+)",
    "loads": r"^system\.cpu\.commitStats0\.numLoadInsts\s+(\S+)",
    "stores": r"^system\.cpu\.commitStats0\.numStoreInsts\s+(\S+)",
    "l1d_accesses": r"^system\.l1d\.demandAccesses::total\s+(\S+)",
    "l1d_misses": r"^system\.l1d\.demandMisses::total\s+(\S+)",
    "l1d_miss_rate": r"^system\.l1d\.overallMissRate::total\s+(\S+)",
}

CONFIG_PATTERN = re.compile(r"l1d_(\d+)kib_(\d+)way")


def extract_stats(path):
    content = path.read_text(errors="replace")
    values = {}

    for name, pattern in PATTERNS.items():
        match = re.search(pattern, content, re.MULTILINE)
        if not match:
            raise ValueError(f"Missing statistic '{name}' in {path}")
        values[name] = float(match.group(1))

    return values


def main():
    rows = []

    for workload, prefix in WORKLOAD_PREFIXES.items():
        paths = sorted(RAW_DIR.glob(f"{prefix}*/stats.txt"))

        if len(paths) != 12:
            raise ValueError(
                f"{workload}: expected 12 configurations, found {len(paths)}"
            )

        for path in paths:
            config_match = CONFIG_PATTERN.search(path.parent.name)
            if not config_match:
                raise ValueError(f"Cannot parse cache configuration: {path}")

            size_kib = int(config_match.group(1))
            associativity = int(config_match.group(2))
            stats = extract_stats(path)

            instructions = stats["instructions"]
            if instructions <= 0:
                raise ValueError(f"Invalid instruction count in {path}")

            loads = stats["loads"]
            stores = stats["stores"]
            branches = stats["branches"]
            accesses = stats["l1d_accesses"]
            misses = stats["l1d_misses"]

            stats.update({
                "workload": workload,
                "l1d_size_kib": size_kib,
                "l1d_assoc": associativity,
                "l1d_mpki": 1000 * misses / instructions,
                "branch_frequency": branches / instructions,
                "memory_instruction_fraction": (
                    (loads + stores) / instructions
                ),
                "memory_access_intensity": accesses / instructions,
                "source_stats": str(path.relative_to(ROOT)),
            })

            rows.append(stats)

    detail = pd.DataFrame(rows).sort_values(
        ["workload", "l1d_size_kib", "l1d_assoc"]
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    detail_path = OUTPUT_DIR / "workload_features_by_config.csv"
    detail.to_csv(detail_path, index=False)

    feature_columns = [
        "instructions",
        "cycles",
        "ipc",
        "branches",
        "loads",
        "stores",
        "l1d_accesses",
        "l1d_misses",
        "l1d_miss_rate",
        "l1d_mpki",
        "branch_frequency",
        "memory_instruction_fraction",
        "memory_access_intensity",
    ]

    # Use medians across the 12 configurations to avoid selecting one
    # particular cache configuration as the workload's representative.
    summary = (
        detail.groupby("workload")[feature_columns]
        .median()
        .reset_index()
    )

    summary_path = OUTPUT_DIR / "workload_features.csv"
    summary.to_csv(summary_path, index=False)

    print(f"Configurations extracted: {len(detail)}")
    print(f"Workloads summarized: {len(summary)}")
    print(f"Per-configuration features: {detail_path.relative_to(ROOT)}")
    print(f"Workload summary: {summary_path.relative_to(ROOT)}")
    print("\nWorkload feature summary:")
    print(summary.round(6).to_string(index=False))


if __name__ == "__main__":
    main()

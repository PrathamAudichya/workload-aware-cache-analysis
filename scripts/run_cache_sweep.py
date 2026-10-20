import csv
import itertools
import math
import os
import subprocess
import sys
from pathlib import Path


# Project paths
ROOT = Path(__file__).resolve().parents[1]

GEM5 = Path.home() / "projects/gem5/build/X86/gem5.opt"
CONFIG = ROOT / "configs/x86_cache.py"
BINARY = ROOT / "workloads/matrix_mul_x86"

OUTPUT = ROOT / "results/raw"
CSV_PATH = ROOT / "data/cache_sweep.csv"


# Experimental parameters
CACHE_SIZES = ["16KiB", "32KiB", "64KiB", "128KiB"]
ASSOCIATIVITIES = [4, 8, 16]


def read_stats(stats_path):
    """Read numeric statistics from gem5 stats.txt."""
    stats = {}

    for line in stats_path.read_text().splitlines():
        parts = line.split()

        if len(parts) < 2:
            continue

        try:
            stats[parts[0]] = float(parts[1])
        except ValueError:
            continue

    return stats


def main():
    if not GEM5.is_file():
        sys.exit(f"gem5 binary not found: {GEM5}")

    if not CONFIG.is_file():
        sys.exit(f"Configuration file not found: {CONFIG}")

    if not BINARY.is_file():
        sys.exit(f"Workload binary not found: {BINARY}")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    failures = []

    experiments = list(
        itertools.product(CACHE_SIZES, ASSOCIATIVITIES)
    )

    print(f"Total configurations: {len(experiments)}")

    for index, (size, assoc) in enumerate(experiments, start=1):
        label = f"l1d_{size.lower()}_{assoc}way"
        outdir = OUTPUT / label

        print(f"\n[{index}/{len(experiments)}] {label}", flush=True)

        command = [
            str(GEM5),
            f"--outdir={outdir}",
            str(CONFIG),
            f"--binary={BINARY}",
            "--l1i-size=32KiB",
            "--l1i-assoc=8",
            f"--l1d-size={size}",
            f"--l1d-assoc={assoc}",
        ]

        result = subprocess.run(
            command,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "run.log").write_text(result.stdout)

        stats_path = outdir / "stats.txt"

        if result.returncode != 0 or not stats_path.is_file():
            failures.append(label)
            print(f"FAILED: {label}")
            print(f"Inspect: {outdir / 'run.log'}")
            print(result.stdout[-2000:])
            continue

        stats = read_stats(stats_path)

        required_stats = [
            "simTicks",
            "simInsts",
            "system.cpu.numCycles",
            "system.cpu.ipc",
            "system.l1i.demandMisses::total",
            "system.l1d.demandMisses::total",
            "system.l1i.overallMissRate::total",
            "system.l1d.overallMissRate::total",
        ]

        missing = [
            key for key in required_stats
            if key not in stats or not math.isfinite(stats[key])
        ]

        if missing:
            failures.append(label)
            print(f"FAILED: missing or invalid statistics: {missing}")
            continue

        row = {
            "workload": "matrix_mul_256",
            "l1i_size": "32KiB",
            "l1i_assoc": 8,
            "l1d_size": size,
            "l1d_assoc": assoc,
            "sim_ticks": stats.get("simTicks"),
            "instructions": stats.get("simInsts"),
            "cpu_cycles": stats.get("system.cpu.numCycles"),
            "ipc": stats.get("system.cpu.ipc"),
            "l1i_demand_misses": stats.get(
                "system.l1i.demandMisses::total"
            ),
            "l1d_demand_misses": stats.get(
                "system.l1d.demandMisses::total"
            ),
            "l1i_miss_rate": stats.get(
                "system.l1i.overallMissRate::total"
            ),
            "l1d_miss_rate": stats.get(
                "system.l1d.overallMissRate::total"
            ),
        }

        rows.append(row)

        print(
            f"IPC={row['ipc']}, "
            f"L1D misses={row['l1d_demand_misses']}, "
            f"L1D miss rate={row['l1d_miss_rate']}"
        )

    columns = [
        "workload",
        "l1i_size",
        "l1i_assoc",
        "l1d_size",
        "l1d_assoc",
        "sim_ticks",
        "instructions",
        "cpu_cycles",
        "ipc",
        "l1i_demand_misses",
        "l1d_demand_misses",
        "l1i_miss_rate",
        "l1d_miss_rate",
    ]

    validation_csv = ROOT / "results" / "raw" / "matrix_sweep_validation.csv"

    if failures or len(rows) != len(experiments):
        print("\\nDataset NOT updated: the sweep was incomplete.")
        print(f"Existing dataset preserved: {CSV_PATH}")
        sys.exit(1)

    validation_csv.parent.mkdir(parents=True, exist_ok=True)
    with validation_csv.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    temporary_csv = CSV_PATH.with_suffix(".csv.tmp")
    with temporary_csv.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
        file.flush()
        os.fsync(file.fileno())

    temporary_csv.replace(CSV_PATH)
    print(f"Validation copy: {validation_csv}")

    print("\n" + "=" * 60)
    print("CACHE SWEEP FINISHED")
    print("=" * 60)
    print(f"Successful configurations: {len(rows)}")
    print(f"Failed configurations: {len(failures)}")
    print(f"Dataset: {CSV_PATH}")

    if failures:
        print("Failed experiments:")
        for label in failures:
            print(f"  - {label}")

    if not rows:
        sys.exit(1)


if __name__ == "__main__":
    main()

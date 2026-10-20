import csv
import itertools
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GEM5 = Path.home() / "projects/gem5/build/X86/gem5.opt"
CONFIG = ROOT / "configs/x86_cache.py"
BINARY = ROOT / "workloads/branch_intensive_x86"

OUTPUT = ROOT / "results/raw"
CSV_PATH = ROOT / "data/branch_cache_sweep.csv"

CACHE_SIZES = ["16KiB", "32KiB", "64KiB", "128KiB"]
ASSOCIATIVITIES = [4, 8, 16]


def read_stats(stats_path):
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
    for path, description in [
        (GEM5, "gem5 binary"),
        (CONFIG, "gem5 configuration"),
        (BINARY, "branch workload"),
    ]:
        if not path.is_file():
            sys.exit(f"{description} not found: {path}")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    experiments = list(
        itertools.product(CACHE_SIZES, ASSOCIATIVITIES)
    )

    rows = []
    failures = []

    print(f"Workload: {BINARY.name}")
    print(f"Total configurations: {len(experiments)}")

    for index, (size, assoc) in enumerate(experiments, start=1):
        label = f"branch_l1d_{size.lower()}_{assoc}way"
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

        row = {
            "workload": "branch_intensive_1M",
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

    with CSV_PATH.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    print("\n" + "=" * 60)
    print("BRANCH WORKLOAD CACHE SWEEP FINISHED")
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

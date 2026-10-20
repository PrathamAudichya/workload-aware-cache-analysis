import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INPUT_FILES = [
    ROOT / "data/cache_sweep.csv",
    ROOT / "data/memory_cache_sweep.csv",
    ROOT / "data/branch_cache_sweep.csv",
]

OUTPUT_FILE = ROOT / "data/combined_cache_dataset.csv"


def main():
    datasets = []
    reference_columns = None

    for path in INPUT_FILES:
        if not path.is_file():
            raise FileNotFoundError(f"Dataset not found: {path}")

        with path.open(newline="") as file:
            reader = csv.DictReader(file)
            columns = reader.fieldnames
            rows = list(reader)

        if not columns:
            raise ValueError(f"Missing CSV header: {path}")

        if reference_columns is None:
            reference_columns = columns
        elif columns != reference_columns:
            raise ValueError(
                f"CSV schema mismatch in {path.name}\n"
                f"Expected: {reference_columns}\n"
                f"Found:    {columns}"
            )

        datasets.append((path, rows))

    combined_rows = []

    for path, rows in datasets:
        print(f"{path.name}: {len(rows)} rows")
        combined_rows.extend(rows)

    with OUTPUT_FILE.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=reference_columns)
        writer.writeheader()
        writer.writerows(combined_rows)

    print(f"\nCombined rows: {len(combined_rows)}")
    print(f"Workloads: {sorted({row['workload'] for row in combined_rows})}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

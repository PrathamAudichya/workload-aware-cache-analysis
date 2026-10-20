# Workload-Aware L1 Data Cache Performance Analysis Using gem5

An experimental study of how L1 data-cache capacity and associativity affect
the performance of different computational workloads using the gem5
architectural simulator.

The project compares cache configurations across matrix multiplication,
memory-intensive, and branch-intensive workloads using simulation statistics,
including instructions per cycle (IPC), simulation ticks, and L1 cache misses.

## Overview

Cache configuration involves trade-offs between capacity, associativity,
miss behavior, and hardware cost. A configuration that performs well for one
workload may not provide the same benefit for another.

This project evaluates a grid of L1 data-cache configurations across three
workload classes to investigate workload-dependent performance behavior.

### Research Questions

- How does L1 data-cache capacity affect workload performance?
- How does associativity influence cache misses and IPC?
- Do different workload classes favor different cache configurations?
- How do alternative configurations compare with a 32 KiB, 8-way baseline?

## Experimental Setup

| Parameter | Configuration |
|---|---|
| Simulator | gem5 |
| Architecture | X86 |
| CPU model | TimingSimpleCPU |
| CPU clock | 2 GHz |
| Memory mode | Timing |
| Main memory | 512 MiB |
| Memory model | DDR3-1600 |
| L1 instruction cache | 32 KiB, 8-way |
| L1 data-cache sizes | 16, 32, 64, 128 KiB |
| L1 data-cache associativity | 4-way, 8-way, 16-way |
| Workloads | 3 |
| Configurations per workload | 12 |
| Total workload/configuration combinations | 36 |

The experiment varies L1 data-cache size and associativity while keeping the
L1 instruction cache fixed.

The evaluated L1D configuration grid is:

| L1D Capacity | 4-way | 8-way | 16-way |
|---|---:|---:|---:|
| 16 KiB | Yes | Yes | Yes |
| 32 KiB | Yes | Yes | Yes |
| 64 KiB | Yes | Yes | Yes |
| 128 KiB | Yes | Yes | Yes |

## Workloads

### 1. Matrix Multiplication

Source: `workloads/matrix_mul.c`

A computational workload used to study cache behavior during matrix
operations and repeated memory accesses.

### 2. Memory-Intensive Workload

Source: `workloads/memory_intensive.c`

A workload designed to exercise memory access behavior and investigate how
cache capacity and associativity relate to performance.

### 3. Branch-Intensive Workload

Source: `workloads/branch_intensive.c`

A workload with branch-heavy control flow, included to compare cache behavior
across a different execution pattern.

## Metrics

The analysis uses the following metrics collected or derived from simulation
results:

- **Instructions:** Number of instructions reported by the simulation.
- **CPU cycles:** CPU-cycle metric recorded in the result datasets.
- **Simulation ticks:** Simulated execution time expressed in gem5 ticks.
- **IPC:** Instructions per cycle; higher values generally indicate greater
  instruction throughput under the modeled configuration.
- **L1I demand misses:** Instruction-cache demand misses.
- **L1D demand misses:** Data-cache demand misses.
- **L1I miss rate:** Instruction-cache demand miss rate.
- **L1D miss rate:** Data-cache demand miss rate.

Simulation ticks are not wall-clock execution time. Results represent the
configured simulated system, not direct measurements of physical hardware.

## Key Findings

The validated datasets identify the highest-IPC configuration for each workload
among the 12 tested L1D configurations.

| Workload | Highest-IPC L1D Configuration | IPC | Simulation Ticks |
|---|---|---:|---:|
| Matrix multiplication | 16 KiB, 8-way | 0.122478 | 249770861500 |
| Memory-intensive | 64 KiB, 4-way | 0.127299 | 486402771000 |
| Branch-intensive | 32 KiB, 8-way | 0.307580 | 1635519570000 |

These configurations maximize IPC in their respective validated datasets.
They are not necessarily the configurations with the fewest simulation ticks,
the lowest miss rate, or the best physical hardware trade-off.

### Interpretation

- The matrix multiplication workload achieves its highest recorded IPC with a
  16 KiB, 8-way L1D cache among the tested configurations.
- The memory-intensive workload achieves its highest recorded IPC with a
  64 KiB, 4-way L1D cache.
- The branch-intensive workload achieves its highest recorded IPC with a
  32 KiB, 8-way L1D cache.
- Increasing cache capacity or associativity does not necessarily improve IPC
  for every workload.

The results illustrate why cache configurations should be evaluated against
representative workloads rather than selected using capacity or associativity
alone.

### Validation and Limitations

Each workload was evaluated across 12 L1D configurations, for 36 configurations
in total. The official per-workload CSV files were checked against their
validated datasets, and the combined dataset was rebuilt from those validated
measurements.

Three repeated simulations produced identical statistics for the memory-
intensive workload at 64 KiB, 4-way and the branch-intensive workload at
32 KiB, 8-way. These checks establish repeatability for those two configurations
only; all 36 configurations were not independently repeated three times.

The original and freshly validated memory and branch datasets had small
differences in timing statistics and L1D miss counts. The validated datasets
are used for the results reported above; the original CSV backups are retained
for traceability.

Simulation ticks are gem5 simulated time, not wall-clock execution time.
Results depend on the modeled system, including the CPU model, cache settings,
and memory configuration. The experiment uses `X86TimingSimpleCPU` and does
not establish physical-hardware performance, power consumption, chip area, or
statistical significance.

## Visualizations

The repository includes plots comparing IPC, L1D demand misses, and simulation
ticks across cache configurations.

### Matrix Multiplication

| Metric | Plot |
|---|---|
| IPC | ![Matrix multiplication IPC](plots/matrix_mul_256_ipc_by_configuration.png) |
| L1D demand misses | ![Matrix multiplication L1D misses](plots/matrix_mul_256_l1d_misses_by_configuration.png) |
| Simulation ticks | ![Matrix multiplication simulation ticks](plots/matrix_mul_256_ticks_by_configuration.png) |

### Memory-Intensive Workload

| Metric | Plot |
|---|---|
| IPC | ![Memory-intensive IPC](plots/memory_intensive_32MiB_ipc_by_configuration.png) |
| L1D demand misses | ![Memory-intensive L1D misses](plots/memory_intensive_32MiB_l1d_misses_by_configuration.png) |
| Simulation ticks | ![Memory-intensive simulation ticks](plots/memory_intensive_32MiB_ticks_by_configuration.png) |

### Branch-Intensive Workload

| Metric | Plot |
|---|---|
| IPC | ![Branch-intensive IPC](plots/branch_intensive_1M_ipc_by_configuration.png) |
| L1D demand misses | ![Branch-intensive L1D misses](plots/branch_intensive_1M_l1d_misses_by_configuration.png) |
| Simulation ticks | ![Branch-intensive simulation ticks](plots/branch_intensive_1M_ticks_by_configuration.png) |

Additional branch-cache analysis plots are available in `plots/branch_cache/`.

## Repository Structure

```text
workload-cache-project/
├── configs/
│   └── x86_cache.py
├── workloads/
│   ├── matrix_mul.c
│   ├── memory_intensive.c
│   └── branch_intensive.c
├── scripts/
│   ├── run_cache_sweep.py
│   ├── run_memory_sweep.py
│   ├── run_branch_sweep.py
│   ├── combine_datasets.py
│   ├── analyze_cache_results.py
│   ├── recommend_cache.py
│   ├── plot_results.py
│   └── plot_branch_results.py
├── data/
│   ├── cache_sweep.csv
│   ├── memory_cache_sweep.csv
│   ├── branch_cache_sweep.csv
│   ├── combined_cache_dataset.csv
│   ├── best_worst_configurations.csv
│   └── cross_workload_summary.csv
├── plots/
├── reports/
│   ├── cache_analysis_report.md
│   └── final_report.md
├── results/
│   └── processed/
│       └── cache_recommendations.csv
├── .gitignore
└── README.md

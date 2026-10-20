# L1 Data Cache Configuration Analysis

## Experimental scope

- Total configurations: 36
- Workloads: 3
- Cache sizes: 16 KiB, 32 KiB, 64 KiB, and 128 KiB.
- Associativities: 4-way, 8-way, and 16-way.
- Primary ranking metric: simulation ticks; lower is better.
- Secondary metric: IPC; higher is better.

## Results

| Workload | Fastest configuration | IPC | Slowest configuration | Tick improvement |
|---|---|---:|---|---:|
| branch_intensive_1M | 32KiB, 8-way | 0.307580 | 128KiB, 8-way | 0.017% |
| matrix_mul_256 | 16KiB, 8-way | 0.122478 | 16KiB, 4-way | 0.015% |
| memory_intensive_32MiB | 64KiB, 4-way | 0.127299 | 128KiB, 16-way | 2.131% |

## Interpretation

The best tested cache configuration depends on the workload. The branch-intensive and matrix-multiplication workloads exhibit small performance differences across configurations, while the memory-intensive workload shows a larger difference between its fastest and slowest configurations.

Cache-miss count alone does not determine execution performance. The fastest configuration may record slightly more cache misses than the slowest configuration.

## Limitations

These conclusions apply only to the tested workloads, cache sizes, associativities, and gem5 configuration. Small differences should not be treated as statistically significant without repeated runs and variability analysis. The results do not establish the optimal configuration for real processors.

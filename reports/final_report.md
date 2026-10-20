# Workload-Aware L1 Data Cache Performance Analysis Using gem5

## Abstract

This project investigates how L1 data-cache capacity and associativity affect simulated processor performance across three workloads: matrix multiplication, a memory-intensive workload, and a branch-intensive workload. Using gem5, the experiments evaluate four L1D capacities and three associativities while holding the L1 instruction cache configuration fixed. The resulting 36 observations are compared using simulated ticks, CPU cycles, instructions per cycle (IPC), and L1D demand misses. The results indicate that the observed sensitivity to L1D configuration differs by workload. These findings apply to the specific workloads and simulation configuration tested; they do not establish a universally optimal cache design.

## 1. Objectives

- Evaluate four L1D cache sizes: 16, 32, 64, and 128 KiB.
- Evaluate 4-way, 8-way, and 16-way L1D associativity.
- Compare performance across three workload types.
- Examine the relationship between execution metrics and cache misses.
- Identify the fastest configuration among those tested for each workload.

## 2. Experimental Methodology

### 2.1 Experimental design

- Workloads: 3
- Total observations: 36
- L1D sizes: 16 KiB, 32 KiB, 64 KiB, and 128 KiB.
- L1D associativities: 4-way, 8-way, and 16-way.
- L1I configuration: 32 KiB, 8-way.
- Total configurations per workload: 12.

Each workload is evaluated across the complete 4-by-3 L1D configuration grid. Other simulation parameters are held fixed according to the project's gem5 configuration.

### 2.2 Simulation environment

- Simulator: gem5.
- Recorded source version: `v25.1.0.1-10-g38716b67fb`.
- CPU model: `X86TimingSimpleCPU`.
- Memory mode: timing.
- CPU clock: 2 GHz.
- Memory: 512 MiB configured with DDR3-1600.
- Cache hierarchy: L1 instruction and L1 data caches connected to the system crossbar; no explicit L2 cache in this configuration.
- Execution mode: syscall emulation.

### 2.3 Performance metrics

- **Simulated ticks:** lower values indicate less simulated time under the simulator's timing model.
- **CPU cycles:** simulated CPU cycles reported by gem5.
- **IPC:** instructions per cycle; higher values generally indicate more instructions completed per cycle.
- **L1D demand misses:** demand accesses that miss in the L1 data cache.
- **L1D miss rate:** the reported L1D overall miss rate.

The primary selection metric is minimum simulated ticks. IPC is used as a secondary performance indicator. Cache-miss count is considered alongside execution metrics rather than treated as a direct substitute for execution performance.

## 3. Results

| Workload | Configurations | Fastest L1D | Fastest IPC | Fastest simulated ticks | Slowest L1D | Tick improvement |
|---|---:|---|---:|---:|---|---:|
| branch_intensive_1M | 12 | 32KiB, 8-way | 0.307580 | 1635519570000 | 128KiB, 8-way | 0.017% |
| matrix_mul_256 | 12 | 16KiB, 8-way | 0.122478 | 249770861500 | 16KiB, 4-way | 0.015% |
| memory_intensive_32MiB | 12 | 64KiB, 4-way | 0.127299 | 486402771000 | 128KiB, 16-way | 2.131% |

### 3.1 Workload-level interpretation

**Branch-intensive workload.** The fastest tested configuration is 32KiB, 8-way. The fastest-to-slowest simulated-tick difference is approximately 0.017%.

**Matrix multiplication.** The fastest tested configuration is 16KiB, 8-way. The fastest-to-slowest simulated-tick difference is approximately 0.015%.

**Memory-intensive workload.** The fastest tested configuration is 64KiB, 4-way. The fastest-to-slowest simulated-tick difference is approximately 2.131%.

These rankings identify the minimum observed simulated ticks in the existing dataset. Small differences should not be interpreted as statistically significant without additional validation.

### 3.2 Cache misses and execution performance

The configuration with the fewest L1D demand misses is not necessarily the configuration with the lowest simulated ticks. Performance also depends on the timing and cost of memory accesses, the access pattern, and other aspects of the simulated system. Cache misses should therefore be interpreted alongside simulated ticks, CPU cycles, and IPC.

## 4. Configuration Recommendations

The following recommendations refer only to the tested configuration grid. They are selected using minimum simulated ticks, not cache area, energy consumption, or a multi-objective cost function.

| Workload | Recommended L1D | Baseline L1D | Tick change vs baseline | IPC change vs baseline |
|---|---|---|---:|---:|
| branch_intensive_1M | 32KiB, 8-way | 32KiB, 8-way | +0.000% | +0.000% |
| matrix_mul_256 | 16KiB, 8-way | 32KiB, 8-way | -0.011% | +0.010% |
| memory_intensive_32MiB | 64KiB, 4-way | 32KiB, 8-way | -0.607% | +0.612% |

A negative tick change means the recommended configuration uses fewer simulated ticks than the baseline; a positive IPC change means higher IPC than the baseline. These changes are relative to the 32 KiB, 8-way baseline, and are not the same as the fastest-to-slowest improvements reported above.

## 5. Limitations

1. Only three workloads and twelve L1D configurations per workload were tested.
2. L1I was fixed at 32 KiB and 8-way; interactions with alternative instruction-cache configurations were not evaluated.
3. No explicit L2 cache was configured in the tested hierarchy.
4. `X86TimingSimpleCPU` is a simplified CPU model and does not represent all performance mechanisms of modern out-of-order processors.
5. The experiments do not measure physical hardware performance, energy consumption, or implementation area.
6. Repeated-run variability has not been characterized. Very small differences must not be treated as statistically significant.
7. The branch-intensive benchmark's name does not imply that branch misprediction behavior was measured directly; this report does not claim to quantify branch misprediction penalties.
8. Recommendations select the fastest observed configuration from the tested grid, not a globally optimal cache design.

## 6. Conclusion

The experiments demonstrate that the observed effect of L1D size and associativity depends on workload characteristics. The memory-intensive workload exhibits a larger performance spread than the branch-intensive and matrix-multiplication workloads. The results also demonstrate why cache-miss counts alone are insufficient for ranking configurations. The selected configurations should be treated as workload-specific recommendations for this gem5 setup, subject to validation through repeat runs and broader workload coverage.

## 7. Reproducibility

The repository contains the simulation configuration, workload source files, sweep scripts, CSV datasets, analysis scripts, and generated plots. See `README.md` for environment setup and execution instructions.

# Workload-Aware Cache Configuration for Heterogeneous Systems (x86, gem5)

## Abstract

Workloads are classified as compute-, memory-, or branch-intensive from measured features (instruction mix, L1D/L2 MPKI, branch MPKI), and each class is mapped to a cache configuration chosen from a 9-configuration gem5 sweep. Twelve training kernels were simulated on every configuration (108 runs). A threshold rule classified all 12 correctly (in-sample). On four held-out kernels, all four were classified correctly and three of four recommended configurations kept at least 95% of baseline performance. The failure (hashchain, 0.574x) shows that class alone does not determine cache need.

## 1. Experimental setup

- Simulator: gem5 v25.1.0.1, x86, syscall-emulation mode, X86O3CPU with a tournament branch predictor, 2 GHz, DDR3-1600 512 MiB, 64 B cache lines (`configs/x86_cache_v2.py`).
- L1I fixed at 32 KiB, 8-way. L1D has 16 MSHRs. No L3 (the reference 12 MiB, 8-way L3 gives a non-power-of-two set count, which gem5 does not accept).
- Baseline: 48 KiB 12-way L1D + 1280 KiB 10-way L2, matching the per-core cache sizes reported by `getconf` on an Intel i5-12450H P-core (`docs/baseline.md`). The pipeline is a gem5 approximation, not a model of that core.
- Sweep grid: L1D 16 KiB/4-way, 32 KiB/8-way, 48 KiB/12-way, crossed with L2 256 KiB/4-way, 512 KiB/8-way, 1280 KiB/10-way. Cache capacity (L1D + L2) is used as a cost proxy; no area or energy model was applied.
- Performance metric: simulated ticks. Speedup = baseline ticks / config ticks. gem5 is deterministic, so repeated runs give identical results.

## 2. Workloads and features

Twelve training kernels (`workloads/kernels.c`), four per intended class, plus four held-out kernels (`workloads/kernels_holdout.c`). Intended classes are defined by benchmark design and are not independent labels.

| Workload | Intended class | IPC | Branch MPKI | L2 MPKI |
|---|---|---:|---:|---:|
| nbody | compute | 2.923 | 1.557 | 0.030 |
| chacha | compute | 2.589 | 0.066 | 0.133 |
| fft | compute | 2.602 | 0.977 | 0.027 |
| matmul_tiled | compute | 1.631 | 1.064 | 0.458 |
| stream | memory | 0.100 | 0.049 | 95.298 |
| pchase | memory | 0.113 | 17.116 | 53.865 |
| spmv | memory | 0.718 | 0.025 | 20.925 |
| stride | memory | 0.289 | 0.024 | 176.792 |
| qsort | branch | 1.068 | 39.872 | 0.330 |
| bst | branch | 0.776 | 8.781 | 0.199 |
| fsm | branch | 1.610 | 21.102 | 0.021 |
| ifchain | branch | 0.741 | 74.495 | 0.022 |

Features are extracted from the baseline run (`scripts/extract_features_v2.py`). L2 MPKI is used as the memory-pressure signal because L1D misses that merge in the MSHRs inflate L1D MPKI. Branch MPKI is computed from committed mispredicted branches. The O3 `numCycles` statistic was not used (it disagreed with ticks and IPC); IPC and ticks were used instead.

## 3. Classification

Rule (`scripts/classify_v2.py`): L2 MPKI > 5 -> memory; otherwise branch MPKI > 5 -> branch; otherwise compute. The thresholds sit in wide gaps: memory kernels have L2 MPKI >= 20.9 while all others are <= 0.46; branch kernels have branch MPKI >= 8.8 while compute kernels are <= 1.56. The rule classified 12/12 training kernels correctly, but the thresholds were set after inspecting these same 12 kernels, so this is in-sample consistency, not generalization.

A depth-3 decision tree on seven features scored 0.75 under leave-one-out cross-validation (3 of 12 wrong), reflecting the very small sample (four kernels per class). Its full-data splits used L2 MPKI first, then branch fraction.

## 4. Sweep results and recommendations

Geometric-mean speedup against the baseline (`scripts/analyze_sweep.py`; per-run data in `data/sweep_results.csv`):

| L1D + L2 | Total KiB | compute | branch | memory |
|---|---:|---:|---:|---:|
| 16K/4w + 256K/4w | 272 | 0.970 | 0.819 | 0.765 |
| 32K/8w + 256K/4w | 288 | 0.994 | 0.830 | 0.765 |
| 48K/12w + 256K/4w | 304 | 0.993 | 0.838 | 0.765 |
| 16K/4w + 512K/8w | 528 | 0.976 | 0.955 | 0.822 |
| 32K/8w + 512K/8w | 544 | 1.001 | 0.978 | 0.822 |
| 48K/12w + 512K/8w | 560 | 1.000 | 0.993 | 0.822 |
| 16K/4w + 1280K/10w | 1296 | 0.976 | 0.962 | 1.000 |
| 32K/8w + 1280K/10w | 1312 | 1.001 | 0.985 | 1.000 |
| 48K/12w + 1280K/10w (baseline) | 1328 | 1.000 | 1.000 | 1.000 |

Recommendation rule: the smallest total capacity at which every workload in the class keeps at least 95% of baseline performance (`data/class_recommendations_safe.csv`). The geomean-within-2% rule (`data/class_recommendations.csv`) selects the same three configurations.

| Class | Recommended config | Capacity | Saved vs baseline | Worst workload (speedup) |
|---|---|---:|---:|---|
| compute | 32 KiB 8-way L1D + 256 KiB 4-way L2 | 288 KiB | 1040 KiB (78%) | matmul_tiled (0.975) |
| branch | 48 KiB 12-way L1D + 512 KiB 8-way L2 | 560 KiB | 768 KiB (58%) | qsort (0.972) |
| memory | 16 KiB 4-way L1D + 1280 KiB 10-way L2 | 1296 KiB | 32 KiB (2%) | pchase (0.999) |

![Training sweep](../plots/training_speedup_vs_capacity.png)

Points at each capacity are the three L1D sizes tried with that L2 size, so each curve steps through the L2 sizes (256, 512, 1280 KiB).

Observations:
- Memory kernels depend on L2 capacity, not L1D size: worst-case speedup is about 0.47 at 256 KiB L2, 0.57 at 512 KiB, and 0.999 at 1280 KiB. The grid has no size between 512 and 1280 KiB, so the true minimum capacity for the memory class may be smaller.
- Compute kernels are nearly insensitive to the caches, except fft, which needs more than a 16 KiB L1D.
- For the branch class, a 32 KiB L1D drops the worst-case speedup to 0.942 (with a 512 KiB L2); 48 KiB keeps it at 0.972.
- Sensitivity varies widely inside each class (slowest/fastest - 1): spmv 110.8%, bst 106.7%, pchase 38.7%, fft 14.8%, qsort 7.7%, matmul_tiled 6.9%, stream 2.3%, stride 0.03%, and 0.0% for chacha, fsm, nbody, and ifchain. Class-level recommendations therefore hide large differences between members.

## 5. Held-out validation

Predictions were recorded before the held-out runs (`docs/holdout_predictions.md`). Each held-out kernel was classified by the rule, assigned its class recommendation, and compared with the baseline in gem5 (`scripts/validate_holdout.py`).

| Workload | Intended | Predicted | Config | Capacity | Speedup vs baseline | Result |
|---|---|---|---|---:|---:|---|
| mandel | compute | compute | 32K/8w + 256K/4w | 288 KiB | 0.9999 | Pass |
| gather | memory | memory | 16K/4w + 1280K/10w | 1296 KiB | 0.9977 | Pass |
| bsearch | branch | branch | 48K/12w + 512K/8w | 560 KiB | 1.0000 | Pass |
| hashchain | branch | branch | 48K/12w + 512K/8w | 560 KiB | 0.5744 | Fail |

Classification: 4/4. Recommendation within 95% of baseline: 3/4.

hashchain is correctly classified (branch MPKI 29.4) but its data footprint is roughly 640 KB, larger than the recommended 512 KiB L2. Its baseline L2 MPKI (0.88) does not reveal that. A controlled L2 sweep (`scripts/run_controlled_hashchain.sh`, `data/controlled_hashchain_capacity.csv`) supports this: from 256 to 1024 KiB, ticks fall about 65% and the L2 demand miss rate falls from 61% to 0.9%. This explains the failure but does not give the classifier a way to predict it. See `reports/holdout_cache_capacity_report.md` for details. The held-out results were not used to change thresholds or recommendations.

## 6. Computer-architecture interpretation

- Compute-bound kernels (high IPC, tiny working sets) gain nothing from large caches, so they can run on a small-cache design with the area spent elsewhere.
- Memory-bound kernels with working sets near or above the L2 size are limited by L2 capacity; a larger L1D adds nothing.
- Branch-bound kernels lose time to mispredictions rather than cache misses, so their cache need is set by working-set size (bst, qsort, hashchain) rather than by the branch behavior itself; fsm, ifchain, and bsearch need almost no cache.
- Heterogeneous-system implication: the three recommendations suggest three core cache profiles (small-cache, mid-size, large-L2) to which a scheduler could route workloads by class. This study simulates single cores only. It does not simulate a heterogeneous multicore, scheduling, or energy, so this mapping is a design implication, not a tested result.

## 7. Limitations

- Small samples: 12 training kernels and 4 held-out kernels. Held-out figures are descriptive, not evidence of generalization.
- Intended classes come from benchmark design; the rule's 12/12 is in-sample, and the tree's leave-one-out accuracy is 0.75.
- Class alone does not determine cache need (hashchain). Capacity-sensitive workloads need an additional feature or measurement.
- The grid is coarse (9 configurations, three L2 sizes) and omits block size, L3, prefetching, and sizes between 512 and 1280 KiB.
- Capacity is a proxy for cost; no area, power, or latency scaling with size was modeled (cache latencies were held fixed per level).
- Kernels are short (about 5 to 80 million instructions), and gem5's O3 model with a fixed DRAM model is not a real Intel core. Results apply to this simulated setup.

## 8. Reproduce

```bash
source .venv/bin/activate
./scripts/build_workloads.sh && ./scripts/build_holdout.sh
./scripts/run_baseline.sh                       # 12 workloads, baseline config
python scripts/extract_features_v2.py           # data/o3_features.csv
python scripts/classify_v2.py                   # data/o3_classification.csv
./scripts/run_sweep.sh                          # 96 more runs (about 3-4 hours)
python scripts/analyze_sweep.py                 # recommendations and sensitivity
./scripts/run_holdout_sweep.sh                  # 36 held-out runs
python scripts/validate_holdout.py              # data/holdout_validation.csv
python scripts/plot_holdout_results.py          # figures
```

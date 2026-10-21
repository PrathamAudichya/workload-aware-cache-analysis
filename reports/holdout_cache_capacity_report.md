# Workload-Aware Cache-Capacity Analysis Using gem5

## Abstract

This experiment evaluates workload classification and cache-configuration recommendations using gem5. Four held-out workloads were evaluated: bsearch, gather, hashchain, and mandel. The classifier correctly identified all four intended workload classes, but only three of the four recommended configurations retained at least 95% of baseline performance.

## 1. Methodology

The experiment extracts workload features, applies a rule-based classifier, and evaluates recommended cache configurations against a fixed baseline.

The held-out workloads are:

| Workload | Intended class |
|---|---|
| bsearch | Branch |
| gather | Memory |
| hashchain | Branch |
| mandel | Compute |

The extracted features include IPC, instruction fractions, branch MPKI, misprediction rate, L1 data-cache metrics, and L2-cache metrics.

The baseline configuration is `l1d48k12_l2k1280k10`. A recommendation passes when its speedup relative to baseline is at least 0.95.

## 2. Results

| Workload | Intended class | Predicted class | Selected capacity (KiB) | Speedup vs. baseline | Result |
|---|---|---|---:|---:|---|
| bsearch | branch | branch | 560 | 1.0000 | Pass |
| gather | memory | memory | 1296 | 0.9977 | Pass |
| hashchain | branch | branch | 560 | 0.5744 | Fail |
| mandel | compute | compute | 288 | 0.9999 | Pass |

Classification accuracy was 4/4 (100%). The recommendation pass rate was 3/4 (75%).

### Hashchain failure analysis

Hashchain is the principal failure case. Although its workload class was identified correctly, the selected configuration achieved only 0.5744 times baseline performance.

Its estimated data footprint is approximately 640 KB, exceeding the selected configuration's 512 KiB L2 cache. Baseline L2 MPKI was approximately 0.88, which did not clearly signal the capacity problem from a single feature snapshot.

The evaluated oracle configuration used a 1280 KiB L2 cache. This is a retrospective sweep result, not the classifier's recommendation.

### Controlled L2-capacity experiment

To investigate the hashchain failure, a follow-up experiment varied L2 capacity while holding the O3 CPU, tournament branch predictor, 48 KiB 12-way L1D, 16 L1D MSHRs, and 8-way L2 associativity constant. The 1280 KiB, 8-way configuration was invalid in gem5 because it produced a non-power-of-two number of cache sets; 1024 KiB was used as the largest valid tested capacity instead.

| L2 capacity | L2 associativity | Simulation ticks | IPC | L2 demand miss rate |
|---:|---:|---:|---:|---:|
| 256 KiB | 8-way | 30,168,102,500 | 0.224659 | 61.49% |
| 512 KiB | 8-way | 18,122,446,500 | 0.373986 | 19.62% |
| 1024 KiB | 8-way | 10,410,146,000 | 0.651052 | 0.93% |

Increasing L2 capacity from 256 KiB to 1024 KiB reduced simulation ticks by approximately 65.5% and lowered the L2 demand miss rate from 61.49% to 0.93%. These results provide controlled evidence that L2 capacity materially affects hashchain performance under this simulated configuration.

This follow-up experiment does not change the original held-out evaluation or its recommendation pass rate. It investigates the failure mechanism; it does not establish that the current classifier can predict the required capacity. Further evaluation should test whether additional features or a capacity-selection method can generalize to unseen workloads.

## 3. Visualizations

- `plots/holdout_ipc_by_class.png`: baseline IPC by intended workload class.
- `plots/holdout_classification_space.png`: L2 MPKI versus branch MPKI, with classification thresholds.
- `plots/holdout_speedup_vs_capacity.png`: speedup versus total cache capacity.

With only four held-out workloads, these figures are descriptive and do not establish generalization.

## 4. Limitations

- The held-out sample contains only four workloads.
- Correct classification does not guarantee a successful cache recommendation.
- The current feature snapshot does not identify every cache-capacity problem.
- Results depend on the simulated CPU, cache hierarchy, memory configuration, and workload implementation.
- The held-out result should not be used to retroactively tune thresholds or recommendations.

## 5. Future Work

Extend the controlled L2-capacity sweep to the remaining workloads, investigate L2 MPKI and other capacity-sensitive features, and develop a capacity-selection method. Evaluate the revised method on additional held-out workloads without tuning on the test set.

## 6. Reproducibility

Activate the project virtual environment:

```bash
source .venv/bin/activate

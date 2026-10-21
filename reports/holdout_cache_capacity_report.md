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

Evaluate each workload at multiple L2 capacities, such as 256 KiB and 512 KiB, and investigate changes in L2 MPKI as a feature. Test the resulting method on additional held-out workloads.

## 6. Reproducibility

Activate the project virtual environment:

```bash
source .venv/bin/activate

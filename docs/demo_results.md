# Input-driven demo results (scripts/recommend_workload.py)

Baseline: 48 KiB 12-way L1D + 1280 KiB 10-way L2, O3 CPU. Runs capped at 20M instructions
where noted (features then describe the start of the program only).

| Run | Input | L2 MPKI | Branch MPKI | IPC | Class | Recommended |
|---|---|---:|---:|---:|---|---|
| mandel (held-out kernel) | none | 0.30 | 0.48 | 2.746 | compute | 32K/8w + 256K/4w (288 KiB); verified 0.9999x baseline |
| demo_param, TABLE_KB=16 | 16 KiB table | 0.08 | 0.03 | 1.973 | compute | 32K/8w + 256K/4w (288 KiB) |
| demo_param, TABLE_KB=4096 | 4096 KiB table | 38.78 | 0.03 | 0.147 | memory | 16K/4w + 1280K/10w (1296 KiB) |

Only the table size changed between the last two rows; the class flips from compute to memory.
The 16 KiB and 4096 KiB runs were classified but not verified in a second gem5 run.

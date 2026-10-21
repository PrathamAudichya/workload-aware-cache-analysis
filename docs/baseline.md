# Baseline (reference hardware: Intel i5-12450H, per P-core, from getconf)
- L1I: 32 KiB, 8-way, 64 B line
- L1D: 48 KiB, 12-way, 64 B line
- L2: 1.25 MiB, 10-way, 64 B line
- L3: 12 MiB shared, 8-way (not modeled: gem5 requires power-of-2 set counts)
- Hybrid CPU: 4 P-cores + 4 E-cores
- Simulated model: gem5 x86, SE mode; does not replicate the real core pipeline

## gem5 model baseline (Phase 2)
- CPU: X86O3CPU, tournament branch predictor, 2 GHz
- L1I 32 KiB 8-way; L1D 48 KiB 12-way (16 MSHRs); L2 1280 KiB 10-way; 64 B line
- No L3 (12 MiB / 8-way gives a non-power-of-2 set count)
- Config: configs/x86_cache_v2.py
- Phase 1 (TimingSimpleCPU, no L2, 36 runs) is kept as earlier results
- Test: matrix_mul -> IPC 1.36, branch MPKI 0.21, mispredict rate 0.97%

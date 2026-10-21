# Baseline (reference hardware: Intel i5-12450H, per P-core, from getconf)
- L1I: 32 KiB, 8-way, 64 B line
- L1D: 48 KiB, 12-way, 64 B line
- L2: 1.25 MiB, 10-way, 64 B line
- L3: 12 MiB shared, 8-way (not modeled: gem5 requires power-of-2 set counts)
- Hybrid CPU: 4 P-cores + 4 E-cores
- Simulated model: gem5 x86, SE mode; does not replicate the real core pipeline

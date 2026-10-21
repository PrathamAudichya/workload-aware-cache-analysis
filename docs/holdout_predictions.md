# Held-out predictions (written BEFORE any gem5 results on these kernels)
Revised once after the full 96-run sweep finished (earlier draft predated the
l1d32k8_l2k1280k10 config); no held-out result had been seen at that point.
Final class recommendations: compute 288 KiB (32KiB/8w L1D + 256KiB L2),
branch 560 KiB (48KiB/12w L1D + 512KiB L2), memory 1296 KiB (16KiB/4w L1D + 1280KiB L2).
- mandel: compute -> expect to pass at 288 KiB
- gather: memory -> expect to pass at 1296 KiB
- bsearch: branch -> expect to pass at 560 KiB
- hashchain: branch -> expect to pass at 560 KiB (hardest test: bst-like pointer chasing)

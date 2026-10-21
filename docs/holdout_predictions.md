# Held-out predictions (written BEFORE running gem5 on these kernels)
- mandel: compute -> expect safe config 32KiB/8w L1D + 256KiB L2
- gather: memory -> expect 16KiB/4w L1D + 1280KiB L2
- bsearch: branch -> classifier says branch; expect little cache sensitivity
- hashchain: branch -> classifier says branch; expect bst-like sensitivity
  (the class rule recommends the full baseline; this is the hardest test)

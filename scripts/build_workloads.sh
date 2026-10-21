#!/bin/bash
set -e
cd "$(dirname "$0")/.."
mkdir -p workloads/bin
for k in NBODY CHACHA FFT MATMUL_TILED STREAM PCHASE SPMV STRIDE QSORT BST FSM IFCHAIN; do
  n=$(echo $k | tr A-Z a-z)
  gcc -O2 -static -DK_$k workloads/kernels.c -o workloads/bin/${n}_x86 -lm
  echo "built $n"
done

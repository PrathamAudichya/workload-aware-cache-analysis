#!/bin/bash
set -e
cd "$(dirname "$0")/.."
mkdir -p workloads/holdout
for k in MANDEL GATHER BSEARCH HASHCHAIN; do
  n=$(echo $k | tr A-Z a-z)
  gcc -O2 -static -DH_$k workloads/kernels_holdout.c -o workloads/holdout/${n}_x86 -lm
  echo "built $n"
done

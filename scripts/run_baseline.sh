#!/bin/bash
cd "$(dirname "$0")/.."
G=~/projects/gem5/build/X86/gem5.opt
OPTS="--cpu-type=o3 --bp-type=tournament --l1d-size=48KiB --l1d-assoc=12 --l1d-mshrs=16 --l2-size=1280KiB --l2-assoc=10"
mkdir -p results/o3_baseline
ls workloads/bin/*_x86 | xargs -P 6 -I{} bash -c '
  n=$(basename {} _x86)
  '"$G"' --outdir=results/o3_baseline/$n configs/x86_cache_v2.py --binary={} '"$OPTS"' > results/o3_baseline/$n.log 2>&1
  echo "done $n"
'

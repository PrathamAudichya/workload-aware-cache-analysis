#!/bin/bash
cd "$(dirname "$0")/.."
G=~/projects/gem5/build/X86/gem5.opt
ROOT=results/o3_sweep
mkdir -p $ROOT
[ -e $ROOT/l1d48k12_l2k1280k10 ] || ln -s ../o3_baseline $ROOT/l1d48k12_l2k1280k10
for l1 in "16KiB 4" "32KiB 8" "48KiB 12"; do
  for l2 in "256KiB 4" "512KiB 8" "1280KiB 10"; do
    [ "$l1 $l2" = "48KiB 12 1280KiB 10" ] && continue
    for b in workloads/bin/*_x86; do echo "$l1 $l2 $b"; done
  done
done | xargs -P 6 -L1 bash -c '
  l1s=$0; l1a=$1; l2s=$2; l2a=$3; bin=$4
  label="l1d${l1s%KiB}k${l1a}_l2k${l2s%KiB}k${l2a}"
  n=$(basename $bin _x86); out='"$ROOT"'/$label/$n
  [ -f $out/stats.txt ] && exit 0
  mkdir -p '"$ROOT"'/$label
  '"$G"' --outdir=$out configs/x86_cache_v2.py --binary=$bin --cpu-type=o3 \
    --bp-type=tournament --l1d-size=$l1s --l1d-assoc=$l1a --l1d-mshrs=16 \
    --l2-size=$l2s --l2-assoc=$l2a > $out.log 2>&1
  echo "done $label $n"
'

#!/bin/bash
# Controlled L2-capacity experiment for the held-out hashchain workload.
# Holds CPU (O3), tournament BP, 48KiB 12-way L1D, 16 MSHRs and 8-way L2 fixed.
cd "$(dirname "$0")/.."
G=~/projects/gem5/build/X86/gem5.opt
BIN=workloads/holdout/hashchain_x86
OUT=data/controlled_hashchain_capacity.csv
echo "workload,l2_size_kib,l2_assoc,sim_ticks,ipc,l2_demand_misses,l2_demand_accesses,l2_demand_miss_rate" > $OUT
for l2 in 256 512 1024; do
  d=results/controlled_hashchain/l2_${l2}k
  rm -rf $d; mkdir -p $d
  $G --outdir=$d configs/x86_cache_v2.py --binary=$BIN --cpu-type=o3 --bp-type=tournament \
     --l1d-size=48KiB --l1d-assoc=12 --l1d-mshrs=16 --l2-size=${l2}KiB --l2-assoc=8 > $d.log 2>&1
  S=$d/stats.txt
  t=$(awk '$1=="simTicks"{print $2; exit}' $S)
  ipc=$(awk '$1=="system.cpu.ipc"{print $2; exit}' $S)
  m=$(awk '$1=="system.l2.demandMisses::total"{print $2; exit}' $S)
  a=$(awk '$1=="system.l2.demandAccesses::total"{print $2; exit}' $S)
  echo "hashchain,$l2,8,$t,$ipc,$m,$a,$(python3 -c "print($m/$a)")" >> $OUT
done
cat $OUT

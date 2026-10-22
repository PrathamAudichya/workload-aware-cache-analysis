import argparse
import os
import m5
from m5.objects import *

p = argparse.ArgumentParser(description="X86 cache sim v2 (timing/O3, optional L2)")
p.add_argument("--binary", required=True)
p.add_argument("--cpu-type", choices=["timing", "o3"], default="timing")
p.add_argument("--bp-type", choices=["default", "local", "bimode", "tournament", "ltage"],
               default="default")
p.add_argument("--l1i-size", default="32KiB")
p.add_argument("--l1i-assoc", type=int, default=8)
p.add_argument("--l1d-size", default="32KiB")
p.add_argument("--l1d-assoc", type=int, default=8)
p.add_argument("--l1d-mshrs", type=int, default=4)
p.add_argument("--l2-size", default="0", help="0 = no L2")
p.add_argument("--l2-assoc", type=int, default=8)
p.add_argument("--block-size", type=int, default=64)
p.add_argument("--max-insts", type=int, default=0, help="stop after N committed instructions")
p.add_argument("--cpu-clock", default="2GHz")
p.add_argument("--mem-size", default="512MiB")
p.add_argument("--dram-device-size", default="512MiB")
args = p.parse_args()

binary = os.path.abspath(args.binary)
if not os.path.isfile(binary):
    raise FileNotFoundError(f"Workload binary not found: {binary}")
if args.block_size & (args.block_size - 1):
    raise ValueError("Block size must be a power of 2")
use_l2 = args.l2_size not in ("0", "0B", "")

system = System()
system.clk_domain = SrcClockDomain(clock=args.cpu_clock, voltage_domain=VoltageDomain())
system.mem_mode = "timing"
system.mem_ranges = [AddrRange(args.mem_size)]
system.cache_line_size = args.block_size

system.cpu = X86TimingSimpleCPU() if args.cpu_type == "timing" else X86O3CPU()
if args.bp_type != "default":
    if args.cpu_type != "o3":
        raise ValueError("--bp-type needs --cpu-type o3")
    bp = {"local": LocalBP, "bimode": BiModeBP,
          "tournament": TournamentBP, "ltage": LTAGE}[args.bp_type]
    system.cpu.branchPred = BranchPredictor(conditionalBranchPred=bp())

system.membus = SystemXBar()

system.l1i = Cache(size=args.l1i_size, assoc=args.l1i_assoc, tag_latency=2,
                   data_latency=2, response_latency=2, mshrs=4, tgts_per_mshr=20)
system.l1d = Cache(size=args.l1d_size, assoc=args.l1d_assoc, tag_latency=2,
                   data_latency=2, response_latency=2, mshrs=args.l1d_mshrs,
                   tgts_per_mshr=20)
system.cpu.icache_port = system.l1i.cpu_side
system.cpu.dcache_port = system.l1d.cpu_side

if use_l2:
    system.l2bus = L2XBar()
    system.l1i.mem_side = system.l2bus.cpu_side_ports
    system.l1d.mem_side = system.l2bus.cpu_side_ports
    system.l2 = Cache(size=args.l2_size, assoc=args.l2_assoc, tag_latency=8,
                      data_latency=8, response_latency=8, mshrs=20, tgts_per_mshr=12)
    system.l2.cpu_side = system.l2bus.mem_side_ports
    system.l2.mem_side = system.membus.cpu_side_ports
else:
    system.l1i.mem_side = system.membus.cpu_side_ports
    system.l1d.mem_side = system.membus.cpu_side_ports

system.cpu.createInterruptController()
system.cpu.interrupts[0].pio = system.membus.mem_side_ports
system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8(device_size=args.dram_device_size)
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports
system.system_port = system.membus.cpu_side_ports

system.workload = SEWorkload.init_compatible(binary)
process = Process()
process.cmd = [binary]
system.cpu.workload = process
system.cpu.createThreads()
if args.max_insts:
    system.cpu.max_insts_any_thread = args.max_insts

root = Root(full_system=False, system=system)
m5.instantiate()

print("=" * 60)
print(f"Workload: {binary}")
print(f"CPU: {args.cpu_type}  BP: {args.bp_type}  clock: {args.cpu_clock}")
print(f"L1I: {args.l1i_size} {args.l1i_assoc}-way | L1D: {args.l1d_size} "
      f"{args.l1d_assoc}-way (MSHRs {args.l1d_mshrs})")
print(f"L2: {args.l2_size if use_l2 else 'none'} {args.l2_assoc}-way | "
      f"block: {args.block_size}B")
print("=" * 60)
ev = m5.simulate()
print(f"Simulation ticks: {m5.curTick()}")
print(f"Exit cause: {ev.getCause()}")

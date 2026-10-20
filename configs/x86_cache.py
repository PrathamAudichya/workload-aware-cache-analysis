import argparse
import os
import m5

from m5.objects import *


parser = argparse.ArgumentParser(
    description="Configurable X86 cache simulation using gem5"
)

parser.add_argument("--binary", required=True)
parser.add_argument("--l1i-size", default="32KiB")
parser.add_argument("--l1d-size", default="32KiB")
parser.add_argument("--l1i-assoc", type=int, default=8)
parser.add_argument("--l1d-assoc", type=int, default=8)
parser.add_argument("--cpu-clock", default="2GHz")
parser.add_argument("--mem-size", default="512MiB")
parser.add_argument("--dram-device-size", default="512MiB")

args = parser.parse_args()

binary = os.path.abspath(args.binary)

if not os.path.isfile(binary):
    raise FileNotFoundError(
        f"Workload binary not found: {binary}"
    )

if args.l1i_assoc < 1 or args.l1d_assoc < 1:
    raise ValueError("Cache associativity must be positive")

system = System()

# Clock configuration
system.clk_domain = SrcClockDomain(
    clock=args.cpu_clock,
    voltage_domain=VoltageDomain()
)

# Memory address space
system.mem_mode = "timing"
system.mem_ranges = [AddrRange(args.mem_size)]

# X86 CPU
system.cpu = X86TimingSimpleCPU()

# Memory interconnect
system.membus = SystemXBar()

# L1 instruction cache
system.l1i = Cache(
    size=args.l1i_size,
    assoc=args.l1i_assoc,
    tag_latency=2,
    data_latency=2,
    response_latency=2,
    mshrs=4,
    tgts_per_mshr=20
)

# L1 data cache
system.l1d = Cache(
    size=args.l1d_size,
    assoc=args.l1d_assoc,
    tag_latency=2,
    data_latency=2,
    response_latency=2,
    mshrs=4,
    tgts_per_mshr=20
)

# Connect CPU to caches
system.cpu.icache_port = system.l1i.cpu_side
system.cpu.dcache_port = system.l1d.cpu_side

# Connect caches to the memory bus
system.l1i.mem_side = system.membus.cpu_side_ports
system.l1d.mem_side = system.membus.cpu_side_ports

# X86 interrupt connections
system.cpu.createInterruptController()

system.cpu.interrupts[0].pio = system.membus.mem_side_ports
system.cpu.interrupts[0].int_requestor = (
    system.membus.cpu_side_ports
)
system.cpu.interrupts[0].int_responder = (
    system.membus.mem_side_ports
)

# DRAM controller
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8(
    device_size=args.dram_device_size
)
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# System port
system.system_port = system.membus.cpu_side_ports

# Configure syscall-emulation workload
system.workload = SEWorkload.init_compatible(binary)

process = Process()
process.cmd = [binary]

system.cpu.workload = process
system.cpu.createThreads()

# Initialize and run simulation
root = Root(full_system=False, system=system)

m5.instantiate()

print("=" * 60)
print("X86 CACHE SIMULATION")
print("=" * 60)
print(f"Workload: {binary}")
print(f"CPU model: X86TimingSimpleCPU")
print(f"CPU clock: {args.cpu_clock}")
print(f"L1 instruction cache: {args.l1i_size}")
print(f"L1 instruction associativity: {args.l1i_assoc}-way")
print(f"L1 data cache: {args.l1d_size}")
print(f"L1 data associativity: {args.l1d_assoc}-way")
print(f"Memory range: {args.mem_size}")
print(f"DRAM device size: {args.dram_device_size}")
print("=" * 60)

exit_event = m5.simulate()

print(f"Simulation ticks: {m5.curTick()}")
print(f"Exit cause: {exit_event.getCause()}")

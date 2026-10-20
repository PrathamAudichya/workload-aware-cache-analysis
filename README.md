# Workload-Aware L1 Data Cache Performance Analysis Using gem5

## Overview

This project evaluates L1 data-cache size and associativity across three workloads using gem5.

## Experimental Design

- L1D sizes: 16 KiB, 32 KiB, 64 KiB, and 128 KiB.
- L1D associativity: 4-way, 8-way, and 16-way.
- L1I configuration: 32 KiB, 8-way.
- Workloads: matrix multiplication, memory-intensive, and branch-intensive.
- Total configurations: 36.

## Results

| Workload | Recommended L1D | Tick improvement, fastest vs slowest |
|---|---|---:|
| Branch-intensive | 16 KiB, 4-way | 0.016% |
| Matrix multiplication | 16 KiB, 8-way | 0.015% |
| Memory-intensive | 64 KiB, 16-way | 2.098% |

## Detailed Report

See reports/final_report.md for methodology, results, recommendations, and limitations.

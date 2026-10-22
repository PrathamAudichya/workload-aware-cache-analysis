// Demo kernel with adjustable inputs: random read-modify-write over a table.
// TABLE_KB must be a power of two. Example:
//   python scripts/recommend_workload.py workloads/demo_param.c --cflags=-DTABLE_KB=4096 --name big
#include <stdio.h>
#include <stdint.h>
#ifndef TABLE_KB
#define TABLE_KB 2048
#endif
#ifndef ITERS
#define ITERS 2000000
#endif
#define N ((TABLE_KB * 1024) / 4)
static uint32_t tab[N];
static uint64_t rng = 88172645463325252ULL;
static inline uint32_t rnd(void) { rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17; return (uint32_t)(rng >> 16); }
int main(void) {
    for (uint32_t i = 0; i < N; i++) tab[i] = i;
    uint32_t s = 0;
    for (int i = 0; i < ITERS; i++) { uint32_t k = rnd() & (N - 1); tab[k] += s; s ^= tab[k]; }
    printf("demo %u (table %d KiB)\n", s, TABLE_KB);
    return 0;
}

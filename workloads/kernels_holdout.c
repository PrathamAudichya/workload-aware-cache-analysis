// Held-out validation kernels (never used to set thresholds or recommendations)
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

static uint64_t rng = 1234567890123456789ULL;
static inline uint32_t rnd(void) {
    rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17;
    return (uint32_t)(rng >> 16);
}

#ifdef H_MANDEL           // compute: Mandelbrot, FP, no data
int main(void) {
    long total = 0;
    for (int py = 0; py < 64; py++) for (int px = 0; px < 64; px++) {
        double cr = -2.0 + px * 3.0 / 64, ci = -1.5 + py * 3.0 / 64, zr = 0, zi = 0;
        int it = 0;
        while (it < 400 && zr*zr + zi*zi < 4.0) { double t = zr*zr - zi*zi + cr; zi = 2*zr*zi + ci; zr = t; it++; }
        total += it;
    }
    printf("mandel %ld\n", total);
    return 0;
}
#endif

#ifdef H_GATHER           // memory: random read-modify-write on a 2 MB table
#define G (1<<19)
static uint32_t tab[G];
int main(void) {
    for (int i = 0; i < G; i++) tab[i] = i;
    uint32_t s = 0;
    for (int i = 0; i < 3000000; i++) { uint32_t k = rnd() & (G-1); tab[k] += s; s ^= tab[k]; }
    printf("gather %u\n", s);
    return 0;
}
#endif

#ifdef H_BSEARCH          // branch: binary search over a small sorted array (16 KB)
#define BS 4096
static int arr[BS];
int main(void) {
    for (int i = 0; i < BS; i++) arr[i] = i * 3;
    long found = 0;
    for (int q = 0; q < 400000; q++) {
        int key = rnd() % (BS * 3), lo = 0, hi = BS - 1;
        while (lo <= hi) { int mid = (lo + hi) >> 1; if (arr[mid] == key) { found++; break; }
                           if (arr[mid] < key) lo = mid + 1; else hi = mid - 1; }
    }
    printf("bsearch %ld\n", found);
    return 0;
}
#endif

#ifdef H_HASHCHAIN        // branch + pointer chasing: chained hash table, ~0.5 MB
#define NB 16384
#define NN 32768
typedef struct hn { uint32_t key; struct hn *next; } hn;
static hn *bucket[NB];
static hn pool[NN];
int main(void) {
    for (int i = 0; i < NN; i++) { pool[i].key = rnd(); uint32_t b = pool[i].key & (NB-1);
                                   pool[i].next = bucket[b]; bucket[b] = &pool[i]; }
    long hits = 0;
    for (int q = 0; q < 400000; q++) {
        uint32_t key = (q & 1) ? pool[rnd() % NN].key : rnd();
        for (hn *p = bucket[key & (NB-1)]; p; p = p->next) if (p->key == key) { hits++; break; }
    }
    printf("hashchain %ld\n", hits);
    return 0;
}
#endif

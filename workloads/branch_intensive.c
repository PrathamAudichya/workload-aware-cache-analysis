#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#ifndef ELEMENTS
#define ELEMENTS 1000000
#endif

#ifndef PASSES
#define PASSES 100
#endif

int main(void)
{
    uint32_t *values = malloc(
        (size_t)ELEMENTS * sizeof(uint32_t)
    );

    if (values == NULL) {
        perror("malloc");
        return 1;
    }

    uint32_t state = 123456789u;

    for (size_t i = 0; i < ELEMENTS; i++) {
        state = state * 1664525u + 1013904223u;
        values[i] = state;
    }

    uint64_t checksum = 0;

    for (int pass = 0; pass < PASSES; pass++) {
        for (size_t i = 0; i < ELEMENTS; i++) {
            if (values[i] & 1u) {
                checksum += values[i];
            } else {
                checksum -= values[i];
            }
        }
    }

    printf("Elements: %d\n", ELEMENTS);
    printf("Passes: %d\n", PASSES);
    printf("Checksum: %llu\n",
           (unsigned long long)checksum);

    free(values);
    return 0;
}

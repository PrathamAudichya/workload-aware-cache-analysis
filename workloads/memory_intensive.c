#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#ifndef ARRAY_MB
#define ARRAY_MB 32
#endif

#ifndef PASSES
#define PASSES 8
#endif

int main(void)
{
    const size_t count =
        ((size_t)ARRAY_MB * 1024 * 1024) / sizeof(uint64_t);

    uint64_t *array = malloc(count * sizeof(uint64_t));

    if (array == NULL) {
        perror("malloc");
        return 1;
    }

    for (size_t i = 0; i < count; i++) {
        array[i] = (uint64_t)i;
    }

    uint64_t checksum = 0;

    for (int pass = 0; pass < PASSES; pass++) {
        for (size_t i = 0; i < count; i++) {
            array[i] += (uint64_t)(pass + 1);
        }
    }

    for (size_t i = 0; i < count; i++) {
        checksum += array[i];
    }

    printf("Array size: %d MiB\n", ARRAY_MB);
    printf("Passes: %d\n", PASSES);
    printf("Checksum: %llu\n",
           (unsigned long long)checksum);

    free(array);
    return 0;
}

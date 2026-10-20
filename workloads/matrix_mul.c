#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#ifndef N
#define N 256
#endif

static double A[N][N];
static double B[N][N];
static double C[N][N];

int main(void)
{
    volatile double checksum = 0.0;

    // Initialize matrices.
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            A[i][j] = (double)((i + j) % 100) / 100.0;
            B[i][j] = (double)((i * 2 + j) % 100) / 100.0;
            C[i][j] = 0.0;
        }
    }

    // Matrix multiplication: compute-intensive workload.
    for (int i = 0; i < N; i++) {
        for (int k = 0; k < N; k++) {
            double temp = A[i][k];

            for (int j = 0; j < N; j++) {
                C[i][j] += temp * B[k][j];
            }
        }
    }

    // Consume the result so the computation remains observable.
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            checksum += C[i][j];
        }
    }

    printf("Matrix size: %d x %d\n", N, N);
    printf("Checksum: %.6f\n", checksum);

    return 0;
}

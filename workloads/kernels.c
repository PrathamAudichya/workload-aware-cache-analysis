// 12 workload kernels, one selected at compile time with -DK_<NAME>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>

static uint64_t rng = 88172645463325252ULL;
static inline uint32_t rnd(void) {            // xorshift64
    rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17;
    return (uint32_t)(rng >> 16);
}

#ifdef K_NBODY            // compute: FP, tiny data
#define N 32
int main(void) {
    static double x[N], y[N], z[N], vx[N], vy[N], vz[N], m[N];
    for (int i = 0; i < N; i++) { x[i]=rnd()%1000/10.0; y[i]=rnd()%1000/10.0; z[i]=rnd()%1000/10.0; m[i]=1+rnd()%10; }
    for (int s = 0; s < 1500; s++) {
        for (int i = 0; i < N; i++) for (int j = 0; j < N; j++) if (i != j) {
            double dx=x[j]-x[i], dy=y[j]-y[i], dz=z[j]-z[i];
            double d2=dx*dx+dy*dy+dz*dz+0.01, inv=1.0/(d2*sqrt(d2));
            vx[i]+=dx*m[j]*inv*0.001; vy[i]+=dy*m[j]*inv*0.001; vz[i]+=dz*m[j]*inv*0.001;
        }
        for (int i = 0; i < N; i++) { x[i]+=vx[i]; y[i]+=vy[i]; z[i]+=vz[i]; }
    }
    printf("nbody %f\n", x[0]+y[1]+z[2]);
    return 0;
}
#endif

#ifdef K_CHACHA           // compute: integer ARX, registers only
#define QR(a,b,c,d) a+=b; d^=a; d=(d<<16)|(d>>16); c+=d; b^=c; b=(b<<12)|(b>>20); \
                    a+=b; d^=a; d=(d<<8)|(d>>24);  c+=d; b^=c; b=(b<<7)|(b>>25);
int main(void) {
    uint32_t s[16]; for (int i = 0; i < 16; i++) s[i] = rnd();
    for (int r = 0; r < 120000; r++) {
        QR(s[0],s[4],s[8],s[12]) QR(s[1],s[5],s[9],s[13]) QR(s[2],s[6],s[10],s[14]) QR(s[3],s[7],s[11],s[15])
        QR(s[0],s[5],s[10],s[15]) QR(s[1],s[6],s[11],s[12]) QR(s[2],s[7],s[8],s[13]) QR(s[3],s[4],s[9],s[14])
    }
    printf("chacha %u\n", s[0]^s[7]^s[15]);
    return 0;
}
#endif

#ifdef K_FFT              // compute: 1024-pt FFT repeated, 16 KB data
#define F 1024
int main(void) {
    static double re[F], im[F], wr[F/2], wi[F/2];
    for (int i = 0; i < F/2; i++) { wr[i]=cos(-2*M_PI*i/F); wi[i]=sin(-2*M_PI*i/F); }
    for (int rep = 0; rep < 400; rep++) {
        for (int i = 0; i < F; i++) { re[i]=(i*7+rep)%13; im[i]=0; }
        for (int i=1,j=0;i<F;i++){ int b=F>>1; for(;j&b;b>>=1) j^=b; j^=b; if(i<j){double t=re[i];re[i]=re[j];re[j]=t;t=im[i];im[i]=im[j];im[j]=t;} }
        for (int len = 2; len <= F; len <<= 1)
            for (int i = 0; i < F; i += len)
                for (int k = 0; k < len/2; k++) {
                    double c=wr[k*(F/len)], s=wi[k*(F/len)];
                    double tr=re[i+k+len/2]*c-im[i+k+len/2]*s, ti=re[i+k+len/2]*s+im[i+k+len/2]*c;
                    re[i+k+len/2]=re[i+k]-tr; im[i+k+len/2]=im[i+k]-ti; re[i+k]+=tr; im[i+k]+=ti;
                }
    }
    printf("fft %f\n", re[1]+im[2]);
    return 0;
}
#endif

#ifdef K_MATMUL_TILED     // compute: tiled 128x128 matmul, ~400 KB
#define M 128
#define T 16
int main(void) {
    static double a[M][M], b[M][M], c[M][M];
    for (int i = 0; i < M; i++) for (int j = 0; j < M; j++) { a[i][j]=(i+j)%7; b[i][j]=(i*j)%5; }
    for (int rep = 0; rep < 2; rep++)
    for (int ii=0;ii<M;ii+=T) for (int kk=0;kk<M;kk+=T) for (int jj=0;jj<M;jj+=T)
        for (int i=ii;i<ii+T;i++) for (int k=kk;k<kk+T;k++) { double r=a[i][k];
            for (int j=jj;j<jj+T;j++) c[i][j]+=r*b[k][j]; }
    printf("matmul_tiled %f\n", c[3][5]+c[100][77]);
    return 0;
}
#endif

#ifdef K_STREAM           // memory: triad, 3 x 8 MB
#define S (1<<20)
static double a[S], b[S], c[S];
int main(void) {
    for (int i = 0; i < S; i++) { b[i]=i; c[i]=2*i; }
    for (int it = 0; it < 4; it++) for (int i = 0; i < S; i++) a[i]=b[i]+3.0*c[i];
    printf("stream %f\n", a[12345]+a[S-1]);
    return 0;
}
#endif

#ifdef K_PCHASE           // memory: random pointer chase over 4 MB
#define P (1<<20)
static uint32_t nx[P];
int main(void) {
    for (uint32_t i = 0; i < P; i++) nx[i]=i;
    for (uint32_t i = P-1; i > 0; i--) { uint32_t j = rnd() % i, t = nx[i]; nx[i]=nx[j]; nx[j]=t; } // Sattolo
    uint32_t p = 0; for (int s = 0; s < 1500000; s++) p = nx[p];
    printf("pchase %u\n", p);
    return 0;
}
#endif

#ifdef K_SPMV             // memory: CSR sparse matrix-vector, ~7 MB
#define R 65536
#define NZ 8
static double val[R*NZ], x[R], y[R];
static uint32_t col[R*NZ];
int main(void) {
    for (int i = 0; i < R*NZ; i++) { val[i]=1.0+(i&3); col[i]=rnd()%R; }
    for (int i = 0; i < R; i++) x[i]=1.0;
    for (int it = 0; it < 6; it++) {
        for (int r = 0; r < R; r++) { double s=0; for (int k=0;k<NZ;k++) s+=val[r*NZ+k]*x[col[r*NZ+k]]; y[r]=s; }
        for (int r = 0; r < R; r++) x[r]=y[r]*0.01;
    }
    printf("spmv %f\n", x[7]);
    return 0;
}
#endif

#ifdef K_STRIDE           // memory: 68-byte stride over 16 MB
#define A (1<<22)
static int arr[A];
int main(void) {
    for (int i = 0; i < A; i++) arr[i]=i;
    long sum = 0;
    for (int pass = 0; pass < 24; pass++) for (int i = pass; i < A; i += 17) sum += arr[i];
    printf("stride %ld\n", sum);
    return 0;
}
#endif

#ifdef K_QSORT            // branch: quicksort on random data
#define Q 150000
static int v[Q];
static void qs(int lo, int hi) {
    while (lo < hi) {
        int p = v[(lo+hi)/2], i = lo, j = hi;
        while (i <= j) { while (v[i]<p) i++; while (v[j]>p) j--; if (i<=j) { int t=v[i]; v[i]=v[j]; v[j]=t; i++; j--; } }
        if (j-lo < hi-i) { qs(lo,j); lo=i; } else { qs(i,hi); hi=j; }
    }
}
int main(void) {
    for (int i = 0; i < Q; i++) v[i]=rnd();
    qs(0, Q-1);
    printf("qsort %d %d\n", v[0], v[Q-1]);
    return 0;
}
#endif

#ifdef K_BST              // branch: BST lookups on random keys
#define B 20000
typedef struct node { uint32_t k; struct node *l, *r; } node;
static node pool[B];
int main(void) {
    node *root = &pool[0]; pool[0].k = rnd();
    for (int i = 1; i < B; i++) {
        pool[i].k = rnd(); node *c = root;
        for (;;) { node **nx = (pool[i].k < c->k) ? &c->l : &c->r; if (!*nx) { *nx=&pool[i]; break; } c=*nx; }
    }
    long hits = 0;
    for (int q = 0; q < 250000; q++) {
        uint32_t key = (q & 1) ? pool[rnd()%B].k : rnd();
        node *c = root; while (c) { if (key == c->k) { hits++; break; } c = (key < c->k) ? c->l : c->r; }
    }
    printf("bst %ld\n", hits);
    return 0;
}
#endif

#ifdef K_FSM              // branch: data-dependent state machine
int main(void) {
    int st = 0; uint64_t acc = 0;
    for (int i = 0; i < 3000000; i++) {
        uint32_t in = rnd() & 7;
        switch (st) {
            case 0: st = (in < 3) ? 1 : (in < 5) ? 2 : 0; acc += 1; break;
            case 1: st = (in & 1) ? 3 : 0; acc += 2; break;
            case 2: st = (in > 4) ? 4 : 1; acc ^= in; break;
            case 3: st = (in == 0) ? 0 : (in < 4) ? 2 : 4; acc += in; break;
            default: st = (in & 2) ? 1 : 3; acc -= 1; break;
        }
    }
    printf("fsm %llu %d\n", (unsigned long long)acc, st);
    return 0;
}
#endif

#ifdef K_IFCHAIN          // branch: unpredictable if-chains
int main(void) {
    uint32_t a = 0, b = 1; 
    for (int i = 0; i < 3000000; i++) {
        uint32_t r = rnd();
        if (r & 1) a += r; else b ^= r;
        if (r & 2) a ^= b; else b += 3;
        if ((r >> 2) & 1) a -= 7; else b -= 5;
        if (((r >> 3) & 3) == 0) a <<= 1; else b >>= 1;
    }
    printf("ifchain %u %u\n", a, b);
    return 0;
}
#endif

// FSL GPU reference ABI v1; one state, one owning thread.
// Disjoint valid global buffers; status 0 success, 1 underflow, 2 capacity, 3 invalid state.
#if defined(__clang__) && defined(__CUDA__)
#define FSL_GPU_ENTRY __attribute__((global))
#else
#define FSL_GPU_ENTRY __global__
#endif
static_assert(sizeof(unsigned long long) == 8, "64-bit slots required");
static_assert(sizeof(unsigned int) == 4, "32-bit status required");
extern "C" FSL_GPU_ENTRY void fsl_execute(unsigned long long *stack, unsigned long long *depth, unsigned long long capacity, unsigned int *status) {
    unsigned int owner = 0, coordinate;
    asm("mov.u32 %0, %%ctaid.x;" : "=r"(coordinate));
    owner |= coordinate;
    asm("mov.u32 %0, %%ctaid.y;" : "=r"(coordinate));
    owner |= coordinate;
    asm("mov.u32 %0, %%ctaid.z;" : "=r"(coordinate));
    owner |= coordinate;
    asm("mov.u32 %0, %%tid.x;" : "=r"(coordinate));
    owner |= coordinate;
    asm("mov.u32 %0, %%tid.y;" : "=r"(coordinate));
    owner |= coordinate;
    asm("mov.u32 %0, %%tid.z;" : "=r"(coordinate));
    owner |= coordinate;
    if (owner != 0 || status == nullptr) return;
    if (stack == nullptr || depth == nullptr) { *status = 3; return; }
    unsigned long long sp = *depth;
    if (sp > capacity) { *status = 3; return; }
    if (sp < 2) { *status = 1; return; }
    unsigned long long v0 = stack[--sp] & 0xffffffffULL;
    (void)v0;
    unsigned long long v1 = stack[--sp] & 0xffffffffULL;
    (void)v1;
    unsigned long long v2 = (v1 + v0) & 0xffffffffULL;
    (void)v2;
    stack[sp++] = v2;
    *depth = sp;
    *status = 0;
}
#undef FSL_GPU_ENTRY

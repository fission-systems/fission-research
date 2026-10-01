// Hand-written GFX9 assembly for static encoding and ELF inspection.
// This is a code fragment, not a runnable kernel or a semantic test.

.text
.globl fsl_gpu_probe
.type fsl_gpu_probe,@function
fsl_gpu_probe:
    s_mov_b32 s0, 1
    v_add_u32_e32 v0, v1, v2
    s_barrier
    s_endpgm

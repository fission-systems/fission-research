/* Explicit register ABI for the first memory-free i386 function body.
 * This is regparm(2), not the default stack-argument cdecl ABI. */
__attribute__((regparm(2))) unsigned fsl_add(unsigned a, unsigned b) { return a + b; }

/* Undefined AF is deliberately not promoted to a known semantic value. */
unsigned long fsl_add(const unsigned long *values) { return values[0] ^ values[1]; }

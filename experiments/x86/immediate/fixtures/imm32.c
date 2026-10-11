/* SysV AMD64: a 32-bit store must preserve the neighboring upper bytes. */
unsigned long fsl_add(unsigned long *values) {
    unsigned long result = values[0] + values[1];
    *(unsigned int *)(values + 1) = 0x87654321u;
    return result;
}

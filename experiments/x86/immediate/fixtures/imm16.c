/* SysV AMD64: an operand-size prefix selects a 16-bit immediate store. */
unsigned long fsl_add(unsigned long *values) {
    unsigned long result = values[0] + values[1];
    *(unsigned short *)(values + 1) = 0x9876u;
    return result;
}

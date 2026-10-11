/* SysV AMD64: arithmetic result before a sign-extended imm32 store. */
unsigned long fsl_add(unsigned long *values) {
    unsigned long result = values[0] + values[1];
    values[1] = (unsigned long)-7;
    return result;
}

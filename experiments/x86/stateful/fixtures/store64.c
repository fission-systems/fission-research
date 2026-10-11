/* SysV AMD64, O2 externally observable store. */
unsigned long fsl_add(unsigned long *values) { values[0] += values[1]; return values[0]; }

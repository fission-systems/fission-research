/* Test-only host adapter. ORIGINAL_CODE comes from locked ELF bytes, not C reimplementation. */
#include <stdint.h>
#include <stdio.h>
extern uint64_t oracle_code(const uint64_t *);
int main(void) {
    uint64_t values[2];
    while (fread(values, sizeof values, 1, stdin) == 1) {
        uint64_t result, flags;
        const uint64_t *pointer = values;
        __asm__ volatile("pushq $2; popfq; call *%[code]; pushfq; popq %[flags]"
                         : "=a"(result), [flags] "=&c"(flags), "+D"(pointer)
                         : [code] "r"(&oracle_code)
                         : "rsi", "rdx", "r8", "r9", "r10", "r11", "memory", "cc");
        uint64_t output[2] = {result, flags};
        if (fwrite(output, sizeof output, 1, stdout) != 1) return 2;
    }
    return ferror(stdin) ? 3 : 0;
}

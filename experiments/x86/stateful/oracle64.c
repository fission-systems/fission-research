/* Locked leaf bytes only: input in RDI, RBP preserved, no RSI/RDX use. */
#include <stdint.h>
#include <stdio.h>
extern uint64_t oracle_code(uint64_t *);
int main(void) {
 uint64_t values[2];
 while (fread(values,sizeof values,1,stdin)==1) {
  uint64_t result,flags,bp,before,after;uint64_t *pointer=values;
  __asm__ volatile("pushq %%rbp; subq $8, %%rsp; movq $0x11223344, %%rbp; movq %%rsp,%[before]; pushq $2; popfq; call *%[code]; pushfq; popq %[flags]; movq %%rbp,%[bp]; movq %%rsp,%[after]; addq $8, %%rsp; popq %%rbp"
    : "=a"(result),[flags] "=&c"(flags),[bp] "=&b"(bp),[before] "=&S"(before),[after] "=&d"(after),"+D"(pointer)
    /* RBP is overwritten before the indirect call; prohibit code input there. */
    : [code] "r"(&oracle_code) : "rbp","r8","r9","r10","r11","memory","cc");
  if ((before & 15) != 0) return 3; /* SysV call-site stack alignment. */
  uint64_t output[6]={result,flags,values[0],values[1],bp,after-before};
  if(fwrite(output,sizeof output,1,stdout)!=1)return 2;
 }
 return ferror(stdin)?3:0;
}

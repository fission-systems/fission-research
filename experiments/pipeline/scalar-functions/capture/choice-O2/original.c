#include <stdint.h>
__attribute__((noinline)) uint64_t candidate(uint64_t a,uint64_t b,uint64_t c){if (a==0) return b+7; return (a^b)+c;}

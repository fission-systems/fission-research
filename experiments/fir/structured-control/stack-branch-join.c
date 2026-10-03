#include <stdint.h>
#include <stddef.h>
uint32_t fsl_execute(uint64_t *stack, size_t *depth, size_t capacity) {
  if (stack == NULL || depth == NULL || *depth > capacity) return 3;
  if (*depth < 1) return 1;
  size_t sp = *depth;
  uint64_t v[10] = {0};
  (void)v;
  size_t pc = 0;
  for (;;) { switch (pc) {
case 0: {
sp -= 1;
v[0] = stack[sp] & 0xffffffffULL;
v[1] = 0xaULL;
v[2] = (v[0] < v[1]);
if (v[2] != 0) {
uint64_t edge[] = {v[0]};
v[3] = edge[0];
pc = 1;
} else {
uint64_t edge[] = {v[0]};
v[6] = edge[0];
pc = 2;
}
break;
}
case 1: {
v[4] = 0x1ULL;
v[5] = (v[3] + v[4]) & UINT64_C(0xffffffff);
uint64_t edge[] = {v[5]};
v[9] = edge[0];
pc = 3;
break;
}
case 2: {
v[7] = 0x2ULL;
v[8] = (v[6] + v[7]) & UINT64_C(0xffffffff);
uint64_t edge[] = {v[8]};
v[9] = edge[0];
pc = 3;
break;
}
case 3: {
stack[sp] = v[9];
sp += 1;
*depth = sp;
return 0;
}
default: return 3;
} }
}

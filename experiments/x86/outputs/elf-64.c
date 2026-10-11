/* x86 mode=64 input-sha256=d9cf89c572e9a193175b8735a341790208fabfe36d704868ed206cb6a85af1ba package-sha256=0423223eaf7238013177aceb9b7c09f7448a682752668e3124ab9c651b46515a; owned decoder owned-x86-v1.
 * Explicit state function: GPR[0..16]=RAX,RCX,RDX,RBX,RSP,RBP,RSI,RDI,R8..R15; GPR[16]=0.
 * flags=CF,PF,ZF,SF,OF,AF then six known bits. Unknown AF is not observable.
 * Disjoint valid storage required in C. Bounded byte memory, flat SS.base=0, no MMU/fault model.
 * Status 0 commits state and return PC; status 3 preserves caller storage. */
/* binary file-sha256=588d20aa4045b9e6694a8d39931f0bbf10881bfcf1b0090a4b3830ba2704184f file-offset=4096 */
#include <stdint.h>
#include <stddef.h>
/* Disjoint arrays; status 0 success, 3 invalid state. */
uint32_t x86_body_58(uint64_t *registers, size_t register_count, uint64_t *flags, size_t flag_count, const uint64_t *fields, size_t field_count) {
    if (!registers || !flags || !fields) return 3;
    if (field_count != 6) return 3;
    if (fields[0] > UINT64_C(0x1f)) return 3;
    if (fields[1] > UINT64_C(0x1f)) return 3;
    if (fields[2] > UINT64_C(0x1f)) return 3;
    if (fields[3] > UINT64_C(0x1f)) return 3;
    if (fields[5] > UINT64_C(0x3)) return 3;
    if (fields[2] >= register_count) return 3;
    if (fields[3] >= register_count) return 3;
    if (fields[0] >= register_count) return 3;
    for (size_t i = 0; i < flag_count; ++i) if (flags[i] > 1) return 3;
    size_t f0 = (size_t)fields[0]; (void)f0;
    size_t f1 = (size_t)fields[1]; (void)f1;
    size_t f2 = (size_t)fields[2]; (void)f2;
    size_t f3 = (size_t)fields[3]; (void)f3;
    size_t f4 = (size_t)fields[4]; (void)f4;
    size_t f5 = (size_t)fields[5]; (void)f5;
uint64_t v[33] = {0}; (void)v;
size_t pc = 0;
for (;;) { switch (pc) {
case 0: {
v[0] = registers[f2] & UINT64_C(0xffffffffffffffff);
v[1] = registers[f3] & UINT64_C(0xffffffffffffffff);
v[2] = fields[5];
v[3] = 0x0ULL;
v[4] = 0x1ULL;
v[5] = 0x2ULL;
v[6] = (v[2] == v[3]);
v[7] = (v[2] == v[4]);
v[8] = (v[2] == v[5]);
if (v[6] != 0) {
uint64_t edge[] = {v[0], v[1]};
v[9] = edge[0];
v[10] = edge[1];
pc = 1;
} else {
uint64_t edge[] = {v[0], v[1], v[7], v[8]};
v[11] = edge[0];
v[12] = edge[1];
v[13] = edge[2];
v[14] = edge[3];
pc = 2;
}
break;
}
case 1: {
uint64_t edge[] = {v[9], v[10]};
v[27] = edge[0];
v[28] = edge[1];
pc = 7;
break;
}
case 2: {
v[15] = (v[12] + v[12]) & UINT64_C(0xffffffffffffffff);
if (v[13] != 0) {
uint64_t edge[] = {v[11], v[15]};
v[16] = edge[0];
v[17] = edge[1];
pc = 3;
} else {
uint64_t edge[] = {v[11], v[15], v[14]};
v[18] = edge[0];
v[19] = edge[1];
v[20] = edge[2];
pc = 4;
}
break;
}
case 3: {
uint64_t edge[] = {v[16], v[17]};
v[27] = edge[0];
v[28] = edge[1];
pc = 7;
break;
}
case 4: {
v[21] = (v[19] + v[19]) & UINT64_C(0xffffffffffffffff);
if (v[20] != 0) {
uint64_t edge[] = {v[18], v[21]};
v[22] = edge[0];
v[23] = edge[1];
pc = 5;
} else {
uint64_t edge[] = {v[18], v[21]};
v[24] = edge[0];
v[25] = edge[1];
pc = 6;
}
break;
}
case 5: {
uint64_t edge[] = {v[22], v[23]};
v[27] = edge[0];
v[28] = edge[1];
pc = 7;
break;
}
case 6: {
v[26] = (v[25] + v[25]) & UINT64_C(0xffffffffffffffff);
uint64_t edge[] = {v[24], v[26]};
v[27] = edge[0];
v[28] = edge[1];
pc = 7;
break;
}
case 7: {
v[29] = fields[4];
v[30] = fields[4];
v[31] = (v[27] + v[28]) & UINT64_C(0xffffffffffffffff);
v[32] = (v[31] + v[30]) & UINT64_C(0xffffffffffffffff);
    registers[f0] = v[32];
return 0;
}
default: return 3;
} }
}
#include <stdint.h>
#include <stddef.h>
/* Disjoint arrays; status 0 success, 3 invalid state. */
uint32_t x86_body_59(uint64_t *registers, size_t register_count, uint64_t *flags, size_t flag_count, const uint64_t *fields, size_t field_count, uint64_t guest_pc, uint64_t *next_pc, uint32_t *next_pc_set, const uint8_t *memory, size_t memory_length, uint64_t memory_base) {
    if (!registers || !flags || !fields || !next_pc || !next_pc_set) return 3;
    (void)guest_pc;
    if (field_count != 6) return 3;
    if (fields[0] > UINT64_C(0x1f)) return 3;
    if (fields[1] > UINT64_C(0x1f)) return 3;
    if (fields[2] > UINT64_C(0x1f)) return 3;
    if (fields[3] > UINT64_C(0x1f)) return 3;
    if (fields[5] > UINT64_C(0x3)) return 3;
    if (fields[0] >= register_count) return 3;
    if (fields[0] >= register_count) return 3;
    if (fields[0] >= register_count) return 3;
    for (size_t i = 0; i < flag_count; ++i) if (flags[i] > 1) return 3;
    size_t f0 = (size_t)fields[0]; (void)f0;
    size_t f1 = (size_t)fields[1]; (void)f1;
    size_t f2 = (size_t)fields[2]; (void)f2;
    size_t f3 = (size_t)fields[3]; (void)f3;
    size_t f4 = (size_t)fields[4]; (void)f4;
    size_t f5 = (size_t)fields[5]; (void)f5;
uint64_t v[5] = {0}; (void)v;
size_t pc = 0;
for (;;) { switch (pc) {
case 0: {
v[0] = registers[f0] & UINT64_C(0xffffffffffffffff);
v[1] = registers[f0] & UINT64_C(0xffffffffffffffff);
    if (!memory || v[1] < memory_base || v[1] - memory_base > memory_length || memory_length - (v[1] - memory_base) < 8) return 3;
v[2] = ((uint64_t)memory[(size_t)(v[1] - memory_base) + 0] << 0) | ((uint64_t)memory[(size_t)(v[1] - memory_base) + 1] << 8) | ((uint64_t)memory[(size_t)(v[1] - memory_base) + 2] << 16) | ((uint64_t)memory[(size_t)(v[1] - memory_base) + 3] << 24) | ((uint64_t)memory[(size_t)(v[1] - memory_base) + 4] << 32) | ((uint64_t)memory[(size_t)(v[1] - memory_base) + 5] << 40) | ((uint64_t)memory[(size_t)(v[1] - memory_base) + 6] << 48) | ((uint64_t)memory[(size_t)(v[1] - memory_base) + 7] << 56);
v[3] = 0x8ULL;
v[4] = (v[0] + v[3]) & UINT64_C(0xffffffffffffffff);
    registers[f0] = v[4];
    if (*next_pc_set) return 3;
    *next_pc = v[2];
    *next_pc_set = 1;
return 0;
}
default: return 3;
} }
}
#include <string.h>
uint32_t fsl_x86(uint64_t *registers, size_t register_count, uint64_t *flags, size_t flag_count, const uint8_t *memory, size_t memory_length, uint64_t memory_base, size_t budget, uint64_t *exit_pc) {
if (!registers || !flags || !memory || !exit_pc || register_count != 17 || flag_count != 12 || registers[16] != 0 || budget == 0 || budget > 1000000 || memory_base > UINT64_MAX - memory_length) return 3;
for (size_t j=0;j<12;j++) if (flags[j] > 1 || (j>=6 && flags[j]!=1)) return 3;
uint64_t r[17], f[12]; memcpy(r, registers, sizeof r); memcpy(f, flags, sizeof f);
uint64_t pc=UINT64_C(0x401000);
for (size_t step=0;step<budget;step++) {
uint64_t next=0; uint32_t changed=0, status=0;
(void)next; (void)changed;
switch(pc) {
case UINT64_C(0x401000): { /* raw=488d0437 */
const uint64_t fields[6]={UINT64_C(0x0),UINT64_C(0x0),UINT64_C(0x7),UINT64_C(0x6),UINT64_C(0x0),UINT64_C(0x0)};
status=x86_body_58(r,17,f,12,fields,6);
if (status) return status;
pc=changed?next:UINT64_C(0x401004); break;
}
case UINT64_C(0x401004): { /* raw=c3 */
const uint64_t fields[6]={UINT64_C(0x4),UINT64_C(0x0),UINT64_C(0x0),UINT64_C(0x0),UINT64_C(0x0),UINT64_C(0x0)};
status=x86_body_59(r,17,f,12,fields,6,pc,&next,&changed,memory,memory_length,memory_base);
if (status) return status;
if (!changed) return 3; memcpy(registers,r,sizeof r); memcpy(flags,f,sizeof f); *exit_pc=next; return 0;
}
default: return 3;
}
}
return 3;
}

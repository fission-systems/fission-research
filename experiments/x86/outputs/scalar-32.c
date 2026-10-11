/* x86 mode=32 input-sha256=8c48c0a3418ee5d8f73ea7d2400ac2ee35a57de3ac5b768efe0ce209591c25c9 package-sha256=0423223eaf7238013177aceb9b7c09f7448a682752668e3124ab9c651b46515a; owned decoder owned-x86-v1.
 * Explicit state function: GPR[0..16]=RAX,RCX,RDX,RBX,RSP,RBP,RSI,RDI,R8..R15; GPR[16]=0.
 * flags=CF,PF,ZF,SF,OF,AF then six known bits. Unknown AF is not observable.
 * Disjoint valid storage required in C. Bounded byte memory, flat SS.base=0, no MMU/fault model.
 * Status 0 commits state and return PC; status 3 preserves caller storage. */
#include <stdint.h>
#include <stddef.h>
/* Disjoint arrays; status 0 success, 3 invalid state. */
uint32_t x86_body_21(uint64_t *registers, size_t register_count, uint64_t *flags, size_t flag_count, const uint64_t *fields, size_t field_count) {
    if (!registers || !flags || !fields) return 3;
    if (field_count != 6) return 3;
    if (fields[0] > UINT64_C(0x1f)) return 3;
    if (fields[1] > UINT64_C(0x1f)) return 3;
    if (fields[2] > UINT64_C(0x1f)) return 3;
    if (fields[3] > UINT64_C(0x1f)) return 3;
    if (fields[5] > UINT64_C(0x3)) return 3;
    if (fields[0] >= register_count) return 3;
    if (fields[0] >= register_count) return 3;
    for (size_t i = 0; i < flag_count; ++i) if (flags[i] > 1) return 3;
    size_t f0 = (size_t)fields[0]; (void)f0;
    size_t f1 = (size_t)fields[1]; (void)f1;
    size_t f2 = (size_t)fields[2]; (void)f2;
    size_t f3 = (size_t)fields[3]; (void)f3;
    size_t f4 = (size_t)fields[4]; (void)f4;
    size_t f5 = (size_t)fields[5]; (void)f5;
uint64_t v[3] = {0}; (void)v;
size_t pc = 0;
for (;;) { switch (pc) {
case 0: {
v[0] = registers[f0] & UINT64_C(0xffffffff);
v[1] = fields[4];
v[2] = (v[1]) & 0xffffffffULL;
    registers[f0] = v[2];
return 0;
}
default: return 3;
} }
}
#include <stdint.h>
#include <stddef.h>
/* Disjoint arrays; status 0 success, 3 invalid state. */
uint32_t x86_body_22(uint64_t *registers, size_t register_count, uint64_t *flags, size_t flag_count, const uint64_t *fields, size_t field_count) {
    if (!registers || !flags || !fields) return 3;
    if (field_count != 6) return 3;
    if (fields[0] > UINT64_C(0x1f)) return 3;
    if (fields[1] > UINT64_C(0x1f)) return 3;
    if (fields[2] > UINT64_C(0x1f)) return 3;
    if (fields[3] > UINT64_C(0x1f)) return 3;
    if (fields[5] > UINT64_C(0x3)) return 3;
    if (fields[0] >= register_count) return 3;
    if (fields[1] >= register_count) return 3;
    if (flag_count <= 0) return 3;
    if (flag_count <= 4) return 3;
    if (flag_count <= 5) return 3;
    if (flag_count <= 11) return 3;
    if (flag_count <= 1) return 3;
    if (flag_count <= 2) return 3;
    if (flag_count <= 3) return 3;
    if (flag_count <= 6) return 3;
    if (flag_count <= 7) return 3;
    if (flag_count <= 8) return 3;
    if (flag_count <= 9) return 3;
    if (flag_count <= 10) return 3;
    if (fields[0] >= register_count) return 3;
    for (size_t i = 0; i < flag_count; ++i) if (flags[i] > 1) return 3;
    size_t f0 = (size_t)fields[0]; (void)f0;
    size_t f1 = (size_t)fields[1]; (void)f1;
    size_t f2 = (size_t)fields[2]; (void)f2;
    size_t f3 = (size_t)fields[3]; (void)f3;
    size_t f4 = (size_t)fields[4]; (void)f4;
    size_t f5 = (size_t)fields[5]; (void)f5;
uint64_t v[54] = {0}; (void)v;
size_t pc = 0;
for (;;) { switch (pc) {
case 0: {
v[0] = registers[f0] & UINT64_C(0xffffffff);
v[1] = registers[f1] & UINT64_C(0xffffffff);
v[2] = (v[0] + v[1]) & UINT64_C(0xffffffff);
v[3] = 0x0ULL;
v[4] = 0x0ULL;
v[5] = 0x1ULL;
v[6] = (v[2] == v[3]);
v[7] = 0x80000000ULL;
v[8] = (v[2] & v[7]) & UINT64_C(0xffffffff);
v[9] = (v[8] == v[7]);
v[10] = 0x1ULL;
v[11] = (v[2] & v[10]) & UINT64_C(0xffffffff);
v[12] = (v[11] == v[10]);
v[13] = 0x2ULL;
v[14] = (v[2] & v[13]) & UINT64_C(0xffffffff);
v[15] = (v[14] == v[13]);
v[16] = 0x4ULL;
v[17] = (v[2] & v[16]) & UINT64_C(0xffffffff);
v[18] = (v[17] == v[16]);
v[19] = 0x8ULL;
v[20] = (v[2] & v[19]) & UINT64_C(0xffffffff);
v[21] = (v[20] == v[19]);
v[22] = 0x10ULL;
v[23] = (v[2] & v[22]) & UINT64_C(0xffffffff);
v[24] = (v[23] == v[22]);
v[25] = 0x20ULL;
v[26] = (v[2] & v[25]) & UINT64_C(0xffffffff);
v[27] = (v[26] == v[25]);
v[28] = 0x40ULL;
v[29] = (v[2] & v[28]) & UINT64_C(0xffffffff);
v[30] = (v[29] == v[28]);
v[31] = 0x80ULL;
v[32] = (v[2] & v[31]) & UINT64_C(0xffffffff);
v[33] = (v[32] == v[31]);
v[34] = (v[12] ^ v[15]) & UINT64_C(0x1);
v[35] = (v[34] ^ v[18]) & UINT64_C(0x1);
v[36] = (v[35] ^ v[21]) & UINT64_C(0x1);
v[37] = (v[36] ^ v[24]) & UINT64_C(0x1);
v[38] = (v[37] ^ v[27]) & UINT64_C(0x1);
v[39] = (v[38] ^ v[30]) & UINT64_C(0x1);
v[40] = (v[39] ^ v[33]) & UINT64_C(0x1);
v[41] = (v[40] == v[4]);
v[42] = v[0] > UINT64_C(0xffffffff) - v[1];
v[43] = (v[0] ^ v[1]) & UINT64_C(0xffffffff);
v[44] = (v[0] ^ v[2]) & UINT64_C(0xffffffff);
v[45] = 0xffffffffULL;
v[46] = (v[43] ^ v[45]) & UINT64_C(0xffffffff);
v[47] = (v[46] & v[44]) & UINT64_C(0xffffffff);
v[48] = (v[47] & v[7]) & UINT64_C(0xffffffff);
v[49] = (v[48] == v[7]);
v[50] = (v[43] ^ v[2]) & UINT64_C(0xffffffff);
v[51] = 0x10ULL;
v[52] = (v[50] & v[51]) & UINT64_C(0xffffffff);
v[53] = (v[52] == v[51]);
    flags[0] = v[42];
    flags[4] = v[49];
    flags[5] = v[53];
    flags[11] = v[5];
    flags[1] = v[41];
    flags[2] = v[6];
    flags[3] = v[9];
    flags[6] = v[5];
    flags[7] = v[5];
    flags[8] = v[5];
    flags[9] = v[5];
    flags[10] = v[5];
    registers[f0] = v[2];
return 0;
}
default: return 3;
} }
}
#include <stdint.h>
#include <stddef.h>
/* Disjoint arrays; status 0 success, 3 invalid state. */
uint32_t x86_body_39(uint64_t *registers, size_t register_count, uint64_t *flags, size_t flag_count, const uint64_t *fields, size_t field_count, uint64_t guest_pc, uint64_t *next_pc, uint32_t *next_pc_set, const uint8_t *memory, size_t memory_length, uint64_t memory_base) {
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
    for (size_t i = 0; i < flag_count; ++i) if (flags[i] > 1) return 3;
    size_t f0 = (size_t)fields[0]; (void)f0;
    size_t f1 = (size_t)fields[1]; (void)f1;
    size_t f2 = (size_t)fields[2]; (void)f2;
    size_t f3 = (size_t)fields[3]; (void)f3;
    size_t f4 = (size_t)fields[4]; (void)f4;
    size_t f5 = (size_t)fields[5]; (void)f5;
uint64_t v[6] = {0}; (void)v;
size_t pc = 0;
for (;;) { switch (pc) {
case 0: {
v[0] = registers[f0] & UINT64_C(0xffffffff);
v[1] = (v[0]) & 0xffffffffffffffffULL;
    if (!memory || v[1] < memory_base || v[1] - memory_base > memory_length || memory_length - (v[1] - memory_base) < 4) return 3;
v[2] = ((uint64_t)memory[(size_t)(v[1] - memory_base) + 0] << 0) | ((uint64_t)memory[(size_t)(v[1] - memory_base) + 1] << 8) | ((uint64_t)memory[(size_t)(v[1] - memory_base) + 2] << 16) | ((uint64_t)memory[(size_t)(v[1] - memory_base) + 3] << 24);
v[3] = 0x4ULL;
v[4] = (v[0] + v[3]) & UINT64_C(0xffffffff);
    registers[f0] = v[4];
v[5] = (v[2]) & 0xffffffffffffffffULL;
    if (*next_pc_set) return 3;
    *next_pc = v[5];
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
uint64_t pc=UINT64_C(0x1000);
for (size_t step=0;step<budget;step++) {
uint64_t next=0; uint32_t changed=0, status=0;
(void)next; (void)changed;
switch(pc) {
case UINT64_C(0x1000): { /* raw=b807000000 */
const uint64_t fields[6]={UINT64_C(0x0),UINT64_C(0x0),UINT64_C(0x0),UINT64_C(0x0),UINT64_C(0x7),UINT64_C(0x0)};
status=x86_body_21(r,17,f,12,fields,6);
if (status) return status;
pc=changed?next:UINT64_C(0x1005); break;
}
case UINT64_C(0x1005): { /* raw=bb05000000 */
const uint64_t fields[6]={UINT64_C(0x3),UINT64_C(0x0),UINT64_C(0x0),UINT64_C(0x0),UINT64_C(0x5),UINT64_C(0x0)};
status=x86_body_21(r,17,f,12,fields,6);
if (status) return status;
pc=changed?next:UINT64_C(0x100a); break;
}
case UINT64_C(0x100a): { /* raw=01d8 */
const uint64_t fields[6]={UINT64_C(0x0),UINT64_C(0x3),UINT64_C(0x0),UINT64_C(0x0),UINT64_C(0x0),UINT64_C(0x0)};
status=x86_body_22(r,17,f,12,fields,6);
if (status) return status;
pc=changed?next:UINT64_C(0x100c); break;
}
case UINT64_C(0x100c): { /* raw=c3 */
const uint64_t fields[6]={UINT64_C(0x4),UINT64_C(0x0),UINT64_C(0x0),UINT64_C(0x0),UINT64_C(0x0),UINT64_C(0x0)};
status=x86_body_39(r,17,f,12,fields,6,pc,&next,&changed,memory,memory_length,memory_base);
if (status) return status;
if (!changed) return 3; memcpy(registers,r,sizeof r); memcpy(flags,f,sizeof f); *exit_pc=next; return 0;
}
default: return 3;
}
}
return 3;
}

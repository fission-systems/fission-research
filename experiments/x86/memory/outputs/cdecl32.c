/* x86 mode=32 input-sha256=03eb65ee1278aaea9e96db8222739d1ba135fbd627cad205af3cafa49abc3a34 package-sha256=c4cc794b0e8f103591df300da4fc1dcfa7edfb78dee9e0e015a7ee0385da9dad; owned decoder owned-x86-v1.
 * Explicit state function: GPR[0..16]=RAX,RCX,RDX,RBX,RSP,RBP,RSI,RDI,R8..R15; GPR[16]=0.
 * flags=CF,PF,ZF,SF,OF,AF then six known bits. Unknown AF is not observable.
 * Disjoint valid storage required in C. Bounded byte memory, flat SS.base=0, no MMU/fault model.
 * Status 0 commits state and return PC; status 3 preserves caller storage. */
/* binary file-sha256=1e5840c7021534dde18c4871cedafb9a55c885be45549b8884cb709277a7f0fc file-offset=4096 */
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
#include <stdint.h>
#include <stddef.h>
/* Disjoint arrays; status 0 success, 3 invalid state. */
uint32_t x86_body_91(uint64_t *registers, size_t register_count, uint64_t *flags, size_t flag_count, const uint64_t *fields, size_t field_count, const uint8_t *memory, size_t memory_length, uint64_t memory_base) {
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
    if (fields[0] >= register_count) return 3;
    for (size_t i = 0; i < flag_count; ++i) if (flags[i] > 1) return 3;
    size_t f0 = (size_t)fields[0]; (void)f0;
    size_t f1 = (size_t)fields[1]; (void)f1;
    size_t f2 = (size_t)fields[2]; (void)f2;
    size_t f3 = (size_t)fields[3]; (void)f3;
    size_t f4 = (size_t)fields[4]; (void)f4;
    size_t f5 = (size_t)fields[5]; (void)f5;
uint64_t v[36] = {0}; (void)v;
size_t pc = 0;
for (;;) { switch (pc) {
case 0: {
v[0] = registers[f2] & UINT64_C(0xffffffff);
v[1] = registers[f3] & UINT64_C(0xffffffff);
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
v[15] = (v[12] + v[12]) & UINT64_C(0xffffffff);
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
v[21] = (v[19] + v[19]) & UINT64_C(0xffffffff);
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
v[26] = (v[25] + v[25]) & UINT64_C(0xffffffff);
uint64_t edge[] = {v[24], v[26]};
v[27] = edge[0];
v[28] = edge[1];
pc = 7;
break;
}
case 7: {
v[29] = fields[4];
v[30] = (v[29]) & 0xffffffffULL;
v[31] = (v[27] + v[28]) & UINT64_C(0xffffffff);
v[32] = (v[31] + v[30]) & UINT64_C(0xffffffff);
v[33] = (v[32]) & 0xffffffffffffffffULL;
    if (!memory || v[33] < memory_base || v[33] - memory_base > memory_length || memory_length - (v[33] - memory_base) < 4) return 3;
v[34] = ((uint64_t)memory[(size_t)(v[33] - memory_base) + 0] << 0) | ((uint64_t)memory[(size_t)(v[33] - memory_base) + 1] << 8) | ((uint64_t)memory[(size_t)(v[33] - memory_base) + 2] << 16) | ((uint64_t)memory[(size_t)(v[33] - memory_base) + 3] << 24);
v[35] = registers[f0] & UINT64_C(0xffffffff);
    registers[f0] = v[34];
return 0;
}
default: return 3;
} }
}
#include <stdint.h>
#include <stddef.h>
/* Disjoint arrays; status 0 success, 3 invalid state. */
uint32_t x86_body_92(uint64_t *registers, size_t register_count, uint64_t *flags, size_t flag_count, const uint64_t *fields, size_t field_count, const uint8_t *memory, size_t memory_length, uint64_t memory_base) {
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
uint64_t v[88] = {0}; (void)v;
size_t pc = 0;
for (;;) { switch (pc) {
case 0: {
v[0] = registers[f2] & UINT64_C(0xffffffff);
v[1] = registers[f3] & UINT64_C(0xffffffff);
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
v[15] = (v[12] + v[12]) & UINT64_C(0xffffffff);
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
v[21] = (v[19] + v[19]) & UINT64_C(0xffffffff);
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
v[26] = (v[25] + v[25]) & UINT64_C(0xffffffff);
uint64_t edge[] = {v[24], v[26]};
v[27] = edge[0];
v[28] = edge[1];
pc = 7;
break;
}
case 7: {
v[29] = fields[4];
v[30] = (v[29]) & 0xffffffffULL;
v[31] = (v[27] + v[28]) & UINT64_C(0xffffffff);
v[32] = (v[31] + v[30]) & UINT64_C(0xffffffff);
v[33] = (v[32]) & 0xffffffffffffffffULL;
    if (!memory || v[33] < memory_base || v[33] - memory_base > memory_length || memory_length - (v[33] - memory_base) < 4) return 3;
v[34] = ((uint64_t)memory[(size_t)(v[33] - memory_base) + 0] << 0) | ((uint64_t)memory[(size_t)(v[33] - memory_base) + 1] << 8) | ((uint64_t)memory[(size_t)(v[33] - memory_base) + 2] << 16) | ((uint64_t)memory[(size_t)(v[33] - memory_base) + 3] << 24);
v[35] = registers[f0] & UINT64_C(0xffffffff);
v[36] = (v[35] + v[34]) & UINT64_C(0xffffffff);
v[37] = 0x0ULL;
v[38] = 0x0ULL;
v[39] = 0x1ULL;
v[40] = (v[36] == v[37]);
v[41] = 0x80000000ULL;
v[42] = (v[36] & v[41]) & UINT64_C(0xffffffff);
v[43] = (v[42] == v[41]);
v[44] = 0x1ULL;
v[45] = (v[36] & v[44]) & UINT64_C(0xffffffff);
v[46] = (v[45] == v[44]);
v[47] = 0x2ULL;
v[48] = (v[36] & v[47]) & UINT64_C(0xffffffff);
v[49] = (v[48] == v[47]);
v[50] = 0x4ULL;
v[51] = (v[36] & v[50]) & UINT64_C(0xffffffff);
v[52] = (v[51] == v[50]);
v[53] = 0x8ULL;
v[54] = (v[36] & v[53]) & UINT64_C(0xffffffff);
v[55] = (v[54] == v[53]);
v[56] = 0x10ULL;
v[57] = (v[36] & v[56]) & UINT64_C(0xffffffff);
v[58] = (v[57] == v[56]);
v[59] = 0x20ULL;
v[60] = (v[36] & v[59]) & UINT64_C(0xffffffff);
v[61] = (v[60] == v[59]);
v[62] = 0x40ULL;
v[63] = (v[36] & v[62]) & UINT64_C(0xffffffff);
v[64] = (v[63] == v[62]);
v[65] = 0x80ULL;
v[66] = (v[36] & v[65]) & UINT64_C(0xffffffff);
v[67] = (v[66] == v[65]);
v[68] = (v[46] ^ v[49]) & UINT64_C(0x1);
v[69] = (v[68] ^ v[52]) & UINT64_C(0x1);
v[70] = (v[69] ^ v[55]) & UINT64_C(0x1);
v[71] = (v[70] ^ v[58]) & UINT64_C(0x1);
v[72] = (v[71] ^ v[61]) & UINT64_C(0x1);
v[73] = (v[72] ^ v[64]) & UINT64_C(0x1);
v[74] = (v[73] ^ v[67]) & UINT64_C(0x1);
v[75] = (v[74] == v[38]);
v[76] = v[35] > UINT64_C(0xffffffff) - v[34];
v[77] = (v[35] ^ v[34]) & UINT64_C(0xffffffff);
v[78] = (v[35] ^ v[36]) & UINT64_C(0xffffffff);
v[79] = 0xffffffffULL;
v[80] = (v[77] ^ v[79]) & UINT64_C(0xffffffff);
v[81] = (v[80] & v[78]) & UINT64_C(0xffffffff);
v[82] = (v[81] & v[41]) & UINT64_C(0xffffffff);
v[83] = (v[82] == v[41]);
v[84] = (v[77] ^ v[36]) & UINT64_C(0xffffffff);
v[85] = 0x10ULL;
v[86] = (v[84] & v[85]) & UINT64_C(0xffffffff);
v[87] = (v[86] == v[85]);
    flags[0] = v[76];
    flags[4] = v[83];
    flags[5] = v[87];
    flags[11] = v[39];
    flags[1] = v[75];
    flags[2] = v[40];
    flags[3] = v[43];
    flags[6] = v[39];
    flags[7] = v[39];
    flags[8] = v[39];
    flags[9] = v[39];
    flags[10] = v[39];
    registers[f0] = v[36];
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
case UINT64_C(0x401000): { /* raw=8b442408 */
const uint64_t fields[6]={UINT64_C(0x0),UINT64_C(0x0),UINT64_C(0x4),UINT64_C(0x10),UINT64_C(0x8),UINT64_C(0x0)};
status=x86_body_91(r,17,f,12,fields,6,memory,memory_length,memory_base);
if (status) return status;
pc=changed?next:UINT64_C(0x401004); break;
}
case UINT64_C(0x401004): { /* raw=03442404 */
const uint64_t fields[6]={UINT64_C(0x0),UINT64_C(0x0),UINT64_C(0x4),UINT64_C(0x10),UINT64_C(0x4),UINT64_C(0x0)};
status=x86_body_92(r,17,f,12,fields,6,memory,memory_length,memory_base);
if (status) return status;
pc=changed?next:UINT64_C(0x401008); break;
}
case UINT64_C(0x401008): { /* raw=c3 */
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

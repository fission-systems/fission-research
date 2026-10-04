// sequence input-sha256=3805c5efdfd4f7e35d5548b580716a918ba05935ee599767d3d9cab61ba31880 package-sha256=39c3146c31657708041b1e7cd4207876f3bb78c41c2fbf3106beec467f7154f1 steps=3
#include <stdint.h>
#include <stddef.h>
/* Disjoint arrays; status 0 success, 3 invalid state. */
uint32_t fsl_sequence_body_0(uint64_t *registers, size_t register_count, uint64_t *flags, size_t flag_count, const uint64_t *fields, size_t field_count) {
    if (!registers || !flags || !fields) return 3;
    if (field_count != 3) return 3;
    if (fields[0] > UINT64_C(0xf)) return 3;
    if (fields[1] > UINT64_C(0xf)) return 3;
    if (fields[2] > UINT64_C(0xf)) return 3;
    if (fields[0] >= register_count) return 3;
    if (fields[0] >= register_count) return 3;
    if (fields[2] >= register_count) return 3;
    if (fields[1] >= register_count) return 3;
    if (flag_count <= 0) return 3;
    if (fields[1] >= register_count) return 3;
    if (flag_count <= 0) return 3;
    if (fields[1] >= register_count) return 3;
    if (flag_count <= 1) return 3;
    if (flag_count <= 0) return 3;
    if (flag_count <= 2) return 3;
    for (size_t i = 0; i < flag_count; ++i) if (flags[i] > 1) return 3;
    size_t f0 = (size_t)fields[0]; (void)f0;
    size_t f1 = (size_t)fields[1]; (void)f1;
    size_t f2 = (size_t)fields[2]; (void)f2;
uint64_t v[18] = {0}; (void)v;
size_t pc = 0;
for (;;) { switch (pc) {
case 0: {
v[0] = registers[f0] & UINT64_C(0xff);
v[1] = (((v[0]) ^ 0x80ULL) - 0x80ULL) & 0xffffffffULL;
v[2] = registers[f0] & UINT64_C(0xff);
v[3] = (v[2]) & 0xffffffffffffffffULL;
    registers[f2] = v[3];
v[4] = 0x0ULL;
v[5] = ((v[1] ^ 0x80000000ULL) < (v[4] ^ 0x80000000ULL));
if (v[5] != 0) {
uint64_t edge[] = {v[1]};
v[6] = edge[0];
pc = 1;
} else {
uint64_t edge[] = {v[1]};
v[10] = edge[0];
pc = 2;
}
break;
}
case 1: {
v[7] = (v[6]) & 0xffffULL;
v[8] = (((v[7]) ^ 0x8000ULL) - 0x8000ULL) & 0xffffffffULL;
    registers[f1] = v[8];
v[9] = 0x1ULL;
    flags[0] = v[9];
uint64_t edge[] = {v[8]};
v[14] = edge[0];
pc = 3;
break;
}
case 2: {
v[11] = (v[10]) & 0xffULL;
v[12] = (((v[11]) ^ 0x80ULL) - 0x80ULL) & 0xffffffffULL;
    registers[f1] = v[12];
v[13] = 0x0ULL;
    flags[0] = v[13];
uint64_t edge[] = {v[12]};
v[14] = edge[0];
pc = 3;
break;
}
case 3: {
v[15] = registers[f1] & UINT64_C(0xffffffff);
v[16] = (v[15] == v[14]);
    flags[1] = v[16];
v[17] = flags[0] & UINT64_C(0x1);
    flags[2] = v[17];
return 0;
}
default: return 3;
} }
}

uint32_t fsl_sequence(uint64_t *registers, size_t register_count, uint64_t *flags, size_t flag_count) {
  if (!registers || !flags || register_count != 3 || flag_count != 3) return 3;
  for (size_t i=0;i<flag_count;++i) if (flags[i]>1) return 3;
  uint64_t next_registers[3] = {0};
  uint64_t next_flags[3] = {0};
  for (size_t i=0;i<register_count;++i) next_registers[i]=registers[i];
  for (size_t i=0;i<flag_count;++i) next_flags[i]=flags[i];
// step=0 address=0x1000 offset=0 length=4 body=0 raw=10a20000
  { const uint64_t fields[3] = {0x0ULL, 0x1ULL, 0x2ULL};
    uint32_t status=fsl_sequence_body_0(next_registers, 3, next_flags, 3, fields, 3);
    if (status!=0) return status; }
// step=1 address=0x1004 offset=4 length=4 body=0 raw=21a00000
  { const uint64_t fields[3] = {0x1ULL, 0x2ULL, 0x0ULL};
    uint32_t status=fsl_sequence_body_0(next_registers, 3, next_flags, 3, fields, 3);
    if (status!=0) return status; }
// step=2 address=0x1008 offset=8 length=4 body=0 raw=02a10000
  { const uint64_t fields[3] = {0x2ULL, 0x0ULL, 0x1ULL};
    uint32_t status=fsl_sequence_body_0(next_registers, 3, next_flags, 3, fields, 3);
    if (status!=0) return status; }
  for (size_t i=0;i<register_count;++i) registers[i]=next_registers[i];
  for (size_t i=0;i<flag_count;++i) flags[i]=next_flags[i];
  return 0;
}

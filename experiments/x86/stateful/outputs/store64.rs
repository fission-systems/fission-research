/* Mutable window transaction; disjoint scratch has exact memory length. Scratch contents are unspecified on failure. */
/* x86 mode=64 input-sha256=25628eedb7da194d68399b5a9fb1e8a727fc6dd0c5733338f93ead2f142e6964 package-sha256=9c9d8479202b7bd842f89ae0d8c17ef1c4d6b4a51c74d1e78b3138ca2fbbe10b; owned decoder owned-x86-v1.
 * Explicit state function: GPR[0..16]=RAX,RCX,RDX,RBX,RSP,RBP,RSI,RDI,R8..R15; GPR[16]=0.
 * flags=CF,PF,ZF,SF,OF,AF then six known bits. Unknown AF is not observable.
 * Disjoint valid storage required in C. Bounded byte memory, flat SS.base=0, no MMU/fault model.
 * Status 0 commits state and return PC; status 3 preserves caller storage. */
/* binary file-sha256=cd9a6bf90f2e0d2586e87f32ea95fc5c0c20ea48c3e6250297030dd762053ab6 file-offset=4096 */
pub fn x86_body_59(registers: &mut [u64], flags: &mut [u64], fields: &[u64], guest_pc: u64, next_pc: &mut u64, next_pc_set: &mut bool, memory: &[u8], memory_base: u64) -> u32 {
    let _ = guest_pc;
    if fields.len() != 6 { return 3; }
    if fields[0] > 0x1fu64 { return 3; }
    if fields[1] > 0x1fu64 { return 3; }
    if fields[2] > 0x1fu64 { return 3; }
    if fields[3] > 0x1fu64 { return 3; }
    if fields[5] > 0x3u64 { return 3; }
    if fields[0] >= registers.len() as u64 { return 3; }
    if fields[0] >= registers.len() as u64 { return 3; }
    if fields[0] >= registers.len() as u64 { return 3; }
    if flags.iter().any(|&value| value > 1) { return 3; }
    let _f0 = fields[0] as usize;
    let _f1 = fields[1] as usize;
    let _f2 = fields[2] as usize;
    let _f3 = fields[3] as usize;
    let _f4 = fields[4] as usize;
    let _f5 = fields[5] as usize;
let mut v = [0u64; 5];
let pc = 0usize;
loop { match pc {
0 => {
v[0] = registers[_f0] & 0xffffffffffffffffu64;
v[1] = registers[_f0] & 0xffffffffffffffffu64;
    if v[1] < memory_base || v[1] - memory_base > memory.len() as u64 || (memory.len() as u64) - (v[1] - memory_base) < 8 { return 3; }
v[2] = ((memory[(v[1] - memory_base) as usize + 0] as u64) << 0) | ((memory[(v[1] - memory_base) as usize + 1] as u64) << 8) | ((memory[(v[1] - memory_base) as usize + 2] as u64) << 16) | ((memory[(v[1] - memory_base) as usize + 3] as u64) << 24) | ((memory[(v[1] - memory_base) as usize + 4] as u64) << 32) | ((memory[(v[1] - memory_base) as usize + 5] as u64) << 40) | ((memory[(v[1] - memory_base) as usize + 6] as u64) << 48) | ((memory[(v[1] - memory_base) as usize + 7] as u64) << 56);
v[3] = 0x8u64;
v[4] = v[0].wrapping_add(v[3]) & 0xffffffffffffffffu64;
    registers[_f0] = v[4];
    if *next_pc_set { return 3; }
    *next_pc = v[2];
    *next_pc_set = true;
return 0;
}
_ => return 3,
} }
}
pub fn x86_body_119(registers: &mut [u64], flags: &mut [u64], fields: &[u64], memory: &[u8], memory_base: u64) -> u32 {
    if fields.len() != 6 { return 3; }
    if fields[0] > 0x1fu64 { return 3; }
    if fields[1] > 0x1fu64 { return 3; }
    if fields[2] > 0x1fu64 { return 3; }
    if fields[3] > 0x1fu64 { return 3; }
    if fields[5] > 0x3u64 { return 3; }
    if fields[2] >= registers.len() as u64 { return 3; }
    if fields[3] >= registers.len() as u64 { return 3; }
    if fields[0] >= registers.len() as u64 { return 3; }
    if fields[0] >= registers.len() as u64 { return 3; }
    if flags.iter().any(|&value| value > 1) { return 3; }
    let _f0 = fields[0] as usize;
    let _f1 = fields[1] as usize;
    let _f2 = fields[2] as usize;
    let _f3 = fields[3] as usize;
    let _f4 = fields[4] as usize;
    let _f5 = fields[5] as usize;
let mut v = [0u64; 35];
let mut pc = 0usize;
loop { match pc {
0 => {
v[0] = registers[_f2] & 0xffffffffffffffffu64;
v[1] = registers[_f3] & 0xffffffffffffffffu64;
v[2] = fields[5];
v[3] = 0x0u64;
v[4] = 0x1u64;
v[5] = 0x2u64;
v[6] = (v[2] == v[3]) as u64;
v[7] = (v[2] == v[4]) as u64;
v[8] = (v[2] == v[5]) as u64;
if v[6] != 0 {
let edge = [v[0], v[1]];
v[9] = edge[0];
v[10] = edge[1];
pc = 1;
} else {
let edge = [v[0], v[1], v[7], v[8]];
v[11] = edge[0];
v[12] = edge[1];
v[13] = edge[2];
v[14] = edge[3];
pc = 2;
}
}
1 => {
let edge = [v[9], v[10]];
v[27] = edge[0];
v[28] = edge[1];
pc = 7;
}
2 => {
v[15] = v[12].wrapping_add(v[12]) & 0xffffffffffffffffu64;
if v[13] != 0 {
let edge = [v[11], v[15]];
v[16] = edge[0];
v[17] = edge[1];
pc = 3;
} else {
let edge = [v[11], v[15], v[14]];
v[18] = edge[0];
v[19] = edge[1];
v[20] = edge[2];
pc = 4;
}
}
3 => {
let edge = [v[16], v[17]];
v[27] = edge[0];
v[28] = edge[1];
pc = 7;
}
4 => {
v[21] = v[19].wrapping_add(v[19]) & 0xffffffffffffffffu64;
if v[20] != 0 {
let edge = [v[18], v[21]];
v[22] = edge[0];
v[23] = edge[1];
pc = 5;
} else {
let edge = [v[18], v[21]];
v[24] = edge[0];
v[25] = edge[1];
pc = 6;
}
}
5 => {
let edge = [v[22], v[23]];
v[27] = edge[0];
v[28] = edge[1];
pc = 7;
}
6 => {
v[26] = v[25].wrapping_add(v[25]) & 0xffffffffffffffffu64;
let edge = [v[24], v[26]];
v[27] = edge[0];
v[28] = edge[1];
pc = 7;
}
7 => {
v[29] = fields[4];
v[30] = fields[4];
v[31] = v[27].wrapping_add(v[28]) & 0xffffffffffffffffu64;
v[32] = v[31].wrapping_add(v[30]) & 0xffffffffffffffffu64;
    if v[32] < memory_base || v[32] - memory_base > memory.len() as u64 || (memory.len() as u64) - (v[32] - memory_base) < 8 { return 3; }
v[33] = ((memory[(v[32] - memory_base) as usize + 0] as u64) << 0) | ((memory[(v[32] - memory_base) as usize + 1] as u64) << 8) | ((memory[(v[32] - memory_base) as usize + 2] as u64) << 16) | ((memory[(v[32] - memory_base) as usize + 3] as u64) << 24) | ((memory[(v[32] - memory_base) as usize + 4] as u64) << 32) | ((memory[(v[32] - memory_base) as usize + 5] as u64) << 40) | ((memory[(v[32] - memory_base) as usize + 6] as u64) << 48) | ((memory[(v[32] - memory_base) as usize + 7] as u64) << 56);
v[34] = registers[_f0] & 0xffffffffffffffffu64;
    registers[_f0] = v[33];
return 0;
}
_ => return 3,
} }
}
pub fn x86_body_120(registers: &mut [u64], flags: &mut [u64], fields: &[u64], memory: &[u8], memory_base: u64) -> u32 {
    if fields.len() != 6 { return 3; }
    if fields[0] > 0x1fu64 { return 3; }
    if fields[1] > 0x1fu64 { return 3; }
    if fields[2] > 0x1fu64 { return 3; }
    if fields[3] > 0x1fu64 { return 3; }
    if fields[5] > 0x3u64 { return 3; }
    if fields[2] >= registers.len() as u64 { return 3; }
    if fields[3] >= registers.len() as u64 { return 3; }
    if fields[0] >= registers.len() as u64 { return 3; }
    if flags.len() <= 0 { return 3; }
    if flags.len() <= 4 { return 3; }
    if flags.len() <= 5 { return 3; }
    if flags.len() <= 11 { return 3; }
    if flags.len() <= 1 { return 3; }
    if flags.len() <= 2 { return 3; }
    if flags.len() <= 3 { return 3; }
    if flags.len() <= 6 { return 3; }
    if flags.len() <= 7 { return 3; }
    if flags.len() <= 8 { return 3; }
    if flags.len() <= 9 { return 3; }
    if flags.len() <= 10 { return 3; }
    if fields[0] >= registers.len() as u64 { return 3; }
    if flags.iter().any(|&value| value > 1) { return 3; }
    let _f0 = fields[0] as usize;
    let _f1 = fields[1] as usize;
    let _f2 = fields[2] as usize;
    let _f3 = fields[3] as usize;
    let _f4 = fields[4] as usize;
    let _f5 = fields[5] as usize;
let mut v = [0u64; 87];
let mut pc = 0usize;
loop { match pc {
0 => {
v[0] = registers[_f2] & 0xffffffffffffffffu64;
v[1] = registers[_f3] & 0xffffffffffffffffu64;
v[2] = fields[5];
v[3] = 0x0u64;
v[4] = 0x1u64;
v[5] = 0x2u64;
v[6] = (v[2] == v[3]) as u64;
v[7] = (v[2] == v[4]) as u64;
v[8] = (v[2] == v[5]) as u64;
if v[6] != 0 {
let edge = [v[0], v[1]];
v[9] = edge[0];
v[10] = edge[1];
pc = 1;
} else {
let edge = [v[0], v[1], v[7], v[8]];
v[11] = edge[0];
v[12] = edge[1];
v[13] = edge[2];
v[14] = edge[3];
pc = 2;
}
}
1 => {
let edge = [v[9], v[10]];
v[27] = edge[0];
v[28] = edge[1];
pc = 7;
}
2 => {
v[15] = v[12].wrapping_add(v[12]) & 0xffffffffffffffffu64;
if v[13] != 0 {
let edge = [v[11], v[15]];
v[16] = edge[0];
v[17] = edge[1];
pc = 3;
} else {
let edge = [v[11], v[15], v[14]];
v[18] = edge[0];
v[19] = edge[1];
v[20] = edge[2];
pc = 4;
}
}
3 => {
let edge = [v[16], v[17]];
v[27] = edge[0];
v[28] = edge[1];
pc = 7;
}
4 => {
v[21] = v[19].wrapping_add(v[19]) & 0xffffffffffffffffu64;
if v[20] != 0 {
let edge = [v[18], v[21]];
v[22] = edge[0];
v[23] = edge[1];
pc = 5;
} else {
let edge = [v[18], v[21]];
v[24] = edge[0];
v[25] = edge[1];
pc = 6;
}
}
5 => {
let edge = [v[22], v[23]];
v[27] = edge[0];
v[28] = edge[1];
pc = 7;
}
6 => {
v[26] = v[25].wrapping_add(v[25]) & 0xffffffffffffffffu64;
let edge = [v[24], v[26]];
v[27] = edge[0];
v[28] = edge[1];
pc = 7;
}
7 => {
v[29] = fields[4];
v[30] = fields[4];
v[31] = v[27].wrapping_add(v[28]) & 0xffffffffffffffffu64;
v[32] = v[31].wrapping_add(v[30]) & 0xffffffffffffffffu64;
    if v[32] < memory_base || v[32] - memory_base > memory.len() as u64 || (memory.len() as u64) - (v[32] - memory_base) < 8 { return 3; }
v[33] = ((memory[(v[32] - memory_base) as usize + 0] as u64) << 0) | ((memory[(v[32] - memory_base) as usize + 1] as u64) << 8) | ((memory[(v[32] - memory_base) as usize + 2] as u64) << 16) | ((memory[(v[32] - memory_base) as usize + 3] as u64) << 24) | ((memory[(v[32] - memory_base) as usize + 4] as u64) << 32) | ((memory[(v[32] - memory_base) as usize + 5] as u64) << 40) | ((memory[(v[32] - memory_base) as usize + 6] as u64) << 48) | ((memory[(v[32] - memory_base) as usize + 7] as u64) << 56);
v[34] = registers[_f0] & 0xffffffffffffffffu64;
v[35] = v[34].wrapping_add(v[33]) & 0xffffffffffffffffu64;
v[36] = 0x0u64;
v[37] = 0x0u64;
v[38] = 0x1u64;
v[39] = (v[35] == v[36]) as u64;
v[40] = 0x8000000000000000u64;
v[41] = (v[35] & v[40]) & 0xffffffffffffffffu64;
v[42] = (v[41] == v[40]) as u64;
v[43] = 0x1u64;
v[44] = (v[35] & v[43]) & 0xffffffffffffffffu64;
v[45] = (v[44] == v[43]) as u64;
v[46] = 0x2u64;
v[47] = (v[35] & v[46]) & 0xffffffffffffffffu64;
v[48] = (v[47] == v[46]) as u64;
v[49] = 0x4u64;
v[50] = (v[35] & v[49]) & 0xffffffffffffffffu64;
v[51] = (v[50] == v[49]) as u64;
v[52] = 0x8u64;
v[53] = (v[35] & v[52]) & 0xffffffffffffffffu64;
v[54] = (v[53] == v[52]) as u64;
v[55] = 0x10u64;
v[56] = (v[35] & v[55]) & 0xffffffffffffffffu64;
v[57] = (v[56] == v[55]) as u64;
v[58] = 0x20u64;
v[59] = (v[35] & v[58]) & 0xffffffffffffffffu64;
v[60] = (v[59] == v[58]) as u64;
v[61] = 0x40u64;
v[62] = (v[35] & v[61]) & 0xffffffffffffffffu64;
v[63] = (v[62] == v[61]) as u64;
v[64] = 0x80u64;
v[65] = (v[35] & v[64]) & 0xffffffffffffffffu64;
v[66] = (v[65] == v[64]) as u64;
v[67] = (v[45] ^ v[48]) & 0x1u64;
v[68] = (v[67] ^ v[51]) & 0x1u64;
v[69] = (v[68] ^ v[54]) & 0x1u64;
v[70] = (v[69] ^ v[57]) & 0x1u64;
v[71] = (v[70] ^ v[60]) & 0x1u64;
v[72] = (v[71] ^ v[63]) & 0x1u64;
v[73] = (v[72] ^ v[66]) & 0x1u64;
v[74] = (v[73] == v[37]) as u64;
v[75] = u64::from(v[34] > 0xffffffffffffffffu64 - v[33]);
v[76] = (v[34] ^ v[33]) & 0xffffffffffffffffu64;
v[77] = (v[34] ^ v[35]) & 0xffffffffffffffffu64;
v[78] = 0xffffffffffffffffu64;
v[79] = (v[76] ^ v[78]) & 0xffffffffffffffffu64;
v[80] = (v[79] & v[77]) & 0xffffffffffffffffu64;
v[81] = (v[80] & v[40]) & 0xffffffffffffffffu64;
v[82] = (v[81] == v[40]) as u64;
v[83] = (v[76] ^ v[35]) & 0xffffffffffffffffu64;
v[84] = 0x10u64;
v[85] = (v[83] & v[84]) & 0xffffffffffffffffu64;
v[86] = (v[85] == v[84]) as u64;
    flags[0] = v[75];
    flags[4] = v[82];
    flags[5] = v[86];
    flags[11] = v[38];
    flags[1] = v[74];
    flags[2] = v[39];
    flags[3] = v[42];
    flags[6] = v[38];
    flags[7] = v[38];
    flags[8] = v[38];
    flags[9] = v[38];
    flags[10] = v[38];
    registers[_f0] = v[35];
return 0;
}
_ => return 3,
} }
}
pub fn x86_body_138(registers: &mut [u64], flags: &mut [u64], fields: &[u64], memory: &mut [u8], memory_base: u64) -> u32 {
    if fields.len() != 6 { return 3; }
    if fields[0] > 0x1fu64 { return 3; }
    if fields[1] > 0x1fu64 { return 3; }
    if fields[2] > 0x1fu64 { return 3; }
    if fields[3] > 0x1fu64 { return 3; }
    if fields[5] > 0x3u64 { return 3; }
    if fields[2] >= registers.len() as u64 { return 3; }
    if fields[3] >= registers.len() as u64 { return 3; }
    if fields[1] >= registers.len() as u64 { return 3; }
    if flags.iter().any(|&value| value > 1) { return 3; }
    let _f0 = fields[0] as usize;
    let _f1 = fields[1] as usize;
    let _f2 = fields[2] as usize;
    let _f3 = fields[3] as usize;
    let _f4 = fields[4] as usize;
    let _f5 = fields[5] as usize;
let mut v = [0u64; 34];
let mut pc = 0usize;
loop { match pc {
0 => {
v[0] = registers[_f2] & 0xffffffffffffffffu64;
v[1] = registers[_f3] & 0xffffffffffffffffu64;
v[2] = fields[5];
v[3] = 0x0u64;
v[4] = 0x1u64;
v[5] = 0x2u64;
v[6] = (v[2] == v[3]) as u64;
v[7] = (v[2] == v[4]) as u64;
v[8] = (v[2] == v[5]) as u64;
if v[6] != 0 {
let edge = [v[0], v[1]];
v[9] = edge[0];
v[10] = edge[1];
pc = 1;
} else {
let edge = [v[0], v[1], v[7], v[8]];
v[11] = edge[0];
v[12] = edge[1];
v[13] = edge[2];
v[14] = edge[3];
pc = 2;
}
}
1 => {
let edge = [v[9], v[10]];
v[27] = edge[0];
v[28] = edge[1];
pc = 7;
}
2 => {
v[15] = v[12].wrapping_add(v[12]) & 0xffffffffffffffffu64;
if v[13] != 0 {
let edge = [v[11], v[15]];
v[16] = edge[0];
v[17] = edge[1];
pc = 3;
} else {
let edge = [v[11], v[15], v[14]];
v[18] = edge[0];
v[19] = edge[1];
v[20] = edge[2];
pc = 4;
}
}
3 => {
let edge = [v[16], v[17]];
v[27] = edge[0];
v[28] = edge[1];
pc = 7;
}
4 => {
v[21] = v[19].wrapping_add(v[19]) & 0xffffffffffffffffu64;
if v[20] != 0 {
let edge = [v[18], v[21]];
v[22] = edge[0];
v[23] = edge[1];
pc = 5;
} else {
let edge = [v[18], v[21]];
v[24] = edge[0];
v[25] = edge[1];
pc = 6;
}
}
5 => {
let edge = [v[22], v[23]];
v[27] = edge[0];
v[28] = edge[1];
pc = 7;
}
6 => {
v[26] = v[25].wrapping_add(v[25]) & 0xffffffffffffffffu64;
let edge = [v[24], v[26]];
v[27] = edge[0];
v[28] = edge[1];
pc = 7;
}
7 => {
v[29] = fields[4];
v[30] = fields[4];
v[31] = v[27].wrapping_add(v[28]) & 0xffffffffffffffffu64;
v[32] = v[31].wrapping_add(v[30]) & 0xffffffffffffffffu64;
v[33] = registers[_f1] & 0xffffffffffffffffu64;
    if v[32] < memory_base || v[32] - memory_base > memory.len() as u64 || (memory.len() as u64) - (v[32] - memory_base) < 8 { return 3; }
    memory[(v[32] - memory_base) as usize + 0] = (v[33] >> 0) as u8;
    memory[(v[32] - memory_base) as usize + 1] = (v[33] >> 8) as u8;
    memory[(v[32] - memory_base) as usize + 2] = (v[33] >> 16) as u8;
    memory[(v[32] - memory_base) as usize + 3] = (v[33] >> 24) as u8;
    memory[(v[32] - memory_base) as usize + 4] = (v[33] >> 32) as u8;
    memory[(v[32] - memory_base) as usize + 5] = (v[33] >> 40) as u8;
    memory[(v[32] - memory_base) as usize + 6] = (v[33] >> 48) as u8;
    memory[(v[32] - memory_base) as usize + 7] = (v[33] >> 56) as u8;
return 0;
}
_ => return 3,
} }
}
pub fn fsl_x86(registers: &mut [u64], flags: &mut [u64], memory: &mut [u8], memory_base: u64, scratch: &mut [u8], budget: usize, exit_pc: &mut u64) -> u32 {
if registers.len()!=17 || flags.len()!=12 || registers[16]!=0 || budget==0 || budget>1000000 || flags.iter().any(|&v|v>1) || flags[6..].iter().any(|&v|v!=1) || memory_base.checked_add(memory.len() as u64).is_none() { return 3; }
if scratch.len()!=memory.len() || memory.len()>1048576 { return 3; }
scratch.copy_from_slice(memory); let destination_memory=memory; let memory=scratch;
let mut r=[0u64;17]; let mut f=[0u64;12]; r.copy_from_slice(registers); f.copy_from_slice(flags);
let mut pc=0x401000u64;
for _step in 0..budget {
let mut next=0u64; let mut changed=false;
let _ = (&memory, memory_base, &next, &changed);
match pc {
0x401000 => { /* raw=488b07 */
let fields=[0x0u64,0x0u64,0x7u64,0x10u64,0x0u64,0x0u64];
let status=x86_body_119(&mut r,&mut f,&fields,memory,memory_base);
if status!=0 { return status; }
pc=if changed {next} else {0x401003u64};
}
0x401003 => { /* raw=48034708 */
let fields=[0x0u64,0x0u64,0x7u64,0x10u64,0x8u64,0x0u64];
let status=x86_body_120(&mut r,&mut f,&fields,memory,memory_base);
if status!=0 { return status; }
pc=if changed {next} else {0x401007u64};
}
0x401007 => { /* raw=488907 */
let fields=[0x10u64,0x0u64,0x7u64,0x10u64,0x0u64,0x0u64];
let status=x86_body_138(&mut r,&mut f,&fields,memory,memory_base);
if status!=0 { return status; }
pc=if changed {next} else {0x40100au64};
}
0x40100a => { /* raw=c3 */
let fields=[0x4u64,0x0u64,0x0u64,0x0u64,0x0u64,0x0u64];
let status=x86_body_59(&mut r,&mut f,&fields,pc,&mut next,&mut changed,memory,memory_base);
if status!=0 { return status; }
if !changed { return 3; } registers.copy_from_slice(&r); flags.copy_from_slice(&f); destination_memory.copy_from_slice(memory); *exit_pc=next; return 0;
}
_ => return 3,
}
}
3
}

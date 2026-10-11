/* x86 mode=64 input-sha256=d9cf89c572e9a193175b8735a341790208fabfe36d704868ed206cb6a85af1ba package-sha256=0423223eaf7238013177aceb9b7c09f7448a682752668e3124ab9c651b46515a; owned decoder owned-x86-v1.
 * Explicit state function: GPR[0..16]=RAX,RCX,RDX,RBX,RSP,RBP,RSI,RDI,R8..R15; GPR[16]=0.
 * flags=CF,PF,ZF,SF,OF,AF then six known bits. Unknown AF is not observable.
 * Disjoint valid storage required in C. Bounded byte memory, flat SS.base=0, no MMU/fault model.
 * Status 0 commits state and return PC; status 3 preserves caller storage. */
/* binary file-sha256=588d20aa4045b9e6694a8d39931f0bbf10881bfcf1b0090a4b3830ba2704184f file-offset=4096 */
pub fn x86_body_58(registers: &mut [u64], flags: &mut [u64], fields: &[u64]) -> u32 {
    if fields.len() != 6 { return 3; }
    if fields[0] > 0x1fu64 { return 3; }
    if fields[1] > 0x1fu64 { return 3; }
    if fields[2] > 0x1fu64 { return 3; }
    if fields[3] > 0x1fu64 { return 3; }
    if fields[5] > 0x3u64 { return 3; }
    if fields[2] >= registers.len() as u64 { return 3; }
    if fields[3] >= registers.len() as u64 { return 3; }
    if fields[0] >= registers.len() as u64 { return 3; }
    if flags.iter().any(|&value| value > 1) { return 3; }
    let _f0 = fields[0] as usize;
    let _f1 = fields[1] as usize;
    let _f2 = fields[2] as usize;
    let _f3 = fields[3] as usize;
    let _f4 = fields[4] as usize;
    let _f5 = fields[5] as usize;
let mut v = [0u64; 33];
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
    registers[_f0] = v[32];
return 0;
}
_ => return 3,
} }
}
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
pub fn fsl_x86(registers: &mut [u64], flags: &mut [u64], memory: &[u8], memory_base: u64, budget: usize, exit_pc: &mut u64) -> u32 {
if registers.len()!=17 || flags.len()!=12 || registers[16]!=0 || budget==0 || budget>1000000 || flags.iter().any(|&v|v>1) || flags[6..].iter().any(|&v|v!=1) || memory_base.checked_add(memory.len() as u64).is_none() { return 3; }
let mut r=[0u64;17]; let mut f=[0u64;12]; r.copy_from_slice(registers); f.copy_from_slice(flags);
let mut pc=0x401000u64;
for _step in 0..budget {
let mut next=0u64; let mut changed=false;
let _ = (&memory, memory_base, &next, &changed);
match pc {
0x401000 => { /* raw=488d0437 */
let fields=[0x0u64,0x0u64,0x7u64,0x6u64,0x0u64,0x0u64];
let status=x86_body_58(&mut r,&mut f,&fields);
if status!=0 { return status; }
pc=if changed {next} else {0x401004u64};
}
0x401004 => { /* raw=c3 */
let fields=[0x4u64,0x0u64,0x0u64,0x0u64,0x0u64,0x0u64];
let status=x86_body_59(&mut r,&mut f,&fields,pc,&mut next,&mut changed,memory,memory_base);
if status!=0 { return status; }
if !changed { return 3; } registers.copy_from_slice(&r); flags.copy_from_slice(&f); *exit_pc=next; return 0;
}
_ => return 3,
}
}
3
}

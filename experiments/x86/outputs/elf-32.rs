/* x86 mode=32 input-sha256=700d0e7fe3ab70f0bf33fbfa41871555e63c60f1bb528dc78a57eba5bfbaa90b package-sha256=0423223eaf7238013177aceb9b7c09f7448a682752668e3124ab9c651b46515a; owned decoder owned-x86-v1.
 * Explicit state function: GPR[0..16]=RAX,RCX,RDX,RBX,RSP,RBP,RSI,RDI,R8..R15; GPR[16]=0.
 * flags=CF,PF,ZF,SF,OF,AF then six known bits. Unknown AF is not observable.
 * Disjoint valid storage required in C. Bounded byte memory, flat SS.base=0, no MMU/fault model.
 * Status 0 commits state and return PC; status 3 preserves caller storage. */
/* binary file-sha256=7d74d7aee6953af304cd24741c97abc291e579d45d146234c069face64f6179a file-offset=4096 */
pub fn x86_body_22(registers: &mut [u64], flags: &mut [u64], fields: &[u64]) -> u32 {
    if fields.len() != 6 { return 3; }
    if fields[0] > 0x1fu64 { return 3; }
    if fields[1] > 0x1fu64 { return 3; }
    if fields[2] > 0x1fu64 { return 3; }
    if fields[3] > 0x1fu64 { return 3; }
    if fields[5] > 0x3u64 { return 3; }
    if fields[0] >= registers.len() as u64 { return 3; }
    if fields[1] >= registers.len() as u64 { return 3; }
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
let mut v = [0u64; 54];
let pc = 0usize;
loop { match pc {
0 => {
v[0] = registers[_f0] & 0xffffffffu64;
v[1] = registers[_f1] & 0xffffffffu64;
v[2] = v[0].wrapping_add(v[1]) & 0xffffffffu64;
v[3] = 0x0u64;
v[4] = 0x0u64;
v[5] = 0x1u64;
v[6] = (v[2] == v[3]) as u64;
v[7] = 0x80000000u64;
v[8] = (v[2] & v[7]) & 0xffffffffu64;
v[9] = (v[8] == v[7]) as u64;
v[10] = 0x1u64;
v[11] = (v[2] & v[10]) & 0xffffffffu64;
v[12] = (v[11] == v[10]) as u64;
v[13] = 0x2u64;
v[14] = (v[2] & v[13]) & 0xffffffffu64;
v[15] = (v[14] == v[13]) as u64;
v[16] = 0x4u64;
v[17] = (v[2] & v[16]) & 0xffffffffu64;
v[18] = (v[17] == v[16]) as u64;
v[19] = 0x8u64;
v[20] = (v[2] & v[19]) & 0xffffffffu64;
v[21] = (v[20] == v[19]) as u64;
v[22] = 0x10u64;
v[23] = (v[2] & v[22]) & 0xffffffffu64;
v[24] = (v[23] == v[22]) as u64;
v[25] = 0x20u64;
v[26] = (v[2] & v[25]) & 0xffffffffu64;
v[27] = (v[26] == v[25]) as u64;
v[28] = 0x40u64;
v[29] = (v[2] & v[28]) & 0xffffffffu64;
v[30] = (v[29] == v[28]) as u64;
v[31] = 0x80u64;
v[32] = (v[2] & v[31]) & 0xffffffffu64;
v[33] = (v[32] == v[31]) as u64;
v[34] = (v[12] ^ v[15]) & 0x1u64;
v[35] = (v[34] ^ v[18]) & 0x1u64;
v[36] = (v[35] ^ v[21]) & 0x1u64;
v[37] = (v[36] ^ v[24]) & 0x1u64;
v[38] = (v[37] ^ v[27]) & 0x1u64;
v[39] = (v[38] ^ v[30]) & 0x1u64;
v[40] = (v[39] ^ v[33]) & 0x1u64;
v[41] = (v[40] == v[4]) as u64;
v[42] = u64::from(v[0] > 0xffffffffu64 - v[1]);
v[43] = (v[0] ^ v[1]) & 0xffffffffu64;
v[44] = (v[0] ^ v[2]) & 0xffffffffu64;
v[45] = 0xffffffffu64;
v[46] = (v[43] ^ v[45]) & 0xffffffffu64;
v[47] = (v[46] & v[44]) & 0xffffffffu64;
v[48] = (v[47] & v[7]) & 0xffffffffu64;
v[49] = (v[48] == v[7]) as u64;
v[50] = (v[43] ^ v[2]) & 0xffffffffu64;
v[51] = 0x10u64;
v[52] = (v[50] & v[51]) & 0xffffffffu64;
v[53] = (v[52] == v[51]) as u64;
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
    registers[_f0] = v[2];
return 0;
}
_ => return 3,
} }
}
pub fn x86_body_39(registers: &mut [u64], flags: &mut [u64], fields: &[u64], guest_pc: u64, next_pc: &mut u64, next_pc_set: &mut bool, memory: &[u8], memory_base: u64) -> u32 {
    let _ = guest_pc;
    if fields.len() != 6 { return 3; }
    if fields[0] > 0x1fu64 { return 3; }
    if fields[1] > 0x1fu64 { return 3; }
    if fields[2] > 0x1fu64 { return 3; }
    if fields[3] > 0x1fu64 { return 3; }
    if fields[5] > 0x3u64 { return 3; }
    if fields[0] >= registers.len() as u64 { return 3; }
    if fields[0] >= registers.len() as u64 { return 3; }
    if flags.iter().any(|&value| value > 1) { return 3; }
    let _f0 = fields[0] as usize;
    let _f1 = fields[1] as usize;
    let _f2 = fields[2] as usize;
    let _f3 = fields[3] as usize;
    let _f4 = fields[4] as usize;
    let _f5 = fields[5] as usize;
let mut v = [0u64; 6];
let pc = 0usize;
loop { match pc {
0 => {
v[0] = registers[_f0] & 0xffffffffu64;
v[1] = (v[0]) & 0xffffffffffffffffu64;
    if v[1] < memory_base || v[1] - memory_base > memory.len() as u64 || (memory.len() as u64) - (v[1] - memory_base) < 4 { return 3; }
v[2] = ((memory[(v[1] - memory_base) as usize + 0] as u64) << 0) | ((memory[(v[1] - memory_base) as usize + 1] as u64) << 8) | ((memory[(v[1] - memory_base) as usize + 2] as u64) << 16) | ((memory[(v[1] - memory_base) as usize + 3] as u64) << 24);
v[3] = 0x4u64;
v[4] = v[0].wrapping_add(v[3]) & 0xffffffffu64;
    registers[_f0] = v[4];
v[5] = (v[2]) & 0xffffffffffffffffu64;
    if *next_pc_set { return 3; }
    *next_pc = v[5];
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
0x401000 => { /* raw=01d0 */
let fields=[0x0u64,0x2u64,0x0u64,0x0u64,0x0u64,0x0u64];
let status=x86_body_22(&mut r,&mut f,&fields);
if status!=0 { return status; }
pc=if changed {next} else {0x401002u64};
}
0x401002 => { /* raw=c3 */
let fields=[0x4u64,0x0u64,0x0u64,0x0u64,0x0u64,0x0u64];
let status=x86_body_39(&mut r,&mut f,&fields,pc,&mut next,&mut changed,memory,memory_base);
if status!=0 { return status; }
if !changed { return 3; } registers.copy_from_slice(&r); flags.copy_from_slice(&f); *exit_pc=next; return 0;
}
_ => return 3,
}
}
3
}

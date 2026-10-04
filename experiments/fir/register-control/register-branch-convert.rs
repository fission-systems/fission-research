pub fn fsl_execute(registers: &mut [u64], flags: &mut [u64], fields: &[u64]) -> u32 {
    if fields.len() != 3 { return 3; }
    if fields[0] > 0xfu64 { return 3; }
    if fields[1] > 0xfu64 { return 3; }
    if fields[2] > 0xfu64 { return 3; }
    if fields[0] >= registers.len() as u64 { return 3; }
    if fields[0] >= registers.len() as u64 { return 3; }
    if fields[2] >= registers.len() as u64 { return 3; }
    if fields[1] >= registers.len() as u64 { return 3; }
    if flags.len() <= 0 { return 3; }
    if fields[1] >= registers.len() as u64 { return 3; }
    if flags.len() <= 0 { return 3; }
    if fields[1] >= registers.len() as u64 { return 3; }
    if flags.len() <= 1 { return 3; }
    if flags.len() <= 0 { return 3; }
    if flags.len() <= 2 { return 3; }
    if flags.iter().any(|&value| value > 1) { return 3; }
    let _f0 = fields[0] as usize;
    let _f1 = fields[1] as usize;
    let _f2 = fields[2] as usize;
let mut v = [0u64; 18];
let mut pc = 0usize;
loop { match pc {
0 => {
v[0] = registers[_f0] & 0xffu64;
v[1] = ((v[0]) ^ 0x80u64).wrapping_sub(0x80u64) & 0xffffffffu64;
v[2] = registers[_f0] & 0xffu64;
v[3] = (v[2]) & 0xffffffffffffffffu64;
    registers[_f2] = v[3];
v[4] = 0x0u64;
v[5] = ((v[1] ^ 0x80000000u64) < (v[4] ^ 0x80000000u64)) as u64;
if v[5] != 0 {
let edge = [v[1]];
v[6] = edge[0];
pc = 1;
} else {
let edge = [v[1]];
v[10] = edge[0];
pc = 2;
}
}
1 => {
v[7] = (v[6]) & 0xffffu64;
v[8] = ((v[7]) ^ 0x8000u64).wrapping_sub(0x8000u64) & 0xffffffffu64;
    registers[_f1] = v[8];
v[9] = 0x1u64;
    flags[0] = v[9];
let edge = [v[8]];
v[14] = edge[0];
pc = 3;
}
2 => {
v[11] = (v[10]) & 0xffu64;
v[12] = ((v[11]) ^ 0x80u64).wrapping_sub(0x80u64) & 0xffffffffu64;
    registers[_f1] = v[12];
v[13] = 0x0u64;
    flags[0] = v[13];
let edge = [v[12]];
v[14] = edge[0];
pc = 3;
}
3 => {
v[15] = registers[_f1] & 0xffffffffu64;
v[16] = (v[15] == v[14]) as u64;
    flags[1] = v[16];
v[17] = flags[0] & 0x1u64;
    flags[2] = v[17];
return 0;
}
_ => return 3,
} }
}

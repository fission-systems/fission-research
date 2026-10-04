// sequence input-sha256=3805c5efdfd4f7e35d5548b580716a918ba05935ee599767d3d9cab61ba31880 package-sha256=39c3146c31657708041b1e7cd4207876f3bb78c41c2fbf3106beec467f7154f1 steps=3
pub fn fsl_sequence_body_0(registers: &mut [u64], flags: &mut [u64], fields: &[u64]) -> u32 {
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

pub fn fsl_sequence(registers: &mut [u64], flags: &mut [u64]) -> u32 {
  if registers.len() != 3 || flags.len() != 3 || flags.iter().any(|&v| v>1) { return 3; }
  let mut next_registers = [0u64; 3];
  let mut next_flags = [0u64; 3];
  next_registers.copy_from_slice(registers);
  next_flags.copy_from_slice(flags);
// step=0 address=0x1000 offset=0 length=4 body=0 raw=10a20000
  { let fields = [0x0u64, 0x1u64, 0x2u64];
    let status = fsl_sequence_body_0(&mut next_registers, &mut next_flags, &fields);
    if status != 0 { return status; } }
// step=1 address=0x1004 offset=4 length=4 body=0 raw=21a00000
  { let fields = [0x1u64, 0x2u64, 0x0u64];
    let status = fsl_sequence_body_0(&mut next_registers, &mut next_flags, &fields);
    if status != 0 { return status; } }
// step=2 address=0x1008 offset=8 length=4 body=0 raw=02a10000
  { let fields = [0x2u64, 0x0u64, 0x1u64];
    let status = fsl_sequence_body_0(&mut next_registers, &mut next_flags, &fields);
    if status != 0 { return status; } }
  registers.copy_from_slice(&next_registers);
  flags.copy_from_slice(&next_flags);
  0
}

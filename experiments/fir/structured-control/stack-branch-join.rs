pub fn fsl_execute(stack: &mut [u64], depth: &mut usize) -> u32 {
  let capacity = stack.len();
  if *depth > capacity { return 3; }
  if *depth < 1 { return 1; }
  let mut sp = *depth;
  let mut v = [0u64; 10];
  let _ = &v;
  let mut pc = 0usize;
  loop { match pc {
0 => {
sp -= 1;
v[0] = stack[sp] & 0xffffffffu64;
v[1] = 0xau64;
v[2] = (v[0] < v[1]) as u64;
if v[2] != 0 {
let edge = [v[0]];
v[3] = edge[0];
pc = 1;
} else {
let edge = [v[0]];
v[6] = edge[0];
pc = 2;
}
}
1 => {
v[4] = 0x1u64;
v[5] = v[3].wrapping_add(v[4]) & 0xffffffffu64;
let edge = [v[5]];
v[9] = edge[0];
pc = 3;
}
2 => {
v[7] = 0x2u64;
v[8] = v[6].wrapping_add(v[7]) & 0xffffffffu64;
let edge = [v[8]];
v[9] = edge[0];
pc = 3;
}
3 => {
stack[sp] = v[9];
sp += 1;
*depth = sp;
return 0;
}
_ => return 3,
} }
}

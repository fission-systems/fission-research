OPENQASM 3.0;
include "stdgates.inc";
bit[2] out;
// Explicit computational-basis preparation
reset $7;
reset $3;
// FIR operation 0
rz(pi/2) $7;
sx $7;
rz(pi/2) $7;
// FIR operation 1
rz(pi/2) $3;
sx $3;
rz(pi/2) $3;
cz $7, $3;
rz(pi/2) $3;
sx $3;
rz(pi/2) $3;
// Terminal observation; this wrapper is not a FIR effect
rz(pi/2) $7;
sx $7;
rz(pi/2) $7;
out[0] = measure $7;
rz(pi/2) $3;
sx $3;
rz(pi/2) $3;
out[1] = measure $3;

OPENQASM 3.0;
include "stdgates.inc";
bit[2] out;
// Explicit computational-basis preparation
reset $135;
reset $139;
// FIR operation 0
rz(pi/2) $135;
sx $135;
rz(pi/2) $135;
// FIR operation 1
rz(pi/2) $139;
sx $139;
rz(pi/2) $139;
cz $135, $139;
rz(pi/2) $139;
sx $139;
rz(pi/2) $139;
// Terminal observation; this wrapper is not a FIR effect
rz(pi/2) $135;
sx $135;
rz(pi/2) $135;
out[0] = measure $135;
rz(pi/2) $139;
sx $139;
rz(pi/2) $139;
out[1] = measure $139;

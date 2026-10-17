OPENQASM 3.0;
include "stdgates.inc";
qubit[1] q;
bit[2] m;
h q[0];
m[0] = measure q[0];
if (m[0] == 1) { x q[0]; }
m[1] = measure q[0];

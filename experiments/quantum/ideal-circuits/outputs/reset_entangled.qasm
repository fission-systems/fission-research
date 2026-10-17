OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
bit[1] m;
h q[0];
cx q[0], q[1];
reset q[0];

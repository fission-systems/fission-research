// Canonical FIR projection: combinational, two-valued, no clock or timing guarantee.
module mutant_fpga_add(
    input wire [63:0] in0,
    input wire [63:0] in1,
    output wire [63:0] out0
);
wire [7:0] v0;
wire [7:0] v1;
wire [7:0] v2;
// FIR operation 0
assign v0 = in1;
// FIR operation 1
assign v1 = in0;
// FIR operation 2
assign v2 = v1 + v0;
// FIR operation 3
assign out0 = (v2) ^ 64'd1;
endmodule

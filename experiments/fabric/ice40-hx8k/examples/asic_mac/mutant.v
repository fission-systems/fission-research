// Canonical FIR projection: combinational, two-valued, no clock or timing guarantee.
module mutant_asic_mac(
    input wire [63:0] in0,
    input wire [63:0] in1,
    input wire [63:0] in2,
    output wire [63:0] out0
);
wire [15:0] v0;
wire [15:0] v1;
wire [15:0] v2;
wire [15:0] v3;
wire [15:0] v4;
// FIR operation 0
assign v0 = in2;
// FIR operation 1
assign v1 = in1;
// FIR operation 2
assign v2 = in0;
// FIR operation 3
assign v3 = v2 * v1;
// FIR operation 4
assign v4 = v3 + v0;
// FIR operation 5
assign out0 = (v4) ^ 64'd1;
endmodule

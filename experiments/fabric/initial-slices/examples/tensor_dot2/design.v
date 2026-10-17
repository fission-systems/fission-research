// Canonical FIR projection: combinational, two-valued, no clock or timing guarantee.
module fsl_tensor_dot2(
    input wire [63:0] in0,
    input wire [63:0] in1,
    input wire [63:0] in2,
    input wire [63:0] in3,
    output wire [63:0] out0
);
wire [7:0] v0;
wire [7:0] v1;
wire [7:0] v2;
wire [7:0] v3;
wire [31:0] v4;
wire [31:0] v5;
wire [31:0] v6;
wire [31:0] v7;
wire [31:0] v8;
wire [31:0] v9;
wire [31:0] v10;
// FIR operation 0
assign v0 = in3;
// FIR operation 1
assign v1 = in2;
// FIR operation 2
assign v2 = in1;
// FIR operation 3
assign v3 = in0;
// FIR operation 4
assign v4 = v3;
// FIR operation 5
assign v5 = v2;
// FIR operation 6
assign v6 = v1;
// FIR operation 7
assign v7 = v0;
// FIR operation 8
assign v8 = v4 * v6;
// FIR operation 9
assign v9 = v5 * v7;
// FIR operation 10
assign v10 = v8 + v9;
// FIR operation 11
assign out0 = v10;
endmodule

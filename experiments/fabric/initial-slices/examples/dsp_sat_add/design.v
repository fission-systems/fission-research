// Canonical FIR projection: combinational, two-valued, no clock or timing guarantee.
module fsl_dsp_sat_add(
    input wire [63:0] in0,
    input wire [63:0] in1,
    output wire [63:0] out0
);
wire [7:0] v0;
wire [7:0] v1;
wire [15:0] v2;
wire [15:0] v3;
wire [15:0] v4;
wire [15:0] v5;
wire [0:0] v6;
wire [7:0] v7;
wire [7:0] v8;
wire [7:0] v9;
wire [7:0] v10;
wire [7:0] v11;
wire [7:0] v12;
wire [7:0] v13;
wire [7:0] v14;
// FIR operation 0
assign v0 = in1;
// FIR operation 1
assign v1 = in0;
// FIR operation 2
assign v2 = v1;
// FIR operation 3
assign v3 = v0;
// FIR operation 4
assign v4 = v2 + v3;
// FIR operation 5
assign v5 = 16'hff;
// FIR operation 6
assign v6 = v5 < v4;
// FIR operation 7
assign v7 = v6;
// FIR operation 8
assign v8 = 8'h0;
// FIR operation 9
assign v9 = 8'hff;
// FIR operation 10
assign v10 = v8 - v7;
// FIR operation 11
assign v11 = v10 ^ v9;
// FIR operation 12
assign v12 = v4;
// FIR operation 13
assign v13 = v12 & v11;
// FIR operation 14
assign v14 = v13 | v10;
// FIR operation 15
assign out0 = v14;
endmodule

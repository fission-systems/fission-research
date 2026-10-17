// Canonical FIR projection: combinational, two-valued, no clock or timing guarantee.
module mutant_lif_step(
    input wire [63:0] in0,
    input wire [63:0] in1,
    output wire [63:0] out0,
    output wire [63:0] out1
);
wire [7:0] v0;
wire [7:0] v1;
wire [15:0] v2;
wire [15:0] v3;
wire [15:0] v4;
wire [15:0] v5;
wire [15:0] v6;
wire [15:0] v7;
wire [15:0] v8;
wire [15:0] v9;
wire [0:0] v10;
wire [0:0] v11;
wire [0:0] v12;
wire [15:0] v13;
wire [15:0] v14;
wire [15:0] v15;
wire [15:0] v16;
wire [15:0] v17;
wire [15:0] v18;
wire [7:0] v19;
// FIR operation 0
assign v0 = in1;
// FIR operation 1
assign v1 = in0;
// FIR operation 2
assign v2 = v1;
// FIR operation 3
assign v3 = v0;
// FIR operation 4
assign v4 = 16'h3;
// FIR operation 5
assign v5 = 16'h2;
// FIR operation 6
assign v6 = v2 * v4;
// FIR operation 7
assign v7 = (v5 >= 64'd16) ? 16'd0 : (v6 >> v5);
// FIR operation 8
assign v8 = v7 + v3;
// FIR operation 9
assign v9 = 16'h64;
// FIR operation 10
assign v10 = v8 < v9;
// FIR operation 11
assign v11 = 1'h1;
// FIR operation 12
assign v12 = v10 ^ v11;
// FIR operation 13
assign v13 = v12;
// FIR operation 14
assign v14 = 16'h0;
// FIR operation 15
assign v15 = 16'hffff;
// FIR operation 16
assign v16 = v14 - v13;
// FIR operation 17
assign v17 = v16 ^ v15;
// FIR operation 18
assign v18 = v8 & v17;
// FIR operation 19
assign v19 = v18;
// FIR operation 20
// FIR operation 21
assign out0 = (v19) ^ 64'd1;
assign out1 = v12;
endmodule

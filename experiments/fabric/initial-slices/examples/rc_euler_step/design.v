// Canonical FIR projection: combinational, two-valued, no clock or timing guarantee.
module fsl_rc_euler_step(
    input wire [63:0] in0,
    input wire [63:0] in1,
    output wire [63:0] out0
);
wire [15:0] v0;
wire [15:0] v1;
wire [31:0] v2;
wire [31:0] v3;
wire [31:0] v4;
wire [31:0] v5;
wire [31:0] v6;
wire [31:0] v7;
wire [31:0] v8;
wire [15:0] v9;
// FIR operation 0
assign v0 = in1;
// FIR operation 1
assign v1 = in0;
// FIR operation 2
assign v2 = v1;
// FIR operation 3
assign v3 = v0;
// FIR operation 4
assign v4 = 32'h3;
// FIR operation 5
assign v5 = 32'h2;
// FIR operation 6
assign v6 = v2 * v4;
// FIR operation 7
assign v7 = v6 + v3;
// FIR operation 8
assign v8 = (v5 >= 64'd32) ? 32'd0 : (v7 >> v5);
// FIR operation 9
assign v9 = v8;
// FIR operation 10
assign out0 = v9;
endmodule

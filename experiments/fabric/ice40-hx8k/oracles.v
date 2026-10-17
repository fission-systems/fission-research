// Independently authored workload specifications. These are not FIR emitters.
// All inputs are unrestricted 64-bit stack slots; typed operands use low bits.
module oracle_fpga_add(input [63:0] in0, in1, output [63:0] out0);
  wire [7:0] sum = in0[7:0] + in1[7:0];
  assign out0 = {56'd0, sum};
endmodule

module oracle_dsp_sat_add(input [63:0] in0, in1, output [63:0] out0);
  wire [8:0] sum = {1'b0,in0[7:0]} + {1'b0,in1[7:0]};
  assign out0 = sum > 9'd255 ? 64'd255 : {56'd0,sum[7:0]};
endmodule

module oracle_tensor_dot2(input [63:0] in0, in1, in2, in3, output [63:0] out0);
  wire [31:0] a = {24'd0,in0[7:0]}, b = {24'd0,in1[7:0]};
  wire [31:0] c = {24'd0,in2[7:0]}, d = {24'd0,in3[7:0]};
  wire [31:0] sum = a*c + b*d;
  assign out0 = {32'd0,sum};
endmodule

module oracle_asic_mac(input [63:0] in0, in1, in2, output [63:0] out0);
  wire [15:0] product = in0[15:0] * in1[15:0];
  wire [15:0] sum = product + in2[15:0];
  assign out0 = {48'd0,sum};
endmodule

module oracle_lif_step(input [63:0] in0, in1, output [63:0] out0, out1);
  wire [15:0] scaled = {8'd0,in0[7:0]} * 16'd3;
  wire [15:0] pre = (scaled >> 2) + {8'd0,in1[7:0]};
  assign out0 = pre >= 16'd100 ? 64'd0 : {56'd0,pre[7:0]};
  assign out1 = pre >= 16'd100 ? 64'd1 : 64'd0;
endmodule

module oracle_pim_bank_xor(input [63:0] in0, in1, output [63:0] out0);
  assign out0 = {32'd0, (in0[31:0] ^ in1[31:0])};
endmodule

module oracle_rc_euler_step(input [63:0] in0, in1, output [63:0] out0);
  wire [31:0] weighted = {16'd0,in0[15:0]} * 32'd3 + {16'd0,in1[15:0]};
  assign out0 = {32'd0,(weighted >> 2)};
endmodule

module oracle_dataflow_diamond(input [63:0] in0, in1, output [63:0] out0);
  wire [15:0] sum = in0[15:0] + in1[15:0];
  wire [15:0] difference = in0[15:0] - in1[15:0];
  wire [15:0] product = sum * difference;
  assign out0 = {48'd0,product};
endmodule

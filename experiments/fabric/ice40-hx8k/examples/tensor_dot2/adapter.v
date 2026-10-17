// Typed port adapter only; no workload semantics or state.
module fsl_target_tensor_dot2(input wire [7:0] in0,input wire [7:0] in1,input wire [7:0] in2,input wire [7:0] in3,output wire [31:0] out0);
wire [63:0] slot0;
fsl_tensor_dot2 body(.in0({56'd0,in0}),.in1({56'd0,in1}),.in2({56'd0,in2}),.in3({56'd0,in3}),.out0(slot0));
assign out0 = slot0[31:0];
endmodule

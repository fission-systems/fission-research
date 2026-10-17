// Typed port adapter only; no workload semantics or state.
module fsl_target_lif_step(input wire [7:0] in0,input wire [7:0] in1,output wire [7:0] out0,output wire [0:0] out1);
wire [63:0] slot0;
wire [63:0] slot1;
fsl_lif_step body(.in0({56'd0,in0}),.in1({56'd0,in1}),.out0(slot0),.out1(slot1));
assign out0 = slot0[7:0];
assign out1 = slot1[0:0];
endmodule

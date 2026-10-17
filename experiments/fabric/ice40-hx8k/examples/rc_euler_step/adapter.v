// Typed port adapter only; no workload semantics or state.
module fsl_target_rc_euler_step(input wire [15:0] in0,input wire [15:0] in1,output wire [15:0] out0);
wire [63:0] slot0;
fsl_rc_euler_step body(.in0({48'd0,in0}),.in1({48'd0,in1}),.out0(slot0));
assign out0 = slot0[15:0];
endmodule

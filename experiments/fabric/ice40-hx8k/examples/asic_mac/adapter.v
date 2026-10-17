// Typed port adapter only; no workload semantics or state.
module fsl_target_asic_mac(input wire [15:0] in0,input wire [15:0] in1,input wire [15:0] in2,output wire [15:0] out0);
wire [63:0] slot0;
fsl_asic_mac body(.in0({48'd0,in0}),.in1({48'd0,in1}),.in2({48'd0,in2}),.out0(slot0));
assign out0 = slot0[15:0];
endmodule

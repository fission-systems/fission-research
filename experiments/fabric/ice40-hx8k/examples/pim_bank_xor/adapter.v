// Typed port adapter only; no workload semantics or state.
module fsl_target_pim_bank_xor(input wire [31:0] in0,input wire [31:0] in1,output wire [31:0] out0);
wire [63:0] slot0;
fsl_pim_bank_xor body(.in0({32'd0,in0}),.in1({32'd0,in1}),.out0(slot0));
assign out0 = slot0[31:0];
endmodule

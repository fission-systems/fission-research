// Typed port adapter only; no workload semantics or state.
module fsl_target_fpga_add(input wire [7:0] in0,input wire [7:0] in1,output wire [7:0] out0);
wire [63:0] slot0;
fsl_fpga_add body(.in0({56'd0,in0}),.in1({56'd0,in1}),.out0(slot0));
assign out0 = slot0[7:0];
endmodule

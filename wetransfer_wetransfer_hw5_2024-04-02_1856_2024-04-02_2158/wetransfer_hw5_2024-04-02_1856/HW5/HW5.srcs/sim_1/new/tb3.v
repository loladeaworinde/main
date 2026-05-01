`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 03/18/2024 08:09:42 PM
// Design Name: 
// Module Name: tb3
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module InstructionDecode_tb;

// Testbench signals
reg clk;
reg reset;
reg [31:0] instruction;
reg [31:0] PC_1;
reg [31:0] A_data;
reg [31:0] B_data;
wire [31:0] A_out;
wire [31:0] B_out;
wire [4:0] DA_out;
wire [6:0] opcode_out;
wire [4:0] FS_out;
wire [4:0] SH_out;
wire MW_out;
wire RW_out;
wire [1:0] MD_out;
wire [1:0] BS_out;
wire PS_out;
wire PC_2;

// Instantiate the InstructionDecode module
InstructionDecode uut (
    .clk(clk),
    .reset(reset),
    .instruction(instruction),
    .PC_1(PC_1),
    .A_data(A_data),
    .B_data(B_data),
    .A_out(A_out),
    .B_out(B_out),
    .DA_out(DA_out),
    .opcode_out(opcode_out),
    .FS_out(FS_out),
    .SH_out(SH_out),
    .MW_out(MW_out),
    .RW_out(RW_out),
    .MD_out(MD_out),
    .BS_out(BS_out),
    .PS_out(PS_out),
    .PC_2(PC_2)
);

// Clock generation
initial begin
    clk = 0;
    forever #5 clk = !clk; // 100MHz clock
end

// Test sequence
initial begin
    // Initialize inputs
    reset = 1;
    instruction = 0;
    PC_1 = 0;
    A_data = 0;
    B_data = 0;
    
    // Apply reset
    #10;
    reset = 0;
    #10;
    
    // Test ADD instruction
    instruction = {7'b0000010, 5'd1, 5'd2, 5'd3, 10'd0}; // Example ADD instruction
    A_data = 32'h00000002; // Data for register 2
    B_data = 32'h00000003; // Data for register 3
    PC_1 = 32'h00000004; // Current PC value
    #10;
    
    instruction = {7'b0000101, 5'd4, 5'd5, 5'd6, 10'd0}; // jmr Example ADD instruction
    A_data = 32'h00000008; // Data for register 2
    B_data = 32'h00000009; // Data for register 3
    PC_1 = 32'h00000004; // Current PC value
    #10; // Wait for clock edge
    
    instruction = {7'b0101110, 5'd27, 5'd28, 15'd0}; // jmr Example ADD instruction
    A_data = 32'h00000006; // Data for register 2
    B_data = 32'h00000007; // Data for register 3
    PC_1 = 32'h00000004; // Current PC value
 
   
    #10; // Wait for clock edge
  instruction = {7'b1100000, 5'd15, 20'd1};// jmr Example ADD instruction
    A_data = 32'h00000005; // Data for register 2
    B_data = 32'h00000003; // Data for register 3
    PC_1 = 32'h00000008; // Current PC value 
    #100;
    $finish;
end

endmodule


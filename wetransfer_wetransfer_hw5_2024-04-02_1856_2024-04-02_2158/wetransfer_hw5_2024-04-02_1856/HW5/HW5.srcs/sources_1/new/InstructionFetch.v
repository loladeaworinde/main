`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 03/15/2024 06:47:47 PM
// Design Name: 
// Module Name: InstructionFetch
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


 module InstructionFetch(
    input clk,
    input reset,
    input [31:0] PC,
    output [31:0] PC_updated,
    output [31:0] IR

);
    reg [31:0] instruction_memory[0:255]; 


initial begin
        $readmemb("divide.mem", instruction_memory);
    end
    
   // Read the instruction from memory
         assign PC_updated = PC + 1;
         assign IR = instruction_memory[PC[31:0]]; 
endmodule


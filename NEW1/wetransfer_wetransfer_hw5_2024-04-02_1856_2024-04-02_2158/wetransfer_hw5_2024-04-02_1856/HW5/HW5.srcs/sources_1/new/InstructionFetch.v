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
    input [31:0] next_PC,
    output wire [31:0] PC_increment,
    output reg [31:0] PC_updated,
    output reg [31:0] IR

);
    wire [31:0] instruction;
    reg [31:0] instruction_memory[0:255]; 


initial begin
        $readmemb("divide.mem", instruction_memory);
    end
    
    assign instruction = instruction_memory[next_PC[31:0]]; // Read the instruction from memory
    assign PC_increment = next_PC + 1;
    
always @(negedge clk) begin
    if (reset) begin
        PC_updated <= 0;
        IR <= 0;
        PC_updated <= 0;
    end else begin
         PC_updated = PC_increment;
         IR <= instruction;
    end
end

endmodule


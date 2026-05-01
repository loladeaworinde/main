`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 03/16/2024 11:43:40 PM
// Design Name: 
// Module Name: memaccess
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


module MEMStage(
    input clk,
    input reset,
    input MW,          // Control signal to write to memory
    input [31:0] address,  
    input [31:0] writeData,  // Data to write to memory
    output wire [31:0] readData // Data read from memory
);
    reg [31:0] dataMemory[0:25]; 
    integer i;
    
    always @(posedge clk) begin
        if (reset) begin
            for (i = 0; i < 25; i = i + 1) begin
                dataMemory[i] <= 32'b0;
                end
        end else 
        begin
            if (MW) begin
                dataMemory[address[31:2]] <= writeData; // Word-aligned addressing
            end

        end
    end
  assign readData = dataMemory[address[31:2]]; 

endmodule


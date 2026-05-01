`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 03/13/2024 09:07:10 PM
// Design Name: 
// Module Name: Register
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


module RegisterFile(
    input clk,
    input reset,
    input RW,
    input [4:0] SA,
    input [4:0] SB,
    input [4:0] DA,
    input [31:0] writeData,
    output [31:0] readData1,
    output [31:0] readData2
);

    reg [31:0] registers [0:31];
    integer i;
    // Reset and Write operations
        assign readData1 = (SA != 0) ? registers[SA] : 32'b0;
        assign readData2 = (SB != 0) ? registers[SB] : 32'b0;
    
    always @(posedge clk) begin
        if (reset) begin          
            for (i = 0; i < 32; i = i + 1) begin
                registers[i] <= 32'b0;
            end
        end else if (RW && DA != 0) begin
            registers[DA] <= writeData;
        end
    end

    // Asynchronous read
    

endmodule

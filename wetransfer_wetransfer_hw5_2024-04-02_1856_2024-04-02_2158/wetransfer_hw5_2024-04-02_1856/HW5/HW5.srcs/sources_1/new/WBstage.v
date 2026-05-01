`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 03/17/2024 12:26:02 AM
// Design Name: 
// Module Name: WBstage
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


module WBStage(
    input clk,
    input reset,
    input [31:0] F_out,  
    input [31:0] memData,    
    input [4:0] DA,
    input RW,      
    input [1:0] MD,
    input N_xor_V,
    output reg [31:0] writeData,   // Data to write to the register file
    output reg [4:0] writeReg,     // Register number to be written to
    output reg writeEnable          // Signal to enable writing to the register
);
    reg [31:0] D_data;
    
    always @(*) begin
    case(MD)
    2'b00: D_data = F_out;
    2'b01: D_data = memData;
    2'b10: D_data = {31'd0, N_xor_V};
    endcase
    end
    
    
    always @(posedge clk) begin
        if (reset) begin
            writeData <= 0;
            writeReg <= 0;
            writeEnable <= 0;
        end else begin
        if (RW)
            writeData <= D_data;
            writeReg <= DA;
            writeEnable <= RW;
        end
    end

endmodule


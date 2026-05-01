`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 03/16/2024 10:17:48 PM
// Design Name: 
// Module Name: EXstage
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


module EXStage(
    input clk,
    input reset,
    input [31:0] A,  
    input [31:0] B,
    input [31:0] PC,  
    input RW,           // Memory Read control signal
    input MW,
    input [4:0] DA,          
    input [4:0] FS,  // ALU control signal
    input [4:0] SH,
    input [1:0]BS,
    input PS,
    input [1:0]MD,
    output [31:0] F_out,  // Result of the ALU operation
    output [31:0] readDataFromMem, // Data read from memory
    output RW_out,       // Output signal to indicate memory read operation to the next stage
    output N_xor_V,
    output [31:0] DA_out,
    output [1:0]muxD_out,
    output [31:0]BrA,
    output [1:0] pcsrc
);

    // Instantiate the ALU
    wire [31:0] F;
    wire ZFlag;  // ALU sets this flag if the result is zero
    wire VFlag;  // ALU sets this flag if there is an overflow
    wire NFlag;  // ALU sets this flag if the result is negative
    wire CFlag;  // ALU sets this flag if there is a carry out
    wire [31:0] dataMemOut;
    wire n_xor_v;
    
    assign n_xor_v = NFlag ^ VFlag;
    assign BrA = B + PC;
    assign pcsrc = {BS[1], (((PS ^ ZFlag) || BS[1]) & BS[0])};
    
    ALU u1(  
        .A(A),
        .B(B),
        .FS(FS),
        .SH(SH),
        .F(F),
        .Z(ZFlag),
        .V(VFlag),
        .N(NFlag),
        .C(CFlag)
    );


    MEMStage u2(
        .clk(clk),
        .reset (reset),
        .address(A),  // The address for memory operations is the output of the ALU
        .writeData(B),  // Data to write to memory (might come from a register)
        .MW(MW),
        .readData(dataMemOut)
    );

    assign RW_out = RW;
    assign DA_out = DA;
    assign muxD_out = MD;
endmodule




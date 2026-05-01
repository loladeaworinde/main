`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 03/18/2024 04:34:34 PM
// Design Name: 
// Module Name: tb
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


`timescale 1ns / 1ps

module ALU_testbench;

    // Inputs
    reg [31:0] A;
    reg [31:0] B;
    reg [4:0] FS;
    reg [4:0] SH;

    // Outputs
    wire [31:0] F;
    wire Z;
    wire V;
    wire N;
    wire C;

    // Instantiate the ALU module
    ALU alu (
        .A(A), 
        .B(B), 
        .FS(FS), 
        .SH(SH), 
        .F(F), 
        .Z(Z), 
        .V(V), 
        .N(N), 
        .C(C)
    );

    // Test sequence
    initial begin
        // Initialize Inputs
        A = 0;
        B = 0;
        FS = 0;
        SH = 0;

        // Add delay for global reset to finish
        #100;
        

        // Test case 7: LSL
        A = 32'h0001; SH = 5'd15; FS = 5'b10000;
        #10;

        // Test case 8: LSR
        A = 32'h0002; SH = 5'd10; FS = 5'b10000;
        #10;
        end
endmodule

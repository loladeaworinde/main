`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 03/16/2024 03:00:11 PM
// Design Name: 
// Module Name: ALU
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


module ALU(
    input [31:0] A,            // Operand A
    input [31:0] B,            // Operand B
    input [4:0] FS,            // Function Select
    input [4:0] SH,            // Shift amount for shift operations
    output reg [31:0] F,       // ALU result
    output reg Z,              // Zero flag
    output reg V,              // Overflow flag
    output reg N,              // Negative flag
    output reg C               // Carry out flag
);

    // Main ALU computation
    always @(*) begin
        // Initialize flags
        Z = 0;
        V = 0;
        N = 0;
        C = 0;

        case (FS)
            5'b00000: begin
            F = A;
            end
            
            5'b00010: begin // ADD
                {C, F} = A + B; //carry
                V = (~A[31] & ~B[31] & F[31]) | (A[31] & B[31] & ~F[31]); // Calculate overflow
            end
            5'b00101: begin // SUB
                {C, F} = A - B; //result and borrow
                V = (~A[31] & B[31] & F[31]) | (A[31] & ~B[31] & ~F[31]); // Calculate overflow
            end
            5'b01000: begin // AND
                F = A & B;
            end
            5'b01010: begin // OR
                F = A | B;
            end
            5'b01100: begin // XOR
                F = A ^ B;
            end
            5'b01110: begin // NOT A
                F = ~A;
            end
            5'b10000: begin // LSL (Logical Shift Left)
                F = A << SH;
                C = A[31]; //  carry
            end
            5'b10001: begin //  for LSR (Logical Shift Right)
                F = A >> SH;
                C = A[0]; //  carry
            end
            
            default: F = 32'b0; // Default case
        endcase
        
        Z = (F == 32'b0);
        N = F[31];
    end
   
endmodule

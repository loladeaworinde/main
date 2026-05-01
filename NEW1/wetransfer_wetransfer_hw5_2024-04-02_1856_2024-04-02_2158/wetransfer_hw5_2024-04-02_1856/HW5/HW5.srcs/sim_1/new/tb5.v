`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 03/18/2024 10:59:40 PM
// Design Name: 
// Module Name: tb5
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


module EXStage_tb();

    // Parameters of EXStage
    parameter WIDTH = 32;
    
    // Testbench Signals
    reg clk_tb;
    reg reset_tb;
    reg [WIDTH-1:0] A_tb;
    reg [WIDTH-1:0] B_tb;
    reg [WIDTH-1:0] PC_tb;
    reg RW_tb;
    reg MW_tb;
    reg [4:0] DA_tb;
    reg [4:0] FS_tb;
    reg [4:0] SH_tb;
    reg [1:0] BS_tb;
    reg PS_tb;
    reg [1:0] MD_tb;
    wire [WIDTH-1:0] F_out_tb;
    wire [WIDTH-1:0] readDataFromMem_tb;
    wire RW_out_tb;
    wire N_xor_V_tb;
    wire [31:0] DA_out_tb;
    wire [1:0] muxD_out_tb;
    wire [WIDTH-1:0] BrA_tb;
    wire [1:0] pcsrc_tb;

    // Instantiate the Unit Under Test (UUT)
    EXStage uut(
        .clk(clk_tb),
        .reset(reset_tb),
        .A(A_tb),
        .B(B_tb),
        .PC(PC_tb),
        .RW(RW_tb),
        .MW(MW_tb),
        .DA(DA_tb),
        .FS(FS_tb),
        .SH(SH_tb),
        .BS(BS_tb),
        .PS(PS_tb),
        .MD(MD_tb),
        .F_out(F_out_tb),
        .readDataFromMem(readDataFromMem_tb),
        .RW_out(RW_out_tb),
        .N_xor_V(N_xor_V_tb),
        .DA_out(DA_out_tb),
        .muxD_out(muxD_out_tb),
        .BrA(BrA_tb),
        .pcsrc(pcsrc_tb)
    );

    // Clock Generation
    always #5 clk_tb = ~clk_tb;  // Generate a clock with a period of 10ns

    // Test Cases
    initial begin
        // Initialize Testbench Signals
        clk_tb = 0;
        reset_tb = 1;
        A_tb = 0;
        B_tb = 0;
        PC_tb = 0;
        RW_tb = 0;
        MW_tb = 0;
        DA_tb = 0;
        FS_tb = 0;
        SH_tb = 0;
        BS_tb = 0;
        PS_tb = 0;
        MD_tb = 0;

        // Wait for global reset
        #15;
        reset_tb = 0;
        
        // Add operation test
        A_tb = 32'd10;
        B_tb = 32'd20;
        PC_tb = 32'd4;
        FS_tb = 5'b00010; // ALU operation code for add
        #10; // Wait for one clock cycle
        
        // Subtraction operation test
        A_tb = 32'd30;
        B_tb = 32'd20;
        FS_tb = 5'b00101; // ALU operation code for sub
        #10;
        
        // Memory write test
        MW_tb = 1'b1; // Enable memory write
        A_tb = 32'd20; // Memory address
        B_tb = 32'd6; // Data to write
        #10;
        
        // Memory read test
        A_tb = 32'd20; // Memory address to read from
        #10;
        
        A_tb = 32'h00000001; // Example operand
        B_tb = 32'd0;        // Not used in shift operation
        FS_tb = 5'b10000;    // ALU operation code for LSL
        SH_tb = 5'd1;        // Shift by 1
        #10; // Wait for one clock cycle

// LSR operation test: Shift right should not affect N or V, but will affect Z if result is zero
        A_tb = 32'h00000002; // Example operand
        B_tb = 32'd0;        // Not used in shift operation
        FS_tb = 5'b10001;    // ALU operation code for LSR
        SH_tb = 5'd1;        // Shift by 1
        #10; // Wait for one clock cycle
        
        // Test case to trigger N and V flags
// Use subtraction as an example where the result will be negative
// and there will be overflow when subtracting a large positive number from a small one
        A_tb = 32'h00000001; // Small positive number
        B_tb = 32'h80000000; // Large negative number represented in two's complement
        FS_tb = 5'b00101;    // ALU operation code for SUB
        #10; // Wait for one clock cycle



        A_tb = 32'h00000000; // Operand to ensure ZFlag is set to 1 due to the result being zero
        B_tb = 32'h00000000; // Operand to ensure ZFlag is set to 1 due to the result being zero
        PS_tb = 1'b1;        // Set PS to 1 to get a different result from ZFlag
        BS_tb = 2'b10;       // Set BS to indicate a branch should take place
        FS_tb = 5'b00000;    // ALU operation that results in a zero output (e.g., AND operation with zero)
        #10; // Wait for one clock cycle
        
        // Reset the system
        reset_tb = 1;
        #10;
        reset_tb = 0;
        
        // More tests can be added here for different instructions and scenarios
    end
endmodule


`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 03/20/2024 01:02:42 AM
// Design Name: 
// Module Name: tbwb
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

module WBStage_tb;

    // Inputs
    reg clk;
    reg reset;
    reg [31:0] F_out;
    reg [31:0] memData;
    reg [4:0] DA;
    reg RW;
    reg [1:0] MD;
    reg N_xor_V;

    // Outputs
    wire [31:0] writeData;
    wire [4:0] writeReg;
    wire writeEnable;

    // Instantiate the Unit Under Test (UUT)
    WBStage uut (
        .clk(clk),
        .reset(reset),
        .F_out(F_out),
        .memData(memData),
        .DA(DA),
        .RW(RW),
        .MD(MD),
        .N_xor_V(N_xor_V),
        .writeData(writeData),
        .writeReg(writeReg),
        .writeEnable(writeEnable)
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = !clk; // Generate a clock with a period of 10 ns
    end

    // Test procedure
    initial begin
        // Initialize inputs
        reset = 1;
        F_out = 0;
        memData = 0;
        DA = 0;
        RW = 0;
        MD = 0;
        N_xor_V = 0;

        // Reset the system
        #100;
        reset = 0; // Release reset

        // Test Case 1: Write F_out to register
        F_out = 32'hA5A5A5A5;
        DA = 5;
        RW = 1;
        MD = 2'b00; // Select F_out
        #10;

        // Test Case 2: Write memData to register
        memData = 32'h5A5A5A5A;
        DA = 10;
        RW = 1;
        MD = 2'b01; // Select memData
        #10;

        // Test Case 3: Write N_xor_V flag to register (as 32-bit with zeros)
        N_xor_V = 1; // Assuming this is a valid value
        DA = 15;
        RW = 1;
        MD = 2'b10; // Select N_xor_V flag
        #10;

        // Test Case 4: Test reset functionality
        reset = 1; // Assert reset
        #10;
        reset = 0; // Deassert reset
        #10;

        // Test Case 5: Test with RW disabled
        F_out = 32'hDEADBEEF;
        DA = 20;
        RW = 0; // RW disabled, should not write
        MD = 2'b00; // Select F_out
        #10;

        
    end

endmodule


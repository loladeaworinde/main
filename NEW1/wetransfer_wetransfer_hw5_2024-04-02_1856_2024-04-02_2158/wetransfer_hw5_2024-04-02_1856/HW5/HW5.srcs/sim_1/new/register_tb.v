`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 03/19/2024 11:47:21 PM
// Design Name: 
// Module Name: register_tb
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

module RegisterFile_tb;

    // Inputs
    reg clk;
    reg reset;
    reg RW;
    reg [4:0] SA;
    reg [4:0] SB;
    reg [4:0] DA;
    reg [31:0] writeData;

    // Outputs
    wire [31:0] readData1;
    wire [31:0] readData2;

    // Instantiate the Unit Under Test (UUT)
    RegisterFile uut (
        .clk(clk), 
        .reset(reset), 
        .RW(RW), 
        .SA(SA), 
        .SB(SB), 
        .DA(DA), 
        .writeData(writeData), 
        .readData1(readData1), 
        .readData2(readData2)
    );

    initial begin
        // Initialize Inputs
        clk = 0;
        reset = 1;
        RW = 0;
        SA = 0;
        SB = 0;
        DA = 0;
        writeData = 0;

        // Wait 100 ns for global reset to finish
        #100;
        
        // Add stimulus here
        reset = 0; // Release reset
        #10;

        // Test 1: Write to a register and read back
        RW = 1; DA = 5; writeData = 32'hA5A5A5A5; // Write A5A5A5A5 to register 5
        #10; RW = 0; SA = 5; SB = 0; // Read from register 5
        #10;

        // Test 2: Write to another register and read both
        RW = 1; DA = 10; writeData = 32'h5A5A5A5A; // Write 5A5A5A5A to register 10
        #10; RW = 0; SA = 5; SB = 10; // Read from register 5 and 10
        #10;

        // Test 3: Reset and check if all registers are cleared
        reset = 1;
        #10; reset = 0; SA = 5; SB = 10;
        #10;

        // Test 4: Ensure register 0 is always 0 when read, regardless of write attempts
        RW = 1; DA = 0; writeData = 32'hFFFFFFFF; // Attempt to write FFFFFFFF to register 0
        #10; RW = 0; SA = 0; SB = 1; // Read from register 0 and 1
        #10;
    end
    
    // Clock generator
    always #5 clk = !clk; // Toggle clock every 5 ns
    
endmodule


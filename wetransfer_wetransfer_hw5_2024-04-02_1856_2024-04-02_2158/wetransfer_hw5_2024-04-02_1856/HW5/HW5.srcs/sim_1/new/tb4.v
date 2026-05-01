`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 03/18/2024 10:35:10 PM
// Design Name: 
// Module Name: tb4
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

module MEMStage_tb();

    reg clk_tb;
    reg reset_tb;
    reg MW_tb;
    reg [31:0] address_tb;
    reg [31:0] writeData_tb;
    wire [31:0] readData_tb;

    // Instantiate the Unit Under Test (UUT)
    MEMStage uut(
        .clk(clk_tb),
        .reset(reset_tb),
        .MW(MW_tb),
        .address(address_tb),
        .writeData(writeData_tb),
        .readData(readData_tb)
    );

    // Clock generation
    always #5 clk_tb = ~clk_tb; // Clock with a period of 10ns

    initial begin
        // Initialize Inputs
        clk_tb = 0;
        reset_tb = 1; // Start with reset to initialize the memory
        MW_tb = 0;
        address_tb = 0;
        writeData_tb = 0;

        // Wait for global reset
        #100;
        reset_tb = 0; // Release reset

        // Test memory write
        address_tb = 4;
        writeData_tb = 32'hAABBCCDD;
        MW_tb = 1; // Enable write
        #10;
        MW_tb = 0; // Disable write for subsequent cycles

        // Test memory read
        #10;
        address_tb = 4; // Set address to the previously written location


        #100;
    end

endmodule


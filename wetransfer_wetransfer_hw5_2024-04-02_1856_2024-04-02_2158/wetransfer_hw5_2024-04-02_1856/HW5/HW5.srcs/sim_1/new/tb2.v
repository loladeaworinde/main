`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 03/18/2024 06:58:54 PM
// Design Name: 
// Module Name: tb2
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

module InstructionFetch_tb;

    // Testbench Inputs
    reg clk_tb;
    reg reset_tb;
    reg [31:0] next_PC_tb;

    // Testbench Outputs
    wire [31:0] PC_tb;
    wire [31:0] PC_updated_tb;
    wire [31:0] IR_tb;

    // Instantiate the InstructionFetch module
    InstructionFetch uut (
        .clk(clk_tb),
        .reset(reset_tb),
        .next_PC(next_PC_tb),
        .PC(PC_tb),
        .PC_updated(PC_updated_tb),
        .IR(IR_tb)
    );

    // Clock generation
    initial begin
        clk_tb = 0;
        forever #5 clk_tb = ~clk_tb; // Generate a clock with period 10 ns
    end

    // Test cases
    initial begin
        // Initialize Inputs
        reset_tb = 1;
        next_PC_tb = 0;

        // Reset the system
        #10;
        reset_tb = 0;

        // Case 1: Normal operation - increment PC
        #10;
        next_PC_tb = 32'd1;

        // Case 2: Check PC update and instruction fetch
        #10;
        next_PC_tb = 32'd2;
        
         #10;
        next_PC_tb = 32'h18;
        
         #10;
        next_PC_tb = 32'd21;

        // Case 3: Test reset functionality
        #10;
        reset_tb = 1;
        #10;
        reset_tb = 0;

        // Additional test cases can be added here

        // Finish the simulation
        #100;
  
    end

    // Monitor changes and print
    
endmodule


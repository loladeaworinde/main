`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 03/19/2024 05:42:35 PM
// Design Name: 
// Module Name: RISC_TB
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



module RISC_CPUPipeline_Testbench();

    reg clk;
    reg reset;


    // Instantiate the RISC CPU with the external PC connections
    RISCCPUTop cpu(
        .clk(clk),
        .reset(reset)


 
    );

 initial begin
    clk = 0;
    forever #5 clk = !clk; // 100MHz clock
end
    
    initial begin
        // Initialize inputs 
        clk = 0;
        reset = 1;


        // Reset the CPU
        #15;  // Hold reset for 100ns
        reset = 0;  // Release reset
        #10;
       

        #500;
     end


endmodule


`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 03/15/2024 08:24:07 PM
// Design Name: 
// Module Name: DecodeOperandFetch
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


module InstructionDecode(
    input [31:0] instruction,
    input [31:0] PC_1,
    input [31:0] A_data,
    input [31:0] B_data,
    output [31:0] A_out,
    output [31:0] B_out,
    output [4:0] DA_out,
    output [6:0] opcode_out,
    output [4:0]FS_out,
    output [4:0] SH_out,
    output MW_out,
    output RW_out,
    output [1:0] MD_out,
    output [1:0] BS_out,
    output PS_out,
    output [31:0] PC_2,
    output [4:0] AA_out,
    output [4:0] BA_out
   
);
    reg CS;
    reg MA;
    reg MB;
    reg [6:0] opcode;
    reg [4:0] FS;
    wire [4:0] SH;
    reg [4:0] DA;
    reg [31:0] A; 
    reg [31:0] B;
    reg [4:0] AA;
    reg [4:0] BA;
    reg MW;
    reg RW;
    reg [1:0] MD;
    reg [1:0] BS;
    reg PS;
    wire [14:0]immediate; 
    reg [31:0] ConstantUnit;
    
    assign immediate = instruction[14:0];
    assign SH = instruction[4:0];
  
   always @(*) begin
    opcode = instruction[31:25];
    DA = instruction[24:20];
    AA = instruction[19:15];
    BA = instruction[14:10];
    
    // Your case statements for decoding remain the same...

    // Update ConstantUnit based on the instruction and CS flag
    if (CS == 1'b0) begin
        ConstantUnit = {17'd0, immediate};
    end else begin
        ConstantUnit = {{17{instruction[14]}}, immediate};
    end

    // Decide the value of A based on MA
    case(MA)
        1'b0: A <= A_data;
        1'b1: A <= PC_1;
        default: A = 32'b0;
    endcase

    // Decide the value of B based on MB
    case(MB)
        1'b0: B <= B_data;
        1'b1: B <= ConstantUnit; // Make sure B gets the value of ConstantUnit when MB is 1
        default: B = 32'b0;
    endcase   

        case (opcode)
            7'b0000000: begin // R-type instruction
             RW = 1'b0;
             BS = 2'b00;
             MW = 1'b0;
            end
     
        7'b0000010: begin
        RW = 1'b1;
        MD = 2'b00;
        BS = 2'b00;
        MW = 1'b0;
        FS = 5'b00010;
        MB = 1'b0;
        MA = 1'b0;        
        end
        7'b0000101: begin
        RW = 1'b1;
        MD = 2'b00;
        BS = 2'b00;
        MW = 1'b0;
        FS = 5'b00101;
        MB = 1'b0;
        MA = 1'b0;     
        end
        7'b1100101:begin
        RW = 1'b1;
        MD = 2'b10;
        BS = 2'b00;
        MW = 1'b0;
        FS = 5'b00101;
        MB = 1'b0;
        MA = 1'b0;     
        end
        7'b0001000: begin
        RW = 1'b1;
        MD = 2'b00;
        BS = 2'b00;
        MW = 1'b0;
        FS = 5'b01000;
        MB = 1'b0;
        MA = 1'b0;     
        end
        7'b0001010: begin
        RW = 1'b1;
        MD = 2'b00;
        BS = 2'b00;
        MW = 1'b0;
        FS = 5'b01010;
        MB = 1'b0;
        MA = 1'b0;     
        end
        7'b0001100: begin
        RW = 1'b1;
        MD = 2'b00;
        BS = 2'b00;
        MW = 1'b0;
        FS = 5'b01100;
        MB = 1'b0;
        MA = 1'b0;     
        end
        7'b0000001: begin
        RW = 1'b0;
        MD = 2'b00;
        BS = 2'b00;
        MW = 1'b1;
        MB = 1'b0;
        MA = 1'b0;     
        end
        7'b0100001: begin
        RW = 1'b1;
        MD = 2'b00;
        BS = 2'b00;
        MW = 1'b0;
        MA = 1'b0;     
        end
        7'b0100010: begin
        RW = 1'b1;
        MD = 2'b00;
        BS = 2'b00;
        MW = 1'b0;
        FS = 5'b00010;
        MB = 1'b1;
        MA = 1'b0; 
        CS = 1'b1;    
        end
        7'b0100101: begin
        RW = 1'b1;
        MD = 2'b00;
        BS = 2'b00;
        MW = 1'b0;
        FS = 5'b00101;
        MB = 1'b1;
        MA = 1'b0; 
        CS = 1'b1;    
        end
        7'b0101110: begin
        RW = 1'b1;
        MD = 2'b00;
        BS = 2'b00;
        MW = 1'b0;
        FS = 5'b01110;
        MA = 1'b0; 
        end
        7'b0101000: begin
        RW = 1'b1;
        MD = 2'b00;
        BS = 2'b00;
        MW = 1'b0;
        FS = 5'b01000;
        MB = 1'b1;
        MA = 1'b0; 
        CS = 1'b0;    
        end
        7'b0101010: begin
        RW = 1'b1;
        MD = 2'b00;
        BS = 2'b00;
        MW = 1'b0;
        FS = 5'b01010;
        MB = 1'b1;
        MA = 1'b0; 
        CS = 1'b1;    
        end
        7'b0101100: begin
        RW = 1'b1;
        MD = 2'b00;
        BS = 2'b00;
        MW = 1'b0;
        FS = 5'b01100;
        MB = 1'b1;
        MA = 1'b0; 
        CS = 1'b1;    
        end
        7'b1100010: begin
        RW = 1'b1;
        MD = 2'b00;
        BS = 2'b00;
        MW = 1'b0;
        FS = 5'b00010;
        MB = 1'b1;
        MA = 1'b0; 
        CS = 1'b1;    
        end
        7'b1100101: begin
        RW = 1'b1;
        MD = 2'b00;
        BS = 2'b00;
        MW = 1'b0;
        FS = 5'b00101;
        MB = 1'b1;
        MA = 1'b0; 
        CS = 1'b1;    
        end
        7'b1000000: begin
        RW = 1'b1;
        MD = 2'b00;
        BS = 2'b00;
        MW = 1'b0;
        FS = 5'b00000;
        MA = 1'b0;    
        end
        7'b0110000: begin
        RW = 1'b1;
        MD = 2'b00;
        BS = 2'b00;
        MW = 1'b0;
        FS = 5'b10000;
        MA = 1'b0;   
        end
        7'b0110001: begin
        RW = 1'b1;
        MD = 2'b00;
        BS = 2'b00;
        MW = 1'b0;
        FS = 5'b10001;
        MA = 1'b0;    
        end
        7'b1100001: begin
        RW = 1'b0;
        BS = 2'b10;
        MW = 1'b0;  
        end
        7'b0100000: begin
         RW = 1'b0;
        BS = 2'b01;
        MW = 1'b0;
        FS = 5'b00000;
        MB = 1'b1;
        MA = 1'b0; 
        CS = 1'b1;
        PS = 1'b0;
        end  
        7'b1100000: begin
          RW = 1'b0;
        BS = 2'b01;
        MW = 1'b0;
        FS = 5'b00000;
        MB = 1'b1;
        MA = 1'b0; 
        CS = 1'b1;
        PS = 1'b1;    
        end
        7'b1000100: begin
          RW = 1'b0;
        BS = 2'b11;
        MW = 1'b0;
        MB = 1'b1; 
        CS = 1'b1;    
        end
        7'b0000111: begin
          RW = 1'b1;
        MD = 2'b00;
        BS = 2'b11;
        MW = 1'b0;
        FS = 5'b00111;
        MB = 1'b1;
        MA = 1'b1; 
        CS = 1'b1;    
        end

        endcase
        
       
    end
    assign PC_1 = PC_2;
     
    
endmodule
`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 03/19/2024 02:35:40 PM
// Design Name: 
// Module Name: RISC_TOP
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

module RISCCPUTop(
    input clk,
    input reset
);

    // Inter-stage signals
    wire [31:0] IF_PC;
    wire [31:0] IF_PC_updated;
    wire [31:0] IF_IR;

    wire [31:0] ID_A_out;
    wire [31:0] ID_B_out;
    wire [4:0] ID_DA_out;
    wire [6:0] ID_opcode_out;
    wire [4:0] ID_FS_out;
    wire [4:0] ID_SH_out;
    wire ID_MW_out;
    wire ID_RW_out;
    wire [1:0] ID_MD_out;
    wire [1:0] ID_BS_out;
    wire ID_PS_out;
    wire [31:0] ID_PC_2;
    wire [4:0] ID_AA_out;
    wire [4:0] ID_BA_out;

    wire [31:0] EX_F_out;
    wire [31:0] EX_readDataFromMem;
    wire EX_RW_out;
    wire EX_N_xor_V;
    wire [4:0] EX_DA_out;
    wire [1:0] EX_muxD_out;
    wire [31:0] EX_BrA;
    wire [1:0] EX_pcsrc;

    wire [31:0] WB_writeData;
    wire [4:0] WB_writeReg;
    wire WB_writeEnable;

    wire [31:0] MUX_C_next_PC;


    // Instantiate IF Stage
    InstructionFetch IF(
        .clk(clk),
        .reset(reset),
        .next_PC(MUX_C_next_PC),
        .PC(IF_PC),
        .PC_updated(IF_PC_updated),
        .IR(IF_IR)
    );

    // Register file connections
    wire [31:0] regFile_readData1;
    wire [31:0] regFile_readData2;

    RegisterFile regFile(
        .clk(clk),
        .reset(reset),
        .RW(WB_writeEnable),
        .SA(ID_AA_out),
        .SB(ID_BA_out),
        .DA(WB_writeReg),
        .writeData(WB_writeData),
        .readData1(regFile_readData1),
        .readData2(regFile_readData2)
    );

    // Instantiate ID Stage
    InstructionDecode ID(
        .clk(clk),
        .reset(reset),
        .instruction(IF_IR),
        .PC_1(IF_PC_updated),
        .A_data(regFile_readData1),
        .B_data(regFile_readData2),
        .A_out(ID_A_out),
        .B_out(ID_B_out),
        .DA_out(ID_DA_out),
        .opcode_out(ID_opcode_out),
        .FS_out(ID_FS_out),
        .SH_out(ID_SH_out),
        .MW_out(ID_MW_out),
        .RW_out(ID_RW_out),
        .MD_out(ID_MD_out),
        .BS_out(ID_BS_out),
        .PS_out(ID_PS_out),
        .PC_2(ID_PC_2),
        .AA_out(ID_AA_out),
        .BA_out(ID_BA_out)
    );

    // Instantiate EX Stage
    EXStage EX(
        .clk(clk),
        .reset(reset),
        .A(regFile_readData1),
        .B(ID_B_out),
        .PC(ID_PC_2),
        .RW(ID_RW_out),
        .MW(ID_MW_out),
        .DA(ID_DA_out),
        .FS(ID_FS_out),
        .SH(ID_SH_out),
        .BS(ID_BS_out),
        .PS(ID_PS_out),
        .MD(ID_MD_out),
        .F_out(EX_F_out),
        .readDataFromMem(EX_readDataFromMem),
        .RW_out(EX_RW_out),
        .N_xor_V(EX_N_xor_V),
        .DA_out(EX_DA_out),
        .muxD_out(EX_muxD_out),
        .BrA(EX_BrA),
        .pcsrc(EX_pcsrc)
    );

    // Instantiate WB Stage
    WBStage WB(
        .clk(clk),
        .reset(reset),
        .F_out(EX_F_out),
        .memData(EX_readDataFromMem),
        .DA(EX_DA_out),
        .RW(EX_RW_out),
        .MD(EX_muxD_out),
        .N_xor_V(EX_N_xor_V),
        .writeData(WB_writeData),
        .writeReg(WB_writeReg),
        .writeEnable(WB_writeEnable)
    );

    // Instantiate MUX_C
    MUX_C muxC(
        .PC_updated(IF_PC_updated),
        .BrA(EX_BrA),
        .RAA(ID_A_out),  
        .MC(EX_pcsrc),
        .next_PC(MUX_C_next_PC)
    );


endmodule


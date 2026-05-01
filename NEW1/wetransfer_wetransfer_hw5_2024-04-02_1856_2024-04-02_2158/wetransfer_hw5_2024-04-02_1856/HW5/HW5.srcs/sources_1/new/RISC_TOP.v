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
    // Define all pipeline registers needed for IF/ID, ID/EX, and EX/WB stages
    reg [31:0] IF_next_PC;
    // IF/ID Pipeline Registers
    reg [31:0] IFID_PC_updated;
    reg [31:0] IFID_IR;

    // ID/EX Pipeline Registers
    reg [31:0] IDEX_A_out;
    reg [31:0] IDEX_B_out;
    reg [4:0] IDEX_DA_out;
    reg [6:0] IDEX_opcode_out;
    reg [4:0] IDEX_FS_out;
    reg [4:0] IDEX_SH_out;
    reg IDEX_MW_out;
    reg IDEX_RW_out;
    reg [1:0] IDEX_MD_out;
    reg [1:0] IDEX_BS_out;
    reg IDEX_PS_out;
    reg [31:0] IDEX_PC_2;

    // EX/WB Pipeline Registers
    reg [31:0] EXWB_F_out;
    reg [31:0] EXWB_readDataFromMem;
    reg EXWB_RW_out;
    reg [4:0] EXWB_DA_out;
    reg [1:0] EXWB_muxD_out;
    reg EXWB_N_xor_out;
    
    reg [31:0] RWB_writeData;
    reg [4:0] RWB_writeReg;
    reg RWB_writeEnable;
    
    wire [31:0] IF_PC;
    wire [31:0] IF_PC_increment;
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

    wire [31:0] MUXC_next_PC;
    
     always @(negedge clk) begin
        if (reset) begin
            IF_next_PC <= 0;
        end else begin
            IF_next_PC <= MUXC_next_PC;
        end
    end

    // Pipeline register captures for IF/ID
    always @(negedge clk) begin
        if (reset) begin
            IFID_PC_updated <= 0;
            IFID_IR <= 0;
        end else begin
            IFID_PC_updated <= IF_PC_updated;
            IFID_IR <= IF_IR;
        end
    end

    // Pipeline register captures for ID/EX
    always @(negedge clk) begin
        if (reset) begin
            IDEX_A_out <= 0;
            IDEX_B_out <= 0;
            IDEX_DA_out <= 0;
            IDEX_opcode_out <= 0;
            IDEX_FS_out <= 0;
            IDEX_SH_out <= 0;
            IDEX_MW_out <= 0;
            IDEX_RW_out <= 0;
            IDEX_MD_out <= 0;
            IDEX_BS_out <= 0;
            IDEX_PS_out <= 0;
            IDEX_PC_2 <= 0;
        end else begin
            IDEX_A_out <= ID_A_out;
            IDEX_B_out <= ID_B_out;
            IDEX_DA_out <= ID_DA_out;
            IDEX_opcode_out <= ID_opcode_out;
            IDEX_FS_out <= ID_FS_out;
            IDEX_SH_out <= ID_SH_out;
            IDEX_MW_out <= ID_MW_out;
            IDEX_RW_out <= ID_RW_out;
            IDEX_MD_out <= ID_MD_out;
            IDEX_BS_out <= ID_BS_out;
            IDEX_PS_out <= ID_PS_out;
            IDEX_PC_2 <= ID_PC_2;
        end
    end

    // Pipeline register captures for EX/WB
    always @(negedge clk) begin
        if (reset) begin
            EXWB_F_out <= 0;
            EXWB_readDataFromMem <= 0;
            EXWB_RW_out <= 0;
            EXWB_DA_out <= 0;
            EXWB_muxD_out <= 0;
            EXWB_N_xor_out <= 0;
        end else begin
            EXWB_F_out <= EX_F_out;
            EXWB_readDataFromMem <= EX_readDataFromMem;
            EXWB_RW_out <= EX_RW_out;
            EXWB_DA_out <= EX_DA_out;
            EXWB_muxD_out <= EX_muxD_out;
            EXWB_N_xor_out <= EX_N_xor_V;
        end
    end
    

    // Inter-stage signals

    // Instantiate IF Stage
    InstructionFetch IF(
        .clk(clk),
        .reset(reset),
        .next_PC(IF_next_PC),
        .PC_increment(IF_PC_increment),
        .PC_updated(IF_PC_updated),
        .IR(IF_IR)
    );
    
 // Register file connections

    
   
    // Instantiate ID Stage
    InstructionDecode ID(
        .clk(clk),
        .reset(reset),
        .instruction(IFID_IR),
        .PC_1(IFID_PC_updated),
        .writeD_WB(WB_writeData),
        .RW_in_WB(WB_writeEnable),
        .DA_WB(WB_writeReg),
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
        .PC_2(ID_PC_2)

    );


    // Instantiate EX Stage
    EXStage EX(
        .clk(clk),
        .reset(reset),
        .A(IDEX_A_out),
        .B(IDEX_B_out),
        .PC(IDEX_PC_2),
        .RW(IDEX_RW_out),
        .MW(IDEX_MW_out),
        .DA(IDEX_DA_out),
        .FS(IDEX_FS_out),
        .SH(IDEX_SH_out),
        .BS(IDEX_BS_out),
        .PS(IDEX_PS_out),
        .MD(IDEX_MD_out),
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
        .F_out(EXWB_F_out),
        .memData(EXWB_readDataFromMem),
        .DA(EXWB_DA_out),
        .RW(EXWB_RW_out),
        .MD(EXWB_muxD_out),
        .N_xor_V(EXWB_N_xor_V),
        .writeData(WB_writeData),
        .writeReg(WB_writeReg),
        .writeEnable(WB_writeEnable)
    );

    // Instantiate MUX_C
    MUX_C muxC(
        .PC_updated(IF_PC_increment),
        .BrA(EX_BrA),
        .RAA(IDEX_A_out),  
        .MC(EX_pcsrc),
        .next_PC(MUXC_next_PC)
    );


endmodule


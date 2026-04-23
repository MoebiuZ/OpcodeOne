#ifndef OPCODEONE_H_
#define OPCODEONE_H_

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <functional>

#define VERSION "0.0.1"

#define ENDIANESS "Big endian"



// MACROS

#define FL (reg[0x0c])
#define SB (reg[0x0d])
#define SP (reg[0x0e])
#define PC (reg[0x0f])


#define READPRI(addr) primary_address_bus[addr]
#define WRITEPRI(addr, val) { primary_address_bus[addr] = (val); }

#define READSEC(addr) secondary_address_bus[addr]
#define WRITESEC(addr, val) { secondary_address_bus[addr] = (val); }


#define OPCODE (READPRI(PC) >> 16)

#define MODE ((READPRI(PC) >> 12) & 0x0f)

#define REG_3 reg[READPRI(PC) & 0x0f]

#define REG_2 reg[(READPRI(PC) >> 4) & 0x0f]

#define REG_1 reg[(READPRI(PC) >> 8) & 0x0f]

#define ADDR READPRI(PC+1)

#define OFFSET1 READPRI(PC+1)

#define OFFSET2 READPRI(PC+2)

#define VALUE READPRI(PC+1)

#define IMM_OFFSET (READPRI(PC >> 8) & 0x0f)


#define REG_PLUS_IMM_D (REG_1 + NEAR_OFFSET)
#define REG_MINUS_IMM_D (REG_1 - NEAR_OFFSET)
#define REG_PLUS_IMM_S (REG_2 + NEAR_OFFSET)
#define REG_MINUS_IMM_S (REG_2 - NEAR_OFFSET)

#define REG_PLUS_REG_OFFSET_D (REG_1 + REG_3)
#define REG_MINUS_REG_OFFSET_D (REG_1 - REG_3)
#define REG_PLUS_REG_OFFSET_S (REG_2 + REG_3)
#define REG_MINUS_REG_OFFSET_S (REG_2 - REG_3)

#define REG_PLUS_OFFSET_D (REG_1 + OFFSET1)
#define REG_MINUS_OFFSET_D (REG_1 - OFFSET1)
#define REG_PLUS_OFFSET_S (REG_2 + OFFSET1)
#define REG_MINUS_OFFSET_S (REG_2 - OFFSET1)

#define ADDR_PLUS_IMM_IMM_OFFSET (ADDR + NEAR_OFFSET)
#define ADDR_MINUS_IMM_OFFSET (ADDR - NEAR_OFFSET)

#define ADDR_PLUS_OFFSET (ADDR + OFFSET2)
#define ADDR_MINUS_OFFSET (ADDR - OFFSET2)

#define ADDR_PLUS_REG_OFFSET (ADDR + REG_3)
#define ADDR_MINUS_REG_OFFSET (ADDR - REG_3)




class OpcodeOne {

public:

	uint32_t *primary_address_bus;
	uint32_t *secondary_address_bus;

	uint32_t reg[16]; // Registers
	/*
		"A": 		0x00,
		"B": 		0x01,
		"C": 		0x02,
		"D": 		0x03,
		"unused1":	0x04,
		"unused2":	0x05,
		"unused3":	0x06,
		"unused4":	0x07,
		"unused5":	0x08,
		"unused6":	0x09,
		"unused7":	0x0a,
		"unused8":	0x0b,
		"FL":		0x0c,
		"SB":		0x0d,
		"SP":		0x0e,
		"PC":		0x0f
	}
	*/
	

	uint8_t halted = 0; // Indicates the machine is halted

	OpcodeOne();
	~OpcodeOne();

	void Run();

	

	void SetIOReadCallback(std::function<uint32_t(uint32_t)> cb);
	void SetIOWriteCallback(std::function<void(uint32_t, uint32_t)> cb);

	
	void Reset();

	// Pin out

	uint8_t GetHLT();
	uint8_t GetABS();


private:


	std::function<uint32_t(uint32_t)> IOReadCallback;
	std::function<void(uint32_t, uint32_t)> IOWriteCallback;

	uint32_t ReadIO(uint32_t addr);
	void WriteIO(uint32_t addr, uint32_t val);

	uint32_t IOReadPlaceholder(uint32_t addr);
	void IOWritePlaceholder(uint32_t addr, uint32_t data);


	// --- Instruction methods ---


	void Inst_ABT();	// ABT (Address Bus Transfer)
	void Inst_ADD();	// ADD (ADDition)
	void Inst_AND();	// AND
	void Inst_BIT();	// BIT
	void Inst_CALL();	// CALL
	void Inst_CMP();	// CMP (CoMPare)
	void Inst_CP();		// CP (CoPy)
	void Inst_DEC();	// DEC (DECrement)
	void Inst_DIV();	// DIV (DIVision)
	void Inst_HALT();	// HALT
	void Inst_IN();		// IN (INput)
	void Inst_INC();	// INC (INCrease)
	void Inst_JMP();	// JMP (JuMP)
	void Inst_LD();		// LD (LoaD)
	void Inst_MUL();	// MUL (MULtiplication)
	void Inst_NAND();	// NAND (Not AND)
	void Inst_NEG();	// NEG (NEGative)
	void Inst_OR();		// OR
	void Inst_OUT();	// OUT (OUTput)
	void Inst_PAR();	// PAR (Primary Address Read)
	void Inst_PAW();	// PAW (Primary Address Write)
	void Inst_POP();	// POP
	void Inst_PUSH();	// PUSH
	void Inst_RET();	// RET (REturn)
	void Inst_ROT();	// ROT (ROTate)
	void Inst_SAR();	// SAR (Secondary Address Read)
	void Inst_SAW();	// SAW (Secondary Address Write)
	void Inst_SH();		// SH (SHift)
	void Inst_SUB();	// SUB (SUBtraction)
	void Inst_SWP();	// SWP (SWaP)
	void Inst_XCHG();	// XCHG (eXCHanGe)
	void Inst_XOR();	// XOR
	
};

#endif
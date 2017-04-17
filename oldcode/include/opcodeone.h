#ifndef OPCODEONE_H_
#define OPCODEONE_H_

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <functional>

#define VERSION "0.0.1"

#define ENDIANESS "Big endian"

#define PC (reg[0x0f])
#define SP (reg[0x0e])



// MACROS 


#define READMEM(addr) memory_bus[addr]
#define WRITEMEM(addr, val) { memory_bus[addr] = (val); }

#define READVID(addr) video_bus[addr]
#define WRITEVID(addr, val) { video_bus[addr] = (val); }




class OpcodeOne {

public:

	uint32_t *memory_bus;
	uint32_t *video_bus;

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

	void Reset();

	void SetIOReadCallback(std::function<uint32_t(uint32_t)> cb);
	void SetIOWriteCallback(std::function<void(uint32_t, uint32_t)> cb);


private:

	// Flags (TODO)
	uint8_t flag_carry;
	uint8_t flag_overflow;
	uint8_t flag_zero;

	std::function<uint32_t(uint32_t)> IOReadCallback;
	std::function<void(uint32_t, uint32_t)> IOWriteCallback;

	uint32_t ReadIO(uint32_t addr);
	void WriteIO(uint32_t addr, uint32_t val);

	uint32_t IOReadPlaceholder(uint32_t addr);
	void IOWritePlaceholder(uint32_t addr, uint32_t data);
	

	// --- Instruction methods ---

	inline void Inst_ADD();		// ADD (ADDition)
	inline void Inst_LD();
	inline void Inst_DBG();
	inline void Inst_HALT();	// HALT
	inline void Inst_MR();	 	// MR (Memory Read)
	inline void Inst_MW();		// MW (Memory Write)
	inline void Inst_VR();	 	// VR (Video memory Read)
	inline void Inst_VW();		// VW (Video memory Write)

	inline void Inst_PUSH();	// PUSH
	inline void Inst_POP();		// POP
	inline void Inst_RET();		// RET (RETurn)
	inline void Inst_JMP();		// JMP (JuMP)
	inline void Inst_CALL();	// CALL
	
};

#endif
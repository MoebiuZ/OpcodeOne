#ifndef INSTRUCTIONS_H_
#define INSTRUCTIONS_H_

#include "opcodeone.h"


#define OPCODE (READMEM(PC) >> 16)

#define MODE ((READMEM(PC) >> 12) & 0x0f)

#define REG_3 reg[READMEM(PC) & 0x0f]

#define REG_2 reg[(READMEM(PC) >> 4) & 0x0f]

#define REG_1 reg[(READMEM(PC) >> 8) & 0x0f]

#define ADDR READMEM(PC+1)

#define OFFSET1 READMEM(PC+1)

#define OFFSET2 READMEM(PC+2)

#define VALUE READMEM(PC+1)

#define NEAR_OFFSET (READMEM(PC >> 8) & 0x0f)


#define REG_PLUS_NEAR_D (REG_1 + NEAR_OFFSET)
#define REG_MINUS_NEAR_D (REG_1 - NEAR_OFFSET)
#define REG_PLUS_NEAR_S (REG_2 + NEAR_OFFSET)
#define REG_MINUS_NEAR_S (REG_2 - NEAR_OFFSET)

#define REG_PLUS_REG_D (REG_1 + REG_3)
#define REG_MINUS_REG_D (REG_1 - REG_3)
#define REG_PLUS_REG_S (REG_2 + REG_3)
#define REG_MINUS_REG_S (REG_2 - REG_3)

#define REG_PLUS_OFFSET_D (REG_1 + OFFSET1)
#define REG_MINUS_OFFSET_D (REG_1 - OFFSET1)
#define REG_PLUS_OFFSET_S (REG_2 + OFFSET1)
#define REG_MINUS_OFFSET_S (REG_2 - OFFSET1)



#define ADDR_PLUS_NEAR (ADDR + NEAR_OFFSET)
#define ADDR_MINUS_NEAR (ADDR - NEAR_OFFSET)

#define ADDR_PLUS_OFFSET (ADDR + OFFSET2)
#define ADDR_MINUS_OFFSET (ADDR - OFFSET2)

#define ADDR_PLUS_REG (ADDR + REG_3)
#define ADDR_MINUS_REG (ADDR - REG_3) 





inline void OpcodeOne::Inst_ADD() {
	/* switch (READ8(PC+1) >> 6) {
	
		
	}

	reg[0] += value + flag_carry;
	
	flag_carry = reg[0] >> 24;*/

}



inline void OpcodeOne::Inst_CALL() {
	SP++;
	WRITEMEM(SP, PC);
	PC = ADDR;
}



inline void OpcodeOne::Inst_LD() {
	switch (MODE) {
		// CP R, R
		case 0x00: REG_1 = REG_2; break;
		// CP R, value
		case 0x01: REG_1= VALUE; PC++; break;
		
		// CP R, R
		default: REG_1 = REG_2; break;
	}
}

// TODO: Extend this function as in assembler
inline void OpcodeOne::Inst_DBG() {
	printf("0x%06x ", REG_1);
}


inline void OpcodeOne::Inst_HALT() {
	halted = 1;	
}


inline void OpcodeOne::Inst_JMP() {
	
}



inline void OpcodeOne::Inst_MR() {
	switch (MODE) {
		// MR R, [R]
		case 0x00: REG_1 = READMEM(REG_2); break;
		// MR R, [R]+near_offset
		case 0x01: REG_1 = READMEM(REG_PLUS_NEAR_S); break;
		// MR R, [R]+reg_offset
		case 0x02: REG_1 = READMEM(REG_PLUS_REG_S); break;
		// MR R, [R]+far_offset
		case 0x03: REG_1 = READMEM(REG_PLUS_OFFSET_S); PC++; break;
		// MR R, [R]-near_offset
		case 0x04: REG_1 = READMEM(REG_MINUS_NEAR_S); break;
		// MR R, [R]-reg_offset
		case 0x05: REG_1 = READMEM(REG_MINUS_REG_S); break;
		// MR R, [R]-far_offset
		case 0x06: REG_1 = READMEM(REG_MINUS_OFFSET_S); PC++; break;
		// MR R, addr
		case 0x07: REG_1 = READMEM(ADDR); PC++; break;
		// MR R, addr+near_offset
		case 0x08: REG_1 = READMEM(ADDR_PLUS_NEAR); PC++; break;
		// MR R, addr+reg_offset
		case 0x09: REG_1 = READMEM(ADDR_PLUS_REG); PC++; break;
		// MR R, addr+far_offset
		case 0x0a: REG_1 = READMEM(ADDR_PLUS_OFFSET); PC += 2; break;
		// MR R, addr-near_offset
		case 0x0b: REG_1 = READMEM(ADDR_MINUS_NEAR); PC++; break;
		// MR R, addr-reg_offset
		case 0x0c: REG_1 = READMEM(ADDR_MINUS_REG); PC++; break;
		// MR R, addr-far_offset
		case 0x0d: REG_1 = READMEM(ADDR_MINUS_OFFSET); PC += 2; break;
	} 
}


inline void OpcodeOne::Inst_MW() {
	switch (MODE) {
		// MW [R], R
		case 0x00: WRITEMEM(REG_1, REG_2); break;
		// MW [R]+near_offset, R
		case 0x01: WRITEMEM(REG_PLUS_NEAR_D, REG_1); break;
		// MW [R]+reg_offset, R
		case 0x02: WRITEMEM(REG_PLUS_REG_D, REG_2); break;
		// MW [R]+far_offset, R
		case 0x03: WRITEMEM(REG_PLUS_OFFSET_D, REG_2); PC++; break;
		// MW [R]-near_offset, R
		case 0x04: WRITEMEM(REG_MINUS_NEAR_D, REG_2); break;
		// MW [R]-reg_offset, R
		case 0x05: WRITEMEM(REG_MINUS_REG_D, REG_2); break;
		// MW [R]-far_offset, R
		case 0x06: WRITEMEM(REG_MINUS_OFFSET_D, REG_2); PC++; break;
		// MW addr, R
		case 0x07: WRITEMEM(ADDR, REG_2); PC++; break;
		// MW addr+near_offset, R
		case 0x08: WRITEMEM(ADDR_PLUS_NEAR, REG_2); PC++; break;
		// MW addr+reg_offset, R
		case 0x09: WRITEMEM(ADDR_PLUS_REG, REG_2); PC++; break;
		// MW addr+far_offset, R
		case 0x0a: WRITEMEM(ADDR_PLUS_OFFSET, REG_2); PC += 2; break;
		// MW addr-near_offset, R
		case 0x0b: WRITEMEM(ADDR_MINUS_NEAR, REG_2); PC++; break;
		// MW addr-reg_offset, R
		case 0x0c: WRITEMEM(ADDR_MINUS_REG, REG_2); PC++; break;
		// MW addr-far_offset, R
		case 0x0d: WRITEMEM(ADDR_MINUS_OFFSET, REG_2); PC += 2; break;
	}
}


inline void OpcodeOne::Inst_POP() {
	SP++;
	REG_1 = READMEM(SP);
}



inline void OpcodeOne::Inst_PUSH() {
	SP--;
	WRITEMEM(SP, REG_1);
}


inline void OpcodeOne::Inst_RET() {
	SP++;
	PC = READMEM(SP);
}


inline void OpcodeOne::Inst_VR() {
	switch (MODE) {
		// VR R, [R]
		case 0x00: REG_1 = READVID(REG_2); break;
		// VR R, [R]+near_offset
		case 0x01: REG_1 = READVID(REG_PLUS_NEAR_S); break;
		// VR R, [R]+reg_offset
		case 0x02: REG_1 = READVID(REG_PLUS_REG_S); break;
		// VR R, [R]+far_offset
		case 0x03: REG_1 = READVID(REG_PLUS_OFFSET_S); PC++; break;
		// VR R, [R]-near_offset
		case 0x04: REG_1 = READVID(REG_MINUS_NEAR_S); break;
		// VR R, [R]-reg_offset
		case 0x05: REG_1 = READVID(REG_MINUS_REG_S); break;
		// VR R, [R]-far_offset
		case 0x06: REG_1 = READVID(REG_MINUS_OFFSET_S); PC++; break;
		// VR R, addr
		case 0x07: REG_1 = READVID(ADDR); PC++; break;
		// VR R, addr+near_offset
		case 0x08: REG_1 = READVID(ADDR_PLUS_NEAR); PC++; break;
		// VR R, addr+reg_offset
		case 0x09: REG_1 = READVID(ADDR_PLUS_REG); PC++; break;
		// VR R, addr+far_offset
		case 0x0a: REG_1 = READVID(ADDR_PLUS_OFFSET); PC += 2; break;
		// VR R, addr-near_offset
		case 0x0b: REG_1 = READVID(ADDR_MINUS_NEAR); PC++; break;
		// VR R, addr-reg_offset
		case 0x0c: REG_1 = READVID(ADDR_MINUS_REG); PC++; break;
		// VR R, addr-far_offset
		case 0x0d: REG_1 = READVID(ADDR_MINUS_OFFSET); PC += 2; break;
	} 
}


inline void OpcodeOne::Inst_VW() {
	switch (MODE) {
		// VW [R], R
		case 0x00: WRITEVID(REG_1, REG_2); break;
		// VW [R]+near_offset, R
		case 0x01: WRITEVID(REG_PLUS_NEAR_D, REG_2); break;
		// VW [R]+reg_offset, R
		case 0x02: WRITEVID(REG_PLUS_REG_D, REG_2); break;
		// VW [R]+far_offset, R
		case 0x03: WRITEVID(REG_PLUS_OFFSET_D, REG_2); PC++; break;
		// VW [R]-near_offset, R
		case 0x04: WRITEVID(REG_MINUS_NEAR_D, REG_2); break;
		// VW [R]-reg_offset, R
		case 0x05: WRITEVID(REG_MINUS_REG_D, REG_2); break;
		// VW [R]-far_offset, R
		case 0x06: WRITEVID(REG_MINUS_OFFSET_D, REG_2); PC++; break;
		// VW addr, R
		case 0x07: WRITEVID(ADDR, REG_2); PC++; break;
		// VW addr+near_offset, R
		case 0x08: WRITEVID(ADDR_PLUS_NEAR, REG_2); PC++; break;
		// VW addr+reg_offset, R
		case 0x09: WRITEVID(ADDR_PLUS_REG, REG_2); PC++; break;
		// VW addr+far_offset, R
		case 0x0a: WRITEVID(ADDR_PLUS_OFFSET, REG_2); PC += 2; break;
		// VW addr-near_offset, R
		case 0x0b: WRITEVID(ADDR_MINUS_NEAR, REG_2); PC++; break;
		// VW addr-reg_offset, R
		case 0x0c: WRITEVID(ADDR_MINUS_REG, REG_2); PC++; break;
		// VW addr-far_offset, R
		case 0x0d: WRITEVID(ADDR_MINUS_OFFSET, REG_2); PC += 2; break;
	}
}

#endif
#include "opcodeone.h"


OpcodeOne::OpcodeOne() {
	SetIOReadCallback(std::bind(&OpcodeOne::IOReadPlaceholder, this, std::placeholders::_1));
	SetIOWriteCallback(std::bind(&OpcodeOne::IOWritePlaceholder, this, std::placeholders::_1, std::placeholders::_2));
}


OpcodeOne::~OpcodeOne() {

}



void OpcodeOne::Run() {

	if (!halted) {
		switch(OPCODE) {

			case 0x01: Inst_HALT(); break;
			case 0x02: Inst_PAR(); break;
			case 0x03: Inst_PAW(); break;
			case 0x04: Inst_SAR(); break;
			case 0x05: Inst_SAW(); break;
			case 0x06: Inst_PUSH(); break;
			case 0x07: Inst_POP(); break;
			case 0x08: Inst_JMP(); break;
			case 0x09: Inst_RET(); break;
			case 0x0a: Inst_ADD(); break;
			case 0x0b: Inst_SUB(); break;
			case 0x0c: Inst_MUL(); break;
			case 0x0d: Inst_DIV(); break;
			case 0x0e: Inst_AND(); break;
			case 0x0f: Inst_OR(); break;
			case 0x10: Inst_XOR(); break;
			case 0x11: Inst_NAND(); break;
			case 0x12: Inst_NEG(); break;
			case 0x13: Inst_IN(); break;
			case 0x14: Inst_OUT(); break;
			case 0x15: Inst_LD(); break;
			case 0x16: Inst_CP(); break;
			case 0x17: Inst_CMP(); break;
			case 0x18: Inst_ROT(); break;
			case 0x19: Inst_SH(); break;
			case 0x1a: Inst_INC(); break;
			case 0x1b: Inst_DEC(); break;			
			case 0x1c: Inst_CALL(); break;
			case 0x1d: Inst_ABT(); break;
			case 0x1e: Inst_BIT(); break;
			case 0x1f: Inst_SWP(); break;
			case 0x20: Inst_XCHG(); break;
			default: break; // NOP (0x00)

		}

		PC++; // All instruction are at least 1 word long. Longer instructions will increase PC accordingly on their cases.

	}
}


void OpcodeOne::Reset() {

	for (int i = 0; i < 16; i++) {
		reg[i] = 0x000000;
	}

	halted = 0;
}


uint32_t OpcodeOne::ReadIO(uint32_t addr) {
	IOReadCallback(addr);
	return addr;
}


void OpcodeOne::WriteIO(uint32_t addr, uint32_t val) {
	IOWriteCallback(addr, val);
}


void OpcodeOne::SetIOReadCallback(std::function<uint32_t(uint32_t)> cb) { 
	IOReadCallback = cb; 
}



void OpcodeOne::SetIOWriteCallback(std::function<void(uint32_t, uint32_t)> cb) { 
	IOWriteCallback = cb; 
}


uint32_t OpcodeOne::IOReadPlaceholder(uint32_t addr) {
	printf("IO Read Callback not set\n");
	return addr;
}



void OpcodeOne::IOWritePlaceholder(uint32_t addr, uint32_t data) {
	printf("IO Write Callback not set\n");
	addr = addr;
	data = data;
}



uint8_t OpcodeOne::GetHLT() {
	return halted;
}
 
uint8_t OpcodeOne::GetABS() {
	return (FL >> 23) & 0x01;
}


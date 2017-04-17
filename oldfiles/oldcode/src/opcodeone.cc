#include "opcodeone.h"
#include "instructions.h"


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
			case 0x02: Inst_MR(); break;
			case 0x03: Inst_MW(); break;
			case 0x04: Inst_VR(); break;
			case 0x05: Inst_VW(); break;
			case 0x06: Inst_LD(); break;
			case 0x07: Inst_DBG(); break;
			case 0x08: Inst_PUSH(); break;
			case 0x09: Inst_POP(); break;
			case 0x0a: Inst_JMP(); break;
			case 0x0b: Inst_RET(); break;
			case 0x0c: Inst_CALL(); break;
		
			default: break; // NOP (0x00)

		}

		PC++;
fflush(stdout);
	}
}


void OpcodeOne::Reset() {

	PC = 0;

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


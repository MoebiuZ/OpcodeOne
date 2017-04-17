#include "assembler.h"


Assembler::Assembler() {}
Assembler::~Assembler() {}

void Assembler::Assemble() {
	instruction("\\b(nop)([^ ]*)");
	PopulateOpcodes();

}


void Assembler::PopulateOpcodes() {
	opcode_list["nop"] = 0x000000;
	opcode_list["add"] = 0x080000;

	printf("%x", opcode_list.at("add"));
}


uint32_t Assembler::GenOpcode(std::string op) {

	
	
	return 0;
}


int main(int argc, char *argv[]) {


	if (argc != 2) {
		printf("Machine assembler v%s\n\nUsage: %s file.mch\n", VERSION, argv[0]);
		return 1;
	}

	Assembler assembler;

	
	assembler.GenOpcode("AdD");


}



#ifndef MACHINE_ASSEMBLER_H
#define MACHINE_ASSEMBLER_H


#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <map>
#include <regex>


#define VERSION	"0.0.1"

#define OP_NOP		0x00
#define OP_			0x040000
#define OP_ADD		0x080000
/*#define OP_			0x0c0000
#define OP_			0x100000
#define OP_			0x140000
#define OP_			0x180000
#define OP_			0x1c0000
#define OP_			0x200000
#define OP_			0x240000
#define OP_			0x280000
#define OP_			0x2c0000
#define OP_			0x300000
#define OP_			0x340000
#define OP_			0x380000
#define OP_			0x3c0000
#define OP_			0x400000
#define OP_			0x440000
#define OP_			0x480000
#define OP_			0x4c0000
#define OP_			0x500000
#define OP_			0x540000
#define OP_			0x580000
#define OP_			0x5c0000
#define OP_			0x600000
#define OP_			0x640000
#define OP_			0x680000
#define OP_			0x6c0000
#define OP_			0x700000
#define OP_			0x740000
#define OP_			0x780000
#define OP_			0x7c0000
#define OP_			0x800000
#define OP_			0x840000
#define OP_			0x880000
#define OP_			0x8c0000
#define OP_			0x900000
#define OP_			0x940000
#define OP_			0x980000
#define OP_			0x9c0000
#define OP_			0xa00000
#define OP_			0xa40000
#define OP_			0xa80000
#define OP_			0xac0000
#define OP_			0xb00000
#define OP_			0xb40000
#define OP_			0xb80000
#define OP_			0xbc0000
#define OP_			0xc00000
#define OP_			0xc40000
#define OP_			0xc80000
#define OP_			0xcc0000
#define OP_			0xd00000
#define OP_			0xd40000
#define OP_			0xd80000
#define OP_			0xdc0000
#define OP_			0xe00000
#define OP_			0xe40000
#define OP_			0xe80000
#define OP_			0xec0000
#define OP_			0xf00000
#define OP_			0xf40000
#define OP_			0xf80000
#define OP_			0xfc0000*/


class Assembler {

public:


	std::regex instruction;




	std::map<std::string, uint32_t> opcode_list;

	Assembler();
	~Assembler();

	void Assemble();

	void PopulateOpcodes();
	uint32_t GenOpcode(std::string op);


private:


};

#endif
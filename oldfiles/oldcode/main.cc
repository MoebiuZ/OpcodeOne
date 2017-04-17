#include "opcodeone.h"



int main(int argc, char *argv[]) {


	if (argc < 2) {
		printf("%s", "No binary file provided");
		return 1;
	}

	// Defining an external memory of 0xffffff bytes
	//uint32_t memory[0xffffff + 1];
	uint32_t *memory;
	uint32_t *video_memory;

	memory = (uint32_t*) calloc(0xffffff + 1, sizeof(uint32_t));
	video_memory = (uint32_t*) calloc(0xffffff + 1, sizeof(uint32_t));


	// Set initial values to external memory

	// WR [A], B
	//memory[0] = 0x04; // Opcode WR and 1 bit Mode...
	//memory[1] = 0x08; // ...2 bit Mode (Indirect), and Registers
	

//	memory[0] = 0x030010;


	// RD A, 0x0000ff

//	memory[1] = 0x021000;
//	memory[2] = 0x0000ff;
/*
	memory[2] = 0x02; // Opcode RD and 1 bit Mode...
	memory[3] = 0x40; // ...2 bit Mode (Absolute) and Register

	memory[4] = 0x00; // Address...
	memory[5] = 0x00;
	memory[6] = 0xff;
*/

	//  Create instance of Machine
	OpcodeOne *opcodeone = new OpcodeOne();
	opcodeone->Reset();


	// "Plug" a memory to Machine address bus
	opcodeone->memory_bus = memory;
	opcodeone->video_bus = video_memory;

	// Initial values of registers A and B
	/*machine->reg[0] = 0x0000ff;
	machine->reg[1] = 0xdeadbe;*/

	uint8_t buffer[3];

	FILE *file = fopen(argv[1], "rb");

	fseek(file, 0, SEEK_END); // seek to end of file
	int filesize = ftell(file); // get current file pointer
	fseek(file, 0, SEEK_SET);

	
	int i = 0;
	for (i = 0; i < filesize; i++) {
		fread(&buffer, 1, 3, file);
		memory[i] = (buffer[0] << 16) | (buffer[1] << 8 ) | buffer[2];
	}

	
fflush(stdout);

	fclose(file);
	

		
	while (!opcodeone->halted) {
		opcodeone->Run(); // Run 1 instruction (Step)
	}

	/*printf("Reg A before WR: 0x%06x\n", machine->reg[0]);
	printf("Reg B before WR: 0x%06x\n\n", machine->reg[1]);*/


	


	
/*
	printf("Byte on memory address 0x0000ff: 0x%02x\n", memory[0x0000ff]);
	printf("Byte on memory address 0x000100: 0x%02x\n", memory[0x000100]);
	printf("Byte on memory address 0x000101: 0x%02x\n\n", memory[0x000101]);

	printf("Value (Word) on memory address 0x0000ff: 0x%06x\n\n", memory[0x0000ff]);


	printf("Reg A after RD: 0x%06x\n", machine->reg[0]);
	printf("Reg B after RD: 0x%06x\n", machine->reg[1]);	
*/
	
	free(memory);
	free(video_memory);
	delete opcodeone;
}
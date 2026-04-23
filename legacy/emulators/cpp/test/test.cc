#include "opcodeone.h"



int main(int argc, char *argv[]) {


	if (argc < 2) {
		printf("%s", "No binary file provided");
		return 1;
	}


	uint32_t *primary_memory;
	uint32_t *secondary_memory;

	primary_memory = (uint32_t*) calloc(0xffffff + 1, sizeof(uint32_t));
	secondary_memory = (uint32_t*) calloc(0xffffff + 1, sizeof(uint32_t));


	
	OpcodeOne *opcodeone = new OpcodeOne();
	opcodeone->Reset();

	// "Plug" a memory to Machine address bus
	opcodeone->primary_address_bus = primary_memory;
	opcodeone->secondary_address_bus = secondary_memory;

	

	uint8_t buffer[3];

	FILE *file = fopen(argv[1], "rb");

	fseek(file, 0, SEEK_END); // seek to end of file
	int filesize = ftell(file); // get current file pointer
	fseek(file, 0, SEEK_SET);

	
	int i = 0;
	for (i = 0; i < filesize; i++) {
		fread(&buffer, 1, 3, file);
		primary_memory[i] = (buffer[0] << 16) | (buffer[1] << 8 ) | buffer[2];
	}

	fclose(file);
	

		
	while (!opcodeone->halted) {
		opcodeone->Run(); // Run 1 instruction (Step)
	}


	free(primary_memory);
	free(secondary_memory);
	delete opcodeone;
}
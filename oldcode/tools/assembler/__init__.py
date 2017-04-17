import instructions
import functions
import re
import sys
import struct



# TODO: Add includes
# TODO: Fix MW VR & VW
# TODO: Not JMP/RET warnings
# TODO: Review code before data
# TODO: Add .org if needed

class Assembler(instructions.Assembler, functions.Assembler):


	REG = "\%(?:A|B|C|D|FL|SB|SP|PC)"
	REG_IND = "\[[ABCD]{1}\]"
	HEX = "0x[0-9a-fA-F]{1,6}"
	INT = "[0-9]{1,8}"
	ALPHANUMERIC = "\w+"
	OFFSET = "(?:([\+\-]{1})(" + INT + "|" + HEX + "|" + REG + ")){0,1}"
	NUMBER_INT = "#" + INT
	LABEL = "(?:(\w+)\:\s+){0,1}"
	spc = "\s+"
	sep = ",\s+"

	MAX_INT = 16777215  # 0xffffff
	OPCODES = { 
		"NOP": 	0x00,
		"HALT": 0x01,
		"MR": 	0x02,
		"MW": 	0x03,
		"VR":	0x04,
		"VW":	0x05,
		"LD":	0x06,
		"DBG":	0x07,
		"PUSH": 0x08,
		"POP":  0x09,
		"JMP":	0x0a,
		"RET":	0x0b,
		"CALL": 0x0c,
		"ARITH":0x0d
	}

	MODES = {
		# Addressing modes
		"INDIRECT": 		0x00,
		"INDIRECT+NEAR": 	0x01,
		"INDIRECT+REG": 	0x02,
		"INDIRECT+FAR": 	0x03,
		"INDIRECT-NEAR":	0x04,
		"INDIRECT-REG":		0x05,
		"INDIRECT-FAR":		0x06,
		"ABSOLUTE":			0x07,
		"ABSOLUTE+NEAR":	0x08,
		"ABSOLUTE+REG":		0x09,
		"ABSOLUTE+FAR":		0x0a,
		"ABSOLUTE-NEAR":	0x0b,
		"ABSOLUTE-REG":		0x0c,
		"ABSOLUTE-FAR":		0x0d,
		"unused1":			0x0e,
		"unused2":			0x0f,

		# Value modes
		"REGISTER":			0x00,
		"VALUE":			0x01
	}

	REGISTERS = {
		"%A": 		0x00,
		"%B": 		0x01,
		"%C": 		0x02,
		"%D": 		0x03,
		"unused1":	0x04,
		"unused2":	0x05,
		"unused3":	0x06,
		"unused4":	0x07,
		"unused5":	0x08,
		"unused6":	0x09,
		"unused7":	0x0a,
		"unused8":	0x0b,
		"%FL":		0x0c,
		"%SB":		0x0d,
		"%SP":		0x0e,
		"%PC":		0x0f
	}



	ARITH_FUNCS = {
		"ADD":	0x00,
		"SUB":	0x01,
		"DIV":	0x02,
		"MUL":	0x03,
		"IDIV":	0x04,
		"IMUL":	0x05
	}


	line_count = 1;
	instructions = []
	code = []
	data = []
	labelpass = []

	binary_file = []
		
	labels = dict()

	current_code_addr = 0
	current_data_addr = 0
	in_code = True

import functions
import re
import sys
import struct



class Assembler(functions.Assembler):

	line_count = 1;	# Line being parsed from .asm file

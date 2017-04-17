import re
import sys
import struct
import codecs


class REMatcher(object):
    def __init__(self, matchstring):
        self.matchstring = matchstring

    def match(self,regexp):
        self.rematch = re.match(regexp, self.matchstring, re.IGNORECASE)
        return bool(self.rematch)

    def group(self,i):
        return self.rematch.group(i)

    def groups(self):
       	return self.rematch.groups()





class Assembler:

	def checkInCode(self):
		if not self.in_code:
			print "Error in line " + str(self.line_count) + ": Instruction not in code section"
			exit()


	def checkInData(self):
		if self.in_code:
			print "Error in line " + str(self.line_count) + " Instruction not in data section"
			exit()



	def writefile(self, file):
		with open(file, "wb") as output:
			for byte in self.code:
				output.write(byte)
				
		output.close()


	def push24(self, num):
		b = bytearray(struct.pack('>I', num))
		self.code.append(chr(b[1]))
		self.code.append(chr(b[2]))
		self.code.append(chr(b[3]))

			
	def push8(self, num):
		self.code.append(chr(num))

	def newlabel(self, label):
		if label != None:
			if label in self.labels:
				self.printerror("Label " + m.group(2) + ": is duplicated")
					
			else:
				self.labels[label] = self.inst_addr

	def enqueuelabel(self, group, position):
	#	if relative:
	#		self.labelpass.append({ "label": group.strip("\(\)"), "position": self.inst_addr+1, "inst_address": self.inst_addr })
	#	else:
		self.labelpass.append({ "label": group.strip("\(\)"), "position": position })


	def printerror(self, text):
		print "Error in line " + str(self.line_count) + ": " + text
		exit()


	def parse_line(self, line):
		line = line.strip(" \t\n\r")
			
		# Remove comments if not inside string
		if re.match(".*?#.*", line):
			if not re.match("[^']*'[^#]*#[^']*", line):
				line = re.sub("\s*#.*", "", line)
		
		m = REMatcher(line.strip(" \t\n\r"))

		if line == '': # Empty line
			pass
			
		elif m.match("(\w+)\:\Z"): # Labels
			if m.group(1) in self.labels:
				self.printerror("Label \'" + m.group(1) + ":\'' is duplicated")
				
			else:
				self.labels[m.group(1)] = self.inst_addr 

		elif m.match("\.code\Z"): # Section.code
			self.in_code = True
					
		elif m.match("\.data\Z"): # Section .data
			self.in_code = False
				
		elif m.match(self.LABEL + "\.DS\s+(?:\'|\")(.+)(?:\'|\")\Z"): # Data String
			self.checkInData()
			self.newlabel(m.group(1))

			i = 0
			for char in m.group(2):
				self.push8( ord(char.encode('latin-1')) )
				i += 1
				if i % 3 == 0:
					self.inst_addr += 1
				
			self.push8(0x00) # String terminator
			i += 1

			# Fix word alignment
			while i % 3 != 0:
				self.push8(0x00)
				i += 1

			self.inst_addr += 1
								
		elif m.match(self.LABEL + "\.DW\s+(" + self.HEX + ")\Z"): # Data Word
			self.checkInData()
			self.newlabel(m.group(1))
			
			self.push24(int(m.group(2), 0))
			self.inst_addr += 1

		elif m.match(self.LABEL + "CALL\Z" + self.sep + "(" + self.HEX + "|\(" + self.ALPHANUMERIC + "\))"):
			self.newlabel(m.group(1))
			self.inst_CALL(m)

		elif m.match(self.LABEL + "LD" + self.spc + 
					"(" + self.REG + ")" + self.sep + 
					"(" + self.REG + "|" + self.HEX + "|" + self.INT + "|\(" + self.ALPHANUMERIC + "\))"
					):

			self.newlabel(m.group(1))
			self.inst_LD(m)


		elif m.match(self.LABEL + "DBG" + self.spc + "(" + self.REG + ")"):
			self.newlabel(m.group(1))
			self.inst_DBG(m)

		elif m.match(self.LABEL + "HALT\Z"):
			self.newlabel(m.group(1))
			self.inst_HALT(m)
		
		elif m.match(self.LABEL + "MR" + self.spc + 
						"(" + self.REG + ")" + self.sep + 
						"(\[" + self.REG + "\]|" + self.HEX + "|\(" + self.ALPHANUMERIC + "\))" + 
						self.OFFSET + "\Z"
					):

			self.newlabel(m.group(1))
			self.inst_MR(m)

		elif m.match(self.LABEL + "MW" + self.spc + "(\[" + self.REG + "\]|" + self.HEX + "|\(" + self.ALPHANUMERIC + "\))" + self.OFFSET + self.sep + "(" + self.REG + ")\Z"):
			self.newlabel(m.group(1))
			self.inst_MW(m)

		elif m.match(self.LABEL + "NOP\Z"):
			self.newlabel(m.group(1))
			self.inst_NOP(m)

		elif m.match(self.LABEL + "POP\Z" + self.sep + "(" + self.REG + ")"):
			self.newlabel(m.group(1))
			self.inst_POP(m)

		elif m.match(self.LABEL + "PUSH\Z" + self.sep + "(" + self.REG + ")"):
			self.newlabel(m.group(1))
			self.inst_PUSH(m)

		elif m.match(self.LABEL + "RET\Z"):
			self.newlabel(m.group(1))
			self.inst_RET(m)

		elif m.match(self.LABEL + "VR" + self.spc + "(" + self.REG + ")" + self.sep + "(\[" + self.REG + "\]|" + self.HEX + ")" + self.OFFSET + "\Z"):
			self.newlabel(m.group(1))
			self.inst_VR(m)

		elif m.match(self.LABEL + "VW" + self.spc + "(\[" + self.REG + "\]|" + self.HEX + ")" + self.OFFSET + self.sep + "(" + self.REG + ")\Z"):
			self.newlabel(m.group(1))
			self.inst_VW(m)

		else:
			self.printerror("Syntax error")
			
							
		self.line_count += 1

		if self.inst_addr > 0xffffff:
			print "Error: The assembled binary will excess the maximum size of 0xffffff words"
			exit()




	def second_pass(self):
		for item in self.labelpass:
			if item['label'] not in self.labels:
				print "Label '" + item['label'] + "' doesn't exist"
				exit()

			#if item['inst_address'] != None:
			#	b = bytearray(struct.pack('>I', self.labels[item['label']] - item['inst_address']))
			#else:
			b = bytearray(struct.pack('>I', self.labels[item['label']]))

			addr = item['position']*3
			self.code[addr] = chr(b[1])
			self.code[addr+1] = chr(b[2])
			self.code[addr+2] = chr(b[3])


	def assemble(self, file):
		self.line_count = 1;
		self.instructions = []
		self.code = []
		self.labelpass = []
		self.labels = dict()
		self.inst_addr = 0
		self.in_code = True

		with codecs.open(file, 'r', encoding='utf-8') as source_file:
			for line in source_file:
				self.parse_line(line)
		
		source_file.close()

		self.second_pass()

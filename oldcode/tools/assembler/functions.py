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
			for word in self.code:
				b = bytearray(struct.pack('>I', word[0]))
				output.write(chr(b[1]))
				output.write(chr(b[2]))
				output.write(chr(b[3]))
				
		output.close()


	def push_code24(self, word):
		self.code.append([word, self.current_code_addr])
		self.current_code_addr += 1

	
	def push_data24(self, word):
		self.data.append([word, self.current_data_addr])
		self.current_data_addr += 1


	def newlabel(self, label):
		if label != None:
			if label in self.labels:
				self.printerror("Label " + m.group(2) + ": is duplicated")
					
			else:
				if self.in_code:
					self.labels[label] = { 'address': self.current_code_addr, 'in_code': True }
					
				else:
					self.labels[label] = { 'address': self.current_data_addr, 'in_code': False }
					
					


	def enqueuelabel(self, group, position):
		self.labelpass.append({ "label": group.strip("()"), "position": position })


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
				if in_code:
					self.labels[m.group(1)] = self.current_code_addr
				else:
					self.labels[m.group(1)] = self.current_data_addr

		elif m.match("\.code\Z"): # Section.code
			self.in_code = True
					
		elif m.match("\.data\Z"): # Section .data
			self.in_code = False
				
		elif m.match(self.LABEL + "\.DS\s+(?:\'|\")(.+)(?:\'|\")\Z"): # Data String
			self.checkInData()
			self.newlabel(m.group(1))

			word = [None] * 3
			i = 0
			for char in m.group(2):
				word[i] = ord(char.encode('latin-1'))
			
				i += 1
				if i % 3 == 0:
					self.push_data24(word[0] << 16 | word[1] << 8 | word[2])
					i = 0
			
			# Null terminator and alignment
			if i % 3 == 0:
				self.push_data24(0x000000)
			else:
				while i % 3 != 0:
					word[i] = 0x00
					i += 1

				self.push_data24(word[0] << 16 | word[1] << 8 | word[2])



		elif m.match(self.LABEL + "\.DW\s+(" + self.HEX + ")\Z"): # Data Word
			self.checkInData()
			self.newlabel(m.group(1))
			
			self.push_data24(int(m.group(2), 0))



		# Instructions
		elif m.match(self.LABEL + "(ADD|SUB|MUL|DIV|IMUL|IDIV)" + self.spc + "(" + self.REG + ")" + self.sep + "(" + self.REG + ")" + self.sep + "(" + self.REG + ")\Z"):
			self.newlabel(m.group(1))
			self.inst_ARITH(m.group(2), m.group(3), m.group(4), m.group(5))

		elif m.match(self.LABEL + "CALL" + self.spc + "(\(" + self.HEX + "\)|\(" + self.ALPHANUMERIC + "\))\Z"):
			self.newlabel(m.group(1))
			self.inst_CALL(m.group(2).strip("()"))

		elif m.match(self.LABEL + "DBG" + self.spc + "(" + self.REG + "|\(" + self.HEX +"\)|\(" + self.REG + "\)|\(" + self.ALPHANUMERIC + "\))\Z"):
			self.newlabel(m.group(1))
			self.inst_DBG(m.group(2))

		elif m.match(self.LABEL + "HALT\Z"):
			self.newlabel(m.group(1))
			self.inst_HALT()

		
		elif m.match(self.LABEL + "LD" + self.spc + "(" + self.REG + ")" + self.sep + "(" + self.REG + "|" + self.HEX + "|" + self.INT + "|\(" + self.ALPHANUMERIC + "\))\Z"):
			self.newlabel(m.group(1))
			self.inst_LD(m.group(2), m.group(3).strip("()"))
		
		elif m.match(self.LABEL + "MR" + self.spc + "(" + self.REG + ")" + self.sep + "(\(" + self.REG + "\)|\(" + self.HEX + "\)|\(" + self.ALPHANUMERIC + "\))" + self.OFFSET + "\Z"):
			self.newlabel(m.group(1))
			self.inst_MR(m.group(2), m.group(3).strip("()"), m.group(4), m.group(5))

		elif m.match(self.LABEL + "MW" + self.spc + "(\(" + self.REG + "\)|\(" + self.HEX + "\)|\(" + self.ALPHANUMERIC + "\))" + self.OFFSET + self.sep + "(" + self.REG + ")\Z"):
			self.newlabel(m.group(1))
			self.inst_MW(m.group(2).strip("()"), m.group(3), m.group(4). m.group(5))

		elif m.match(self.LABEL + "NOP\Z"):
			self.newlabel(m.group(1))
			self.inst_NOP()

		elif m.match(self.LABEL + "POP\Z" + self.sep + "(" + self.REG + ")"):
			self.newlabel(m.group(1))
			self.inst_POP(m.group(2))

		elif m.match(self.LABEL + "PUSH\Z" + self.sep + "(" + self.REG + ")"):
			self.newlabel(m.group(1))
			self.inst_PUSH(m.group(2))

		elif m.match(self.LABEL + "RET\Z"):
			self.newlabel(m.group(1))
			self.inst_RET()

		elif m.match(self.LABEL + "VR" + self.spc + "(" + self.REG + ")" + self.sep + "(\(" + self.REG + "\)|\(" + self.HEX + "\)|\(" + self.ALPHANUMERIC + "\))" + self.OFFSET + "\Z"):
			self.newlabel(m.group(1))
			self.inst_VR(m.group(2), m.group(3).strip("()"), m.group(4), m.group(5))

		elif m.match(self.LABEL + "VW" + self.spc + "(\(" + self.REG + "\)|\(" + self.HEX + "\)|\(" + self.ALPHANUMERIC + "\))" + self.OFFSET + self.sep + "(" + self.REG + ")\Z"):
			self.newlabel(m.group(1))
			self.inst_VW(m.group(2).strip("()"), m.group(3), m.group(4). m.group(5))

		else:
			self.printerror("Syntax error")
			
							
		self.line_count += 1

		'''
		if self.current_code_addr > 0xffffff:
			print "Error: The assembled binary will excess the maximum size of 0xffffff words"
			exit()
		'''




	def second_pass(self):

		code_size = len(self.code)
		
		for item in self.labelpass:
			if item['label'] not in self.labels:
				print "Label '" + item['label'] + "' doesn't exist"
				exit()


			if self.labels[item['label']]['in_code']:
				self.code[item['position']][0] = self.labels[item['label']]['address']
			else:
				self.code[item['position']][0] = self.labels[item['label']]['address'] + code_size 

		self.code.extend(self.data)



	def assemble(self, file):
		self.line_count = 1;
		self.instructions = []
		self.code = []
		self.labelpass = []
		self.labels = dict()
		self.current_code_addr = 0
		self.current_data_addr = 0
		self.in_code = True

		with codecs.open(file, 'r', encoding='utf-8') as source_file:
			for line in source_file:
				self.parse_line(line)
		
		source_file.close()

		self.second_pass()

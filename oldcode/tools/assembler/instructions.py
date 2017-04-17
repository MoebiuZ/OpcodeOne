import re

class Assembler:




	def inst_ARITH(self, func, reg1 = "%A", reg2 = "%A", reg3 = "%A"):
		self.checkInCode()
		opcode = self.OPCODES['ARITH']

		self.push_code24((opcode << 16) | ( (self.ARITH_FUNCS[func] << 4) | self.REGISTERS[reg1] ) << 8 | (self.REGISTERS[reg2] << 4 | self.REGISTERS[reg3]))



	def inst_CALL(self, address):
		self.checkInCode()
		opcode = self.OPCODES['CALL']
		
		if re.match(self.HEX, address):
			addr = address
		elif re.match(self.ALPHANUMERIC, address):
			self.enqueuelabel(address, self.current_code_addr+1)
			addr = "0xdeadbe"

		self.push_code24(opcode << 16)
		self.push_code24(int(addr, 0))
		


	def inst_LD(self, dest, src):
		self.checkInCode()
		opcode = self.OPCODES['LD']
		mode = ''
		r_1 = '%A'
		r_2 = '%A'
		r_3 = '%A'
		value = ''
		
		r_1 = dest.upper()
		if re.match(self.REG, dest):
			mode = "REGISTER"
			r_src = src.upper()
		elif re.match(self.HEX + "|" + self.INT, src):
			mode = "VALUE"
			value = src
		elif re.match(self.ALPHANUMERIC, src):
			mode = "VALUE"
			self.enqueuelabel(src, self.current_code_addr+1)
			value = "0xdeadbe"
		
		self.push_code24((opcode << 16) | (((self.MODES[mode] << 4) | (self.REGISTERS[r_1])) << 8) | (self.REGISTERS[r_2] << 4))
		if value != '':
			self.push_code24(int(value, 0))



	def inst_DBG(self, src):
		self.checkInCode()
		opcode = self.OPCODES['DBG']
		r_1 = "%A"
		addr = ""

		value = src.strip("()")
		if re.match("\(" + self.REG + "\)", src):
			mode = "INDIRECT"
			r_1 = value
		elif re.match(self.REG, value):
			mode = "REGISTER"
			r_1 = value
		elif re.match(self.HEX, value):
			mode = "ABSOLUTE"
			addr = value
		elif re.match(self.ALPHANUMERIC, value):
			mode = "ABSOLUTE"
			self.enqueuelabel(value, self.current_code_addr+1)
			addr = "0xdeadbe"

		self.push_code24((opcode << 16) | (((self.MODES[mode] << 4) | (self.REGISTERS[r_1])) << 8) | 0x00)
		if addr != '':
			self.push_code24(int(addr, 0))



	def inst_HALT(self):
		self.checkInCode()
		opcode = self.OPCODES['HALT']
		self.push_code24(opcode << 16)


	def inst_MR(self, dest, src, sign, ofst):
		self.checkInCode()
		opcode = self.OPCODES['MR']
		mode = ''
		r_1 = '%A'
		r_2 = '%A'
		r_3 = '%A'
		addr = ''
		offset = ''
		near = False
							
		r_1 = dest.upper()
		if re.match(self.REG, src, re.IGNORECASE):
			mode += "INDIRECT"
			r_2 = src.upper()
		elif re.match(self.HEX, src):
			mode += "ABSOLUTE"
			addr = src
		elif re.match(self.ALPHANUMERIC, src):
			mode = "ABSOLUTE"
			self.enqueuelabel(src, self.current_code_addr+1)
			offset = "0xdeadbe"

		if (sign != None): # There is offset
			mode += sign
			if re.match(self.REG, ofst, re.IGNORECASE):
				mode += "REG"
				r_3 = ofst.upper()
			elif re.match(self.INT, ofst):
				if int(ofst, 0) <= 15:
					mode += "NEAR"
					near = True
					r_3 = ofst
				elif int(ofst, 0) > self.MAX_INT:
					self.printerror("Max. offset 16777215")
				else:
					mode += "FAR"
					offset = ofst
			else:
				mode += "FAR"
				offset = ofst

		self.push_code24((opcode << 16) | (((self.MODES[mode] << 4) | self.REGISTERS[r_1]) << 8) | ((self.REGISTERS[r_2] << 4) | (int(r_3) if near else self.REGISTERS[r_3])))
		if addr != '':
			self.push_code24(int(addr, 0))
		if offset != '':
			self.push_code24(int(offset, 0))



	def inst_MW(self, dest, sign, ofst, src):
		self.checkInCode()
		opcode = self.OPCODES['MW']
		mode = ''
		r_1 = '%A'
		r_2 = '%A'
		r_3 = '%A'
		addr = ''
		offset = ''
		near = False
					
		r_2 = src.upper()
		if re.match(self.REG, dest, re.IGNORECASE):
			mode += "INDIRECT"
			r_1 = dest.upper()
		elif re.match(self.HEX, dest):
			mode += "ABSOLUTE"
			addr = dest
		elif re.match(self.ALPHANUMERIC, dest):
			mode = "ABSOLUTE"
			self.enqueuelabel(dest, self.current_code_addr+1)
			offset = "0xdeadbe"

		if (sign != None): # There is offset
			mode += sign
			if re.match(self.REG, ofst, re.IGNORECASE):
				mode += "REG"
				r_3 = ofst.upper()
			elif re.match(self.INT, ofst):
				if int(ofst, 0) <= 15:
					mode += "NEAR"
					near = True
					r_3 = ofst
				elif int(ofst, 0) > self.MAX_INT:
					self.printerror("Max. offset 16777215")
				else:
					mode += "FAR"
					offset = ofst
			else:
				mode += "FAR"
				offset = ofst

		self.push_code24((opcode << 16) | (((self.MODES[mode] << 4) | self.REGISTERS[r_1]) << 8) | ((self.REGISTERS[r_2] << 4) | (int(r_3) if near else self.REGISTERS[r_3])))
		if addr != '':
			self.push_code24(int(addr, 0))
		if offset != '':
			self.push_code24(int(offset, 0))



	def inst_NOP(self):
		self.checkInCode()
		opcode = self.OPCODES['NOP']
		self.push_code24(opcode << 16)



	def inst_POP(self, register):
		self.checkInCode()
		opcode = self.OPCODES['POP']
		self.push_code24((opcode << 16) | (self.REGISTERS[register] << 8))
		


	def inst_PUSH(self, register):
		self.checkInCode()
		opcode = self.OPCODES['PUSH']
		self.push_code24((opcode << 16) | (self.REGISTERS[register] << 8))
		


	def inst_RET(self):
		self.checkInCode()
		opcode = self.OPCODES['RET']
		self.push_code24(opcode << 16)



	def inst_VR(self, dest, src, sign, ofst):
		self.checkInCode()
		opcode = self.OPCODES['VR']
		mode = ''
		r_1 = '%A'
		r_2 = '%A'
		r_3 = '%A'
		addr = ''
		offset = ''
		near = False
		
						
		r_1 = dest.upper()
		if re.match(self.REG, src, re.IGNORECASE):
			mode += "INDIRECT"
			r_2 = src.upper()
		elif re.match(self.HEX, src):
			mode += "ABSOLUTE"
			addr = src
		elif re.match(self.ALPHANUMERIC, src):
			mode = "ABSOLUTE"
			self.enqueuelabel(src, self.current_code_addr+1)
			offset = "0xdeadbe"

		if (sign != None): # There is offset
			mode += sign
			if re.match(self.REG, ofst, re.IGNORECASE):
				mode += "REG"
				r_3 = ofst.upper()
			elif re.match(self.INT, ofst):
				if int(ofst, 0) <= 15:
					mode += "NEAR"
					near = True
					r_3 = ofst
				elif int(ofst, 0) > self.MAX_INT:
					self.printerror("Max. offset 16777215")
				else:
					mode += "FAR"
					offset = ofst
			else:
				mode += "FAR"
				offset = ofst
		
		self.push_code24((opcode << 16) | (((self.MODES[mode] << 4) | self.REGISTERS[r_1]) << 8) | ((self.REGISTERS[r_2] << 4) | (int(r_3) if near else self.REGISTERS[r_3])))
		if addr != '':
			self.push_code24(int(addr, 0))
		if offset != '':
			self.push_code24(int(offset, 0))



	def inst_VW(self, dest, sign, ofst, src):
		self.checkInCode()
		opcode = self.OPCODES['VW']
		mode = ''
		r_1 = '%A'
		r_2 = '%A'
		r_3 = '%A'
		addr = ''
		offset = ''
		near = False
					
		r_2 = src.upper()
		if re.match(self.REG, dest, re.IGNORECASE):
			mode += "INDIRECT"
			r_1 = dest.upper()
		elif re.match(self.HEX, dest):
			mode += "ABSOLUTE"
			addr = dest
		elif re.match(self.ALPHANUMERIC, dest):
			mode = "ABSOLUTE"
			self.enqueuelabel(dest, self.current_code_addr+1)
			offset = "0xdeadbe"

		if (sign != None): # There is offset
			mode += sign
			if re.match(self.REG, ofst, re.IGNORECASE):
				mode += "REG"
				r_3 = ofst.upper()
			elif re.match(self.INT, ofst):
				if int(ofst, 0) <= 15:
					mode += "NEAR"
					near = True
					r_3 = ofst
				elif int(ofst, 0) > self.MAX_INT:
					self.printerror("Max. offset 16777215")
				else:
					mode += "FAR"
					offset = ofst
			else:
				mode += "FAR"
				offset = ofst

		self.push_code24((opcode << 16) | (((self.MODES[mode] << 4) | self.REGISTERS[r_1]) << 8) | ((self.REGISTERS[r_2] << 4) | (int(r_3) if near else self.REGISTERS[r_3])))
		if addr != '':
			self.push_code24(int(addr, 0))
		if offset != '':
			self.push_code24(int(offset, 0))
